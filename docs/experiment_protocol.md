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

Minimisation de noyaux UNSAT Piste F/C :

```bash
make bench-relation-unsat-cores
```

Cette commande écrit `reports/relation_unsat_core_probe.json`. Le rapport
reprend les lignes `interaction_unsat` du CSP relationnel matérialisé et cherche
des noyaux de relations de cardinalité minimale sous une borne explicite. Pour
chaque noyau, il reporte les relations, les variables, les quartets source, les
tests de suppression et les projections brutes qui expliquent le conflit. Un
noyau trouvé est un diagnostic local du modèle matérialisé ; il ne prouve ni
UNSAT global, ni NP-difficulté, ni correction d'un solver.

Conflits `sparse_partial_matching` Piste F/C :

```bash
make bench-sparse-matching
```

Cette commande écrit `reports/sparse_matching_conflict_probe.json`. Le rapport
isole les relations de forme `sparse_partial_matching`, leurs projections
gauche/droite, les unaires restrictives sur les mêmes variables, les
intersections vides projection/unaire, et les composantes formées seulement de
relations sparse. Une composante sparse insatisfiable ou une intersection vide
est un diagnostic local du CSP matérialisé ; elle ne devient pas un gadget sans
contrôle des parasites, du promise PC-tree et d'une construction globale de `D`.

Noyaux binaires sparse Piste F/C :

```bash
make bench-sparse-binary-cores
```

Cette commande écrit `reports/sparse_binary_core_probe.json`. Elle reprend les
composantes `sparse_partial_matching` insatisfiables et vérifie si elles
survivent sans `constant_reject`, si leur conflit vient de projections
disjointes sur une variable partagée, et si le retrait d'une relation ou d'un
quartet source réouvre des affectations. Une ligne sans constante serait un
candidat expérimental plus fort ; une ligne avec constante reste un diagnostic
local du CSP matérialisé.

Couverture positive-only des solveurs de quartets Piste C :

```bash
make bench-quartet-coverage
```

Cette commande écrit `reports/quartet_solver_coverage_probe.json`. Elle compare
la candidate courante aux solveurs expérimentaux `solve_quartet_2sat` et
`solve_quartet_treewidth_csp` sur des arbres `p3_block_tree(k)`. Le rapport
compte seulement les témoins `True` dont l'ordre est directement vérifié cR et
représenté par construction comme couverture potentielle. Les résultats
`False`/UNSAT du modèle relationnel restent des diagnostics tant que les
obligations de preuve globales ne sont pas fermées.

Supports exacts d'obstructions de frontiers Piste A/D :

```bash
make bench-frontier-obstructions
```

Cette commande écrit `reports/frontier_obstruction_support_probe.json`. Elle
énumère les frontiers représentées sous `frontier_limit`, teste chaque ordre par
le prédicat fixed-order bad-side, puis profile le premier quartet cR interdit
des frontiers non-cR avec `measure_obstruction_support` et
`quartet_support_paths`. Le rapport compare aussi le silence des projections
locales `I_x(v)` et les variantes d'arcs de mauvais témoins. Une ligne
tronquée est incomplète ; un support multi-niveau est un diagnostic de
corrélation, pas une preuve de non-existence globale ni une décision candidate.

Audit strict Algorithm 5.2 Piste F :

```bash
make bench-strict-algorithm52
```

Cette commande écrit `reports/strict_algorithm52_audit.json`. Elle énumère
exactement les ordres ou frontiers de petites instances, calcule les ensembles
`strict_quasi`, `strict_precircular` et `strict_circular`, puis les compare aux
ordres vérifiés produits par `strict_algorithm52_report`. Un mismatch est un
contre-exemple de complétude de l'artefact strict et doit être régressé. Une
absence de mismatch reste une preuve expérimentale bornée ; elle ne suffit pas à
intégrer un rejet `False`, ni à traiter les cas non stricts.

Couverture positive-only stricte Piste F :

```bash
make bench-strict-positive-coverage
```

Cette commande écrit `reports/strict_positive_coverage.json`. Elle compare
`candidate.py` à `strict_algorithm52_report` sur des tailles incluant `n > 8`.
Un témoin strict est compté seulement s'il est strict circular, passe aussi le
prédicat bad-side cR, et est représenté par le PC-tree quand il y en a un.
Les lignes où Algorithm 5.2 ne trouve rien, atteint sa limite, ou trouve un
témoin non représenté restent des diagnostics ; elles ne produisent jamais un
rejet.

