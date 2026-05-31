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

## T075 - Supports exacts des frontiers non-cR

Statut : diagnostic A/D borné, contre-signal contre les règles locales
indépendantes.

Artefact ajouté : `tools/pc_frontier_obstruction_support_probe.py` et cible
`make bench-frontier-obstructions`.

Le probe énumère des frontiers représentées exactement sous `frontier_limit`.
Pour chaque frontier, il teste `passes_bad_side_precircular_cR`. Pour les
frontiers non-cR profilées, il extrait le premier quartet cR interdit, mesure
ses projections par `measure_obstruction_support`, calcule
`quartet_support_paths`, et compare le résultat au rapport local
`project_farthest_sets_to_pc_nodes`.

Résultat du sweep borné `n=5..8`, `balanced/mixed` :

- `40` lignes complètes, `0` troncature ;
- `624` frontiers inspectées, `494` non-cR ;
- les `40` lignes ont des projections `I_x(v)` silencieuses ;
- les `494` frontiers non-cR silencieuses profilées exigent toutes un support
  multi-niveau (`support_path_count_histogram = {"3": 494}`) ;
- aucun premier quartet profilé n'est contenu dans un support local unique.

Conclusion : T075 renforce T040/T046. Les projections locales par nœud peuvent
être parfaitement silencieuses pendant que l'obstruction fixed-order existe
dans chaque frontier. Une règle locale utile doit donc mémoriser une relation de
bord ou construire une contrainte globale auxiliaire ; elle ne peut pas se
limiter aux ensembles `I_x(v)` indépendants par nœud.

## R004 - Notes externes 2026-05-31 sur projection P-noeud

Statut : hypothèses externes à tester, pas résultat.

Les notes fournies le 2026-05-31 remettent au centre la question suivante :
pour un P-noeud `v` de branches `B_1,...,B_k`, les projections
`I_x(v) = { i : B_i intersecte F_x }` ont-elles une structure d'intervalles
circulaires ou de famille convexe ? Cette question est utile comme diagnostic,
mais T046/T075 montrent déjà que les `I_x(v)` farthest seuls sont insuffisants.

La version à tester maintenant doit donc projeter les obligations bad-side
complètes :

```text
same_side(a,c;b,d) pour b,d in B_ac
```

sur les branches des nœuds PC. Le rapport attendu n'est plus seulement
`I_x(v)` intervalle ou non, mais :

- quels atomes bad-side traversent un nœud ;
- quelles branches portent les deux endpoints et les deux mauvais témoins ;
- si la contrainte devient locale, binaire entre voisins, ou réellement
  multi-niveau ;
- si les familles projetées ressemblent à circular-ones/circle graph, ou si
  elles simulent cyclic ordering arbitraire.

Le screenshot manuscrit du 2026-05-31 est conservé comme seed ambigu dans
`docs/source_materials/images/handwritten_block_gadget_2026-05-31.png`. Il ne
doit pas être traité comme contre-exemple tant qu'une matrice explicite, un
PC-tree et un oracle/shrink ne sont pas versionnés.

## T083 - Projection bad-side complète sur nœuds PC

Statut : diagnostic implémenté, explicitement non décisionnel.

Artefacts ajoutés : `project_bad_side_obligations_to_pc_nodes(D,T)` dans
`src/pc_circular/solvers/local_constraints.py` et
`tools/pc_bad_side_projection_probe.py`, lancé par
`make bench-r004-bad-side-projections`.

Le diagnostic part des mauvais témoins exacts `B_ac` et crée une obligation
unique pour chaque paire non ordonnée `b,d in B_ac` :

```text
same_side(a,c;b,d)
```

Il projette ensuite cette obligation sur les nœuds internes du PC-tree :

- branches contenant les endpoints `{a,c}` ;
- branches contenant les témoins `{b,d}` ;
- nœuds support du quartet ;
- rôle local `4distinct`, `endpoints_collapsed`, `witnesses_collapsed`,
  `mixed_endpoint_witness`, `partial_boundary`, etc. ;
- histogrammes de support et charges d'interface.

Ce que T083 apprend déjà avant benchmark large :

