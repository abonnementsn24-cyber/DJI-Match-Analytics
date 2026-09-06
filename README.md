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
Données de matchs → Elo (force des équipes) → Poisson (buts attendus)
                  → matrice des scores → probabilités 1/N/2, BTTS, scores
```

1. **Elo** : chaque match met à jour la force estimée des deux équipes
   (avantage du terrain inclus), en pondérant plus fortement les victoires
   larges.
2. **Poisson** : l'écart de rating Elo entre les deux équipes ajuste leurs
   buts attendus autour de moyennes de ligue, avec une légère correction
   Dixon-Coles sur les scores faibles (0-0, 1-0, 0-1, 1-1).
3. **Décision** : si une équipe a joué moins de 5 matchs, l'API renvoie
   `"reliable": false` avec une raison plutôt qu'une prédiction fantaisiste.
   Un indice de confiance (faible/moyenne/élevée) est renvoyé sinon, basé
   sur la taille de l'historique disponible.
4. **Backtesting** : `/backtest` rejoue tous les matchs stockés en
   chronologique (sans anticipation) et mesure le Brier score et la
   précision du modèle — la priorité avant de faire confiance aux
   probabilités affichées.

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
| `GET /predict?home=X&away=Y` | Prédiction complète pour un match |
| `GET /teams` | Liste des équipes connues |
| `GET /backtest` | Rapport de calibration sur l'historique stocké |
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
- Étendre le moteur avec un modèle ML complémentaire (ensemble avec
  Poisson+Elo plutôt qu'un remplacement).
- Suivre dans le temps la calibration réelle du modèle (comparaison
  prédiction vs résultat, historique de performance).
