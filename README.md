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
make bench-permutation-like
make bench-permutation-composition
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

`make bench-permutation-like` écrit `reports/permutation_like_probe.json`. Il
teste les profils locaux `permutation_like` observés sur `paired_farthest`
contre les ordres quasi-circulaires exacts en petite taille. C’est un contrôle
promise-aware borné, pas une reconstruction Hsu/McConnell générale.

`make bench-permutation-composition` écrit
`reports/permutation_composition_probe.json`. Il teste si ces profils
`permutation_like` se composent sur plusieurs blocs `P3` sans parasites
restrictifs. C’est un stress de gadget local, pas une preuve de dureté.

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