- sur le gadget `B_ac={b,d}` en star, l'obligation est vue dans un unique nœud
  avec quatre branches distinctes ;
- sur `P(P(0,1),P(2,3))`, la même obligation traverse trois supports
  `root`, `0`, `1`, donc elle n'est pas locale à un seul nœud ;
- sur l'instance égal-distance, il n'y a aucune obligation bad-side ;
- sur la régression T046 matching low-hub, les projections farthest `I_x(v)`
  restent silencieuses alors que les obligations bad-side sont actives et
  multi-niveaux.

Conclusion : la projection complète est le bon objet de mesure pour R004, mais
elle confirme aussi que les règles locales par nœud restent dangereuses. La
prochaine étape utile est de chercher si les obligations multi-niveaux se
factorisent par une petite relation d'interface sur P-nœuds, ou si elles
produisent des familles de corrélations de type cyclic ordering.

## T084 - Test largeur 4 empirique sur P-nœuds

Statut : diagnostic implémenté, non décisionnel.

Artefacts ajoutés : `src/pc_circular/solvers/width4_experiments.py` et
`tools/pc_pnode_width4_probe.py`, lancé par `make bench-pnode-width4`.

Définition testée dans le scaffold :

```text
A_v = ordres circulaires des branches d'un nœud P induits par les frontiers
      représentées et vérifiées cR.
```

Pour chaque quadruplet de branches `Q`, le probe calcule `R_Q`, la restriction
de `A_v` à `Q`. Il réfute la largeur 4 seulement si l'énumération est complète
et si un ordre de branches absent de `A_v` satisfait toutes les contraintes
`R_Q`.

Résultat du sweep borné `n=5..8`, `star/balanced/mixed`, plus le témoin
high-girth `n=9` :

- `103` lignes, `103` complètes, `0` troncature ;
- `35` lignes avec au moins un nœud `P` testé ;
- `0` nœud réfuté ;
- `0` nœud unsupported ;
- `max_frontiers_seen=20160`, couvrant le cas high-girth `n=9` sous star ;
- `max_missing_order_count=0`.

Interprétation : ce sweep ne casse pas la conjecture largeur 4 dans le modèle
testé, y compris sur des garde-fous star/high-girth. Cela ne prouve rien de
général : l'objet testé est la projection de frontiers globales dans le
scaffold enraciné, pas encore une relation d'interface locale complète avec
branche parent/outside.

Prochaine action : enrichir T084 avec les métriques d'interface issues de T083
ou chercher activement une famille synthétique où une famille d'ordres de
branches non fermée par largeur 4 est réellement réalisable par une matrice
`D` et un PC-tree.

## T085 - Formalisation du gadget manuscrit 4 blocs

Statut : diagnostic de provenance implémenté, non décisionnel.

Artefact ajouté : `tools/pc_handwritten_gadget_probe.py`, lancé par
`make bench-handwritten-gadget`. Le screenshot reste une source de provenance ;
la source de vérité mathématique versionnée est le générateur explicite du
probe.

Modèle testé :

```text
A = {A0,A1}, B = {B0,B1}, C = {C0,C1}, D = {D0,D1}
```

Le probe teste deux profils de distances :

- lecture fidèle au croquis : intra-bloc `2`, inter-bloc par défaut `2`,
  paires hautes sélectionnées `3` ;
- contrôle blocs visibles : intra-bloc `1`, inter-bloc par défaut `2`,
  paires hautes sélectionnées `3`.

Il énumère des ensembles bornés de paires hautes, incluant le seed visible
`A0-D1`, `A1-C1`, `B0-C0` et toutes les lectures par endpoints du motif de
blocs visible `(A,D)`, `(A,C)`, `(B,C)`. Pour chaque matrice, il compare :

- un root `P` libre sur les quatre blocs ;
- les trois roots `C` fixant les ordres de blocs `ABCD`, `ABDC`, `ACBD` ;
- la projection farthest `I_x(v)` et les obligations bad-side projetées au
  root.

Résultat du sweep borné :

