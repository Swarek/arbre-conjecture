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

## T040 - Faux silence local sur PC-tree raffiné

Statut : contre-exemple régressé contre une suffisance locale naïve.

`even_high_cycle_plus_low_hub(7)` avec `balanced_pc_tree(7, kind="mixed")` a
`16` frontiers, toutes non-cR par oracle exact. Pourtant
`project_farthest_sets_to_pc_nodes` ne signale aucun nœud local problématique :
`circular_ones_status == "compatible"`, `proper_nontrivial_count == 0`,
`laminar_violation_count == 0` et `declared_order_interval_violation_count == 0`
sur tous les nœuds.

Conclusion : les projections `I_x(v)` peuvent détecter une obstruction au root
d'un star tree, mais devenir silencieuses quand le PC-tree raffine en nœuds
binaires. Une contrainte utile devra donc soit construire une contrainte globale
auxiliaire de type circular-ones à intersecter avec le PC-tree, soit conserver
des corrélations entre niveaux.

## T046 - Contre-exemple minimal matching low-hub aux règles locales `I_x(v)`

Statut : contre-exemple régressé.

Un sidecar a trouvé le premier cas négatif dans le sous-cas matching low-hub :
`matching_high_graph_plus_low_hub(5)` avec
`P(P(1,3), P(2,4), 0)`. L'oracle PC-tree répond `False`, mais
`project_farthest_sets_to_pc_nodes` reste silencieux sur tous les nœuds :
pas de violation laminaire, pas de violation d'intervalle déclaré, et
`circular_ones_status == "compatible"`.

Minimalité bornée : les graphes hauts matching low-hub `n <= 4` ne produisent
pas de négatif PC-tree dans le probe du sidecar. Ce cas `n=5` est donc la
régression locale minimale connue pour cette règle.

Conclusion : une règle locale fondée seulement sur les ensembles projetés
`I_x(v)` ne peut pas décider l'existence, même dans le sous-cas matching
low-hub. La prochaine piste locale doit transporter l'ordre relatif des paires
ou construire une vraie intersection globale.

## T022 - Rapport `project_farthest_sets_to_pc_nodes`

Statut : diagnostic implémenté, explicitement non décisionnel.

Artefact ajouté : `project_farthest_sets_to_pc_nodes(D, T)` dans
`src/pc_circular/solvers/local_constraints.py`.

Pour chaque nœud interne, le rapport contient :

- `path`, `kind`, `degree`, `label_count` ;
- tailles de branches et ensembles de labels enfants ;
- histogramme des tailles `|I_x(v)|` ;
- projection de chaque `F_x` sur les branches ;
- ensembles propres non triviaux ;
- nombre et exemples de violations laminaires ;
- nombre et exemples de violations d'intervalle dans l'ordre local déclaré ;
- statut circular-ones brute force si le degré est au plus `8`, avec témoin
  d'ordre de branches quand un ordre compatible est trouvé, `unsupported_degree`
  sinon.

Tests ajoutés :

- égal-distance sur star : tous les `I_x` sont de taille `n-1`, la laminarité
  échoue, mais les projections restent des intervalles circulaires ; cela
  empêche de transformer la laminarité en filtre ;
- nœud `C` à cinq feuilles : un point avec `F_x = {0,2}` produit une violation
  d'intervalle dans l'ordre déclaré.

Probe rapide `n=8` :

- `equal/star` : `proper=8`, `laminar=28`, `interval=0` ;
- `random/star` : `proper=7`, `laminar=8`, `interval=6`,
  `circular_ones_false=1` ;
- `random/mixed` et `paired_farthest/mixed` : diagnostic muet sur ce scaffold
  binaire (`proper=0`) ;
- `cycle` : pas de signal sur l'instance naturelle testée.

Conclusion : l'outil est utile pour produire des signaux d'obstruction et pour
orienter Piste C/D sur des gros nœuds, mais il est trop faible ou trop bruyant
pour décider l'existence. Il ne doit pas être appelé par `candidate.py`.

## Prochaine action

Construire un outil qui énumère tous les mauvais ordres représentés par un petit
PC-tree et mesure si chaque violation possède un support local borné. Si le
diagnostic `I_x(v)` est ajouté, le garder dans les rapports d'obstruction et
non comme décision d'existence.
