# Pipeline de données

```
Fournisseur (football-data.org, ...)
   │  FootballProvider (interface abstraite)
   ▼
Découverte (CompetitionDiscoveryService)
   │  liste des compétitions/aires exposées par le fournisseur — jamais une liste codée en dur
   ▼
Normalisation (normalization_service)
   │  Provider*Mapping : (provider, provider_id) → entité canonique
   │  jamais de fusion automatique par ressemblance de nom
   ▼
Synchronisation (sync_service)
   │  competitions → seasons → teams → matches (idempotent, upsert par provider_id)
   ▼
Base de données (PostgreSQL en prod, SQLite en dev)
   │  competitions, seasons, teams, competition_season_teams, matches,
   │  team_match_stats, elo_history, predictions, model_metrics, feature_snapshots
   ▼
Feature engineering (analytics/replay_engine.py, analytics/team_state.py, analytics/elo.py)
   │  rejeu chronologique : Elo, forme (générale + domicile/extérieur, 5/10 matchs),
   │  H2H (3-5 dernières confrontations), repos — toujours "avant le match"
   ▼
Prédiction (analytics/model_variants.py, ml/predict.py)
   │  5 modèles indépendants → probabilités 1/N/2, buts attendus
   ▼
Historique (predictions, immuable)
   │  écrite une fois avant le coup d'envoi, verrouillée (`locked`) au coup d'envoi
   ▼
Résultat réel (evaluation_service, dès que le match passe à FINISHED)
   │  met à jour UNIQUEMENT actual_result / correct / brier_score / log_loss
   ▼
Métriques (backtest_service, model_metrics)
   │  agrégation par modèle, compétition, pays, continent, saison, confiance
```

## Étape par étape

### 1. Découverte

`GET /v4/competitions` (et `/v4/areas`) chez football-data.org sont
accessibles **sans clé API** — vérifié en conditions réelles : 189
compétitions, 62 pays/zones, tous continents représentés. `discover_competitions()`
diffuse cette liste dans `competitions` via `ProviderCompetitionMapping`,
sans jamais supposer une liste de championnats à l'avance. Lancer
`python -m app.cli discover` (ou `POST /api/v1/admin/discover`) régulièrement
suffit à faire apparaître une nouvelle compétition sans déploiement.

### 2. Normalisation

Un club peut être nommé différemment selon le fournisseur ("Manchester
United" vs "Man United"). `ProviderTeamMapping`/`ProviderCompetitionMapping`
associent `(provider, provider_id)` → ligne canonique (`Team`/`Competition`).
La clé de correspondance est toujours l'identifiant du fournisseur, jamais une
comparaison de chaînes de caractères — deux équipes ne sont jamais fusionnées
automatiquement sur la seule ressemblance de leur nom.

### 3. Synchronisation

`sync_service.sync_competition()` enchaîne : saisons → équipes de la saison
courante (ou demandée) → matchs (programmés et terminés). Chaque appel est
idempotent : les matchs déjà connus (`provider_id` unique) sont mis à jour
(score, statut) plutôt que dupliqués. Nécessite `FOOTBALL_DATA_API_KEY` (les
endpoints équipes/matchs/classements de football-data.org renvoient 403 sans
clé — vérifié en conditions réelles) ; sans clé, l'endpoint
`POST /api/v1/admin/sync` renvoie explicitement 409 plutôt que d'échouer
silencieusement.

### 4. Feature engineering — **sans fuite de données**

C'est le point le plus sensible du pipeline (§24 du cahier des charges) :
**pour une prédiction concernant un match du 15 septembre 2026, aucune
donnée postérieure au 15 septembre 2026 (avant le coup d'envoi) ne doit être
utilisée** — ni pour l'Elo, ni pour le classement, ni pour la forme, ni pour
le H2H, ni pour l'entraînement du modèle ML.

`analytics/replay_engine.py` garantit cette contrainte structurellement : un
seul générateur (`iter_matches_chronologically`) rejoue **tous** les matchs
dans l'ordre chronologique global (toutes compétitions confondues, car l'Elo
et la forme sont des propriétés d'une équipe, pas d'une compétition). Pour
chaque match, l'état (`LeagueState`, `EloState`) exposé au moment de la
prédiction reflète strictement ce qui est connu *avant* ce match — la mise à
jour avec le résultat du match n'est appliquée qu'après. Les prédictions
**et** l'entraînement du modèle ML consomment ce même générateur : il n'existe
pas un second chemin de code qui recalculerait les features différemment
(donc pas de risque de divergence entre "ce qui est mesuré en backtest" et
"ce que l'utilisateur voit réellement").

`tests/test_no_leakage.py` vérifie explicitement cette propriété : la
prédiction d'un match ne change pas si l'on ajoute des matchs *postérieurs*
à la base, et l'Elo d'une équipe avant son premier match reste la valeur
initiale par défaut.

### 5. Prédiction

Les 5 modèles (`analytics/model_variants.py` + `ml/predict.py`) consomment le
même état pré-match. `Prediction` est créée avec `locked=False` tant que le
coup d'envoi (`utc_date`) n'est pas passé — une prédiction sur un match futur
peut donc être rafraîchie si de nouvelles données arrivent avant le match
(nouvelle forme, blessure resynchronisée, etc.), mais **jamais après le coup
d'envoi**.

### 6. Historique immuable

Dès que `utc_date ≤ maintenant`, `locked=True` : les colonnes de probabilité,
buts attendus, confiance et résultat prédit ne sont plus jamais réécrites.

### 7. Résultat réel

`evaluation_service.evaluate_finished_predictions()` compare, pour chaque
prédiction dont le match est désormais `FINISHED`, le résultat prédit au
résultat réel, et **met à jour uniquement** `actual_result`, `correct`,
`brier_score`, `log_loss`. Aucune autre colonne n'est touchée — la
prédiction originale reste consultable telle qu'elle était avant le match.

### 8. Métriques et backtesting

`backtest_service.py` agrège la table `predictions` (jamais un recalcul) :
accuracy, précision/recall/F1 par classe, matrice de confusion, Brier score,
log loss, courbe et erreur de calibration — globalement ou filtré par
compétition/pays/continent/saison/niveau de confiance. Le modèle "le
meilleur" est toujours désigné par le **Brier score le plus bas**, jamais
par l'accuracy seule (une accuracy de 55 % avec des probabilités mal
calibrées vaut moins qu'une accuracy de 50 % bien calibrée).

## Qualité des données

`quality_service.recompute_data_quality()` note chaque compétition A/B/C/D
selon le nombre de matchs terminés synchronisés (≥200 / ≥50 / ≥10 / moins).
Le moteur de prédiction refuse explicitement d'estimer un match si l'une des
deux équipes a moins de `MIN_MATCHES_FOR_PREDICTION` (défaut 5) matchs connus
— jamais d'invention de données manquantes.