- `730` lignes testées ;
- `730` lignes `P` libre positives, `0` négative ;
- `416` lignes où `P` libre est positif mais au moins un `C` fixé est négatif ;
- `256` lignes où `P` libre est positif mais `C=ABCD` est négatif ;
- `224` lignes avec un seul ordre de branches accepté ;
- `196` lignes où `I_x(v)` est silencieux mais bad-side est actif ;
- `max_obligation_count=71` et
  `max_root_four_branch_obligation_count=6`.

Le seed manuscrit lui-même donne, dans les deux profils, un seul ordre de
branches accepté pour le `P` libre : `ABDC`. Les ordres `ABCD` et `ACBD` sont
rejetés. Dans le profil plat `2/2/3`, la projection farthest est silencieuse
alors que bad-side est actif ; c'est un témoin utile contre les diagnostics
fondés seulement sur `I_x(v)`.

Interprétation : le croquis formalise bien un phénomène "ordre de branches
imposé vs P libre". Il ne donne pas un `False` pour le P-noeud libre, donc ce
n'est ni une preuve de dureté ni une réfutation du lemme de largeur 4. Il
renforce l'idée que le signal pertinent est bad-side complet, et que la suite
doit tester la relation d'interface à ordre de branches fixé.

Prochaine expérience recommandée : un probe `pnode_interface_product_report`
qui fixe un P-noeud, un ordre circulaire de branches `sigma` et un contexte
extérieur, énumère les complétions internes de chaque branche, puis compare la
relation exacte acceptée `A_exact` avec le produit cartésien de ses projections
internes. Un échec de factorisation donnerait une corrélation de bord minimale ;
une réussite bornée devra aussi mesurer la taille de la relation résiduelle.

## T086 - Produit d'interface à ordre de branches fixé

Statut : diagnostic implémenté, réfutation du produit cartésien indépendant
dans le scaffold général.

Artefacts ajoutés : `src/pc_circular/solvers/interface_experiments.py` et
`tools/pc_pnode_interface_probe.py`, lancé par `make bench-pnode-interface`.

Définition testée :

```text
Fixer un root interne, un ordre de branches sigma.
Chaque branche i a un ensemble de complétions linéaires L_i.
A_exact subset product_i L_i contient les tuples dont la composition
globale dans l'ordre sigma est cR.
```

Le test compare `A_exact` au produit des projections unaires `prod_i pi_i(A)`.
Il calcule aussi la plus petite arité `k` telle que les projections `k`-aires
reconstruisent exactement `A_exact`.

Résultat du sweep T086 :

- `9` lignes, toutes complètes ;
- `8` lignes factorisées ;
- `1` ligne réfutée ;
- `max_false_product_count=2` ;
- `max_minimal_coupling_support_size=2`.

La réfutation minimale est
`single_bad_side_quartet_instance()` avec
`T = P(P(0,1), P(2,3))` et ordre de branches `(0,1)`. La relation acceptée a
`2` tuples, mais le produit des projections en contient `4`; les deux tuples
faux produisent une violation bad-side de type `same_side(0,2;1,3)`.

Contrôles :

- égal-distance sur le même arbre factorise complètement ;
- le seed manuscrit T085 factorise une fois l'ordre de branches fixé : les
  ordres rejetés par T085 viennent du mauvais ordre de branches, pas d'une
  corrélation interne restante ;
- T046 matching low-hub est vide pour l'ordre root testé, donc factorise
  seulement de façon vacue.

Interprétation : la conjecture "interface = produit cartésien des complétions
internes" est fausse dans le scaffold PC-tree général. Cela ne réfute pas une
version promise-aware plus forte, mais cela impose déjà de transporter au moins
des relations résiduelles binaires de bord dans une DP correcte.

## T087 - Interface P-nœud avec contexte extérieur explicite

Statut : diagnostic implémenté, réfutation du produit cartésien indépendant
avec contexte fixé.

Artefacts ajoutés : `fixed_context_interface_product_report` dans
`src/pc_circular/solvers/interface_experiments.py` et
`tools/pc_pnode_context_interface_probe.py`, lancé par
`make bench-pnode-context-interface`.

Définition testée :

