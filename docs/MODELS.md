# Modèles statistiques — description mathématique

Tous les modèles produisent en sortie une paire de buts attendus
`(λ_domicile, λ_extérieur)`, transformée ensuite en probabilités 1/N/2, BTTS,
over/under et scores les plus probables via une **matrice de Poisson**
commune (`app/analytics/poisson.py`). Seule la façon de calculer `λ` diffère
d'un modèle à l'autre.

## 1. Matrice de Poisson (commune à tous les modèles buts-based)

Pour des buts attendus `λ_h` (domicile) et `λ_a` (extérieur), la probabilité
d'un score exact `(i, j)` sous hypothèse d'indépendance est :

```
P(i, j) = Poisson(i; λ_h) × Poisson(j; λ_a)
        = (e^-λ_h · λ_h^i / i!) × (e^-λ_a · λ_a^j / j!)
```

**Correction Dixon-Coles** sur les scores faibles (0-0, 1-0, 0-1, 1-1), pour
corriger la légère sur-indépendance de l'hypothèse de Poisson pure aux petits
scores :

```
τ(0,0) = 1 − λ_h·λ_a·ρ
τ(0,1) = 1 + λ_h·ρ
τ(1,0) = 1 + λ_a·ρ
τ(1,1) = 1 − ρ
τ(i,j) = 1  sinon
```

avec `ρ = -0.06`. La matrice est renormalisée pour sommer à 1 après
application de `τ`.

De cette matrice découlent directement :

- `P(1) = Σ_{i>j} P(i,j)`, `P(N) = Σ_{i=j} P(i,j)`, `P(2) = Σ_{i<j} P(i,j)`
- `P(BTTS) = Σ_{i≥1, j≥1} P(i,j)`
- `P(+2.5 buts) = Σ_{i+j≥3} P(i,j)`
- Top-5 scores = les 5 cellules `(i,j)` de plus forte probabilité

## 2. Modèle 1 — Poisson Basic

Force d'attaque/défense de chaque équipe (séparée domicile/extérieur), sur
**tout l'historique disponible**, relative à la moyenne de ligue :

```
attaque_domicile(A)  = (buts marqués par A à domicile / matchs à domicile de A) / moyenne_ligue_domicile
défense_extérieur(B) = (buts encaissés par B à l'extérieur / matchs extérieur de B) / moyenne_ligue_domicile

λ_h = moyenne_ligue_domicile × attaque_domicile(A) × défense_extérieur(B)
λ_a = moyenne_ligue_extérieur × attaque_extérieur(B) × défense_domicile(A)
```

`moyenne_ligue_domicile`/`extérieur` sont recalculées en continu à partir de
tous les matchs déjà rejoués (fallback à 1.45/1.15 tant qu'aucun match n'est
connu).

## 3. Modèle 2 — Poisson Form

Identique au modèle 1, mais les moyennes d'attaque/défense ne portent que sur
les **10 derniers matchs à domicile / à l'extérieur** de chaque équipe
(`FORM_WINDOW_LONG`, configurable). Réagit plus vite à une série en cours,
au prix d'une variance plus élevée sur peu de matchs.

## 4. Modèle 3 — Elo Model

Système Elo chronologique classique, complètement indépendant des statistiques
de buts :

```
E_domicile = 1 / (1 + 10^((R_extérieur − (R_domicile + avantage_terrain)) / 400))

résultat_réel = 1 si victoire domicile, 0.5 si nul, 0 si défaite

Δ = K × multiplicateur_écart_buts × (résultat_réel − E_domicile)

R_domicile' = R_domicile + Δ
R_extérieur' = R_extérieur − Δ
```

avec `multiplicateur_écart_buts` : 1.0 pour un écart de 0-1 but, 1.5 pour 2
buts, `(11 + écart) / 8` au-delà (pondère davantage les victoires larges).
`K` (défaut 20), `avantage_terrain` (défaut 65 points) et le rating initial
(défaut 1500) sont configurables (`ELO_K_FACTOR`, `ELO_HOME_ADVANTAGE`,
`ELO_INITIAL_RATING`).

**Chaque match met à jour l'Elo des deux équipes ; l'historique complet
(`elo_history`) conserve le rating avant/après chaque match** — une
prédiction sur un match passé n'utilise jamais l'Elo actuel des équipes, mais
l'Elo tel qu'il était juste avant ce match (voir `docs/DATA_PIPELINE.md`).

Conversion Elo → buts attendus :