Contrôle seuil clean-side Piste D/E :

```bash
make bench-threshold-roundness
```

Cette commande écrit `reports/threshold_roundness_probe.json`. Elle compare
trois prédicats d'ordre fixé : définition cR directe par quadruples,
bad-side, et clean-side par seuil
`N_{d(a,b)}[a] intersect N_{d(a,b)}[b]`. Un mismatch est un contre-exemple
prioritaire à régresser. Une absence de mismatch établit seulement une
équivalence expérimentale bornée pour ordre fixé ; elle ne décide pas
l'existence dans un PC-tree compact.

PC-représentabilité des ordres cR Piste D :

```bash
make bench-cr-pc-representability
```

Cette commande écrit `reports/cr_pc_representability_probe.json`. Elle énumère
les ordres cR d'une matrice sur petites tailles, puis cherche une famille
`PCNode` du scaffold dont les frontiers sont exactement cet ensemble. Les caps
`max_families_per_subset` rendent une ligne incomplète si le learner déborde.
Une ligne complète non représentable est un contre-exemple au scaffold enraciné
du dépôt ; elle doit être minimisée et comparée à un modèle Hsu/McConnell plus
fidèle avant toute conclusion externe.

Audit non enraciné du contre-exemple T079 Piste D :

```bash
make bench-unrooted-pc-representability
```

Cette commande écrit `reports/unrooted_pc_representability_probe.json`. Elle
énumère explicitement de petits PC-trees non enracinés à `5` feuilles, avec
topologies par Prüfer, types `P/C`, ordres cycliques des nœuds `C`, et
frontiers induites par les embeddings autorisés. Elle sert à auditer le premier
contre-exemple T079 hors du scaffold enraciné. Une ligne complète négative est
un signal plus fort, mais encore borné à `n=5` et à ce modèle expérimental.

Profondeur d'obstructions locales Piste E :

```bash
make bench-local-obstruction-depth
```

Cette commande écrit `reports/local_obstruction_depth_probe.json`. Elle scanne
les sous-matrices induites par taille croissante et reporte
`min_negative_subset_size` quand une obstruction cR est visible sous le cap. Une
ligne négative de taille minimale `k` prouve que tous les sous-ensembles plus
petits sont cR-positifs dans ce scan, tandis que l'instance complète est
négative par héritage. Si aucun sous-ensemble négatif n'est vu et que l'oracle
global exact est appelé, la ligne peut aussi signaler une obstruction au-delà
du cap. Ce rapport est un diagnostic local-to-global, pas une règle de rejet
pour `candidate.py`.

Probe chirotope high-girth Piste C/E :

```bash
make bench-chirotope-high-girth
```

Cette commande écrit `reports/chirotope_high_girth_probe.json`. Elle remplace
chaque contrainte bad-side de `D` par une contrainte de même côté de corde
`same_side(a,c;b,d)`, puis résout exactement ce système par énumération
d'ordres circulaires jusqu'à une borne. Les petites tailles sont recroisées
avec `exact_oracle_all_orders`. Une ligne `high_girth_candidate` est une cible
red-team : globalement négative, mais sans sous-matrice négative visible sous le
cap local. L'absence de candidate dans le sweep ne prouve pas de borne
universelle sur les obstructions.

Projection bad-side complète sur nœuds PC Piste A/B :

```bash
make bench-r004-bad-side-projections
```

Cette commande écrit `reports/r004_bad_side_pc_node_projection_probe.json`. Elle
calcule les obligations exactes `same_side(a,c;b,d)` dérivées des mauvais
témoins `b,d in B_ac`, les projette sur chaque nœud interne du PC-tree, et
mesure si elles sont locales, multi-niveaux, ou concentrées sur quatre branches
distinctes. Le rapport sert à tester les hypothèses R004 sur les P-nœuds et les
interfaces ; il ne fournit ni solver, ni certificat `False`.

Probe largeur 4 P-nœud Piste A/B :

```bash
make bench-pnode-width4
```

Cette commande écrit `reports/pnode_width4_probe.json`. Elle énumère des
frontiers représentées sous cap, extrait les ordres de branches des nœuds `P`
parmi les frontiers cR, puis teste si cette famille est exactement récupérée
par ses restrictions à toutes les sous-familles de quatre branches. Une ligne
`refuted` complète serait une réfutation expérimentale forte de la conjecture
largeur 4 dans le scaffold ; une absence de réfutation reste seulement un
signal expérimental.

