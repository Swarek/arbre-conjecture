# Piste F - Complexité et sous-cas

## Question

Quels sous-cas semblent tractables, et quelles familles stressent les filtres
locaux ou les heuristiques de recherche ?

## Famille planted-cycle

Statut : générateur ajouté.

`permuted_cycle` construit un cycle metric puis relabellise les points. C’est un
sous-cas polynomial-looking : le graphe des distances 1 devrait révéler le cycle
planté, puis le problème se rapproche d’un test de représentation de cet ordre
par le PC-tree.

Usage :

```bash
make bench-piste-f
```

Résultat observé star :

- `n=8` : `1/2520` ordre cR valide ;
- `24/2520` ordres passent farthest, donc farthest a déjà 23 faux positifs.

## Famille paired-farthest

Statut : générateur ajouté.

`paired_farthest` crée des paires farthest uniques. C’est une famille
hard-looking parce qu’elle met une pression d’alternance sur les gros nœuds `P`.

Résultat observé star :

- `n=6` : `3/60` ordres cR valides, `4/60` ordres farthest-pass ;
- `n=8` : `12/2520` ordres cR valides, `24/2520` ordres farthest-pass.

Résultat observé mixed :

- aucun ordre cR valide dans les diagnostics `n=4,6,8` du premier benchmark.

## Témoin paired-farthest par matching maximal

Statut : sous-cas structurel intégré à `candidate.py` pour positifs
représentés.

Le détecteur ne regarde pas le nom du générateur. Il reconnaît une structure à
trois niveaux `low < mid < high` :

- les arêtes `high` forment un matching parfait sur les sommets appariés ;
- il y a au plus un neutre sans arête `high`, à distance `low` de tous ;
- les arêtes `low` entre sommets appariés forment deux cliques disjointes de
  même taille ;
- les mates `high` sont dans des cliques opposées ;
- les autres arêtes entre cliques opposées valent `mid`.

Pour une clique `A = (a_0, ..., a_{m-1})`, l'ordre construit est :

```text
a_0, ..., a_{m-1}, mate(a_0), ..., mate(a_{m-1}), neutral?
```

Raison de correction : par la caractérisation bad-side d'un ordre fixé, les
seuls témoins mauvais d'une paire même côté sont tous dans l'autre bloc ; les
seuls témoins mauvais d'une paire croisée non mate `{A_i, B_j}` sont
`B_i` et `A_j`, qui sont du même côté de la corde grâce au même ordre des
paires dans les deux blocs. Une paire mate à distance `high` n'a pas de témoin
mauvais.

Résultat T020 :

- `paired_farthest/star` grandes tailles passe par
  `candidate_paired_farthest_matching_witness` pour tous les `n > 8` ;
- benchmark ciblé : `0` timeout et `0` incomplet pour `paired_farthest/star` ;
- `paired_farthest/mixed` reste incomplet en grande taille dans le scaffold
  lorsque le témoin reconstruit n'est pas représenté ;
- un contre-exemple `n=4` montre qu'un témoin paired-farthest cR non représenté
  ne doit pas être accepté pour un PC-tree non-star.

Résultat T021 :

- sur `balanced` et `mixed` fanout 2, les nœuds internes binaires rendent `P`
  et `C` localement équivalents dans le scaffold courant ;
- scan seeds `0..999` sur `paired_farthest` :
  - `n=6` : `202` témoins canoniques représentés, `96` cas où le canonique
    est non représenté mais l'oracle est `True`, `702` oracle `False` ;
  - `n=8` : `36` canoniques représentés, `20` positifs non canoniques,
    `944` oracle `False` ;
  - `n=10` : `6` canoniques représentés, `12` positifs non canoniques,
    `982` oracle `False` ;
- shrink par permutations : pas de phénomène "canonique non représenté mais
  oracle True" à `n=4`; il apparaît minimalement à `n=6` ;
- régression positive ajoutée : `n=6 seed=1`, le témoin canonique
  `(0,1,3,5,4,2)` est non représenté, mais l'ordre représenté
  `(0,1,2,5,4,3)` est cR et l'oracle PC-tree répond `True` ;
- régression négative ajoutée : `n=6 seed=21`, l'ordre
  `(0,1,2,5,3,4)` passe la condition brute de croisement farthest, mais viole
  cR sur le quadruplet `(0,1,2,5)`.

Une probe locale a testé une génération d'ordres side-by-side dérivés des
rotations des frontiers représentées. Elle retrouve tous les positifs oracle
observés sur `paired_farthest` `n=6/8`, mais la version naïve devient trop
coûteuse en grande taille ; une version bornée trouve peu de hits au-delà de
`n=10`. Cette idée reste donc hors `candidate.py` tant qu'elle n'a pas de preuve
de complétude ou de borne utile.

Complément T032 :

- dans `reports/complexity_paired_farthest_mixed.json`, les incomplets restants
  sont exactement `n=16` et `n=20`, `10/10` chacun, sans timeout ;
- la raison mécanique est que le nombre de frontiers du scaffold `mixed` dépasse
  `EXACT_PC_TREE_FRONTIER_LIMIT` : `8192` à `n=16`, `131072` à `n=20` ;
- sur les repeats benchmark `n=16,20`, un diagnostic side-by-side représenté
  n'a trouvé aucun témoin cR. Un certificat positif ne devrait donc pas résoudre
  ces lignes ; il faudrait soit un certificat négatif, soit une preuve de
  complétude du diagnostic structurel.

## Sous-cas universel par témoins mauvais

Statut : sous-cas prouvé intégré à `candidate.py`.

Pour une paire `{a,b}`, définir :

```text
B(a,b) = {w != a,b : max(D[a][w], D[w][b]) > D[a][b]}
```

Si `|B(a,b)| <= 1` pour toute paire, alors tout ordre circulaire est circular
Robinson. Par le lemme bad-side T014, une violation cR demanderait deux témoins
mauvais pour une même paire, situés sur les deux arcs opposés. Le cas constant
hors diagonale est inclus, car tous les ensembles `B(a,b)` sont vides.

Artefacts :

- `has_at_most_one_bad_witness_per_pair` dans `predicates.py` ;
- `sample_frontier` dans `pc_tree.py` pour produire un témoin représenté sans
  énumération ;
- `candidate_universal_bad_witness_bound_all_orders` dans `candidate.py`.

Contre-exemples aux faux amis :

- une matrice presque constante avec toutes les distances `2` sauf une arête
  basse `D[0][2]=1` sort du sous-cas et peut violer cR ;
- deux arêtes hautes disjointes ne suffisent pas non plus comme règle générale.

Résultat T016 : probe large-n `n=9..30` sur star/balanced/mixed, `33` checks,
témoin cR et représenté/échantillonné ; le faux ami à arête basse reste
placeholder incomplet.

## Sous-cas strict

Statut : prometteur, mais pas encore implémentable sans transcription validée
des sources.

Résultat exploratoire T022 :

- dans le strict, les inégalités deviennent strictes (`scR`, `sqcR`) ;
- pour un ordre fixé, le papier donne un test `O(n^2)` via unimodalité stricte
  et obstructions farthest de type Prop. 4.5 ;
- Algorithm 5.2 produit un ordre compatible en `O(n log n)` si l'espace est
  strict quasi-circular/strict circular, avec reconnaissance complète après
  vérification `O(n^2)` ;
- Prop. 5.9 indique qu'un strict quasi-circular possède seulement un ou deux
  ordres compatibles modulo opposés, et qu'un strict circular en possède un.

Limite importante : une transcription naïve en probe rate `cycle_metric(6)` et
produit des mismatches sur des matrices `n=4`, valeurs `{1,2,3}`. Ce n'est pas
une réfutation du papier ; cela montre que les choix de `J`-sets, ties et
orientations doivent être codés avec une preuve/test avant toute intégration.

API expérimentale envisagée :

- `is_strict_quasi_circular_order(D, order)` ;
- `is_strict_precircular_order_cR(D, order)` ;
- `strict_algorithm52_candidates(D) -> report` ;
- `strict_subcase_solve(D, pc_tree=None, quasi_orders=None)` seulement quand
  tous les candidats stricts sont générés et vérifiés représentés/cR.

Tests requis avant `candidate.py` :

- exemple Fig. 2.2 du PDF : ordre strict quasi non cR et autre ordre cR ;
- `cycle_metric(n)` pour `n=5,6,7` ;
- exhaustif `n=4`, valeurs `{1,2,3}`, contre définition directe ;
- comparaison oracle PC-tree sur star/balanced/mixed petits `n` ;
- cas non applicables : equal-distance, non strict, random hors strict ;
- régression témoin strict cR mais non représenté par `T`.

Résultat T023 :

- prédicats d'ordre fixé ajoutés :
  `is_strict_robinson_linear`, `is_strict_quasi_circular_order`,
  `is_strict_precircular_order_cR`, `is_strict_circular_robinson_order` ;
- `strict_order_report(D, pc_tree=None, max_n=8)` énumère les ordres stricts
  seulement pour petites tailles et marque `complete=False` au-delà ;