```text
Fixer un focus interne, un ordre de branches sigma et un contexte linéaire.
Chaque ordre global testé vaut :
context_before + frontier(focus, sigma, tuple_interne) + context_after.
```

Le test compare encore `A_exact` au produit des projections unaires et calcule
la première arité qui reconstruit exactement `A_exact`.

Résultat du sweep T087 :

- `5` lignes, toutes complètes ;
- `4` lignes factorisées ;
- `1` ligne réfutée ;
- `max_false_product_count=2` ;
- `max_minimal_coupling_support_size=2`.

La réfutation est `context_coupling_seed_matrix()` avec focus
`P(P(0,1),P(2,3))`, contexte `(4) ... (5)` et ordre de branches `(0,1)`.
La relation acceptée a `2` tuples, mais le produit des projections en contient
`4`. Les faux tuples produisent des violations bad-side explicites, par exemple
`same_side(0,3;1,2)`.

Contrôles :

- égal-distance avec le même focus et contexte factorise complètement ;
- T046 matching low-hub avec hub placé en contexte collapse vers une relation
  vide ;
- les deux profils du seed manuscrit T085 collapsent aussi vers une relation
  vide quand le bloc `D` est placé en contexte fixe.

Interprétation : fixer explicitement l'extérieur ne suffit pas à rendre les
branches indépendantes. La suite doit mesurer une vraie relation résiduelle de
bord, au moins binaire dans ce seed, puis tester sa taille/composabilité sur
des patches plus grands. Les collapses à relation vide sont informatifs mais
ne sont pas des preuves positives de factorisation utile.

## T088 - Arité des relations résiduelles d'interface

Statut : diagnostic implémenté, non décisionnel.

Artefact ajouté : `tools/pc_residual_interface_probe.py`, lancé par
`make bench-residual-interface`.

Le probe calcule la relation exacte `A_exact` des complétions internes
acceptées, puis mesure la fermeture par projections d'arité `1,2,...`. Il ne
demande plus si la relation est un produit unaire ; il demande quelle arité est
nécessaire pour la reconstruire exactement.

Résultat du sweep T088 :

- contrôle T087 : relation acceptée de taille `2`, arité minimale `2` ;
- recherche two-level sur focus `P2 x P2 x P2`, contexte `(6) ... (7)` ;
- `24157` cas inspectés, recherche complète jusqu'à `4` paires hautes ;
- `21460` relations vides, `183` relations pleines, `2514` non triviales ;
- histogramme d'arité minimale : `{1: 24103, 2: 54}` ;
- aucun cas d'arité `3` trouvé dans ce budget.

Meilleur témoin non unaire two-level :

```text
high_pairs = {(0,2), (1,3)}
A_exact = {(0,0,0), (0,0,1), (1,1,0), (1,1,1)}
```

Il impose une égalité entre les deux premières branches, tandis que la troisième
branche reste libre. Les projections unaires créent `4` faux tuples ; les
projections binaires reconstruisent exactement la relation.

Interprétation : dans cette famille bornée, la relation résiduelle dépasse bien
le produit unaire mais ne dépasse pas le binaire. C'est un signal utile pour
une DP d'interface binaire, pas une preuve. La prochaine attaque doit chercher
une arité `3` avec branches `P3`, distances à plus de niveaux, contexte plus
riche ou patches composés.

## T089 - Stress d'interfaces résiduelles plus riches

Statut : diagnostic implémenté, non décisionnel.

Artefact ajouté : `tools/pc_residual_interface_stress_probe.py`, lancé par
`make bench-residual-interface-stress`.

Objectif : attaquer T088 avec deux familles plus riches :

- `P2 x P2 x P2 x P2`, qui augmente le nombre de branches de l'interface ;
- `P3 x P3 x P3`, qui augmente le domaine interne de chaque branche.

Contrôles déterministes :

- `p2x4_binary_seed`, paires hautes `{(0,2),(1,3)}` :
  `accepted_tuple_count=8`, arité minimale `2` ;
- `p3x3_binary_seed`, paires hautes `{(0,4),(0,5),(1,7),(2,6)}` :
  `accepted_tuple_count=24`, arité minimale `2`.

Résultat du stress random sparse two-level :

