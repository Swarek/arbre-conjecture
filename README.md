# PC-tree circular Robinson research setup

Ce dépôt prépare une boucle reproductible pour étudier le problème suivant :
décider si un PC-arbre représentant des ordres quasi-circulaires admissibles
d’un espace de dissimilarité fini contient au moins un ordre circular Robinson.

Entrée principale : une matrice symétrique `D` sur `X = {0, ..., n-1}`, à
diagonale nulle, et éventuellement un PC-arbre `T`. Sortie visée : `True/False`
et, si `True`, un ordre circulaire témoin représenté par `T`.

Le dépôt ne prétend pas résoudre le problème général. La candidate courante est
une baseline : brute force exacte pour `n <= 8`, un sous-cas large-n prouvé où
chaque paire a au plus un témoin mauvais global, un certificat positif
minimum-cycle quand l'ordre reconstruit est représenté et vérifié cR, puis
un sous-cas three-level à matching farthest unique, puis un sous-cas exact où
une famille explicite `quasi_orders` finie est sous une limite explicite, puis
un sous-cas exact où le PC-tree fourni a un nombre de frontiers certifié sous
une limite explicite, puis un certificat négatif par petite sous-matrice
interdite de taille 4, 5 ou 6, puis un certificat négatif pour graphe haut
non biparti avec hub bas, puis un certificat négatif pour cycle haut pair
induit de longueur au moins 6 avec hub bas, puis un témoin positif
strong-ordering low-hub accepté seulement s'il est directement vérifié cR et
représenté par le PC-tree, puis des recherches exactes bornées du sous-cas
matching low-hub qui énumèrent soit les ordres complets, soit seulement les
projections high-vertices relevées dans le PC-tree, puis échantillonnage
incomplet documenté au-delà.
Un témoin positif échantillonné est certifié par vérification directe de
l'ordre ; un échec d'échantillonnage reste incomplet.
Les tests servent à protéger les expériences, pas à remplacer une preuve.