- Fig. 2.2 est régressée : ordre `(0,1,2,3)` strict quasi mais non strict
  pre-circular, ordre `(0,1,3,2)` strict circular ;
- `equal_distance_instance(4)` verrouille le rejet strict des égalités ;
- `cycle_metric(6)` verrouille l'ordre strict positif unique modulo
  rotation/renversement ;
- un témoin strict cR non représenté par un PC-tree `C` de 4 feuilles est
  régressé pour empêcher toute future intégration qui accepterait un ordre hors
  arbre ;
- probe exhaustive `n=4`, valeurs `{1,2,3}` : `2187` couples matrice-ordre
  sans désaccord entre strict pre-circular et définition stricte par arcs.

Décision : garder ces fonctions comme base expérimentale. La prochaine étape
strict doit être la génération exhaustive des un ou deux ordres compatibles
stricts annoncés par Prop. 5.9 ou une reproduction validée d'Algorithm 5.2.

Résultat T024 :

- `strict_algorithm52_report(D, pc_tree=None, max_candidates=10000)` génère des
  candidats inspirés de l'Algorithm 5.2 puis les filtre par représentation
  PC-tree et par les prédicats stricts directs ;
- le cas disjoint `N cap F = empty` génère les deux orientations possibles des
  segments `N` et `F`, ce qui récupère `cycle_metric(6)` alors que la
  transcription naïve T022 le ratait ;
- Fig. 2.2 reste un garde : deux ordres sont strict quasi, un seul est strict
  circular ;
- un exemple random `n=5 seed=33` montre un strict positif qui n'est couvert ni
  par le témoin minimum-cycle ni par le témoin paired-farthest existants ;
- la régression PC-tree non-star vérifie que les ordres stricts non représentés
  sont comptés séparément et ne deviennent pas des témoins représentés ;
- exhaustif `n=4`, valeurs `{1,2,3}` : le rapport récupère exactement les
  ordres strict quasi et strict circular exacts pour les `729` matrices ;
- probe cycles `n=4..7`, equal-distance, random `n=5/6` seeds `0..199` :
  aucun désaccord avec les ordres stricts exacts.

Limite T024 : le rapport est un générateur filtré, pas une preuve. Il ne traite
pas les cas non stricts, et l'étape suivante doit soit prouver que la génération
couvre les ordres stricts représentés, soit l'utiliser seulement comme
diagnostic/certificat positif.

## PC-tree exact à nombre de frontiers borné

Statut : sous-cas exact intégré à `candidate.py`, énumératif mais complet quand
la borne est sous le seuil.

`candidate_exact_bounded_pc_tree_frontiers` s'applique seulement quand un
`pc_tree` est fourni et qu'aucune famille `quasi_orders` explicite ne remplace
ce PC-tree. La candidate calcule d'abord un upper bound récursif saturé sur le
nombre de frontiers du scaffold :

- feuille : `1` ;
- nœud `P` interne : produit des enfants fois `degree!` ;
- nœud `C` interne : produit des enfants fois `2` ;
- nœud `P` racine depuis T040 : produit des enfants fois les permutations
  circulaires de branches modulo renversement ;
- nœud `C` racine depuis T040 : produit des enfants sans facteur `2`
  supplémentaire, car l'orientation inverse est le même ordre circulaire modulo
  renversement ;
- toute multiplication est saturée à `EXACT_PC_TREE_FRONTIER_LIMIT + 1`.

Si cette borne est au plus la limite, la candidate énumère toutes les frontiers
canoniques représentées, les teste par `is_precircular_order_cR`, et retourne
une décision complète positive ou négative. Si la borne dépasse la limite, elle
ne conclut pas et laisse les certificats positifs/placeholder existants gérer la
suite.

Résultat T028 :

- `n=9`, C-tree rigide et métrique plateau-cycle : positif exact, sans passer
  par les témoins minimum-cycle ou paired-farthest ;
- `n=9`, C-tree rigide et contre-exemple 4 points étendu : négatif exact ;
- `n=9`, star sur la même matrice : la borne dépasse la limite, les 64 premiers
  échantillons ne contiennent aucun témoin, mais un ordre cR existe hors sample ;
  la candidate reste donc `complete=False`.

Limites :

- ce sous-cas ne prouve pas de complexité générale, seulement une énumération
  complète lorsque la borne indépendante est petite ;
- l'upper bound surcompte parfois à cause de la canonicalisation circulaire, ce
  qui est sûr mais peut rater des opportunités ;
- le résultat concerne le scaffold PC-tree enraciné du dépôt, pas une
  implémentation complète Hsu/McConnell non enracinée.

## Famille explicite `quasi_orders` bornée

Statut : sous-cas exact intégré à `candidate.py` pour une entrée explicite déjà
énumérée par l'appelant.

`candidate_exact_bounded_quasi_orders` s'applique quand `quasi_orders` expose
une longueur et que cette longueur est au plus `EXACT_QUASI_ORDER_LIMIT`. La
candidate inspecte alors toute la famille fournie, valide chaque ordre, et teste
directement `is_precircular_order_cR`. Un résultat négatif complet signifie
seulement qu'aucun ordre de cette famille explicite n'est cR.

Résultat T029 :

- famille vide non universelle : négatif exact complet ;
- `n=10`, liste d'un seul mauvais ordre : négatif exact complet ;
- `n=10`, 64 mauvais ordres puis un témoin cR : témoin trouvé alors que
  l'ancien sampling l'aurait manqué ;
- liste de taille supérieure à la limite et itérateur non dimensionné : la
  candidate ne conclut pas négativement et reste `complete=False` si le sampling
  ne trouve rien.

Limites :

- pas d'intersection `quasi_orders ∩ pc_tree` : l'API actuelle donne priorité à
  la famille explicite ;
- pas d'impact direct attendu sur `make bench`, qui appelle la candidate avec
  `pc_tree=star` et sans `quasi_orders` ;
- l'appelant supporte le coût de construction de la famille explicite.

## Attribution des placeholders `mixed/star`

Statut : diagnostic de benchmark, pas solver.

T030 ajoute une métadonnée `resolved_kind` aux générateurs et au benchmark de
complexité. Pour `kind="mixed"`, le tirage de sous-famille reste le même qu'avant
(`random`, `cycle`, `block`, `ultrametric`, `equal`, `non_strict`), mais le
rapport JSON agrège désormais les timeouts, incomplets et solvers par
sous-famille résolue.

Résultat T030 sur `make bench` avec seed `20260521` :

- `0` timeout ;
- `42` incomplets au total, comme avant ;
- `42/42` incomplets sont des instances `random` ;
- les sous-familles `cycle`, `block`, `ultrametric`, `equal` et `non_strict`
  ne produisent aucun placeholder dans ce benchmark fort `mixed/star`.

Conséquence expérimentale : le prochain progrès sur `mixed/star` ne doit pas
viser les sous-familles structurées déjà couvertes par les certificats existants.
Il faut soit attaquer `random` directement comme famille de contre-exemples et
de non-existence potentielle, soit ajouter un benchmark séparé pour isoler un
sous-cas random prouvable.

Limites :

- cette attribution ne prouve pas que tous les randoms sont négatifs ;
- elle ne donne pas de certificat pour `paired_farthest/mixed`, qui reste une
  famille ciblée séparée ; après T028, cette famille est toutefois complète pour
  `n=10,12` par énumération PC-tree bornée, et reste incomplète à `n=16,20` ;
- elle dépend du seed et doit rester visible dans le rapport JSON.

## Petite sous-matrice interdite

Statut : certificat négatif intégré à `candidate.py`.

T031 utilise l'hérédité de la propriété cR : tout ordre cR complet induit un
ordre cR sur chaque sous-ensemble de labels. La candidate inspectait d'abord des
sous-matrices induites de 4 points. Si l'une d'elles n'a aucun ordre cR exact,
la matrice complète est rejetée, indépendamment du PC-tree fourni.

Résultat T031 :

- `make check` et `make hunt-counterexamples` restent verts ;
- `make bench` sur `mixed/star`, seed `20260521`, passe à `0` timeout et
  `0` incomplet jusqu'à `n=100` ;
- les `42` anciens placeholders `random` sont désormais tous classés par
  `candidate_small_forbidden_submatrix_obstruction` ;
- probe subagent : sur les `42` cas ciblés, le premier témoin 4-points apparaît
  toujours avant 256 sous-ensembles, et sur `400/400` randoms purs testés pour
  `n in {10,20,60,100}`, la limite `4096` trouve une obstruction.

Limites :

- la limite de `4096` sous-ensembles est un budget de recherche, pas une preuve
  d'absence d'obstruction ;
- si aucune obstruction n'est trouvée, la candidate doit rester incomplète en
  négatif ;
- ce certificat ne prouve pas une caractérisation des matrices random et ne
  remplace pas une preuve générale.

Résultat T032 :

- un contre-exemple minimal `n=5`, valeurs `{1,2}`, montre que toutes les
  sous-matrices 4-points peuvent être cR alors que la matrice complète ne l'est
  pas ;
- le générateur `four_local_non_cr_core` conserve ce noyau, et
  `padded_four_local_non_cr(n)` l'étend à de grandes tailles sans créer
  d'obstruction 4-points dans les probes ;
