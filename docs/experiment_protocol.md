# Experiment protocol

Ce dépôt impose deux familles de gates : correction et complexité.

## Gates de correction

Quick correctness :

```bash
make quick
```

Cette commande lance `pytest -q`, puis l’oracle exact rapide :

```bash
python tools/pc_circular_conjecture_test.py \
  --candidate src/pc_circular/solvers/candidate.py:solve \
  --exhaustive-n 4 \
  --values 1,2,3 \
  --random 100 \
  --max-n 7 \
  --self-check \
  --shrink
```

Strong correctness :

```bash
make check
```

Cette commande augmente l’exhaustif à `n = 5`, les tests aléatoires à `1000` et
`max-n = 8`.

La sortie `JUSTE` signifie que la candidate coïncide avec l’oracle exact sur les
instances générées par le script. Elle ne prouve pas la correction globale.

Counterexample hunt :

```bash
make hunt-counterexamples
```

Cette commande garde l’exhaustif rapide mais augmente fortement la recherche
aléatoire et active le shrink. Elle doit être utilisée après une amélioration de
solver qui passe `make quick`, avant de considérer le résultat comme stable.

## Gates de complexité

Quick benchmark :

```bash
make bench-quick
```

Strong benchmark :

```bash
make bench
```

Les benchmarks mesurent médiane, p95, timeouts, nombre de runs incomplets et un
ajustement grossier `time ~= C * n^p`, comparé à un modèle exponentiel. Les
timeouts et résultats incomplets doivent rester visibles dans le JSON.

Pour `--instance-kind mixed`, le rapport doit aussi conserver l'attribution par
`resolved_kind` : counts de sous-familles, timeouts, incomplets, positifs et
solvers par sous-famille. Cette attribution sert à choisir la prochaine piste ;
elle ne transforme pas un benchmark en preuve.

Benchmarks ciblés Piste F :

```bash
make bench-piste-f
```

Cette commande écrit des rapports dédiés aux familles `cycle/mixed`,
`permuted_cycle/star` et `paired_farthest`, avec diagnostics exacts jusqu’à
`n <= 8` pour compter les frontiers, les ordres cR valides, les ordres passant
farthest, et les faux positifs farthest.

Benchmark interne Piste C :

```bash
make bench-csp-quick
```

Cette commande mesure les expériences CSP/nogoods hors `candidate.py` :
temps de compilation, temps du solve pruné, filtre cR direct, nombre de nogoods,
branches prunées et mismatches. Un mismatch doit être traité comme un
contre-exemple de la piste expérimentale, pas comme une faiblesse de l’oracle.

Stress largeur Piste C/F :

```bash
make bench-width-stress
```

Cette commande écrit `reports/p3_width_stress.json` pour les arbres
`p3_block_tree(k)`. Elle sert à vérifier que la DP treewidth garde ses limites
visibles : largeur exacte, caps dépassés, témoins validés, et lignes
incomplètes. Elle ne valide pas la candidate générale.

Stress domaine single-P Piste F :

```bash
make bench-single-p-stress
```

Cette commande écrit `reports/single_p_domain_stress.json` pour un PC-tree star.
Elle garde visible le cas où le CSP a une seule variable et treewidth `0`, mais
où le domaine local du nœud `P` est factoriel. Elle ne valide pas la candidate
générale et ne doit pas être confondue avec une preuve de dureté.

Catalogue relations Piste F :

```bash
make bench-relation-catalog
```

Cette commande écrit `reports/relation_catalog.json` pour des arbres
`p3_block_tree(k)`. Le rapport catalogue les relations non booléennes entre
petits nœuds `P`, les contraintes parasites unaires/constantes, les densités,
les tailles de domaine et les mismatches de validation. Une relation non
booléenne observée est un signal expérimental, pas une réduction NP-hard.

Minage de formes relationnelles Piste F :

```bash
make bench-relation-shapes
```

