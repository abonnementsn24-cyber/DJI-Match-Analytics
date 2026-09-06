# DJI Match Analytics

Outil d'**analyse statistique** de matchs de football : probabilités de
résultat (victoire/nul/défaite), buts attendus, probabilité que les deux
équipes marquent (BTTS), et scores les plus probables — calculés à partir
d'un modèle **Poisson + Elo** sur des données historiques.

> **Ce n'est pas un outil de pari.** Il ne propose aucune fonction de mise,
> aucune connexion à un bookmaker, et n'annonce jamais un résultat comme
> certain. Quand les données sont insuffisantes, l'outil l'affiche
> explicitement plutôt que de fabriquer une prédiction.

## Comment ça marche

```
Données de matchs → Elo + statistiques de forme/domicile-extérieur/H2H
                  → buts attendus (3 modèles) → matrice de Poisson
                  → probabilités 1/N/2, BTTS, scores
```

Trois modèles sont calculés et comparables côte à côte, du plus simple au
plus complet :

| Modèle | Principe |
| --- | --- |
| `simple` | Force d'attaque/défense de chaque équipe (domicile/extérieur séparés) sur tout l'historique, vs. moyenne de ligue. |
| `form` | Même principe, mais sur les 10 derniers matchs seulement (réagit plus vite à une bonne/mauvaise série). |
| `combined` | Moyenne du modèle Elo et du modèle de forme, ajustée par la confrontation directe (H2H) historique. C'est le modèle utilisé par défaut. |

1. **Elo** : chaque match met à jour la force estimée des deux équipes
   (avantage du terrain inclus), en pondérant plus fortement les victoires
   larges.
2. **Statistiques par équipe** : matchs joués, buts marqués/encaissés à
   domicile et à l'extérieur, forme sur les 10 derniers matchs, et
   historique des confrontations directes (H2H) — tout est reconstruit en
   rejouant les matchs stockés dans l'ordre chronologique.
3. **Poisson** : les buts attendus (selon le modèle choisi) alimentent une
   matrice de scores Poisson, avec une légère correction Dixon-Coles sur
   les scores faibles (0-0, 1-0, 0-1, 1-1).
4. **Décision** : si une équipe a joué moins de 5 matchs, l'API renvoie
   `"reliable": false` avec une raison plutôt qu'une prédiction fantaisiste.
   Un indice de confiance (faible/moyenne/élevée) est renvoyé sinon, basé
   sur la taille de l'historique disponible.
5. **Backtesting** : `/backtest` (et `/backtest/compare` pour les 3
   modèles) rejoue tous les matchs stockés en chronologique (sans
   anticipation) et mesure le Brier score, le log loss, la précision et
   une courbe de calibration — la priorité avant de faire confiance aux
   probabilités affichées. `/backtest/compare` indique aussi quel modèle
   est le mieux calibré (Brier score le plus bas) sur l'historique
   disponible, plutôt que de supposer que le plus complexe est le
   meilleur.

## Structure du projet

```
backend/    API FastAPI (moteur Poisson+Elo, connecteur football-data.org)
frontend/   Tableau de bord web statique (HTML/CSS/JS, aucun build requis)
scripts/    Script de génération de données de démonstration
```

## Démarrer le backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Données de démo (matchs fictifs) pour tester sans clé API :
python ../scripts/seed_sample_data.py

uvicorn app.main:app --reload
```

L'API tourne sur `http://127.0.0.1:8000` (documentation interactive sur
`/docs`). Par défaut elle utilise une base SQLite locale
(`backend/match_analytics.db`) ; définissez `DATABASE_URL` (ex. une URL
PostgreSQL) pour utiliser une autre base.

### Endpoints principaux

| Endpoint | Description |
| --- | --- |
| `GET /predict?home=X&away=Y&model=combined` | Prédiction complète pour un match (`model` : `simple`, `form` ou `combined`) |
| `GET /predict/compare?home=X&away=Y` | Prédiction des 3 modèles côte à côte |
| `GET /teams` | Liste des équipes connues |
| `GET /teams/{name}/stats` | Statistiques d'une équipe (domicile/extérieur, forme récente) |
| `GET /h2h?team_a=X&team_b=Y` | Historique des confrontations directes entre deux équipes |
| `GET /standings?competition=X` | Classement calculé à partir des matchs stockés |
| `GET /backtest?model=combined` | Rapport de calibration (Brier score, log loss, précision, courbe de calibration) pour un modèle |
| `GET /backtest/compare` | Backtest des 3 modèles + indication du mieux calibré |
| `POST /data/import/football-data?competition=PL` | Importe les matchs terminés depuis football-data.org |

### Importer de vraies données

Créez une clé gratuite sur [football-data.org](https://www.football-data.org/),
puis :

```bash
export FOOTBALL_DATA_API_KEY=votre_cle
curl -X POST "http://127.0.0.1:8000/data/import/football-data?competition=PL&season=2023"
```

## Démarrer le tableau de bord

Le dossier `frontend/` est du HTML/CSS/JS statique, sans dépendance ni
build :

```bash
cd frontend
python3 -m http.server 8080
```

Ouvrez `http://127.0.0.1:8080`, renseignez l'URL de l'API (par défaut
`http://127.0.0.1:8000`) et deux noms d'équipes.

## Tests

```bash
cd backend
pytest
```

## Feuille de route

- Ajouter les grands championnats et compétitions africaines/internationales
  via le connecteur football-data.org.
- Intégrer des données de composition/blessures quand disponibles.
- Étendre le moteur avec un modèle ML complémentaire (ensemble avec les
  modèles existants plutôt qu'un remplacement).
- Enregistrer chaque prédiction générée et la comparer au résultat réel une
  fois le match joué, pour suivre la calibration dans le temps plutôt que de
  ne la mesurer que rétrospectivement via `/backtest`.
- Tableau de bord des matchs du jour/à venir, avec pages détaillées par
  match et historique des prédictions passées.