- `P2x4` : `5000` essais, `384` relations non triviales,
  histogramme `{1: 4981, 2: 19}`, aucun cas `>2` ;
- `P3x3` : `1500` essais, `198` relations non triviales,
  histogramme `{1: 1478, 2: 22}`, aucun cas `>2` ;
- meilleur témoin `P3x3` non unaire observé : `4` tuples acceptés, arité `2`.

Interprétation : le signal "interfaces binaires possibles" survit à deux
stress plus riches, mais cela reste un résultat expérimental borné. Comme T088
et T089 n'ont pas trouvé d'arité `3`, la prochaine étape ne doit pas être une
simple augmentation du nombre de seeds sparse two-level ; il faut changer de
source de difficulté, vers patches composés, contexte extérieur non figé, ou
graphe d'entrelacement/circle graph des contraintes same-side.

## T090 - Projection de relation résiduelle de bord

Statut : diagnostic implémenté, non décisionnel.

Artefact ajouté : `tools/pc_boundary_residual_projection_probe.py`, lancé par
`make bench-boundary-residual-projection`.

Objectif : tester un mécanisme que T088/T089 ne couvraient pas. Une relation
exacte sur toutes les branches peut être binaire, mais une DP de patch composé
doit parfois cacher des branches internes et ne garder qu'une relation de bord.
Le probe projette donc la relation acceptée sur tous les sous-ensembles de bord
de taille au moins `3`, puis mesure l'arité minimale de projections qui
reconstruit exactement chaque relation projetée.

Résultat du benchmark T090 :

- contrôle `P2x4` avec paires hautes `{(0,2),(1,3)}` : relation de bord
  non unaire, reconstruite exactement par projections binaires ;
- sweep `P2x4` sparse two-level : `20000` cas scannés, `2645` relations
  complètes non triviales, projections de bord histogramme `{1: 9315, 2: 168}`,
  aucun cas `>2` ;
- sweep `P2x5` sparse two-level : `20000` cas scannés, `3166` relations
  complètes non triviales, projections de bord histogramme `{1: 37708, 2: 792}`,
  aucun cas `>2` ;
- random multi-niveaux `P2x4` : `500` essais, aucune projection de bord
  non triviale.

Interprétation : même après élimination d'une ou plusieurs branches internes,
ce banc borné ne trouve pas d'arité de bord supérieure au binaire. C'est un
signal supplémentaire pour les interfaces binaires, mais pas une preuve. Après
T088/T089/T090, la piste ne doit plus chercher seulement plus de seeds
two-level ; il faut changer vers un contexte extérieur avec degrés de liberté
ou vers le lab circle graph / split decomposition.

## T091 - Lab interlacement/circle graph des contraintes locales

Statut : diagnostic implémenté, non décisionnel.

Artefacts ajoutés :

- `src/pc_circular/solvers/circle_graph_experiments.py`
- `tools/pc_circle_graph_lab_probe.py`
- cible `make bench-circle-graph-lab`

Idée testée : une obligation `same_side(a,c;b,d)` pleinement visible dans un
nœud `P`, avec les quatre labels dans quatre branches distinctes, dit que la
corde de branches `(a,c)` ne doit pas croiser la corde `(b,d)`. Le probe
énumère donc les ordres circulaires de branches satisfaisant toutes ces
contraintes de non-interlacement, puis les compare aux ordres de branches
réellement induits par les frontiers globales cR.

Résultat du benchmark T091 :

- `120` lignes, toutes complètes sous les limites du benchmark ;
- `80` lignes avec P-nœuds ;
- `35` lignes avec au moins une contrainte locale pleinement visible ;
- `0` ligne où un ordre de branches venant d'une frontier cR manque dans le
  modèle local ;
- `17` lignes localement UNSAT, toutes avec `0` frontier cR vue ;
- `25` lignes avec superset local, mais `0` superset contraint : ces cas sont
  vacus, sans paire de cordes locale ;
- maximum observé : `140` paires de cordes contraintes sur un nœud.