- la candidate inspecte maintenant les tailles
  `SMALL_FORBIDDEN_SUBMATRIX_ORDERS = (4, 5)`, toujours avec la même règle :
  seul un témoin induit trouvé donne un rejet complet ;
- benchmark ciblé `four_local_non_cr/star`, tailles
  `5,6,8,9,10,12,20,40`, répétitions `3` : `0` timeout, `0` incomplet ; pour
  `n > 8`, les rejets passent par
  `candidate_small_forbidden_submatrix_obstruction` avec obstruction d'ordre 5.

Résultat T033 :

- un contre-exemple minimal `n=6`, valeurs `{1,2}`, montre que toutes les
  sous-matrices 5-points peuvent être cR alors que la matrice complète ne l'est
  pas ;
- le générateur `five_local_non_cr_core` conserve ce noyau, et
  `padded_five_local_non_cr(n)` l'étend à de grandes tailles sans créer
  d'obstruction 5-points dans les probes ;
- la candidate inspecte maintenant les tailles
  `SMALL_FORBIDDEN_SUBMATRIX_ORDERS = (4, 5, 6)`, toujours après les témoins
  positifs directs et sans conclure si aucune obstruction inspectée n'est
  trouvée ;
- benchmark ciblé `five_local_non_cr/star`, tailles
  `6,7,8,9,10,12,20,40`, répétitions `3` : `0` timeout, `0` incomplet ; pour
  `n > 8`, les rejets passent par
  `candidate_small_forbidden_submatrix_obstruction` avec obstruction d'ordre 6.

Résultat structurel T033/T034 :

- le noyau 6-points est une relabellisation d'un cycle haut impair `C5` plus un
  hub bas universel ;
- le générateur `odd_high_cycle_plus_low_hub(n)` encode cette famille pour
  `n-1` impair ;
- T034 généralise ce certificat à tout graphe haut non biparti avec au moins un
  hub bas universel ;
- la candidate utilise désormais
  `candidate_non_bipartite_high_graph_low_hub_obstruction`, qui rejette en temps
  polynomial les matrices binaires dont le graphe des arêtes hautes est non
  biparti et possède au moins un hub isolé ;
- le générateur `non_bipartite_high_graph_plus_low_hub(n)` ajoute un triangle
  haut avec branches hautes comme famille non-cycle ;
- benchmark ciblé `odd_high_cycle_plus_low_hub/star`, tailles
  `6,8,10,12,20,40`, répétitions `3` : `0` timeout, `0` incomplet ; les tailles
  `n >= 10` passent maintenant par le certificat non-biparti au lieu du
  placeholder ;
- benchmark ciblé `non_bipartite_high_graph_plus_low_hub/star`, tailles
  `6,8,10,12,20,40`, répétitions `3` : `0` timeout, `0` incomplet ; `n=40`
  médiane `0.00052s`.

Résultat structurel T035 :

- les graphes hauts bipartis avec hub bas ne sont pas tous positifs ;
- le premier négatif biparti minimal apparaît à `6` sommets non-hub, et les
  `60` négatifs exhaustifs sont les labellisations de `C6` ;
- le générateur `even_high_cycle_plus_low_hub(n)` encode les cycles hauts
  induits pairs avec hub bas ;
- la candidate ajoute `candidate_even_high_cycle_low_hub_obstruction`, qui
  rejette en temps polynomial le sous-cas exact cycle pair induit de longueur
  `>=6` plus hubs bas ;
- `C4` plus hub et `K_{3,3}` plus hub restent des contrôles positifs à ne pas
  rejeter par cette branche ;
- benchmark ciblé `even_high_cycle_plus_low_hub/star`, tailles
  `7,9,11,13,21,41,61,81`, répétitions `10` : `0` timeout, `0` incomplet ;
  à `n=81`, médiane `0.00248s`.

Limite ajoutée :

- les obstructions 4-points ne sont pas une caractérisation ; les obstructions
  `(4,5,6)` ne doivent pas non plus être présentées comme une caractérisation
  sans preuve séparée.
- la conjecture plus large "low-hub binaire positif ssi graphe haut admet un
  strong ordering" reste une piste, pas une candidate intégrée.

Résultat expérimental T036 :

- `low_hub_strong_ordering_report` ajoute un diagnostic borné pour la conjecture
  strong-ordering du cas hub bas binaire ;
- le rapport est hors `candidate.py` et retourne `complete=False` si la limite
  factorielle est atteinte ;
- contrôles positifs : `C4`, `K3,3`, matching, chain/Ferrers ;
- contrôles négatifs : `C6`, `C8`, tree haut à 7 non-hub ;
- exhaustif oracle `m <= 5` sans mismatch ; exhaustif diagnostic `m=6` :
  `5117` strong-ordering, `60` bipartis sans strong-ordering, `27591` non
  bipartis ;
- prochaine intégration possible seulement après preuve de suffisance et
  reconnaissance polynomial-time, ou comme sous-cas positif borné avec garde
  `represents_order`.

Résultat T037 :

- la candidate intègre maintenant ce diagnostic seulement dans le second sens :
  si un strong ordering fournit un ordre témoin et que cet ordre est vérifié
  par le prédicat fixed-order exact puis par `represents_order` quand un PC-tree est
  fourni, la réponse positive est complète ;
- les familles `chain_high_graph_plus_low_hub` et
  `complete_bipartite_high_graph_plus_low_hub` servent de positifs large-n
  indépendants du brute force ;
- benchmarks ciblés star, tailles `5,6,8,10,12,16,20,40,80`, répétitions
  `10` : `0` timeout et `0` incomplet pour les deux familles ; à `n=80`,
  médianes `1.7726s` et `1.8263s` ;
- `make bench` reste `0` timeout et `0` incomplet jusqu'à `n=100` sur
  `mixed/star`, avec médiane `2.0845s` à `n=100`.

Limites T037 :

- aucun échec du diagnostic strong-ordering n'est converti en rejet ;
- la recherche interne reste bornée et partiellement factorielle ;
- le témoin positif peut exister sans être représenté par un PC-tree non-star,
  donc le garde de représentation est obligatoire ;
- il manque encore une famille matching low-hub positive en benchmark ciblé
  pour éviter de suradapter les prochaines preuves aux chain/complete.

Résultat T038 :

- les validations d'ordre fixé dans la candidate passent par
  `passes_bad_side_precircular_cR`, équivalent exact de cR mais en `O(n^3)` ;
- le benchmark fort `mixed/star` reste `0` timeout et `0` incomplet jusqu'à
  `n=100`, avec médiane `0.0275s` et p95 `0.0362s` à `n=100` ;
- les benchmarks ciblés low-hub strong-ordering passent à `0.2485s` médiane
  pour chain et `0.3284s` pour complete à `n=100`, contre environ `4.3s` et
  `4.5s` dans le micro-benchmark simulant l'ancien test de quadruplets.

Limite T038 : le gain ne produit pas de nouveaux ordres et ne prouve pas la
reconnaissance strong-ordering. Il rend seulement les prochaines attaques
large-n moins chères.

Résultat T039 :

- `matching_high_graph_plus_low_hub` ajoute la famille positive manquante, avec
  labels permutables et un ou plusieurs hubs bas ;
- `low_hub_strong_ordering_report` essaie d'abord le couple d'ordres obtenu en
  concaténant les deux parts de chaque composante bipartie. Pour un matching,
  cela aligne automatiquement les mates et trouve le témoin en un seul essai
  même après permutation des labels ;
- le benchmark ciblé `matching_high_graph_plus_low_hub/star`, tailles
  `5,7,9,11,21,41,81,101`, répétitions `10`, timeout `2s`, donne `0` timeout
  et `0` incomplet ; à `n=101`, médiane `0.1810s`, p95 `0.1852s` ;
- la correction associée inclut le niveau bas `0` dans la détection binaire, ce
  qui évite de classer un triangle haut `low=0` comme graphe haut vide.

Limites T039 :

- la priorité composante-alignée n'est qu'un ordre de recherche. Avec
  `max_permutation_pairs=1`, un scan subagent trouve seulement `1542/5117`
  positifs strong-ordering à `m=6` ;
- les statuts `unsupported_permutation_limit` restent incomplets, pas négatifs ;
- un PC-tree non-star peut ne pas représenter le premier témoin strong-ordering.

Résultat T040 :

- la candidate ne s'arrête plus au premier témoin strong-ordering global quand
  un PC-tree est fourni. Elle parcourt l'itérateur borné
  `iter_low_hub_strong_ordering_witnesses` et accepte seulement un ordre qui
  passe le prédicat fixed-order exact et `represents_order(T, order)` ;
- régression non-star : matching low-hub `n=18`, racine `C`, deux blocs `P`.
  Le PC-tree a une borne de frontiers au-dessus de la limite exacte, les
  `64` premiers samples ne sont pas cR, mais un témoin cR représenté existe ;
- résultat observé : le nouveau chemin trouve un témoin représenté après `761`
  couples de permutations, avec `complete=True` positif. Le benchmark ciblé
  matching/star reste `0` timeout et `0` incomplet jusqu'à `n=101`.

