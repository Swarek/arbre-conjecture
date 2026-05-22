# Piste A - Contraintes locales P/C

## Question

Peut-on transformer les violations circular Robinson en contraintes locales sur
les permutations de branches des nœuds `P` et les orientations des nœuds `C` ?

## Intuition

Si un mauvais ordre contient un quartet cR interdit, alors les quatre feuilles du
quartet se projettent sur des branches d’un ou plusieurs nœuds PC-tree. Une
contrainte locale pourrait interdire certains patterns de branches sans
énumérer toutes les frontiers.

## Essais

### T004 - Projection locale des obstructions

Statut : preuve expérimentale / outil.

Implémenté :

- `find_precircular_cR_violation(D, order)` ;
- `find_farthest_crossing_violation(D, order)` ;
- `classify_order_obstructions(D, order)` ;
- `measure_obstruction_support(D, T, order)`.

Tests :

- `tests/test_local_constraints.py`;
- `make quick`;
- `make check`.

Résultat :

- Un quartet cR interdit peut être projeté sur les branches d’un nœud `P/C`.
- Sur un star tree à 4 feuilles, le quartet `(0,1,2,3)` a un support de 4
  branches à la racine.
- Sur un arbre imbriqué, le même quartet se voit à la racine avec support 2 et
  plus profondément avec les paires contenues.

Limite :

Cette projection ne prouve aucune suffisance. Une interdiction locale peut
manquer les corrélations entre plusieurs nœuds.

## Contre-exemples liés

Les contre-exemples farthest de la Piste E montrent que les contraintes locales
basées seulement sur farthest sont insuffisantes. Cette piste doit donc utiliser
les quartets cR exacts, pas seulement les cordes farthest.

## Prochaine action

Construire un outil qui énumère tous les mauvais ordres représentés par un petit
PC-tree et mesure si chaque violation possède un support local borné. Chercher
ensuite un contre-exemple où toutes les obstructions visibles localement sont
compatibles, mais aucun ordre global ne marche.
