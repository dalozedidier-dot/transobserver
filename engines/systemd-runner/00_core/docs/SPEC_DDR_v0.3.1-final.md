# System D — DD-R
## Spécification exécutable v0.3.1-final

### Objet
Runner descriptif qui transforme `TEST_MATRIX.md` (Markdown) en rapports JSON :
- `extraction_report.json`
- `ddr_report.json`
- `e_report.json` (optionnel)

Le modèle est conservé :
- Séries proxy = IDs séquentiels **1..n** (n = nombre d’items de liste dans la section).
- Invariants : **mean, median, MAD, p90, p99**.
- Divergence relative : **div_rel = |post - pre| / |pre|** (base = pre).
- Seuil **eps** fixe.
- Classification **DDR** + test **Équilibre E**.

---

## 1) Variables globales (déterministes)

- `eps = 0.02`
- `min_n_for_moments = 5`  → **variance/std/entropy** neutralisés si n < 5
- `min_n_for_quantiles = 2` → **p90/p99** neutralisés si n < 2
- `min_n_for_MAD = 2` → **MAD** neutralisé si n < 2

Champ `entropy` : réservé (non implémenté en v0.3.1-final), valeur `null`.

---

## 2) Parsing Markdown

### 2.1 Blocs de code fenced
Détection d’ouverture/fermeture (après 0–3 espaces) :
- ouvre si la ligne commence par ``` ou ~~~
- ferme si la ligne répète **le même fence**

Comportement :
- tant que `in_code_block = True` : **toutes les lignes sont ignorées**, y compris les listes.
- si un fence n’est jamais refermé : **tout le reste du fichier est ignoré** (déterministe).

### 2.2 Normalisation Unicode (matching headings uniquement)
Appliquée uniquement au matching des titres/labels, jamais au contenu des items.

Procédure :
1) `NFC`
2) `casefold()`
3) `NFKD`
4) suppression des caractères de catégorie Unicode `Mn`
5) collapse des espaces multiples (→ 1 espace)
6) `strip()`

### 2.3 Items de liste
Un item est détecté si la ligne match :
- `- item`
- `* item`
- `1. item`

### 2.4 Unassigned items et règles d’arrêt
Définitions :
- `assigned` = items de liste classés dans une section valide
- `unassigned` = items de liste hors section valide (hors code blocks)
- `total_list_items = assigned + unassigned`
- `ratio = unassigned / total_list_items`

Règles :
- `--strict-parsing` : stop immédiat si `unassigned > 0` → **exit code 2**
- `--max-unassigned-ratio X` : stop si `ratio > X` → **exit code 2**
- fichier introuvable → **exit code 3**

---

## 3) Séries proxy
Pour chaque section retenue :
- `IDs = [1, 2, ..., n]`

---

## 4) Invariants

Sur une série `IDs` :

- `mean`
- `median`
- `MAD = median(|x - median(x)|)`
- `p90`, `p99` : quantiles **linéaires** avec `pos = (n-1)q`  
  - `lo=floor(pos)`, `hi=ceil(pos)`
  - si `lo==hi` → `xs[lo]`
  - sinon `xs[lo] + frac*(xs[hi]-xs[lo])`, `frac=pos-lo`

Moments (neutralisés si `n < min_n_for_moments`) :
- `variance` (ddof=1)
- `std` (ddof=1)
- `entropy` : réservé (null)

---

## 5) Comparaison pré/post

### Divergence relative
`div_rel(pre, post) = |post - pre| / |pre|`

Cas particuliers :
- si `pre == 0` → **NON_CALCULABLE** (`null`)
- si `pre` ou `post` est `null` → `null`

### Décision par invariant
- `null` → NON_CALCULABLE
- `div_rel > eps` → KO
- sinon → OK

---

## 6) Classification DDR
Soit `ok`, `ko`, `nc` les listes d’invariants.

- si `nc ≠ ∅` → `INCONCLUSIF`
- si `ok = ∅` et `ko ≠ ∅` → `ILLUSION`
- si `ok ≠ ∅` et `ko ≠ ∅` → `PARTIAL`
- si `ko = ∅` → `RESTORED`

---

## 7) Équilibre E (non compensable)
Sur les invariants testés (mean, median, MAD, p90, p99) :

- si un invariant **calculable** est KO → `INCOMPATIBLE`
- sinon si aucun invariant calculable → `INCONCLUSIF`
- sinon → `COMPATIBLE`

---

## 8) Résumé humain (strictement descriptif)
Dans `ddr_report.json` :

- `summary_humain.resume` : phrase descriptive
- listes `invariants_ok`, `invariants_ko`
- `divergences_rel`
- `neutralized`
- notes (ex : quantiles calculés)

Aucun champ d’interprétation causale.

---

## 9) Tests intégrés (stdlib)
Flag `--run-tests` inclut au minimum :
- parsing fenced non fermé
- headings NFD / accents combinés
- `div_rel(pre=0)` → `null`
- `MAD` n=1 → `null`
- quantiles n=2 interpolation linéaire
- neutralisation moments si n < min_n_for_moments