Limites T040 :

- la recherche reste bornée par `LOW_HUB_STRONG_ORDERING_PERMUTATION_LIMIT` ;
- aucun échec de l'itérateur n'est un rejet ;
- la reconnaissance strong-ordering reste énumérative, même si la suffisance du
  témoin `hubs,A,B` est maintenant documentée comme preuve bad-side.

Résultat T041 :

- `permuted_chain_high_graph_plus_low_hub` ajoute la famille chain/Ferrers
  relabellisée, qui bloquait l'énumération factorielle du diagnostic
  strong-ordering ;
- `low_hub_ferrers_strong_ordering_report` détecte un graphe haut Ferrers en
  vérifiant l'emboîtement des voisinages d'une part, puis construit l'ordre
  strong-ordering polynomialement ;
- `candidate.py` l'utilise seulement comme témoin positif : l'ordre est encore
  validé par `passes_bad_side_precircular_cR` et par `represents_order` si un
  PC-tree est fourni ;
- benchmark ciblé `permuted_chain_high_graph_plus_low_hub/star`, tailles
  `9,11,15,17,21,41,81,101`, répétitions `10`, timeout `2s` : `0` timeout et
  `0` incomplet ; à `n=101`, médiane `0.2606s`, p95 `0.2677s`.

Limites T041 :

- Ferrers est suffisant, pas nécessaire : matching low-hub reste un positif
  non-Ferrers ;
- le témoin Ferrers construit peut ne pas être représenté par un PC-tree
  non-star même si l'oracle PC-tree est positif ; T041 ajoute une régression où
  la candidate doit continuer la recherche et trouve un témoin représenté ;
- un tri par degrés seulement n'est pas un substitut au test d'inclusion des
  voisinages ;
- un échec Ferrers ne prouve rien et ne doit pas être converti en rejet.

Résultat T042 :

- `permuted_disjoint_chain_high_graph_plus_low_hub` ajoute la famille où le
  graphe haut est une union de composantes chain/Ferrers relabellisées ;
- avant T042, cette famille saturait la limite de `100000` couples de
  permutations dès `n=17` et la candidate restait placeholder sur star ;
- `low_hub_component_ferrers_strong_ordering_report` reconnaît chaque composante
  Ferrers, concatène les composantes dans le même ordre côté `A` et côté `B`,
  puis construit un témoin strong-ordering ;
- `candidate.py` l'utilise seulement comme témoin positif vérifié par
  `passes_bad_side_precircular_cR` et `represents_order` ;
- benchmark ciblé `permuted_disjoint_chain_high_graph_plus_low_hub/star`,
  tailles `13,17,21,31,41,81,101`, répétitions `10`, timeout `2s` : `0`
  timeout et `0` incomplet ; à `n=101`, médiane `0.2433s`, p95 `0.2454s`.

Limites T042 :

- union de composantes Ferrers est un sous-cas strict des graphes bipartis à
  strong ordering ; un petit graphe connecté non-Ferrers strong-ordering reste
  hors certificat ;
- si l'ordre des composantes diffère côté `A` et côté `B`, la preuve est fausse
  et deux arêtes disjointes suffisent à produire une violation ;
- un cas non-star `n=17` avec matching high graph a un témoin représenté connu,
  mais la candidate actuelle peut rester incomplète parce que l'intersection
  PC-tree/ordres component-wise n'est pas encore résolue ;
- un échec component-Ferrers ne prouve rien et ne doit pas être converti en
  rejet.

Résultat T043 :

- `pc_tree_guided_low_hub_matching_witness_report` ajoute un certificat positif
  polynomial-like pour le sous-cas matching haut avec hubs bas et PC-tree
  fourni ;
- le rapport est sample-first : il teste `sample_frontier(T)` et son inverse
  avant toute énumération bornée, puis ne parcourt des frontiers canoniques que
  si ce premier témoin échoue ;
- `candidate.py` l'utilise seulement après validation directe cR et
  `represents_order`, avec le solver
  `candidate_low_hub_pc_tree_guided_matching_witness` ;
- le cas non-star T042 `n=17` est résolu avec `templates_checked=1`,
  `frontiers_sampled=0`, `segments_checked=10` ;
- le cas non-star T040 `n=18` passe d'un témoin trouvé après `761` couples de
  permutations à `templates_checked=1`, `frontiers_sampled=0`,
  `segments_checked=3` ;
- `make bench` reste à `0` timeout et `0` incomplet jusqu'à `n=100`; à `n=100`,
  médiane `0.0314s`, p95 `0.0369s`, fit polynomial empirique `p ~= 1.80`.

Limites T043 :

- matching haut seulement : ce n'est pas une reconnaissance générale des
  graphes bipartis à strong ordering ;
- les hubs peuvent devoir être séparés dans un ordre représenté ; T043 force un
  bloc de hubs et manque donc un positif split-hubs `n=6` ;
- `frontier_limit` peut cacher un positif : un cas `n=8` échoue à `64` et
  réussit à `80` ;
- aucun échec du rapport ne doit être converti en rejet.

Résultat T044 :

- le même rapport teste désormais la projection du frontier avant la
  construction segmentaire : si les endpoints du matching forment
  `seq + mate(seq)` après suppression des hubs, le frontier lui-même est
  retourné comme témoin ;
- le split-hubs `n=6` de T043 devient positif avec
  `projected_frontiers_checked=1` et `segments_checked=0` ;
- une régression candidate large `n=12` avec hubs séparés et deux blocs `P`
  passe par `candidate_low_hub_pc_tree_guided_matching_witness`, alors que le
  témoin component-Ferrers canonique n'est pas représenté ;
- le cas non-crossing C `n=6` reste négatif exact ;
- `make bench` reste à `0` timeout et `0` incomplet jusqu'à `n=100`; à `n=100`,
  médiane `0.03139s`, p95 `0.03742s`, fit polynomial empirique `p ~= 1.79`.

Limites T044 :

- la caractérisation est pour un ordre fixé dans le sous-cas matching, pas une
  décision PC-tree compacte ;
- l'API `PCNode` actuelle sait énumérer des frontiers et tester un ordre, mais
  pas intersecter directement avec `seq + mate(seq)` ;
- le cas frontier tardive `n=8` reste manqué à `frontier_limit=64` ;
- un échec T044 reste incomplet.

Résultat T045 :

- `exact_low_hub_matching_projection_search_report` décide exactement le
  sous-cas matching low-hub si l'ensemble des candidats `seq + mate(seq)` avec
  hubs insérés est épuisé sous `max_candidate_orders` ;
- la candidate l'appelle seulement après les certificats rapides T043/T044 et
  seulement si le PC-tree dépasse déjà la borne exacte générale de frontiers ;
- le cas frontier tardive `n=8` est trouvé par le rapport exact, ce qui explique
  le positif sans dépendre d'un frontier précoce ;
- un rigide non-crossing `n=12` est rejeté complètement côté candidate :
  `21120` candidats uniques, `0` représenté, `0` check cR payé ;
- la correction lazy permet de trouver un témoin `n=13` sous `100000`
  candidats uniques malgré une borne brute supérieure à `100000` ;
- `make bench` reste à `0` timeout et `0` incomplet jusqu'à `n=100`; à `n=100`,
  médiane `0.03311s`, p95 `0.03756s`, fit polynomial empirique `p ~= 1.81`.

Limites T045 :

- limite combinatoire, pas polynomial-time ;
- la limite candidate reste `100000` pour éviter de ralentir les benchmarks ;
- les cas T040/T042 restent mieux traités par T043, et les placeholders mixed
  `n=17` ne sont pas résolus ;
- un dépassement de limite reste incomplet, jamais négatif.

Résultat T046 :

- `exact_low_hub_matching_projected_pc_tree_search_report` enlève le facteur
  combinatoire des hubs du sous-cas T045 : la borne devient `2^m * m!` sur les
  projections du matching, au lieu de multiplier par tous les placements
  possibles des hubs ;
- le relèvement récursif garde la contrainte de représentation du PC-tree
  original, donc un enfant `P/C` dont les endpoints projetés sont séparés par un
  autre enfant est rejeté ;
- côté candidate, cette recherche est appelée avant l'énumération complète T045
  et seulement lorsque le PC-tree dépasse déjà la borne exacte générale ;
- le cas rigide non-crossing `n=12` est rejeté après `192` projections et `0`
  ordre relevé, au lieu de parcourir des milliers d'ordres complets ;
- un stress `5` paires + `8` hubs avec chaque paire enfermée dans son propre
  enfant `P` est rejeté complètement par la candidate, sans payer les
  placements de hubs.

Limites T046 :

- le sous-cas est toujours matching low-hub seulement ;
- `projection_limit_exceeded` reste incomplet ;
- l'énumération des ordres de paires reste factorielle et doit être remplacée
  par une vraie DP/CSP avant de revendiquer une complexité polynomiale ;
- le benchmark `mixed/star` peut rester vert sans prouver que cette branche est
  générale, car beaucoup de positifs restent des témoins certifiés ponctuels.