Interprétation : dans ce sweep, dès qu'une contrainte `same_side` est pleinement
visible au P-nœud, le modèle de non-croisement de cordes est aussi fort que les
ordres de branches cR observés localement. C'est un signal intéressant pour la
route circle/interlacement, mais très borné : les contraintes partiellement
visibles, les corrélations multi-niveaux et la vraie split decomposition ne
sont pas encore traitées.

## T092 - Obligations partielles autour du lab circle

Statut : diagnostic implémenté, non décisionnel.

Artefacts ajoutés :

- `src/pc_circular/solvers/partial_obligation_experiments.py`
- `tools/pc_partial_obligation_lab_probe.py`
- cible `make bench-partial-obligation-lab`

Idée testée : compléter T091 en gardant les obligations `same_side` qui touchent
un P-nœud mais ne donnent pas deux cordes de branches pleinement visibles. Le
probe sépare :

- `full_four_branch` : l'ancien cas T091, deux cordes locales ;
- `full_collapsed` : les quatre labels visibles mais certains rôles tombent
  dans la même branche ;
- `partial2` / `partial3` : seuls deux ou trois rôles visibles au nœud ;
- `support:*` versus `projection:*` : le nœud détermine réellement le quartet
  selon `quartet_support_paths`, ou il voit seulement une projection.

Résultat du benchmark T092 :

- `120` lignes, toutes complètes ;
- `80` lignes avec P-nœuds ;
- `0` ligne où un ordre de branche cR manque dans le modèle local ;
- `52` nœuds en superset local vacu, et `52/52` avec information partielle ou
  multi-niveau ;
- `0` superset local contraint ;
- histogramme grossier : `4distinct=1576`, `partial_boundary=2499`,
  `mixed_endpoint_witness=25`, `collapsed_separate_roles=19` ;
- classification fine : notamment `support:full_four_branch=1576`,
  `support:partial2:EW:split:clean=682`,
  `support:partial3:missing_witness:s2:mixed=267`,
  `support:partial3:missing_endpoint:s2:mixed=205` ;
- maxima : `max_non_chord_obligation_count=159`,
  `max_support_boundary_obligation_count=123`,
  `max_projection_only_obligation_count=36`.

Interprétation : les supersets vacus de T091 ne sont pas des nœuds sans signal
bad-side ; dans ce sweep, ils sont tous corrélés à des obligations ouvertes que
le modèle de cordes pleinement visibles ignore. Cela pousse la piste A vers une
relation de séparateur explicite. Ce n'est pas encore une sémantique exacte, et
cela ne justifie aucun `False` dans `candidate.py`.

## T093 - Dépendance au contexte des obligations partielles

Statut : diagnostic implémenté, lemme négatif expérimental dans le scaffold.

Artefacts ajoutés :

- extension de `src/pc_circular/solvers/partial_obligation_experiments.py`
- `tools/pc_partial_context_lab_probe.py`
- cible `make bench-partial-context-lab`

Idée testée : pour chaque P-nœud, chaque obligation `same_side` projetée et
chaque ordre local de branches, grouper les frontiers globales représentées. Si
un groupe contient à la fois des frontiers satisfaisant et violant la même
obligation, alors l'ordre local des branches ne décide pas cette obligation.

Témoin minimal :

- matrice `single_bad_side_quartet_instance()` ;
- arbre `P(P(0,1), P(2,3))` ;
- à la racine, même ordre local de branches `(0,1)` ;
- même obligation `same_side(0,2;1,3)` ;
- frontier satisfaisante `(0,1,3,2)` ;
- frontier violante `(0,1,2,3)`.

Résultat du benchmark T093 :

- `120` lignes, toutes complètes ;
- `80` lignes avec P-nœuds ;
- `35` lignes avec groupes mixtes ;
- `35` lignes avec groupes mixtes support-boundary ;
- `0` groupe mixte fully-visible ;
- `support_boundary_obligation_count=1952` ;
- `context_group_count=2361947` ;
- `mixed_group_count=1585` ;
- `support_boundary_mixed_group_count=1223`.