Probe gadget manuscrit 4 blocs Piste A/R004 :

```bash
make bench-handwritten-gadget
```

Cette commande écrit `reports/handwritten_gadget_probe.json`. Elle encode le
screenshot manuscrit du 2026-05-31 comme une famille bornée de matrices à
quatre blocs de deux feuilles, puis compare par oracle exact un root `P` libre
et des roots `C` fixant les trois ordres circulaires de blocs. Le rapport est
un artefact de diagnostic/provenance : il ne décide pas l'existence générale,
ne prouve pas la dureté, et ne justifie aucun changement dans `candidate.py`.

Probe interface P-nœud à ordre fixé Piste A/R004 :

```bash
make bench-pnode-interface
```

Cette commande écrit `reports/pnode_interface_probe.json`. Elle fixe un ordre
de branches au root, énumère les complétions linéaires internes de chaque
branche, calcule la relation exacte `A_exact` des tuples qui donnent un ordre
cR, puis compare `A_exact` au produit cartésien de ses projections unaires. Une
ligne `factorizes=false` est une réfutation expérimentale de la factorisation
produit pour ce scaffold fixé, pas une preuve de dureté ni un rejet général.

Probe interface P-nœud avec contexte extérieur Piste A/R004 :

```bash
make bench-pnode-context-interface
```

Cette commande écrit `reports/pnode_context_interface_probe.json`. Elle fixe un
contexte extérieur linéaire autour d'un nœud focal, compose
`context_before + focus + context_after`, puis répète le test de factorisation
de `A_exact`. Une réfutation non vide indique qu'une relation résiduelle
d'interface est nécessaire même sous contexte fixé. Une relation vide doit être
interprétée comme collapse de contexte, pas comme preuve positive.

Probe relation résiduelle d'interface Piste A/B :

```bash
make bench-residual-interface
```

Cette commande écrit `reports/residual_interface_probe.json`. Elle calcule
`A_exact` et les fermetures par projections d'arité `1,2,...` pour des
interfaces fixes. Le sweep par défaut reprend le seed T087 puis énumère des
matrices two-level sur un focus `P2 x P2 x P2` jusqu'à une taille bornée de
paires hautes. Une ligne exigeant une arité strictement supérieure à `2` serait
un contre-signal fort contre une interface binaire ; son absence reste une
preuve expérimentale bornée seulement.

Contrôle promise-aware des permutations locales Piste F/C :

```bash
make bench-permutation-like
```

Cette commande écrit `reports/permutation_like_probe.json`. Le rapport scanne
les profils locaux `permutation_like` dans `paired_farthest` sur `p3_block_tree`
et, pour les petites tailles, compare exactement les frontiers du scaffold avec
tous les ordres quasi-circulaires de `D`. Il reporte les parasites, les hashes,
les cycles de permutation et les affectations acceptées qui restent quasi. Ce
contrôle ne reconstruit pas le PC-tree Hsu/McConnell en général.

Composition multi-blocs des permutations locales Piste F/C :

```bash
make bench-permutation-composition
```

Cette commande écrit `reports/permutation_composition_probe.json`. Le rapport
cherche des réseaux de relations `permutation_like` sur plusieurs blocs `P3`,
mesure leurs composantes, les parasites restrictifs et les affectations
acceptées par le CSP matérialisé. Un candidat propre exigerait au moins deux
arêtes `permutation_like` dans une même composition, sans parasite restrictif et
avec des affectations acceptées. L'absence d'un tel candidat dans un sweep est
un signal négatif expérimental pour cette famille, pas une preuve d'impossibilité.

Composantes de relations non booléennes Piste F/C :

```bash
make bench-relation-components
```

Cette commande écrit `reports/relation_component_probe.json`. Le rapport reprend
les relations binaires non booléennes du CSP matérialisé et construit leurs
composantes de graphe, toutes formes confondues : `permutation_like`,
`partial_bijection`, `active_two_regular`, sélecteurs et ponts de petit domaine.
Un candidat propre exigerait une composante multi-arêtes sans parasite
restrictif et avec des affectations acceptées. Une composante multi-arêtes
bloquée par `constant_reject` ou par une unaire reste un contre-signal de
composabilité, pas une preuve d'impossibilité.

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