## Témoin cycle par distances minimales

Statut : certificat positif intégré pour tout PC-tree du scaffold où le témoin
est représenté, pas critère complet.

Si les arêtes de distance minimale positive forment un cycle simple couvrant
tous les sommets, `candidate.py` reconstruit cet ordre. Il l'accepte seulement
si l'ordre passe `is_precircular_order_cR` et si la représentation est sûre :
pas de PC-tree, ou `represents_order(T, order)` vrai pour le scaffold P/C/leaf.

Résultat T018 :

- `permuted_cycle/star` grandes tailles passe par
  `candidate_minimum_distance_cycle_witness` ;
- benchmark ciblé : `0` timeout et `0` incomplet pour `permuted_cycle/star`,
  avec la branche minimum-cycle utilisée pour tous les `n > 8` ;
- `paired_farthest` ne déclenche pas ce témoin et reste un stress négatif ;
- benchmark ciblé : `paired_farthest/star` garde `60` runs incomplets sur les
  tailles `n > 8`, et `paired_farthest/mixed` en garde `40` ;
- un contre-exemple `n=6` montre que "graphe minimum = cycle" ne suffit pas pour
  cR ; le garde fixed-order est donc indispensable ;
- à T018, les PC-trees non-star étaient volontairement exclus de cette branche
  faute de test de représentation non énumératif.

Résultat T019 :

- `represents_order` teste maintenant l'appartenance d'un ordre fixé au
  PC-tree scaffold sans énumérer les frontiers quand `limit is None` ;
- le test parse récursivement des blocs contigus d'enfants, avec rotations et
  renversement autorisés seulement au root circulaire ;
- comparaison exhaustive contre `enumerate_frontiers` sur petits arbres :
  `11837` checks locaux sans désaccord ;
- `cycle/mixed` grandes tailles passe par
  `candidate_minimum_distance_cycle_witness` pour tous les `n > 8` ;
- `permuted_cycle` avec labels aléatoires reste rarement représenté par
  balanced/mixed dans le scaffold, donc la branche n'est pas forcée hors cas
  réellement représentés.

## Artefacts

- `permuted_cycle_metric`;
- `paired_farthest_matching`;
- `instance_by_kind(..., kind="permuted_cycle")`;
- `instance_by_kind(..., kind="paired_farthest")`;
- `has_at_most_one_bad_witness_per_pair`;
- `sample_frontier`;
- `candidate_minimum_distance_cycle_witness`;
- `candidate_paired_farthest_matching_witness`;
- `pc_tree_guided_low_hub_matching_witness_report`;
- `pc_tree_projected_matching_frontier_found`;
- `exact_low_hub_matching_projection_search_report`;
- `represents_order` non énumératif quand `limit is None`;
- `--diagnostics-up-to` dans `tools/pc_circular_complexity_benchmark.py`;
- `make bench-piste-f`.

## Prochaine action

Utiliser `paired_farthest` pour casser tout filtre local ou farthest-like.
Utiliser `permuted_cycle` comme sous-cas où un futur solver devrait reconnaître
un témoin caché sans brute force star.
Chercher ensuite un sous-cas plus structuré que le critère universel, par
exemple paired-farthest représenté par PC-tree non-star avec choix de témoin
prouvé, matching low-hub avec hubs séparés, planted-cycle représenté par un
vrai PC-tree Hsu/McConnell, ou degré interne borné.

## Résultat T048 - Support sharing comme signal de complexité

Statut : preuve expérimentale de partage de supports, pas borne asymptotique.

Le regroupement des atoms bad-side par support donne de grands gains sur les
produits de domaines : sidecar Piste F observe des ratios de produit groupé
entre `8x` et `43x` sur `n=6..10` pour `cycle/random/paired_farthest`, et le
benchmark interne rapide mesure `72256 -> 6224`.

Limite : le coût de test des atoms reste inchangé dans l'implémentation naïve
(`atom_checks=72256`). Pour transformer ce signal en résultat de complexité, il
faut soit borner la taille des groupes de support, soit compiler chaque groupe
en une contrainte plus compacte que la liste de ses atoms.

## Résultat T049 - Early stop dans les groupes de support

Statut : amélioration empirique de coût, pas borne de complexité.

La variante first-hit réduit le scan atom-par-atom en s'arrêtant dès qu'une
affectation de support est prouvée mauvaise. Sur `make bench-csp-quick`,
`atom_checks` passe de `72256` à `41872`. Le sidecar complexité mesure `160` cas
jusqu'à `n=8` et observe `48888/87328` checks évités, soit `56.0%`.

Limite : equal-distance n'a aucun atom bad-side, donc aucun gain ; les cas où
aucun atom ne hit rapidement paient encore presque tout le groupe. Ce résultat
ne donne pas de borne asymptotique sans structure sur l'ordre des atoms ou la
taille des groupes.

## Résultat T050 - No-hit comme coût dominant restant

Statut : diagnostic de complexité empirique.

Le profil T050 montre que la moitié environ des affectations de support de la
gate CSP rapide n'ont aucun atom hit : `3320/6224`, soit `0.5334`. Ces no-hit
coûtent `30520` checks, proche des `30384` checks sauvés sur les hits.

Par famille `n=4..8`, le no-hit est faible sur random (`21.9%`) et matching
low-hub (`25.7%`), mais fort sur cycle (`50.0%`) et paired-farthest (`44.4%`).
Cela suggère que l'obstacle de complexité restant n'est pas seulement trouver
un meilleur ordre de scan, mais certifier rapidement l'absence d'atom violé dans
un groupe.

## Résultat T051 - Pair-side exact mais non plus rapide

Statut : résultat empirique de complexité, hors candidate.

Le benchmark interne enrichi confirme les familles no-hit adverses. Sur la gate
rapide, les no-hit coûtent surtout :

- `cycle` : ratio no-hit `0.500`, part des checks no-hit `0.801`,
  couverture unaire no-hit `0.0` ;
- `ultrametric` : ratio no-hit `0.900`, part `0.965`, couverture unaire
  `0.889` ;
- `non_strict` : ratio no-hit `0.962`, part `0.996`, couverture unaire
  `0.960` ;
- `block` : ratio no-hit `0.750`, part `0.867`, couverture unaire `0.667` ;
- `paired_farthest` : ratio no-hit `0.333..0.455`, couverture unaire faible.

Le test pair-side/composantes n'a aucun mismatch sur `192` lignes, mais son
travail agrégé est `1.7732` fois le first-hit mesuré. Cela réfute l'idée qu'une
simple reformulation par paires suffit à améliorer la complexité sans cache ou
DP supplémentaire.

## Résultat T052 - Cache triple et modèle bitset

Statut : mesure de complexité interne, hors candidate.

Le cache par `(pair,witness,signature_triple)` réduit fortement les projections
de côtés (`24690` hits pour `12778` misses sur la gate rapide), mais le travail
total pair-side cached reste `1.1836x` first-hit. Par famille, il gagne sur
`cycle`, `block`, `ultrametric`, `non_strict`, mais perd sur `random`,
`permuted_cycle` et `paired_farthest`.

Le modèle bitset-composantes descend à `0.6650x` first-hit globalement. Ratios
par famille/tree observés : environ `0.48` pour `ultrametric`, `0.55` pour
`block`, `0.59` pour `cycle`, `0.83..0.84` pour `random`, `0.75..0.89` pour
`permuted_cycle`, et `1.01..1.07` pour `paired_farthest`.

Conclusion complexité : le goulot n'est plus seulement la projection de côtés ;
il faut compresser les checks de composantes. `paired_farthest` reste la famille
à garder comme stress test pour tout modèle bitset.

## Résultat T053 - Bitset réel versus modèle

Statut : résultat de complexité empirique hors candidate.

T053 transforme le modèle bitset T052 en profil exécuté. Sur
`make bench-csp-quick`, il garde `0` mismatch mais le coût réel est moins bon
que le modèle :

- first-hit atom-checks : `41872` ;
- projection bitset : `27822`, ratio `0.6645` ;
- bitset réel avec visites de témoins : `44936`, ratio `1.0732` ;
- visites de témoins : `29868` ;
- hits/misses du cache de composantes : `3000/12068`.

Lecture par familles sur la gate rapide :

- `ultrametric`, `non_strict`, `block` et `cycle` restent les contrôles où le
  bitset réel est proche ou meilleur que first-hit ;
- `random`, `permuted_cycle` et surtout `paired_farthest` restent les stress où
  les visites de témoins rendent le profil plus cher ;
- `paired_farthest/mixed` est autour de `1.55x` en coût réel sur l'agrégat
  rapide, malgré un modèle de projection autour de `1.07x`.

Conclusion : la projection de masques reste un signal utile, mais une
implémentation directe ne donne pas encore de gain. La prochaine mesure de
complexité doit compter les états distincts de masques par rapport aux
affectations de support, surtout sur `random`, `permuted_cycle` et
`paired_farthest`.

## Résultat T054 - Cardinalité des états de masques

Statut : mesure de complexité empirique hors candidate.