Commandes principales :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make unit
make quick
make check
make hunt-counterexamples
make bench-quick
make bench
make bench-piste-f
make bench-csp-quick
make bench-width-stress
make bench-single-p-stress
make bench-relation-catalog
make bench-relation-shapes
make bench-relation-chains
make bench-relation-unsat-cores
make bench-sparse-matching
make bench-sparse-binary-cores
make bench-quartet-coverage
make bench-frontier-obstructions
make bench-strict-algorithm52
make bench-strict-positive-coverage
make bench-threshold-roundness
make bench-cr-pc-representability
make bench-unrooted-pc-representability
make bench-local-obstruction-depth
make bench-chirotope-high-girth
make bench-r004-bad-side-projections
make bench-pnode-width4
make bench-handwritten-gadget
make bench-pnode-interface
make bench-pnode-context-interface
make bench-residual-interface
make bench-residual-interface-stress
make bench-boundary-residual-projection
make bench-circle-graph-lab
make bench-partial-obligation-lab
make bench-partial-context-lab
make bench-separator-signature-lab
make bench-context-signature-ladder
make bench-context-gap-relation
make bench-context-gap-composition
make bench-context-gap-arity
make bench-context-gap-multi-arity
make bench-context-gap-high-arity
make bench-permutation-like
make bench-permutation-composition
make bench-relation-components
make acceptance
```

`make quick` lance les tests unitaires puis l’oracle exact rapide. `make check`
lance la correction forte sur petites instances. `make bench-quick` écrit un
rapport JSON dans `reports/complexity_report_quick.json`; `make bench` lance une
version plus lourde.

`make hunt-counterexamples` lance une recherche aléatoire plus longue avec
shrink. Elle est faite pour les moments où une candidate semble marcher et doit
être attaquée avant d’être considérée comme un progrès stable.

`make bench-piste-f` lance des benchmarks ciblés sur des familles explicites :
`cycle/mixed` comme sous-cas représenté non-star, `permuted_cycle/star` comme
sous-cas planted-cycle, et `paired_farthest` comme famille hard-looking à
appariements farthest. Ces familles ne sont pas ajoutées au `mixed` par défaut.

`make bench-csp-quick` mesure les expériences internes Piste C : compilation de
nogoods, solve pruné, filtre direct et métriques de pruning. Ce n’est pas la
gate de la candidate générale.

`make bench-width-stress` écrit `reports/p3_width_stress.json` pour la famille
`p3_block_tree(k)`. Ce benchmark montre comment les relations de quartets
restent résolubles à largeur bornée puis deviennent incomplètes sous cap ; il
sert à documenter les limites de la piste DP/treewidth.

`make bench-single-p-stress` écrit `reports/single_p_domain_stress.json` pour
le cas d'un seul gros nœud `P`. Il sert de garde-fou contre une mauvaise lecture
de la treewidth : le graphe primal peut avoir largeur `0` pendant que le domaine
local contient déjà `(n-1)!/2` ordres circulaires.

`make bench-relation-catalog` écrit `reports/relation_catalog.json` pour des
arbres composés de petits blocs `P3`. Il catalogue les relations de quartets
non booléennes, les parasites unaires/constantes et les limites de validité du
scaffold. Ce n’est pas une preuve de NP-difficulté.

`make bench-relation-shapes` régénère le catalogue puis écrit
`reports/relation_shape_search.json`. Il classe les profils non booléens en
formes structurelles (`sparse_partial_matching`, `active_two_regular`,
sélecteurs, etc.) et garde les tags de composabilité visibles. Ce n’est pas une
preuve de NP-difficulté ni de polynomialité.

`make bench-relation-chains` écrit `reports/relation_chain_probe.json`. Il
compose les relations non booléennes fonctionnelles observées entre blocs `P3`
et compare les comptes satisfaisant les seules relations fonctionnelles, les
relations binaires, les parasites et tout le CSP matérialisé. C’est un
diagnostic de corrélation, pas une décision générale.

`make bench-relation-unsat-cores` écrit
`reports/relation_unsat_core_probe.json`. Il minimise les lignes
`interaction_unsat` de ce CSP matérialisé en noyaux de relations, avec tests de
suppression et projections brutes. C’est un artefact de diagnostic, pas un
certificat global de non-existence.

`make bench-sparse-matching` écrit
`reports/sparse_matching_conflict_probe.json`. Il isole les relations
`sparse_partial_matching`, leurs projections, leurs conflits avec les unaires et
leurs composantes binaires. C’est un diagnostic de parasites et de compression,
pas un gadget de dureté.

`make bench-sparse-binary-cores` écrit
`reports/sparse_binary_core_probe.json`. Il inspecte les composantes sparse
binaires insatisfiables, teste la suppression des constantes, les intersections
de projections partagées et les retraits de relations/quartets source. C’est un
diagnostic de noyau local, pas une preuve de dureté.

`make bench-quartet-coverage` écrit
`reports/quartet_solver_coverage_probe.json`. Il compare la candidate courante
aux solveurs expérimentaux 2-SAT/treewidth sur `p3_block_tree(k)` et ne compte
que les témoins positifs validés directement comme couverture potentielle. Les
résultats `False` restent diagnostiques.

`make bench-frontier-obstructions` écrit
`reports/frontier_obstruction_support_probe.json`. Il énumère des frontiers
exactement représentées sous limite, compte les ordres cR/non-cR, et profile le
premier quartet cR interdit de chaque mauvais ordre via ses supports PC-tree.
C'est un diagnostic des corrélations multi-niveaux, pas un solver.

`make bench-strict-algorithm52` écrit `reports/strict_algorithm52_audit.json`.
Il compare les candidats stricts issus de `strict_algorithm52_report` aux
ordres stricts exacts énumérés sur petites instances et PC-trees bornés. C'est
un audit de complétude borné pour le sous-cas strict, pas une preuve générale.

`make bench-strict-positive-coverage` écrit
`reports/strict_positive_coverage.json`. Il mesure si les témoins stricts
validés par Algorithm 5.2 ajouteraient des `exists=True` par rapport à
`candidate.py` sur des tailles au-delà du brute force. Les échecs restent
incomplets ; le rapport ne justifie jamais un `False`.

`make bench-threshold-roundness` écrit `reports/threshold_roundness_probe.json`.
Il compare la reformulation fixed-order par seuils
`N_{d(a,b)}[a] intersect N_{d(a,b)}[b]` au prédicat bad-side et à la définition
cR directe. C'est un contrôle d'équivalence pour ordre fixé, pas un solveur
d'existence dans le PC-tree.

`make bench-cr-pc-representability` écrit
`reports/cr_pc_representability_probe.json`. Il teste, dans la grammaire
`PCNode` bornée du dépôt, si l'ensemble des ordres cR d'une matrice est
exactement une famille de frontiers PC-tree. Les résultats négatifs sont des
contre-exemples au scaffold, pas encore au modèle Hsu/McConnell complet.

`make bench-unrooted-pc-representability` écrit
`reports/unrooted_pc_representability_probe.json`. Il audite le premier
contre-exemple T079 avec une énumération brute-force de petits PC-trees non
enracinés à 5 feuilles. C'est un contrôle borné, pas un solveur scalable.

`make bench-local-obstruction-depth` écrit
`reports/local_obstruction_depth_probe.json`. Il scanne les sous-matrices
induites par taille croissante et mesure la plus petite obstruction cR visible,
quand elle existe. C'est un diagnostic local-to-global contre les certificats
par petites sous-matrices, pas une intégration dans `candidate.py`.

`make bench-chirotope-high-girth` écrit
`reports/chirotope_high_girth_probe.json`. Il transforme les contraintes
bad-side en contraintes de même côté de corde et les résout par énumération
exacte des ordres circulaires jusqu'à une taille bornée. Il cherche des
obstructions globales invisibles sous un cap local ; ce n'est pas un solveur
SAT scalable.

`make bench-r004-bad-side-projections` écrit
`reports/r004_bad_side_pc_node_projection_probe.json`. Il projette les
obligations exactes `same_side(a,c;b,d)` sur les nœuds du PC-tree et mesure
leur support local/multi-niveau. C'est le probe R004 pour tester les notes sur
P-nœuds ; il ne décide pas l'existence et ne modifie pas `candidate.py`.

`make bench-pnode-width4` écrit `reports/pnode_width4_probe.json`. Il teste
empiriquement, sous énumération complète bornée, si les ordres de branches
acceptés sur un nœud `P` sont déterminés par leurs restrictions à quatre
branches. Une absence de réfutation n'est pas une preuve de largeur 4.

`make bench-handwritten-gadget` écrit `reports/handwritten_gadget_probe.json`.
Il formalise le screenshot manuscrit 4 blocs x 2 feuilles comme une recherche
bornée d'interprétations `P` libre vs `C` fixé. C'est un diagnostic de
provenance, pas un solver ni une preuve de dureté.

`make bench-pnode-interface` écrit `reports/pnode_interface_probe.json`. Il
fixe un ordre de branches au root et compare la relation exacte des complétions
internes cR au produit cartésien de ses projections. Un mismatch réfute la
factorisation produit dans le scaffold testé, mais ne décide pas le problème
général.

`make bench-pnode-context-interface` écrit
`reports/pnode_context_interface_probe.json`. Il fixe un contexte extérieur
linéaire autour d'un P-nœud focal et répète le test de factorisation des
complétions internes. Un mismatch non vide indique qu'une relation résiduelle
de bord est nécessaire même avec ce contexte fixé.

`make bench-residual-interface` écrit
`reports/residual_interface_probe.json`. Il mesure l'arité minimale des
projections nécessaires pour reconstruire exactement une relation résiduelle
d'interface. Le sweep par défaut cherche une relation au-delà du binaire dans
un focus `P2 x P2 x P2` two-level borné ; une absence de témoin est
expérimentale, pas une preuve.

`make bench-residual-interface-stress` écrit
`reports/residual_interface_stress_probe.json`. Il stress le même diagnostic
sur `P2 x P2 x P2 x P2` et `P3 x P3 x P3` sparse two-level, avec seeds
binaires contrôlés. C'est une attaque expérimentale plus large de l'hypothèse
interface binaire, pas une preuve.

`make bench-boundary-residual-projection` écrit
`reports/boundary_residual_projection_probe.json`. Il projette une relation
résiduelle exacte sur des variables de bord après avoir caché au moins une
branche interne. C'est une attaque expérimentale de la composition de patches,
pas une DP prouvée.

`make bench-circle-graph-lab` écrit `reports/circle_graph_lab_probe.json`. Il
traduit les obligations `same_side` pleinement visibles sur un nœud `P` en
contraintes de non-croisement entre cordes de branches, puis compare les ordres
locaux autorisés aux ordres de branches vus dans les frontiers cR. C'est un lab
circle/interlacement borné, pas une split decomposition ni un solver.

`make bench-partial-obligation-lab` écrit
`reports/partial_obligation_lab_probe.json`. Il complète le lab précédent en
comptant les obligations bad-side qui touchent un nœud `P` sans former deux
cordes de branches pleinement visibles. C'est un diagnostic de séparateur, pas
une décision d'existence.

`make bench-partial-context-lab` écrit
`reports/partial_context_lab_probe.json`. Il teste si ces obligations
partielles sont décidées par le seul ordre local des branches. Les groupes
mixtes signalent une dépendance au contexte ou aux ordres internes ; ce n'est
pas un solver.

`make bench-context-gap-high-arity` écrit
`reports/context_gap_high_arity_probe.json`. Il relance le diagnostic de gaps
multi-obligations en tuple sizes `3` et `4` pour chercher une arité supérieure
au binaire. Les caps de tuples restent visibles ; l'absence de témoin n'est pas
une preuve de DP binaire.

`make bench-permutation-like` écrit `reports/permutation_like_probe.json`. Il
teste les profils locaux `permutation_like` observés sur `paired_farthest`
contre les ordres quasi-circulaires exacts en petite taille. C’est un contrôle
promise-aware borné, pas une reconstruction Hsu/McConnell générale.

`make bench-permutation-composition` écrit
`reports/permutation_composition_probe.json`. Il teste si ces profils
`permutation_like` se composent sur plusieurs blocs `P3` sans parasites
restrictifs. C’est un stress de gadget local, pas une preuve de dureté.

`make bench-relation-components` écrit
`reports/relation_component_probe.json`. Il élargit le stress T070 à toutes les
relations binaires non booléennes observées, mesure leurs composantes
multi-arêtes et garde les parasites visibles. C’est un diagnostic du scaffold,
pas une preuve de composabilité ou de dureté.

Dans `tools/pc_circular_conjecture_test.py`, la sortie `JUSTE` signifie seulement
que la candidate a été égale à l’oracle exact sur les instances générées par ce
script. Cela ne prouve pas la correction globale.

Les prochains travaux doivent remplacer la baseline par un algorithme prouvé ou
par des sous-cas clairement énoncés, en maintenant des contre-exemples,
benchmarks et obligations de preuve à jour.

Pour reprendre la boucle de recherche, lire `docs/agent_loop_guide.md`.
Pour lire l’évolution par piste, utiliser `docs/tracks/README.md`.
Pour les notes issues des documents locaux, lire `docs/source_notes.md`.
Les PDF/captures conservés dans le dépôt et leurs hashes sont listés dans
`docs/source_materials/README.md`.
