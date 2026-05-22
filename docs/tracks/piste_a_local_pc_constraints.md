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

## T021 - Projection locale des farthest sets

Statut : diagnostic utile, pas critère de décision.

Hypothèse testée : pour un nœud PC-tree de branches `B_i`, les projections

```text
I_x(v) = { i : B_i intersecte F_x }
```

pourraient être laminaires, ou des arcs dans l'ordre local d'un nœud `C`, ou
des contraintes circular-ones sur un nœud `P`.

Résultats subagent lecture seule :

- laminarité brute non nécessaire : `random/star`, `cycle/star`,
  `permuted_cycle/star`, `block/star` produisent des faux rejets ;
- `equal_distance_instance(6)` est cR pour tout ordre, mais les
  `I_x = X \\ {x}` cassent massivement la laminarité ;
- circular-ones local est plus plausible comme obstruction mais très
  incomplet : sur `random/star`, stress `n=5..8`, `144` flags sans faux rejet
  observé, mais `76` faux silences où l'oracle est `False` ;
- sur `paired_farthest/balanced` et `paired_farthest/mixed`, beaucoup de
  projections sont singletons, donc le diagnostic est presque muet ;
- sur gros nœuds `P` ou `C` de fanout élevé, les violations locales sont un bon
  signal d'obstruction potentielle, sans preuve de suffisance.

Contre-exemples notés :

- faux rejet laminarité avec oracle `True` sur une matrice random `n=5` ;
- faux silence circular-ones avec oracle `False` sur une autre matrice random
  `n=5`.

Décision : ajouter plus tard un rapport
`project_farthest_sets_to_pc_nodes(D, T)` dans `local_constraints.py` si l'on a
besoin d'un diagnostic, avec histogrammes `|I_x|`, violations laminaires,
violations d'intervalles pour `C`, et circular-ones exact seulement pour petit
degré. Ne pas intégrer comme filtre dans `candidate.py`.

## Prochaine action

Construire un outil qui énumère tous les mauvais ordres représentés par un petit
PC-tree et mesure si chaque violation possède un support local borné. Si le
diagnostic `I_x(v)` est ajouté, le garder dans les rapports d'obstruction et
non comme décision d'existence.
