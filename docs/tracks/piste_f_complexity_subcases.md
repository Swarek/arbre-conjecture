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