```
diff = (R_domicile + avantage_terrain) − R_extérieur

λ_h = 1.45 × e^(0.42 × diff / 400)
λ_a = 1.15 × e^(-0.42 × diff / 400)
```

## 5. Modèle 4 — Ensemble

Moyenne pondérée des trois modèles précédents, ajustée par la confrontation
directe (H2H) et le repos :

```
λ_h = w_basic·λ_h(basic) + w_form·λ_h(form) + w_elo·λ_h(elo)
λ_a = w_basic·λ_a(basic) + w_form·λ_a(form) + w_elo·λ_a(elo)
```

`w_basic + w_form + w_elo = 1` (défaut : 1/3 chacun — **valeur de départ,
volontairement neutre, à ajuster uniquement à partir de comparaisons réelles
via `/api/v1/backtesting`, jamais fixée à la main sans mesure**).

**Ajustement H2H** : sur les `H2H_MAX_MATCHES` (défaut 5) dernières
confrontations directes connues *avant* le match, on calcule l'écart de buts
moyen du point de vue de l'équipe à domicile, puis on l'applique en
multiplicateur borné à ±15 % :

```
ajustement = clamp(écart_moyen × 0.05, −0.15, +0.15)
λ_h *= (1 + ajustement)
λ_a *= (1 − ajustement)
```

**Ajustement repos** : si les deux équipes ont un nombre de jours de repos
connu, l'écart (borné à ±14 jours) est appliqué en multiplicateur borné à
±5 %, selon le même principe.

Le poids de ces deux ajustements sur l'attaque/défense H2H est
volontairement limité (§6 du cahier des charges : « ne pas donner un poids
trop important à cette variable »).

## 6. Modèle 5 — Machine Learning

Classification à 3 classes (`HOME`/`DRAW`/`AWAY`), `HistGradientBoostingClassifier`
de scikit-learn par défaut (`LogisticRegression` disponible en alternative).

**Features** (`app/ml/features.py`), toutes calculées à partir de l'état
*avant* le match (aucune fuite) :

`écart Elo (avec avantage terrain), attaque/défense domicile-extérieur
(historique complet), points par match et buts marqués en forme récente
(domicile/extérieur), écart de buts moyen en H2H, nombre de confrontations
H2H connues, écart de jours de repos`.

**Split chronologique strict** (jamais de split aléatoire sur données
temporelles, §7 du cahier des charges) :

```
train = 70% des matchs les plus anciens
val   = 15% suivants
test  = 15% les plus récents
```

En dessous de 60 matchs exploitables, l'entraînement est refusé
(`MIN_TRAINING_SAMPLES`) plutôt que de produire un modèle non significatif.
Les buts attendus affichés à côté d'une prédiction ML restent ceux du modèle
Ensemble (le classifieur n'a pas de notion de buts) — c'est un choix
d'affichage assumé, documenté ici plutôt que présenté comme une prédiction de
score générée par le ML.

## 7. Calibration

Deux mécanismes distincts, dans `app/analytics/`:

- **Mesure** (`metrics.py`) : courbe de calibration par buckets de 10 points
  de pourcentage (probabilité annoncée moyenne vs. fréquence réelle
  observée), et erreur de calibration globale (moyenne pondérée des écarts
  absolus par bucket — *Expected Calibration Error*).
- **Correction** (`calibration.py`) : régression isotonique un-contre-tous
  par classe (HOME/DRAW/AWAY) si ≥200 échantillons évalués, sinon Platt
  scaling (régression logistique sur la probabilité brute) si ≥30
  échantillons, sinon la transformation identité (pas assez de données pour
  corriger sans sur-ajuster). Les probabilités corrigées sont renormalisées
  pour sommer à 1.

## 8. Indice de confiance

Voir `app/analytics/confidence.py`. Composite pondéré de quatre facteurs
(jamais seulement la probabilité maximale, §10 du cahier des charges) :

- **Écart de probabilités** : écart entre les deux issues les plus probables
  (un match 45/35/20 est moins "clair" qu'un match 70/20/10).
- **Volume de données** : nombre de matchs connus pour les deux équipes
  (saturé à 30 matchs par défaut).
- **Convergence entre modèles** : dispersion (écart-type) de la probabilité
  de victoire domicile entre les modèles disponibles — les modèles
  s'accordent-ils ?
- **Calibration historique** (quand disponible) : erreur de calibration du
  modèle utilisé, issue de `/api/v1/backtesting`.

Sous le seuil `MIN_MATCHES_FOR_PREDICTION` (défaut 5 matchs par équipe), la
confiance est directement `INSUFFICIENT_DATA` et aucune probabilité n'est
calculée.