Le profil T054 compte les états distincts de masques par support groupé. Sur
`make bench-csp-quick`, les compteurs principaux sont :

- `6224` affectations de support vues ;
- `2920` états distincts, ratio `0.4692` ;
- bucket moyen `2.1315`, bucket max `4` ;
- `0` état mixte, `0` mismatch ;
- coût complet de construction de l'état `1.9412x` first-hit ;
- coût de projection `0.9038x` first-hit.

Le probe stress `n=8` garde la même forme : ratio global `0.4921`, bucket moyen
`2.032`, bucket max `4`. Par famille, `cycle`, `non_strict`,
`permuted_cycle`, `random` et `paired_farthest` restent tous autour de
`0.45..0.50`.

Conclusion complexité : la compression par état de masque existe, mais elle est
faible et ne croît pas clairement avec `n` dans les probes bornées. Cela réfute
une version optimiste de la DP bitset où les états locaux seraient massivement
moins nombreux que les affectations. La prochaine piste doit soit trouver un
état plus quotienté mais encore sound, soit changer d'axe vers un sous-cas
prouvable ou une obstruction de complexité.

## Résultat T055 - Quotients plus abstraits

Statut : mesure de complexité empirique hors candidate.

Les quotients T055 réduisent davantage la cardinalité locale :

- `full` : ratio `0.4692` ;
- `mask_multiset` : `0.3959` ;
- `hit_components` / `hit_pairs` : `0.2121` ;
- `decision_only` : `0.1825` ;
- contrôle négatif `side_blind_schema` : `0.1250` mais `358` états mixtes.

Le probe stress `n=8` confirme la tendance : `mask_multiset` reste autour de
`0.4088`, `hit_components` autour de `0.2273`, et le contrôle sans masques a
`181` états mixtes.

Conclusion complexité : il existe des quotients locaux plus forts, mais les
plus compressés sont des vues très proches de la décision locale et ne donnent
pas une structure DP composable. Le quotient `mask_multiset` est le meilleur
candidat non tautologique à tester ensuite contre un contexte parent.

## Résultat T056 - Collisions contextuelles des quotients

Statut : mesure de complexité empirique hors candidate.

T056 mesure les collisions de contexte pour les quotients T055. Le coût est
volontairement borné dans `make bench-csp-quick` par `max_pairs=20` paires de
supports voisins par ligne ; les lignes incomplètes sont visibles dans le JSON.

Sur la gate CSP rapide :

- `35728` affectations contextuelles inspectées ;
- `1828` paires de supports profilées ;
- `74` lignes incomplètes sur ce diagnostic borné ;
- `assignment_signature` a `0` collision, comme contrôle ;
- `mask_multiset` a `856` collisions contextuelles ;
- `full` a `190` collisions contextuelles ;
- les quotients plus compressés (`hit_components`, `decision_only`) ont des
  milliers de collisions.

Sur le probe stress `n=8` avec repeats `2` :

- `9072` affectations contextuelles ;
- `400` paires de supports profilées ;
- `20` lignes incomplètes ;
- `mask_multiset` a `26` collisions ;
- `full` a `8` collisions ;
- `assignment_signature` reste à `0`.

Interprétation complexité : la compression locale de T055 n'est pas suffisante
comme signal de tractabilité. Même l'état de masques complet peut être trop
pauvre pour composer des supports voisins. Une future DP devra payer soit par
des états plus riches, soit par des obligations ouvertes, ce qui affaiblit
l'hypothèse d'une petite table d'états issue des seuls masques fermés.

## Résultat T057 - Coût des obligations ouvertes one-hop

Statut : mesure empirique hors candidate.

T057 teste le prix d'un état enrichi par les réponses ouvertes vers supports
voisins. Sur `make bench-csp-quick`, le profil est encore borné à
`max_pairs=20`, avec les incomplétudes visibles :

- `192` lignes supportées, `0` mismatch ;
- `6224` affectations locales inspectées ;
- `35728` checks de réponses ouvertes ;
- `1828` paires de supports profilées ;
- `74` lignes incomplètes sur le diagnostic ouvert ;
- moyenne `5.7404` entrées de bord par affectation locale.

Ratios d'états sur la gate CSP rapide :

- `boundary_response` : `1374` états, ratio `0.2208`, bucket moyen `4.5298` ;
- `local_boundary_response` : `1634` états, ratio `0.2625`, bucket moyen
  `3.8091` ;
- `mask_multiset_plus_boundary` : `2671` états, ratio `0.4291`, bucket moyen
  `2.3302` ;
- `full_plus_boundary` : `2969` états, ratio `0.4770`, bucket moyen `2.0963`.

La réparation a un coût net : `mask_multiset_plus_boundary` est à peine plus
gros que `mask_multiset` (`0.4291` contre `0.3959`) et supprime les mélanges de
réponse de bord mesurés, mais il reste proche des états fermés complets.
`boundary_response` compresse davantage, mais il mélange le hit local et doit
être combiné avec celui-ci pour une signature de production.

Probe stress `n=8`, repeats `2` : `20` lignes, `0` mismatch, `2088`
affectations locales, `9072` checks ouverts, `20` lignes incomplètes.
Les ratios restent dans la même zone : `local_boundary_response=0.2126`,
`mask_multiset_plus_boundary=0.4119`, `full_plus_boundary=0.4895`.

Interprétation complexité : les obligations ouvertes one-hop ne sont pas
immédiatement quasi-injectives, donc la piste DP n'est pas réfutée par T057.
Mais le coût est déjà énumératif et borné ; il faut maintenant mesurer une
composition de second ordre. Si celle-ci force des tables de réponses pour des
chaînes de supports, la signature risque de réencoder l'énumération globale.

## Revue externe post-T057 - largeur et dureté

Statut : orientation de complexité, non preuve.

La revue externe GPT 5.5 Pro propose de séparer trois lectures de complexité :

- sous-cas booléen : contraintes de quartets de portée `<= 2` sur variables
  booléennes, donc réduction 2-SAT si le lemme de portée est validé ;
- sous-cas treewidth : CSP exact de quartets résolu par DP en
  `O(n^4 q^(w+1))` quand le domaine maximal `q` et la treewidth `w` sont bornés ;
- piste NP-hardness : cataloguer les relations binaires réalisables entre deux
  petits nœuds `P` pour voir si une relation de disequality domaine 3 ou une
  autre relation CSP dure peut être simulée.

Action prioritaire Piste F : construire un catalogue expérimental de relations
binaires induites par deux petits nœuds `P`, en gardant visibles les contraintes
parasites dues aux distances globales. Si toutes les relations observées restent
bijunctives ou fortement structurées, cela renforce la piste algorithmique ; si
une relation dure apparaît, elle nourrit une réduction NP-hard plus sérieuse.

## Résultat T058 - Signal largeur/2-SAT par quartets

Statut : mesure de complexité empirique hors candidate.

T058 ajoute une mesure directe de la portée effective des contraintes de
quartets. Sur `make bench-csp-quick`, tous les quartets profilés ont une portée
effective d'acceptation au plus binaire :

- `quartet_scope_quartets_profiled=2688` ;
- support structurel conservateur taille `3` pour tous les quartets ;
- portée effective type taille `2` pour tous les quartets ;
- portée effective acceptation taille `0` pour `1536` quartets et taille `2`
  pour `1152` quartets ;
- `quartet_scope_projection_mismatches=0` ;
- `quartet_scope_two_sat_candidate_quartet_count=2688` ;
- `quartet_scope_non_boolean_effective_acceptance_scope_count=0`.

Interprétation : pour les arbres balanced/mixed binaires de la gate, la relation
de quartet observée tombe dans le sous-cas 2-SAT potentiel. Ce n'est pas une
preuve du problème général : les probes fanout `3` gardent une portée effective
`<=2` mais introduisent des domaines non booléens (`630` quartets non booléens
sur `180` cas stress), ce qui renvoie vers le catalogue de relations binaires.

Prochaine mesure complexité : construire le graphe primal des relations
effectives et calculer une borne de treewidth. Sans cette largeur, le fait que
les contraintes soient binaires ne suffit pas à garantir un algorithme
polynomial efficace sur grands `P`.

## Résultat T059 - Graphe primal et catalogue relationnel

Statut : mesure empirique de largeur et de relations, hors candidate.

T059 ajoute `quartet_effective_relation_report`, qui passe des portées T058 aux
relations CSP fusionnées par scope effectif. Les métriques de complexité
importantes sont maintenant visibles dans `make bench-csp-quick` :

- nombre de relations fusionnées ;
- classes de relations : constantes, unaires, binaires booléennes, binaires non
  booléennes, haute arité ;
- `row_class` séparant clairement candidat 2-SAT et catalogue non booléen ;
- graphe primal des scopes fusionnés ;
- bornes greedy min-fill/min-degree de treewidth ;
- compteur de mismatches relation-CSP vs cR direct.

Sur les tests ciblés :

- `cycle_metric(5)` avec `balanced_pc_tree(5, kind="mixed")` donne `3`
  relations binaires booléennes fusionnées, treewidth upper bound `2`, et `0`
  mismatch ;