Cette commande régénère le catalogue puis écrit
`reports/relation_shape_search.json`. Le rapport classe les relations non
booléennes par forme (`sparse_partial_matching`, `partial_bijection`,
`active_two_regular`, sélecteurs, ponts de petit domaine) et par tags de
composabilité (`unary_gated`, `constant_blocked`, `parasite_free`). Les
`candidate_gadgets` ne doivent jamais inclure une relation expliquée par un
parasite `constant_reject`. Ce rapport oriente la recherche de gadgets ou de
compressions ; il ne prouve ni NP-difficulté ni polynomialité.

Composition de relations fonctionnelles Piste F/C :

```bash
make bench-relation-chains
```

Cette commande écrit `reports/relation_chain_probe.json`. Le rapport construit
le CSP relationnel complet pour `p3_block_tree(k)`, isole les profils
fonctionnels non booléens, mesure leurs composantes/cycles, puis compare les
comptes acceptés par les seules relations fonctionnelles, les seules relations
binaires non booléennes, les parasites et toutes les relations. Une ligne
`interaction_unsat` est un signal expérimental de corrélation entre contraintes,
pas un certificat négatif du problème général.

## Interprétation

Un algorithme qui passe les gates peut encore être faux. Après chaque succès, il
faut essayer activement de le casser avec de nouveaux générateurs, des PC-arbres
différents et des cas non stricts avec beaucoup d’égalités.

La bonne boucle n’est pas seulement "faire passer les tests". Elle est :
proposer une hypothèse, la faire passer sur oracle, chercher des
contre-exemples, shrinker les désaccords, puis seulement mesurer la complexité.

Pour un Goal long, l’agent principal peut appeler jusqu’à 5 subagents afin de
tester des idées différentes en parallèle. Les subagents doivent produire des
résultats comparables : hypothèse, commandes, contre-exemples trouvés ou non,
raison d’échec, et prochaine décision. L’agent principal reste responsable de la
synthèse et des commits.

Solutions interdites :

- cutoff de taille retournant `False` sans justification ;
- détection du nom du script de test ;
- import de l’oracle dans `candidate.py` ;
- comportement différent selon les seeds de benchmark ;
- optimisation uniquement pour les familles générées ;
- suppression d’un contre-exemple pour faire passer les tests.

Règles de recherche :

1. L’agent doit maintenir au moins 4 pistes actives différentes.
2. Si une piste ne donne ni meilleur benchmark, ni preuve partielle, ni nouveau
   contre-exemple après 2 itérations, il doit changer de piste.
3. Chaque conjecture cassée doit produire au moins un artefact : nouveau test,
   nouveau générateur, contre-exemple minimal, lemme négatif ou entrée dans
   `experiment_log`.
4. L’agent doit tester des familles différentes : random, cycle, block,
   ultrametric, equal-distance, gros P-node, balanced PC-tree, cas non stricts
   avec beaucoup d’égalités, et cas où certains ordres marchent et d’autres non.
5. L’agent ne doit pas seulement optimiser pour les tests fournis.
6. Si l’agent trouve un algorithme qui passe les tests, il doit essayer
   activement de le casser.
7. Si l’existence polynomiale semble bloquée, il doit explorer une piste de
   complexité/réduction NP-hard ou un sous-cas polynomial clairement prouvé.
8. Toute note doit séparer théorème prouvé, conséquence directe, conjecture,
   preuve expérimentale et intuition.

Pour le Goal courant, une sortie alternative honnête exige une exploration
documentée d’au moins 50 pistes ou tentatives actives avant de conclure qu’aucune
voie valide ne reste. Cette barre ne réduit pas les gates de correction ; elle
évite seulement un abandon trop précoce.

La documentation doit être double :

- `docs/experiment_log.md` pour l’historique chronologique ;
- `docs/tracks/README.md` et `docs/tracks/piste_*.md` pour l’historique par
  piste.

Toute modification des tests doit être justifiée dans `docs/experiment_log.md`.
