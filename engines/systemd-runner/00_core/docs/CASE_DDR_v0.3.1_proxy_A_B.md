# Cas DD-R v0.3.1 — Proxy A/B (n=4 vs n=3)

Version : v0.3.1-DDR-final v0.2.5  
Statut : **EXECUTED=OK**, **COMPATIBILITÉ=KO**, **DDR=PARTIAL**

## Objet
Application du framework **DD-R** à la matrice `TEST_MATRIX.md` v0.3.1 visible (sections : règles globales n=4, conventions sorties n=3, A tests structure n=4, B métrologie n=3).  
Phases proxy : **pre=A (n=4)**, **post=B (n=3)**.

## Structures et variables
- Pre : A tests structure (n=4, ID=[1,2,3,4])
- Post : B métrologie (n=3, ID=[1,2,3])
- Seuils de calculabilité :
  - `min_n_for_moments=5` → neutralise `variance`, `std`, `entropie`
  - `min_n_for_quantiles=2` → autorise `p90`, `p99`
  - `min_n_for_MAD=2` → autorise `MAD`
- Définitions :
  - `MAD_definition = median(|x - median(x)|)`
  - `quantile_method = linear ((n-1)q interpolation)`
  - `div_rel(x,y) = |y-x|/|x|` (base pre)
- Invariants : `mean, median, MAD, p90, p99`
- `eps=0.02`

## Application DD-R
Règle : `div_rel > eps` → **KO** (sinon OK), sur invariants calculables.

## Résultats
### Observables
- Pre : mean=2.5, median=2.5, MAD=1.0, p90=3.7, p99=3.97
- Post : mean=2.0, median=2.0, MAD=1.0, p90=2.8, p99=2.98

### Divergences relatives (base pre)
- mean = 0.20 → KO
- median = 0.20 → KO
- MAD = 0.00 → OK
- p90 ≈ 0.243 → KO
- p99 ≈ 0.249 → KO

### Agrégation
- `invariants_ok = [MAD]`
- `invariants_ko = [mean, median, p90, p99]`
- **DDR = PARTIAL**
- `statut_execution = OK`
- `statut_compatibilite = KO`

## Limites
- Phases proxy arbitraires non temporelles.
- `min_n_for_moments=5` neutralise variance/std/entropie (n<5).
- Matrice visible tronquée (sections supplémentaires absentes).