- `equal_distance_instance(6)` C-only donne une tautologie de scope vide et
  aucun sommet actif ;
- `four_local_non_cr_core()` C-only donne une relation constante rejetante :
  c'est un UNSAT réel, pas un cas `unsupported` ;
- trois blocs `P3` sur `cycle_metric(9)` donnent `6` relations binaires non
  booléennes fusionnées, treewidth upper bound `3`, et un catalogue non 2-SAT ;
- trois blocs `P3` sur `paired_farthest_matching(9, seed=7)` gardent aussi les
  relations non booléennes visibles et trouvent `0` affectation cR.

Interprétation complexité : la portée binaire ne suffit pas à conclure 2-SAT.
Le critère 2-SAT exige en plus que tous les domaines effectifs soient booléens.
Les nœuds `P3` produisent des domaines de taille `6`, donc ils alimentent la
piste relation-catalog / dureté potentielle. La treewidth mesurée est une borne
heuristique sur le graphe primal du scaffold, pas une preuve de complexité.

Prochaine action Piste F : comparer les catalogues non booléens sur familles
random, cycle, paired-farthest, equal-distance et gros `P`, puis chercher une
relation de type égalité/disequality/permutation sur domaines `3+` qui pourrait
servir de gadget de dureté. Toute hypothèse NP-hard doit rester marquée
conjecture tant que les contraintes parasites dues à la globalité de `D` ne
sont pas contrôlées.

## Résultat T060 - 2-SAT booléen effectif

Statut : sous-cas algorithmique exact dans le scaffold T059, hors candidate.

T060 ajoute `solve_quartet_2sat`, qui résout les lignes
`row_class="two_sat_candidate"` du rapport relationnel. Le coût de résolution
après construction des relations est linéaire dans le nombre de clauses 2-CNF ;
la construction actuelle des relations reste énumérative et ne constitue donc
pas encore une solution générale en fonction de `n` et `|T|`.

Sur `make bench-csp-quick` :

- `192` lignes supportées ;
- `0` mismatch et `0` `quartet_relation_validation_mismatches` ;
- `192` lignes 2-SAT complètes ;
- `143` lignes SAT ;
- `49` lignes UNSAT par clause vide ;
- `0` incomplet 2-SAT ;
- `1167` clauses générées, dont `1118` binaires et `49` vides ;
- `0` échec de témoin SAT.

Interprétation complexité : ce résultat valide le sous-cas booléen du CSP de
quartets comme cible 2-SAT propre. Il ne traite pas les domaines non booléens
des nœuds `P3+`, et ne doit pas être utilisé pour conclure `False` dans la
candidate tant que la preuve de suffisance du modèle relationnel n'est pas
écrite. Le prochain vrai levier de complexité est donc soit une intégration
positive-only vérifiée, soit une DP par treewidth sur les relations non
booléennes.

## Résultat T061 - DP relationnelle à treewidth bornée

Statut : sous-cas FPT expérimental dans le scaffold T059, hors candidate.

T061 ajoute une résolution par élimination de facteurs pour les relations de
quartets matérialisées. Le solveur calcule une treewidth exacte sous cap,
refuse les lignes trop larges comme incomplètes, et traite les domaines non
booléens tant que le produit des domaines des bags reste borné par la largeur.

Sur `make bench-csp-quick` :

- `192` lignes supportées ;
- `186` lignes DP complètes ;
- `137` lignes SAT ;
- `49` lignes UNSAT dans le CSP relationnel ;
- `6` lignes incomplètes par `treewidth_cap_exceeded` ;
- treewidth exacte maximale `3` sur les lignes complètes ;
- `0` échec de témoin SAT.

Tests de complexité ajoutés :

- trois blocs `P3` donnent des domaines taille `6`, non 2-SAT, mais résolubles
  à treewidth `3` ;
- le même schéma en paired-farthest donne un UNSAT relationnel exact ;
- un cap `max_treewidth=2` sur ce cas retourne incomplet, ce qui garde visible
  le paramètre de largeur.

Interprétation complexité : la bonne borne expérimentale est maintenant
`O(m q^(w+1))` après construction des relations, avec `q` taille maximale de
domaine local et `w` treewidth du graphe primal. La construction actuelle du
rapport reste le coût dominant et n'est pas encore une solution polynomiale
générale. Le générateur `p3_block_tree(k)` doit devenir le stress principal pour
montrer quand cette piste devient exponentielle.

## Résultat T062 - Largeur croissante des blocs P3

Statut : stress test de complexité, hors candidate.

T062 ajoute `make bench-width-stress`, qui mesure la famille
`p3_block_tree(k)` sur `cycle`, `paired_farthest` et `equal`.

Résultat du rapport `reports/p3_width_stress.json` :

- `k=2` cycle : treewidth exacte `1` ;
- `k=3` cycle : treewidth exacte `3` ;
- `k=4` cycle : treewidth exacte `4` ;
- `k=5` cycle : treewidth upper bound `5`, mais incomplet sous cap `4` ;
- contrôles equal-distance : treewidth active `0`, toujours SAT ;
- paired-farthest : rejets relationnels constants pour `k>=3` dans ce stress ;
- `0` mismatch de validation et `0` échec de témoin.

Interprétation complexité : cette famille montre que la DP T061 est bien une
piste FPT par largeur, pas une preuve de tractabilité générale. Elle doit rester
dans les benchmarks de recherche pour empêcher une confusion entre "relations
binaires" et "problème facile".

## Résultat T064 - Single P-node : treewidth zéro, domaine factoriel

Statut : stress de complexité sur la taille de domaine, hors candidate.

La revue red-team R003 signale une faiblesse de toute lecture "CSP binaire +
treewidth" : un PC-tree star a une seule variable locale, donc treewidth `0`,
mais le domaine du noeud `P` contient `(n-1)!/2` ordres circulaires.

T064 ajoute `make bench-single-p-stress`. Le rapport
`reports/single_p_domain_stress.json` mesure des familles `equal`, `cycle`,
`random`, `paired_farthest`, `single_quartet` et `four_local_non_cr` sur des
tailles `4..10`.

Résultat observé :

- `30` lignes profilées ;
- `treewidth_zero_rows=30` ;
- `max_domain_size=181440` à `n=10` ;
- `max_complete_domain_size=20160` à `n=9` ;
- `incomplete_exact_count_rows=4` sous limite `25000` ;
- `max_unordered_bad_side_constraints=650` ;
- `cycle n=9` : `1/20160` ordre cR ;
- `random n=9` : `0/20160` ordre cR sur la seed du rapport ;
- equal-distance : tous les ordres inspectés sont cR.

Conclusion : la classification FPT doit au minimum mentionner deux paramètres :
la treewidth du graphe primal et la taille/representabilite compacte des
domaines locaux. Le cas single `P` est maintenant un garde-fou contre toute
revendication de polynomialite fondee seulement sur une largeur faible.

Prochaine action Piste F : cataloguer les relations non booleennes entre petits
noeuds `P`, mais en reportant toujours les contraintes parasites et la taille
des domaines. La piste de durete reste plausible, pas prouvee.

## Résultat T065 - Catalogue non booléen P3/P3

Statut : signal expérimental pour dureté/tractabilité, non preuve.

T065 ajoute `make bench-relation-catalog`. Le rapport
`reports/relation_catalog.json` catalogue les relations effectives fusionnées
entre blocs `P3` sur des arbres `p3_block_tree(2)` et `p3_block_tree(3)`.

Métriques principales :

- `rows=20`, toutes complètes ;
- `validation_mismatches=0` ;
- `binary_non_boolean_relation_instances=38` ;
- `unique_binary_non_boolean_catalog_hashes=27` ;
- `rows_with_constant_reject_parasite=12` ;
- `rows_with_unary_non_boolean_parasite=18` ;
- `max_primal_treewidth_upper_bound=3` ;
- `max_relation_domain_product=36` ;
- densité binaire min `0.0556`, max `0.3333` ;
- `zero_accept_rows=13`.

Conclusion prudente :

- La diversité de relations non booléennes montre que les petits nœuds `P`
  produisent bien un langage plus riche que 2-SAT.
- Les parasites unaires et constantes sont fréquents ; ils peuvent rendre un
  gadget non composable.
- Les UNSAT observés sont `relation_unsat_only`, pas des certificats négatifs
  du problème général.
- Une future piste NP-hard doit isoler une relation utile avec contrôle des
  contraintes parasites et du promise `T=T(D)`.

Prochaine action Piste F : chercher une relation non booléenne plus structurée
dans ce catalogue, par exemple permutation-like, égalité, disequality ou
implication cyclique, puis tenter de l'isoler sans `constant_reject` parasite.

## Résultat T066 - Formes des profils relationnels non booléens

Statut : diagnostic de structure, non preuve.

T066 ajoute `make bench-relation-shapes`. L'outil régénère le catalogue T065,
puis classe chaque profil binaire non booléen par forme et tags de
composabilité. Les classes observées dans `reports/relation_shape_search.json`
sont :

- `sparse_partial_matching` : relation fonctionnelle des deux côtés avec peu
  de tuples acceptés ;