Interprétation : les obligations pleinement visibles restent décidées par
l'ordre local de branches dans ce sweep, ce qui contrôle T091. En revanche, les
obligations partielles/support ne sont pas des contraintes fermées sur l'ordre
local des branches. La prochaine abstraction doit transporter une relation de
séparateur ou d'interface, pas seulement un ordre local enrichi par des cordes.

## T094 - Signature visible de séparateur

Statut : diagnostic implémenté, lemme négatif expérimental.

Artefacts ajoutés :

- extension de `src/pc_circular/solvers/partial_obligation_experiments.py`
- `tools/pc_separator_signature_lab_probe.py`
- cible `make bench-separator-signature-lab`

Idée testée : raffiner la clé de T093
`(P-node, obligation same_side, ordre local de branches)` par une signature qui
garde, pour chaque branche touchée, l'ordre des rôles visibles
`endpoint/witness` dans la frontier.

Résultat local : sur le témoin minimal
`single_bad_side_quartet_instance()` avec `P(P(0,1),P(2,3))`, la signature
distingue bien `(0,1,3,2)` de `(0,1,2,3)`. Le groupe mixte branch-order de T093
disparaît pour ce témoin.

Résultat du benchmark T094 :

- `120` lignes, toutes complètes ;
- `80` lignes avec P-nœuds ;
- `branch_order_mixed_group_count=1434` ;
- `separator_signature_mixed_group_count=1957` ;
- `support_boundary_separator_mixed_group_count=1428` ;
- `fully_visible_separator_mixed_group_count=0`.

Contre-signal : `cycle/mixed/n=4` garde déjà des groupes mixtes sous la
signature visible. Exemple : même obligation `same_side(0,3;1,2)`, même ordre
local `(0,1)`, même signature visible `endpoint 0` dans une branche et
`witness 1` dans l'autre, mais `(0,1,2,3)` satisfait et `(0,1,3,2)` viole.
Les deux rôles absents sont précisément dans le contexte extérieur du nœud.

Interprétation : l'ordre des rôles visibles est utile pour comprendre le témoin
minimal, mais il n'est pas une contrainte locale suffisante. La piste A doit
maintenant représenter les côtés des obligations ouvertes vis-à-vis du contexte
extérieur, ou passer explicitement à une relation résiduelle.

## T095 - Ladder de signatures de contexte

Statut : diagnostic implémenté, lemme négatif expérimental.

Artefacts ajoutés :

- extension de `src/pc_circular/solvers/partial_obligation_experiments.py`
- `tools/pc_context_signature_ladder_probe.py`
- cible `make bench-context-signature-ladder`

Idée testée : comparer plusieurs signatures croissantes pour les obligations
ouvertes :

- `t094_visible_per_branch` ;
- `visible_global`, qui garde l'ordre global des rôles visibles entre branches ;
- `visible_global_plus_missing_order`, qui ajoute l'ordre des rôles absents du
  nœud ;
- `full_context_order`, contrôle qui encode l'ordre des quatre rôles avec leur
  localisation visible/extérieur.

Résultat du benchmark T095 :

- `120` lignes, toutes complètes ;
- `80` lignes avec P-nœuds ;
- `t094_visible_per_branch` : `2048` groupes mixtes ;
- `visible_global` : `1861` groupes mixtes ;
- `visible_global_plus_missing_order` : `1793` groupes mixtes ;
- `full_context_order` : `0` groupe mixte ;
- tous les modes gardent `0` groupe mixte fully-visible.

Lecture : ajouter l'ordre des rôles manquants aide certains seeds, mais ne
suffit pas. Le seed `cycle/mixed/n=5` reste mixte avec
`visible_global_plus_missing_order` : l'obligation `same_side(0,4;1,2)` peut
avoir le même ordre visible et le même rôle manquant, tout en satisfaisant ou
violant selon la position d'insertion de ce rôle extérieur. La prochaine
signature locale doit donc représenter un ensemble de positions/côtés possibles
du contexte extérieur, ou assumer explicitement une relation résiduelle.

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

Auditer maintenant la piste stricte Algorithm 5.2 ou formaliser une relation de
bord exacte pour les quartets, puisque le probe T075 remplit le diagnostic
frontier/support demandé et confirme que le signal local `I_x(v)` reste
insuffisant.
