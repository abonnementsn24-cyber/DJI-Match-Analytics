# EMDJI Match Analytics

**Football Intelligence & Predictive Analytics**

Plateforme d'**analyse statistique** de matchs de football : probabilités de
résultat (1/N/2), buts attendus, BTTS, scores les plus probables et indice de
confiance — calculés par cinq modèles indépendants et comparables, mesurés
objectivement par un moteur de backtesting chronologique.

> **Ceci n'est pas un outil de pari.** Aucune fonctionnalité de mise, aucune
> connexion à un bookmaker, aucune cote, aucune recommandation financière.
> Une prédiction n'est jamais présentée comme une certitude ; quand
> l'historique est insuffisant, l'application l'affiche explicitement
> (`"Données insuffisantes pour produire une estimation fiable"`) plutôt que
> d'inventer un chiffre.

## Sommaire

- [Architecture](#architecture)
- [Démarrage rapide](#démarrage-rapide)
- [Variables d'environnement](#variables-denvironnement)
- [Découverte et synchronisation des données](#découverte-et-synchronisation-des-données)
- [Base de données et migrations](#base-de-données-et-migrations)
- [API](#api)
- [Modèles statistiques](#modèles-statistiques)
- [Backtesting](#backtesting)
- [Tests](#tests)
- [Déploiement](#déploiement)
- [Mode démo vs données réelles](#mode-démo-vs-données-réelles)
- [Ce que l'application ne fait jamais](#ce-que-lapplication-ne-fait-jamais)

## Architecture

```
emdji-match-analytics/
  frontend/            Next.js (App Router) + TypeScript + Tailwind CSS
    src/app/             Pages (dashboard, matches, competitions, teams, models, backtesting, history, settings)
    src/components/      Composants réutilisables (cartes de match, graphiques, nav)
    src/lib/              Client API, formatage, types TypeScript
  backend/
    app/
      api/v1/             Routes FastAPI
      core/               Configuration, sécurité, logs
      db/                 Session SQLAlchemy, base déclarative
      models/             Modèles ORM (competitions, matches, predictions, ...)
      schemas/            (réservé) schémas Pydantic additionnels
      providers/          Interface FootballProvider + implémentation football-data.org
      services/           Découverte, synchronisation, normalisation, backtesting, standings
      analytics/          Elo, Poisson, feature engineering, calibration, moteur de replay chronologique
      ml/                 Modèle 5 (classification HOME/DRAW/AWAY), entraînement, prédiction
      jobs/                (réservé) tâches planifiées
      cli.py               Commandes d'administration (discover, sync, ...)
    alembic/              Migrations de base de données
    tests/                 Suite de tests pytest
  docker/                 Dockerfiles backend/frontend
  docs/
    MODELS.md              Description mathématique des modèles
    DATA_PIPELINE.md        Pipeline complet API → DB → features → prédiction → historique
  scripts/
    seed_demo_data.py       Génère des données fictives multi-continents pour le mode démo
  docker-compose.yml
  .env.example
```

Le moteur statistique ne dépend **jamais** directement de football-data.org :
toute la couche `providers/` est abstraite derrière l'interface
`FootballProvider`, ce qui permet d'ajouter un second fournisseur (API-Football,
SportMonks, ...) sans toucher au reste du code.

## Démarrage rapide

### Backend (sans Docker, SQLite, mode démo)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Crée le schéma (SQLite par défaut)
alembic upgrade head

# Génère des données de démonstration (fictives, multi-continents)
python ../scripts/seed_demo_data.py

# Calcule Elo historique + prédictions des 5 modèles + évaluation
python -c "
from app.db.session import SessionLocal
from app.services.prediction_service import generate_all_predictions
from app.services.evaluation_service import evaluate_finished_predictions
db = SessionLocal()
print(generate_all_predictions(db))
print('evaluated:', evaluate_finished_predictions(db))
db.close()
"

uvicorn app.main:app --reload
```

L'API tourne sur `http://127.0.0.1:8000` (documentation interactive automatique
sur `/docs`, spec OpenAPI sur `/openapi.json`).

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # ou créez .env.local avec NEXT_PUBLIC_API_BASE_URL
npm run dev
```

Le dashboard tourne sur `http://127.0.0.1:3000` et redirige vers `/dashboard`.

### Avec Docker Compose (PostgreSQL inclus)

```bash
cp .env.example .env   # ajustez FOOTBALL_DATA_API_KEY si vous en avez une
docker compose up --build
```

- Backend : `http://localhost:8000`
- Frontend : `http://localhost:3000`
- PostgreSQL : port 5432 (volume persistant `postgres_data`)

Le conteneur backend exécute automatiquement `alembic upgrade head` au
démarrage. Semez les données de démo ou synchronisez de vraies données ensuite
via `docker compose exec backend python ../scripts/seed_demo_data.py` (ou la
CLI `discover`/`sync` ci-dessous).

## Variables d'environnement

Voir [`.env.example`](.env.example) pour la liste complète et commentée.
Principales variables :

| Variable | Rôle |
| --- | --- |
| `DATABASE_URL` | SQLite (dev) ou PostgreSQL (prod). Jamais de secret en dur dans le code. |
| `FOOTBALL_DATA_API_KEY` | Active les données réelles. Vide = mode démo automatique. |
| `ADMIN_API_TOKEN` | Protège `/api/v1/admin/*`. Vide en dev, obligatoire en prod. |
| `ELO_*`, `ENSEMBLE_WEIGHT_*`, `FORM_WINDOW_*` | Paramètres du moteur, configurables sans changer le code. |
| `NEXT_PUBLIC_API_BASE_URL` | URL de l'API vue par le serveur Next.js. |

## Découverte et synchronisation des données

L'application ne contient **aucune liste figée** de championnats. La
découverte interroge le fournisseur en direct :

```bash
# Découvre toutes les compétitions actuellement exposées par football-data.org
# (fonctionne même sans clé API — l'endpoint /v4/competitions est public en lecture)
python -m app.cli discover

# Synchronise saisons + équipes + matchs d'une compétition (nécessite une clé API)
python -m app.cli sync PL 2025

# Génère les prédictions des 5 modèles pour les matchs qui en manquent
python -m app.cli generate-predictions PL

# Met à jour résultat réel / correct / métriques des matchs désormais terminés
python -m app.cli evaluate
```

Les mêmes actions sont exposées en HTTP, protégées par `ADMIN_API_TOKEN` :
`POST /api/v1/admin/discover`, `/sync`, `/generate-predictions`, `/evaluate`,
`/train-ml`.

Testé en conditions réelles (sans clé API) : la découverte remonte **189
compétitions réelles réparties sur 62 pays/zones**, couvrant l'Afrique,
l'Europe, l'Amérique du Sud, l'Amérique du Nord, l'Asie, l'Océanie et les
compétitions internationales — directement depuis l'API, sans aucune liste
codée en dur dans ce dépôt. La synchronisation des équipes/matchs/classements
nécessite en revanche une clé API valide (plan gratuit ou payant selon la
compétition).

## Base de données et migrations

13 tables (voir `backend/app/models/`) : `countries`, `competitions`,
`seasons`, `teams`, `competition_season_teams`, `matches`, `team_match_stats`,
`elo_history`, `predictions`, `model_metrics`, `feature_snapshots`,
`provider_team_mappings`, `provider_competition_mappings`.

```bash
cd backend
alembic revision --autogenerate -m "description du changement"
alembic upgrade head
```

## API

Toutes les routes sont préfixées `/api/v1`. Documentation interactive
complète sur `/docs`. Principaux endpoints :

| Endpoint | Description |
| --- | --- |
| `GET /matches/today`, `/matches/upcoming` | Matchs du jour / à venir, avec prédiction embarquée |
| `GET /matches?tab=today\|tomorrow\|week\|finished` | Match Center filtrable (continent, pays, compétition, équipe) |
| `GET /matches/{id}` | Détail d'un match |
| `GET /matches/{id}/prediction?model=ensemble&compare=true` | Prédiction (un modèle, ou comparaison des 5) |
| `GET /matches/{id}/h2h` | Confrontations directes + Elo des deux équipes |
| `GET /teams/{id}`, `/teams/{id}/form` | Fiche équipe, forme récente domicile/extérieur |
| `GET /competitions` | Arborescence continent → pays → compétitions (découverte automatique) |
| `GET /competitions/{id}/standings\|/matches\|/teams` | Classement, calendrier, effectif |
| `GET /countries/{id}` | Compétitions d'un pays |
| `GET /models`, `/models/metrics` | Liste des modèles + métriques de backtesting |
| `GET /backtesting` | Comparaison des modèles (filtrable compétition/pays/continent/saison/confiance) |
| `POST /admin/*` | Découverte, synchronisation, génération de prédictions, évaluation, entraînement ML (protégé) |

## Modèles statistiques

Voir [`docs/MODELS.md`](docs/MODELS.md) pour le détail mathématique. Résumé :

| Modèle | Principe |
| --- | --- |
| **Poisson Basic** | Force d'attaque/défense (domicile/extérieur séparés) sur tout l'historique, vs. moyenne de ligue. |
| **Poisson Form** | Même principe sur les 10 derniers matchs seulement. |
| **Elo Model** | Buts attendus dérivés uniquement de l'écart de rating Elo chronologique. |
| **Ensemble** | Moyenne pondérée des trois précédents (poids configurables), ajustée par H2H et repos. |
| **Machine Learning** | Classification HOME/DRAW/AWAY (HistGradientBoosting), split chronologique train/val/test — jamais de split aléatoire sur données temporelles. |

Chaque prédiction inclut un **indice de confiance** (Très faible → Très
élevée, ou "Données insuffisantes") basé sur l'écart entre probabilités, le
volume de données, la convergence entre modèles et — quand disponible — la
calibration historique du modèle.

## Backtesting

Le moteur de replay chronologique (`app/analytics/replay_engine.py`) rejoue
**tous** les matchs stockés dans l'ordre, match par match : à chaque match, il
calcule les features et génère une prédiction en n'utilisant que les données
disponibles *avant* ce match, puis met à jour l'état (Elo, forme, H2H) avec le
résultat réel. C'est la même fonction qui alimente à la fois les prédictions
en direct et le backtesting — il n'existe pas deux chemins de code
divergents, donc pas de risque que le backtest mesure autre chose que ce que
l'application affiche réellement.

`GET /api/v1/backtesting` renvoie, par modèle : nombre de matchs évalués,
accuracy, précision/recall/F1 par classe, matrice de confusion, Brier score,
log loss, courbe et erreur de calibration — et désigne automatiquement le
modèle le mieux calibré (**Brier score le plus bas**, jamais l'accuracy
seule).

## Tests

```bash
cd backend
pytest
```

Couvre : Elo, Poisson, modèles combinés, absence de fuite de données
(chronologie stricte), calibration, backtesting, découverte/synchronisation
(fournisseur simulé), et l'API.

```bash
cd frontend
npm run build   # build de production + vérification TypeScript
npx eslint .    # lint
```

## Déploiement

`docker-compose.yml` fournit une stack complète (PostgreSQL + backend +
frontend) prête pour un premier déploiement. Pour un déploiement séparé :

- **Backend** : n'importe quel hébergeur Python (conteneur, PaaS) exécutant
  `alembic upgrade head` puis `uvicorn app.main:app`. Nécessite `DATABASE_URL`
  (PostgreSQL recommandé) et éventuellement `FOOTBALL_DATA_API_KEY` +
  `ADMIN_API_TOKEN`.
- **Frontend** : `npm run build && npm run start`, ou toute plateforme
  compatible Next.js. Nécessite `NEXT_PUBLIC_API_BASE_URL` pointant vers le
  backend.
- **Jobs planifiés** (§19 du cahier des charges) : la synchronisation
  matinale, le rafraîchissement pré-match, l'évaluation post-match et le
  recalcul nocturne des métriques sont exposés comme fonctions Python pures
  (`services/*`) et comme endpoints admin — brancher un scheduler (cron,
  APScheduler, Celery beat) dessus ne nécessite aucun changement de code. Non
  câblé par défaut dans cette V1 pour rester simple à déployer.

## Mode démo vs données réelles

Sans `FOOTBALL_DATA_API_KEY`, l'application tourne automatiquement en **mode
démo** : `scripts/seed_demo_data.py` charge des matchs entièrement fictifs
(compétitions préfixées `DEMO -`) répartis sur trois continents, pour que
toutes les fonctionnalités soient démontrables sans clé API. Le frontend
affiche un bandeau **"Mode démo"** ou **"Données réelles"** selon le cas
(`GET /api/v1/system/status`), pour qu'il n'y ait jamais de confusion entre
les deux.

## Ce que l'application ne fait jamais

Aucune connexion à un bookmaker, aucune automatisation de pari, aucun montant
suggéré, aucune cote affichée, aucune prédiction présentée comme certaine ou
garantie, aucune donnée inventée pour compenser un historique insuffisant, et
aucune fuite d'information future dans une prédiction historique (voir
`docs/DATA_PIPELINE.md` §Data leakage et `tests/test_no_leakage.py`).