- `partial_bijection` : matching partiel moins sparse ;
- `left_selector` / `right_selector` : un seul côté fonctionnel ;
- `active_two_regular` : support actif 2-régulier ;
- `small_domain_bridge` : relation asymétrique de type `2 x 6` ;
- `total_cover_dense` : relation couvrante non fonctionnelle.

Résultat `make bench-relation-shapes` :

- `catalog_rows=20`, toutes complètes ;
- `validation_mismatches=0` ;
- `binary_relation_instances=38` ;
- histogramme des formes :
  `active_two_regular=10`, `left_selector=5`, `partial_bijection=3`,
  `right_selector=4`, `small_domain_bridge=6`,
  `sparse_partial_matching=9`, `total_cover_dense=1` ;
- `functional_relation_instances=27` ;
- `candidate_gadget_instances=0` ;
- `positive_parasite_free_relation_instances=0` ;
- tous les profils observés ont encore un parasite restrictif dans leur ligne
  de contexte.

Conclusion prudente : les relations ont des formes structurées, ce qui donne
des cibles concrètes pour les prochaines recherches, mais aucune relation
positive n'est encore isolée sans parasite. La piste de dureté doit maintenant
chercher une élimination de parasites ou une composition de chaînes
fonctionnelles ; la piste algorithmique doit expliquer pourquoi ces formes
resteraient compressibles si elle veut aller au-delà d'une classification FPT.

## Résultat T067 - Composition de chaînes/cycles fonctionnels

Statut : diagnostic expérimental, non preuve.

T067 ajoute `make bench-relation-chains`. Le rapport
`reports/relation_chain_probe.json` reconstruit le CSP relationnel complet sur
`p3_block_tree(k)`, classe les relations binaires non booléennes avec la
taxonomie T066, puis compose les profils fonctionnels
`permutation_like`, `sparse_partial_matching`, `partial_bijection` et
sélecteurs.

Métriques principales du benchmark T067 :

- `rows=40`, toutes complètes ;
- `validation_mismatches=0` ;
- `rows_with_functional_relations=31` ;
- `rows_with_restrictive_parasite_free_functional_candidate=2` ;
- `rows_with_restrictive_parasite_free_permutation_like=2` ;
- `rows_with_global_unsat_not_unary_or_constant=1` ;
- `rows_with_functional_cycle_components=2` ;
- `rows_with_functional_cycle_obstruction=1` ;
- `rows_with_constant_reject=28`.

Interprétation prudente :

- Le sweep ciblé `paired_farthest` trouve deux relations `permutation_like`
  positives sans parasite restrictif. Elles ont encore le caveat de scaffold et
  ne prouvent pas un gadget NP-hard.
- Une ligne `five_local_non_cr` donne `interaction_unsat` : les parasites seuls
  et la relation fonctionnelle seule acceptent des affectations, mais leur
  combinaison rejette tout. C'est un contre-signal utile contre les quotients
  qui sépareraient trop agressivement contraintes unaires et binaires.
- Une obstruction de cycle fonctionnel apparaît, mais dans une ligne déjà
  bloquée par `constant_reject`; elle n'est donc pas un gadget autonome.

Prochaine action Piste F : minimiser l'interaction UNSAT et lancer une recherche
promise-aware autour des deux permutations-like `paired_farthest`, en essayant
de supprimer aussi le `constant_accept` ou de le montrer inoffensif.

## Résultat T068 - Noyau UNSAT minimal d'interaction

Statut : diagnostic expérimental, non preuve.

T068 ajoute `make bench-relation-unsat-cores`. Le rapport
`reports/relation_unsat_core_probe.json` cherche des noyaux de cardinalité
minimale dans les lignes `interaction_unsat` du CSP matérialisé.

Métriques principales du benchmark T068 :

- `rows=40`, toutes complètes ;
- `validation_mismatches=0` ;
- `interaction_unsat_rows=1` ;
- `rows_with_minimal_core=1` ;
- `min_core_size=2` ;
- `constant_reject_rows=28`.

Le noyau minimal du cas `five_local_non_cr` sur `p3_block_tree(2)` contient :

- relation `1` : unaire non booléenne sur le bloc `0`, valeurs acceptées
  `[0,1,3,5]` ;
- relation `2` : binaire `sparse_partial_matching` entre `0` et `1`, tuples
  bruts acceptés `[(2,3),(4,1)]` ;
- conflit : projection gauche `[2,4]` disjointe de l'unaire `[0,1,3,5]`.

Interprétation prudente : le signal T067 `interaction_unsat` est maintenant un
artefact minimal et régressé, mais il n'est pas un gadget NP-hard autonome. Il
montre surtout qu'une relation fonctionnelle sparse peut devenir contradictoire
avec une seule contrainte unaire parasite.

## Résultat T069 - Robustesse promise-aware des profils `permutation_like`

Statut : diagnostic expérimental, non preuve.

T069 ajoute `make bench-permutation-like`. Le rapport
`reports/permutation_like_probe.json` teste les profils `permutation_like`
`paired_farthest` sur `p3_block_tree(2)` contre une énumération exhaustive des
ordres quasi-circulaires exacts en `n=6`.

Métriques principales du benchmark T069 :

- `rows=128`, toutes complètes ;
- `validation_mismatches=0` ;
- `permutation_like_rows=11` ;
- `parasite_free_permutation_like_rows=11` ;
- `permutation_like_exact_quasi_scaffold_rows=11` ;
- `exact_quasi_scaffold_rows=11` ;
- `anomaly_count=0`.

Conclusion prudente : les profils `permutation_like` observés sont plus
prometteurs que de simples artefacts de scaffold arbitraire en petite taille,
car ils coïncident avec l'exactitude quasi-circulaire du scaffold et les
affectations acceptées restent quasi. La piste dureté/gadget reste ouverte, mais
les obligations fortes demeurent : passage à grande taille, reconstruction
Hsu/McConnell, contrôle des parasites et composition de plusieurs relations.

## Résultat T070 - Composition multi-blocs des profils `permutation_like`

Statut : diagnostic expérimental, non preuve.

T070 ajoute `make bench-permutation-composition`. Le rapport
`reports/permutation_composition_probe.json` cherche des composantes de plusieurs
arêtes `permutation_like` dans `paired_farthest/P3x{k}`.

Métriques principales du benchmark T070 :

- `rows=192`, toutes complètes ;
- `validation_mismatches=0` ;
- `permutation_like_rows=6` ;
- `permutation_like_relation_instances=6` ;
- `multi_permutation_rows=0` ;
- `composition_candidate_rows=0` ;
- `max_permutation_component_edges=1`.

Par taille de scaffold :

- `k=2` : `5` lignes `permutation_like`, toutes isolées et propres ;
- `k=3` : `0` ligne `permutation_like`, `56` lignes avec `constant_reject` ;
- `k=4` : `1` ligne `permutation_like`, bloquée par parasites, et `64` lignes
  avec `constant_reject`.

Conclusion prudente : le gadget local T069 ne se compose pas directement dans
ce générateur. La piste dureté doit soit construire une autre famille globale
de `D`, soit accepter que `paired_farthest/P3x{k}` produit surtout des parasites
dès que plus de deux blocs interagissent.

## Résultat T071 - Composantes toutes relations non booléennes

Statut : diagnostic expérimental, non preuve.

T071 ajoute `make bench-relation-components`. Le rapport
`reports/relation_component_probe.json` élargit T070 en construisant les
composantes de toutes les relations binaires non booléennes observées dans
`paired_farthest/P3x{k}`.

Critère de succès recherché : une composante multi-arêtes parasite-free, avec
des affectations acceptées. Ce serait un candidat de gadget plus robuste que
les bijections isolées T070.

Métriques principales du benchmark T071 :

- `rows=192`, toutes complètes ;
- `validation_mismatches=0` ;
- `binary_nonboolean_relation_instances=617` ;
- `multi_edge_component_rows=127` ;
- `parasite_free_multi_edge_rows=0` ;
- `sat_parasite_free_multi_edge_rows=0` ;
- `rows_with_constant_reject=156` ;
- `max_component_edges=6`, `max_component_nodes=5`.

Les formes multi-arêtes observées sont dominées par `active_two_regular`
(`333` occurrences dans les composantes multi-arêtes), puis
`small_domain_bridge` (`90`), `total_cover_dense` (`34`), sélecteurs gauche et
droite (`33` et `31`) et `partial_bijection` (`16`). Aucun de ces réseaux n'est
isolé des parasites dans le sweep.

Risque principal : si les composantes multi-arêtes n'apparaissent que sous
`constant_reject` ou unaire restrictive, le signal est un blocage de scaffold,
pas une preuve qu'une autre construction globale de `D` ne puisse pas isoler la
relation.

Conclusion prudente : T071 réfute une explication trop étroite de T070
centrée uniquement sur `permutation_like`. Des réseaux non booléens existent,
mais leur usage comme gadgets est bloqué par parasites dans la famille
`paired_farthest/P3x{k}`. La prochaine piste F la plus concrète est de cibler
`sparse_partial_matching` et les conflits unaire+binaire T068, car c'est déjà un
noyau minimal explicite.
