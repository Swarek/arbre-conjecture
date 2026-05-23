# Piste C - SAT / CSP / contraintes d’ordre cyclique

## Question

Peut-on encoder exactement les choix locaux du PC-tree et les quartets cR
interdits en CSP, puis exploiter cet encodage pour un solver ?

## Intuition

Chaque nœud interne a un choix local :

- nœud `C` : orientation forward/reverse ;
- nœud `P` : permutation de ses enfants.

Une affectation complète détermine une frontier. Les quartets cR interdits
deviennent des nogoods sur les choix locaux qui rendent le quartet cycliquement
ordonné de façon interdite.

## Encodage proposé

Statut : conjecture algorithmique / non intégré.

Variables :

- une variable par nœud interne ;
- domaine `{forward, reverse}` pour `C` ;
- domaine des permutations d’enfants pour `P`, d’abord limité aux petits degrés.

Contraintes :

- exactement une valeur par variable ;
- pour chaque quadruplet interdit `(x,y,z,t)`, interdire les affectations où
  `x,y,z,t` apparaissent dans cet ordre cyclique.

Première cible :

- backtracking finite-domain sans dépendance SAT externe ;
- `n <= 7`;
- degrés internes `<= 3`;
- comparaison stricte avec l’oracle exact.

## Obstacles

Les grands nœuds `P` donnent des contraintes naturellement 4-aires sur l’ordre
cyclique de branches. Une réduction 2-SAT pure serait probablement fausse sans
structure supplémentaire.

## Tests à créer

- les frontiers générées par affectations doivent égaler `enumerate_frontiers`;
- les ordres acceptés par CSP doivent égaler les ordres cR exacts sur petits
  arbres balanced/mixed ;
- les régressions non strictes doivent passer ;
- un gros `P` doit être traité comme permutation-domain ou explicitement marqué
  non 2-SAT.

## Tentative T009 - Prop. 4.5 comme nogood de frontier

Statut : preuve expérimentale / scaffold, non intégré dans `candidate.py`.

Changement : `prop45_nogood_frontier_report` énumère des frontiers bornées ou
complètes, filtre optionnellement les ordres non quasi-circulaires, puis compare
le filtre Prop. 4.5 avec `is_precircular_order_cR`. Le rapport expose le premier
rejet, les faux positifs, les faux négatifs, un témoin accepté et si
l’énumération a été tronquée.

Invariant testé : sur les ordres quasi-circulaires, le filtre Prop. 4.5 doit
coïncider avec cR exact. Le test exhaustif `n=4` couvre les matrices à valeurs
`{1,2,3}` qui possèdent au moins un ordre quasi-circulaire.

Limite : ce n’est pas encore un CSP de choix locaux du PC-tree. C’est une
énumération contrôlée qui prépare les nogoods et les métriques de désaccord.

Risque : si le PC-tree fourni n’est pas garanti quasi-circulaire pour `D`,
`require_quasi=True` saute les ordres hors précondition ; `require_quasi=False`
doit être interprété comme diagnostic seulement.

Prochaine action : implémenter un vrai moteur de domaines locaux pour petits
nœuds `P/C`, en commençant par `source="cr"` pour valider le moteur sans
nouvelle hypothèse mathématique, puis comparer à `source="prop45"`.

## Tentative T010 - Domaines locaux P/C et source cR directe

Statut : conséquence directe expérimentale / scaffold, non intégré dans
`candidate.py`.

Changement : `build_local_domains` crée une variable par nœud interne, avec
domaine forward/reverse pour `C` et permutations bornées pour `P`.
`frontier_from_assignment` reconstruit la frontier d’une affectation complète.
`solve_nogood_csp(source="cr")` énumère ces affectations, déduplique les
frontiers circulaires canoniques, puis accepte exactement celles qui vérifient
`is_precircular_order_cR`.

Invariant testé : pour les PC-trees supportés, les frontiers reconstruites par
affectations locales coïncident avec `enumerate_frontiers`. Le filtre
`source="cr"` coïncide avec `enumerate_frontiers(T)` filtré par cR exact.

Limite : il n’y a pas encore de pruning compact ni de clauses projetées sur un
petit support. Le moteur énumère les affectations et sert à valider la couche de
variables avant compression. Un nœud `P` de degré supérieur à `max_p_degree`
renvoie `unsupported` et ne produit pas de décision négative.

Résultat expérimental : probe sur `1600` instances `n=4..7`, arbres
balanced/mixed, familles `random/cycle/block/ultrametric/equal/non_strict/
paired_farthest/permuted_cycle` : aucun désaccord entre CSP `source="cr"` et le
filtre exact de frontiers.

Prochaine action : compiler de vrais nogoods de quartets cR sur supports de
variables, puis chercher si ces nogoods prunent avant énumération complète ou si
des collisions forcent une signature plus riche.

## Tentative T011 - Nogoods compilés de quartets cR

Statut : preuve expérimentale / scaffold, non intégré dans `candidate.py`.

Changement : `forbidden_cr_atoms` génère les quartets ordonnés dont l’inégalité
cR échoue. `quartet_support_paths` calcule le sous-arbre de variables locales
pertinentes pour les quatre labels. `compile_cr_nogoods` projette les
affectations violant un atom sur ce support, puis
`solve_compiled_nogood_csp` compare les signatures compilées aux affectations.

Invariant testé : un nogood compilé ne doit rejeter qu’une affectation dont la
frontier viole `is_precircular_order_cR`, et toute frontier non-cR doit matcher
au moins un nogood. Les tests couvrent un split imbriqué, un test négatif où
retirer une variable du support change la projection du quartet, un cas de
wrapping autour de la coupure linéaire, et l’égalité avec le filtre cR direct.

Résultat expérimental : probe sur `960` instances `n=4..7`, arbres
balanced/mixed, familles `random/cycle/block/ultrametric/equal/non_strict/
paired_farthest/permuted_cycle` : aucun désaccord entre le solveur à nogoods
compilés et `solve_nogood_csp(source="cr")`. `153512` nogoods uniques ont été
produits dans cette probe, ce qui montre que la compilation est encore
énumérative et peut être volumineuse.

Limite : la compilation inspecte encore les affectations complètes pour découvrir
les signatures. Ce n’est pas une preuve de complexité ni un algorithme compact.

Prochaine action : mesurer la taille des supports et chercher des familles où le
nombre de nogoods explose, puis tenter un backtracking qui prune dès qu’une
signature partielle matche un nogood.

## Tentative T012 - Backtracking pruné par nogoods compilés

Statut : preuve expérimentale / amélioration de recherche, non intégré dans
`candidate.py`.

Changement : `solve_pruned_nogood_csp` explore les domaines locaux en
backtracking. Les nogoods sont indexés par la dernière variable de leur support
selon l’ordre d’exploration ; dès qu’un choix complète une signature de nogood,
la branche est coupée avant reconstruction de la frontier.

Invariant testé : les frontiers acceptées par le backtracking pruné doivent être
exactement celles du filtre cR direct. Une validation optionnelle compare le
résultat final à `accepted_frontiers_by_csp(source="cr")`.

Résultat expérimental : probe sur `640` instances `n=4..7`, arbres
balanced/mixed, familles `random/cycle/block/ultrametric/equal/non_strict/
paired_farthest/permuted_cycle` : aucun désaccord avec le filtre cR direct.
Le backtracking a visité `7396` feuilles contre `19200` affectations complètes
possibles, avec `4284` branches prunées.

Limite : le pruning arrive après une compilation qui énumère encore toutes les
affectations pour produire les nogoods. Le gain mesuré concerne donc seulement
la phase de solve post-compilation.

Prochaine action : mesurer séparément coût de compilation et coût de solve,
chercher les familles où les nogoods explosent, puis décider si Piste C reste
prometteuse ou si Piste B/F doit reprendre la priorité.

## Tentative T013 - Benchmark interne CSP/nogoods

Statut : benchmark expérimental / signal de décision.

Changement : ajout de `tools/pc_csp_internal_benchmark.py` et du target
`make bench-csp-quick`. Le rapport JSON sépare `compile_seconds`,
`solve_seconds`, `direct_seconds`, nombre d’atoms, nombre de nogoods uniques,
tailles de support, espace d’affectations complet, feuilles visitées et branches
prunées.

Résultat observé : sur `192` lignes (`n=4..7`, arbres balanced/mixed, huit
familles, trois répétitions), aucun mismatch. Médians observés :
compilation `~0.00104s`, solve pruné `~0.000284s`, filtre direct `~0.000304s`.
Le solve pruné visite `2208` feuilles sur `5760` affectations possibles et
prune `1280` branches, mais la compilation produit déjà `31616` nogoods uniques.

Interprétation : le pruning post-compilation est mesurable, mais la compilation
semble être le coût dominant même sur petites tailles. La piste C doit maintenant
soit éviter l’énumération de compilation, soit céder la priorité à Piste B/F.

Prochaine action : créer un rapport de décision Piste C vs Piste B/F, et tester
une signature DP/collision ou un sous-cas polynomial avant de continuer à
raffiner le CSP énumératif.

## Prochaine action

Créer un rapport de décision Piste C vs Piste B/F, puis tester une signature
DP/collision ou un sous-cas polynomial avant de continuer à raffiner le CSP
énumératif.

## Tentative T028 - Exact PC-tree borné dans la candidate

Statut : sous-cas exact hors CSP, utile comme baseline de décision complète.

La candidate inclut désormais un cas où le nombre de frontiers du PC-tree
scaffold est certifié sous `EXACT_PC_TREE_FRONTIER_LIMIT`. Cela contourne le
CSP/nogood quand le domaine total est déjà petit : toutes les frontiers sont
énumérées directement et testées par le prédicat cR exact.

Intérêt pour Piste C : cette branche fournit une référence complète pour les
petits domaines locaux, et rappelle qu'un solveur CSP compact ne gagne que
lorsque l'espace de frontiers dépasse cette limite. Si le PC-tree est déjà
petit, l'énumération exacte simple est plus robuste qu'une compilation de
nogoods.

## Tentative T027 - Nogoods bad-side par paire

Statut : amélioration de représentation expérimentale, non intégrée dans
`candidate.py`.

Changement : `forbidden_bad_side_atoms` génère les deux orientations
`(a,y,b,t)` et `(a,t,b,y)` pour chaque paire `{a,b}` et chaque couple de
mauvais témoins `y,t in B(a,b)`. `compile_bad_side_nogoods` projette ces atomes
sur les mêmes supports de variables que les quartets cR, puis
`solve_compiled_bad_side_nogood_csp` et
`solve_pruned_bad_side_nogood_csp` réutilisent les solveurs CSP existants.

Invariant testé : un ordre est rejeté par un atome bad-side ssi il viole cR.
L'exhaustif `n=4`, valeurs `{1,2,3}`, vérifie aussi que les atomes bad-side sont
un sous-ensemble des atomes `forbidden_cr_atoms`.

Résultat observé : sur un probe borné `cycle/equal/random/paired_farthest`,
arbres `mixed`, `n=5..7`, les atomes et nogoods bad-side sont exactement deux
fois moins nombreux que les quartets ordonnés dans les cas non triviaux, avec
le même nombre de branches prunées et aucun mismatch de validation. Sur des
arbres fanout 3 :

- `cycle8_mixed_f3` : `416/832` atomes, `1178/2356` nogoods, validation `0/0` ;
- `paired8_1008_mixed_f3` : `168/336` atomes, `796/1592` nogoods,
  validation `0/0` ;
- `equal6_mixed` : aucun atome/nogood, ce qui verrouille les égalités.

Limite : la compilation découvre toujours les signatures en énumérant les
affectations complètes. Le gain est donc une simplification de représentation,
pas une preuve de solveur compact ni de borne polynomiale.

## Tentative T046 - Projection matching low-hub comme étape vers CSP compact

Statut : intégration candidate bornée, pas encore CSP/nogoods local.

Changement : `exact_low_hub_matching_projected_pc_tree_search_report` sépare le
sous-cas matching low-hub en deux niveaux. Il énumère les projections
`seq + mate(seq)` des endpoints du matching, puis relève chaque projection dans
le PC-tree original avec un parseur récursif des blocs `P/C`. Les hubs deviennent
des labels epsilon pour la condition cR, mais ils restent contraints par la
structure du PC-tree.

Intérêt pour Piste C : cela isole la contrainte CSP qui manque. Une future
compilation compacte devrait éviter l'énumération `2^m * m!` en portant
l'ordre commun des paires dans les états/nogoods locaux. Une 2-SAT naïve avec
un booléen "endpoint dans la première moitié" est insuffisante : le test de
régression `test_matching_low_hub_side_split_boolean_encoding_is_not_sufficient`
garde un PC-tree rigide où chaque paire est split côté A/B mais où l'ordre des
mates est désynchronisé.

Résultat subagent : la granularité minimale ressemble à des nogoods 4-aires ou
à une DP transportant l'ordre relatif des paires ouvertes. Les supports locaux
de `quartet_support_paths` peuvent être réutilisés, mais la compilation actuelle
énumère encore les affectations complètes ; le prochain essai utile est une
compilation par produit des domaines du support seulement.

Limite : T046 est un meilleur exact borné, pas une preuve de CSP polynomial.
Tout dépassement de `max_projection_orders` reste incomplet.

## Tentative T047 - Compilation bad-side par produits de supports

Statut : artefact Piste C, non intégré à `candidate.py`.

Changement : `compile_bad_side_nogoods_support_local` compile les atomes
bad-side en parcourant seulement les domaines des variables retournées par
`quartet_support_paths`. Le reconstructeur
`_project_atom_order_from_support_assignment` projette les quatre labels d'un
atom depuis une affectation partielle du support. Les nogoods sont ensuite
dédupliqués par signature effective de pruning.

Invariant testé : les signatures support-local doivent être les mêmes que les
signatures de pruning découvertes par `compile_bad_side_nogoods`, même si
l'identité orientée de l'atom diffère. Cette nuance est nécessaire : une
canonicalisation globale peut inverser l'orientation visible d'un quartet à
cause d'un label hors atom, alors que la signature de rejet reste la même.

Résultats :

- tests ciblés `tests/test_sat_like_experiments.py` : `26 passed` ;
- probe local `577` couples famille/tree sans mismatch de signatures ni de
  solveur contre `accepted_frontiers_by_csp(source="cr")` ;
- sidecar contre-exemples : `1491` cas `n=4..7`, `0` mismatch de signatures
  seules et `0` mismatch solveur, mais `1271` mismatches stricts
  `(atom, signature)`, ce qui confirme que l'atom est seulement diagnostique ;
- `make bench-csp-quick` : `192` lignes, `0` mismatch, `0` mismatch de
  signatures, `total_support_unique_nogoods=2904` contre
  `total_unique_nogoods=31616`.

Interprétation complexité : T047 déplace le coût de
`full_assignment_space * atoms` vers `sum_support_products`. Le ratio médian
observé dans `make bench-csp-quick` est `0.25`, mais la médiane de compilation
support-local reste plus lente sur les petits arbres du benchmark
(`0.00276s` contre `0.00104s`) car l'espace complet y est minuscule. Sur des
probes plus larges `n=9..12`, le sidecar complexité observe des gains nets
quand `full_assignment_space * atoms` devient dominant.

Prochaine action : regrouper les atomes par support/signature partielle ou
chercher une borne sur `sum_support_products`. Ne pas convertir ce diagnostic
en rejet candidate tant que les gros `P` restent unsupported et que la borne
globale n'est pas prouvée.

## Tentative T048 - Compilation bad-side groupée par support

Statut : compression de métrique Piste C, non intégrée à `candidate.py`.

Changement : `compile_bad_side_nogoods_grouped_support_local` groupe les atoms
bad-side par `quartet_support_paths`, énumère le produit de domaines une seule
fois par support distinct, puis teste tous les atoms du groupe et déduplique les
nogoods par signature effective. Le rapport expose maintenant
`support_group_count`, `grouped_support_product_total`,
`support_product_total_if_ungrouped`, `grouped_vs_ungrouped_support_ratio`,
`atom_checks`, `max_atoms_per_support` et `effective_signature_count`.

Invariant testé : les signatures groupées doivent coïncider avec T047
support-local et le solveur pruné groupé doit accepter exactement les frontiers
du CSP cR direct. Comme en T047, l'identité `atom` ou `pair` stockée dans un
nogood est diagnostique seulement.

Résultats :

- tests ciblés `tests/test_sat_like_experiments.py` : `31 passed` ;
- probe indépendant `n=4..7`, arbres balanced/mixed, familles
  `random/cycle/block/ultrametric/equal/non_strict/paired_farthest/
  permuted_cycle/matching_high_graph_plus_low_hub` : `130` cas,
  `0` mismatch de signatures, `0` mismatch solveur et `0` mismatch direct ;
- `make bench-csp-quick` : `192` lignes, `0` mismatch, `0` grouped mismatch,
  `0` mismatch de signatures, `total_grouped_unique_nogoods=2904`, identique à
  T047 ;
- produit support T047 `72256` contre produit groupé `6224`, ratio médian
  `0.11111` ;
- `total_grouped_atom_checks=72256`, donc le coût atom-par-atom n'est pas
  encore réduit.

Interprétation complexité : le regroupement prouve expérimentalement que les
supports sont très partagés sur les familles testées. Il réduit
`sum_support_products` vers `sum_unique_support_products`, mais le compilateur
naïf paie encore `sum_support_products` en reconstructions/tests d'atoms.

Prochaine action : factoriser les atoms d'un même support pour éviter de tester
chaque atom séparément, ou chercher une preuve que les groupes de supports ont
une taille bornée dans les PC-trees issus de la quasi-circularité.

## Tentative T049 - Groupes de support avec arrêt au premier hit

Statut : optimisation expérimentale Piste C, non intégrée à `candidate.py`.

Changement : `compile_bad_side_nogoods_grouped_first_hit_support_local` reprend
T048, mais arrête le scan des atoms d'un groupe dès qu'une affectation de
support produit un premier atom interdit. La signature de pruning ne dépendant
que de l'affectation de support, les autres atoms violés par la même signature
sont redondants pour le solveur pruné.

Invariant testé : les signatures first-hit doivent être identiques à celles de
T048 et T047. Les compteurs `atom_hits`, `atoms_with_nogoods` et
`pairs_with_nogoods` deviennent des diagnostics de premiers hits, pas une
énumération complète des violations.

Résultats :

- tests ciblés `tests/test_sat_like_experiments.py` : `39 passed` ;
- `make bench-csp-quick` : `192` lignes, `0` mismatch, `0` first-hit mismatch,
  `0` mismatch de signatures, mêmes `2904` signatures que T047/T048 ;
- `total_grouped_atom_checks=72256` contre
  `total_first_hit_atom_checks=41872`, soit `30384` checks évités ;
- probe indépendant `n=4..7`, familles diverses et arbres balanced/mixed :
  `130` cas, `0` mismatch de signatures, `0` mismatch direct,
  `49760 -> 24168` atom checks.
- sidecar contre-exemples : `220` cas supportés, `0` mismatch de signatures,
  `0` mismatch de frontiers acceptées, max `84` atoms dans un support groupé,
  gain combiné `356612 -> 82052` atom checks ;
- sidecar complexité : `160` cas jusqu'à `n=8`, gain global
  `48888/87328` checks (`56.0%`), avec gains nuls attendus sur equal-distance
  faute d'atom bad-side.

Interprétation : T049 confirme que beaucoup d'affectations de support trouvent
un atom interdit avant d'épuiser le groupe. Le gain reste dépendant de l'ordre
des atoms et ne remplace pas une compilation symbolique du groupe.

Limite de diagnostic : le test minimal `n=4` verrouille que first-hit peut
préserver toutes les signatures tout en sous-comptant `atoms_with_nogoods` et
`pairs_with_nogoods`. Les champs `atom`, `pair`, `bad_witnesses`, `atom_hits`,
`atoms_with_nogoods` et `pairs_with_nogoods` sont donc seulement des
représentants de premiers témoins dans ce mode.

Prochaine action : mesurer les cas où le premier hit arrive tard ou n'arrive
pas, puis tenter de remplacer le scan séquentiel par une contrainte agrégée sur
les positions relatives des quatre labels.

## Tentative T050 - Profil des positions first-hit

Statut : instrumentation Piste C, non intégrée à `candidate.py`.

Changement : le compilateur first-hit expose désormais les affectations de
support avec hit, sans hit, l'histogramme des positions de premier hit, la
position maximale, la position moyenne, les checks dépensés sur no-hit et les
checks sauvés sur hit. `atom_checks_if_exhaustive_seen` sépare aussi les runs
bornés/incomplets de la borne exhaustive complète.

Résultats :

- tests ciblés `tests/test_sat_like_experiments.py` : `40 passed` ;
- `make bench-csp-quick` : `192` lignes, `0` mismatch,
  `0` first-hit mismatch, `0` mismatch de signatures ;
- `total_first_hit_assignments=2904`,
  `total_first_hit_no_hit_assignments=3320`, ratio no-hit `0.5334` ;
- `total_first_hit_atom_checks=41872` sur une baseline vue `72256` ;
- `total_first_hit_checks_spent_on_no_hit=30520` contre
  `total_first_hit_checks_saved_on_hits=30384` ;
- position maximale de premier hit `36`, position moyenne médiane `3.0`.

Probe par familles `n=4..8` :

- random : no-hit `21.9%`, saved ratio `64.5%`, max position `36` ;
- cycle : no-hit `50.0%`, saved ratio `38.6%`, max position `17` ;
- paired-farthest : no-hit `44.4%`, saved ratio `50.5%`, max position `19` ;
- matching low-hub : no-hit `25.7%`, saved ratio `58.4%`, max position `3` ;
- equal-distance : aucun atom bad-side, donc aucun coût.

Interprétation : les hits trouvés sont souvent précoces, mais plus de la moitié
des affectations de support n'ont aucun hit sur la gate rapide. Le coût restant
est donc principalement un problème de certification "aucun atom du groupe ne
hit", pas seulement d'ordre de scan des atoms.

Prochaine action : construire une contrainte agrégée par support qui décide
directement l'existence d'un atom hit pour une affectation, ou isoler les
familles no-hit dominantes pour chercher une borne structurelle.

## Tentative T051 - Profil support-level hit/no-hit

Statut : diagnostic Piste C exact sur la gate interne, non intégré à
`candidate.py`.

Changement : ajout de `bad_side_grouped_support_outcome_profile`. Pour chaque
support groupé, le diagnostic mesure les affectations hit/no-hit, les checks
first-hit équivalents, les tranches unaires pures, puis un test agrégé par
paire endpoint et composantes de graphe de mauvais témoins. Le test pair-side
déclare un hit quand une composante de témoins d'une même paire `{a,b}` contient
des témoins des deux côtés de l'arc.

Résultats :

- tests ciblés `tests/test_sat_like_experiments.py` et
  `tests/test_csp_internal_benchmark.py` : `44 passed` ;
- `make bench-csp-quick` : `192` lignes, `0` mismatch,
  `0` first-hit mismatch, `0` mismatch de signatures ;
- `profile_pair_side_split_mismatches=0` ;
- les compteurs du profil coïncident avec T050 :
  `total_first_hit_no_hit_assignments=3320` et
  `total_profile_no_hit_exhaustive_atom_checks=30520` ;
- couverture unaire no-hit globale `1888/3320`, mais `0%` sur `cycle` et
  `permuted_cycle` dans la gate rapide ;
- le travail pair-side/composantes vaut `74248` checks contre `41872`
  atom-checks first-hit, ratio `1.7732`.

Interprétation : le test pair-side/composantes est une reformulation exacte du
hit/no-hit support-level sur les probes, mais sa version naïve ne réduit pas le
coût. Les tranches unaires pures expliquent une partie des familles très
structurées (`non_strict`, `ultrametric`, `block`) mais échouent totalement sur
les familles cycliques. T051 est donc surtout un résultat négatif contrôlé : la
compression doit réutiliser les côtés/composantes de façon plus globale, pas les
recalculer par affectation.

Prochaine action : précompiler les côtés de témoins par paire à travers les
variables du PC-tree, ou basculer vers une signature DP qui transporte les
composantes de témoins ouvertes au lieu d'une table d'affectations.

## Tentative T052 - Cache des côtés de témoins

Statut : diagnostic Piste C exact sur la gate interne, hors `candidate.py`.

Hypothèse testée : le côté d'un témoin `w` par rapport à une paire `{a,b}` ne
dépend que de la signature locale du support minimal du triple `(a,b,w)`.
Le profil T052 ajoute donc une clé de cache
`(pair,witness,signature_triple)`, où `signature_triple` contient tous les
choix de `quartet_support_paths(T, (a,b,w))`.

Résultats :

- tests ciblés : `45 passed` ;
- `make bench-csp-quick` : `192` lignes, `0` mismatch et
  `profile_pair_side_split_mismatches=0` ;
- travail pair-side brut : `74248` checks, ratio `1.7732` contre first-hit ;
- travail pair-side avec cache des côtés : `49558` checks, ratio `1.1836` ;
- hits/misses du cache de côtés : `24690` / `12778` ;
- modèle bitset-composantes : `27846` checks, ratio `0.6650`.

Interprétation : le cache de projections triples supprime une grande partie des
recalculs de côtés, mais le coût des checks de composantes reste trop haut. En
revanche, le modèle bitset indique qu'une représentation des composantes par
masques de témoins pourrait battre first-hit sur les familles de la gate, sauf
cas paired-farthest où le ratio reste proche de `1`.

Contre-exemple verrouillé contre une clé trop faible : dans
`C(leaf(0), P(leaf(1), leaf(2)), leaf(3))`, la paire `(0,2)` et le témoin `1`
ont besoin du choix imbriqué `(1,)`; une clé qui garde seulement le choix root
confond les deux côtés.

Prochaine action : implémenter un diagnostic bitset réel par composante, en
gardant la comparaison stricte aux signatures first-hit et au CSP cR direct.

## Tentative T053 - Profil bitset/composantes réel

Statut : diagnostic Piste C exact sur la gate interne, hors `candidate.py`.

Hypothèse testée : le modèle T052
`side_cache_misses + component_checks` peut être rapproché d'une exécution
réelle en cachant des masques de côtés par composante. Pour une paire `{a,b}`,
une composante de mauvais témoins produit un hit exactement quand son masque de
côtés vaut `0b11`.

Changement : ajout de `_component_side_cache_key` et
`_pair_side_bitset_outcome`. Le profil garde les compteurs T052 historiques et
ajoute les compteurs réels :
`pair_side_split_bitset_component_cache_*`,
`pair_side_split_bitset_witness_visits`,
`pair_side_split_bitset_checks`,
`pair_side_split_bitset_projection_checks` et
`pair_side_split_bitset_mismatches`.

Résultats :

- tests ciblés : `49 passed` ;
- `make bench-csp-quick` : `192` lignes, `0` mismatch,
  `profile_pair_side_split_mismatches=0` et
  `profile_pair_side_split_bitset_mismatches=0` ;
- coût first-hit : `41872` atom-checks ;
- coût bitset réel : `44936` checks, ratio `1.0732` ;
- coût de projection bitset : `27822` checks, ratio `0.6645` ;
- visites de témoins bitset : `29868` ;
- hits/misses du cache de composantes : `3000/12068` ;
- hits/misses du cache de côtés dans le profil bitset : `17114/12754`.

Interprétation : le test bitset est sémantiquement aligné avec le scan
atomique sur la gate, et il protège explicitement les composantes : des témoins
sur deux côtés mais dans deux composantes distinctes ne suffisent pas. En
revanche, le coût réel reste supérieur à first-hit parce que les visites de
témoins dominent. Le modèle de projection T052 reste proche (`0.6645` contre
`0.6650`), mais il suppose une structure plus forte qui éviterait ces visites.

Familles de stress :

- `cycle` et `non_strict` restent des contrôles positifs (`0.867x` et `0.583x`
  en coût réel sur les agrégats rapides mesurés par sidecar) ;
- `random` et `paired_farthest` sont les stress négatifs : sur la gate rapide,
  `random` est autour de `1.37x..1.39x`, `paired_farthest` autour de
  `1.41x..1.55x` en coût réel.

Conclusion : T053 réfute l'idée qu'un simple cache de masques de composantes
suffise. La prochaine compression doit éviter les visites de témoins par
composante, par exemple via tables de masques par support de composante, DP
transportant les masques ouverts, ou règle spéciale pour `paired_farthest`.

## Tentative T054 - Cardinalité des états de masques

Statut : diagnostic Piste C exact localement, hors `candidate.py`.

Hypothèse testée : si les états
`((pair, component, side_mask), ...)` sont beaucoup moins nombreux que les
affectations de support, une future DP pourrait transporter ces états plutôt
que les affectations locales complètes. Le hit/no-hit local est dérivé de l'état
par `any(mask == 0b11)`.

Changement : le profil support-level compte maintenant
`component_mask_state_count`, les états hit/no-hit, les états mixtes, les
mismatches contre le scan atomique, les tailles de buckets et les coûts de
construction/projection de l'état. Les états incluent la paire endpoint, la
composante group-local et le masque ; les paires sont triées pour stabiliser la
signature.

Résultats `make bench-csp-quick` :

- `192` lignes supportées, `0` mismatch ;
- `component_mask_state_mismatches=0` et `component_mask_state_mixed_count=0` ;
- `2920` états pour `6224` affectations de support, ratio `0.4692` ;
- bucket moyen `2.1315`, bucket max `4` ;
- coût de construction complet de l'état `1.9412x` first-hit ;
- coût de projection de l'état `0.9038x` first-hit.

Par famille rapide :

- `ultrametric` : ratio `0.419`, meilleur quotient observé ;
- `block` : `0.438` ;
- `paired_farthest` : `0.450..0.465` ;
- `random` : `0.479..0.487` ;
- `cycle` et `permuted_cycle` : `0.500`.

Probe stress `n=8` sur `random/cycle/non_strict/paired_farthest/permuted_cycle`
balanced/mixed : ratio global `0.4921`, bucket moyen `2.032`, bucket max `4`,
toujours `0` état mixte. Les familles stress restent donc proches du facteur 2.

Interprétation : T054 donne un quotient local exact, mais la compression est
faible et stable autour de deux affectations par état. C'est insuffisant comme
argument DP compact. Pour continuer cette piste, il faudrait montrer une
composition parent-enfant des états qui évite les visites de témoins, ou
trouver un état plus abstrait qui reste sound sans perdre labels, paires,
composantes et choix imbriqués.

## Tentative T055 - Quotients d'états de masques

Statut : diagnostic Piste C, hors `candidate.py`.

Hypothèse testée : des projections plus abstraites de l'état T054 peuvent
compresser davantage tout en gardant le hit/no-hit local. Chaque quotient est
évalué par `state_count`, ratio, bucket max/moyen et surtout `mixed_count`. Un
quotient mixte contient à la fois des affectations hit et no-hit et est donc
réfuté comme classifieur local.

Quotients profilés :

- `full` : état T054 complet ;
- `pair_mask_multiset` : garde la paire et le multiset de masques ;
- `mask_multiset` : garde seulement le multiset global de masques ;
- `hit_components` : garde seulement les composantes split `0b11` ;
- `hit_pairs` : garde seulement les paires ayant une composante split ;
- `decision_only` : garde seulement le booléen hit/no-hit local ;
- `side_blind_schema` : contrôle négatif qui garde la structure sans masques.

Résultats `make bench-csp-quick` :

- `full` : ratio `0.4692`, `0` mixte ;
- `mask_multiset` : ratio `0.3959`, `0` mixte ;
- `hit_components` et `hit_pairs` : ratio `0.2121`, `0` mixte ;
- `decision_only` : ratio `0.1825`, `0` mixte mais quotient tautologique ;
- `side_blind_schema` : ratio `0.1250`, `358` états mixtes.

Probe stress `n=8` :

- `full` : ratio `0.4921` ;
- `mask_multiset` : `0.4088` ;
- `hit_components` : `0.2273` ;
- `decision_only` : `0.1821` ;
- `side_blind_schema` : `181` états mixtes.

Contre-exemple minimal au contrôle négatif : sur `cycle_metric(4)` avec
`balanced_pc_tree(4, kind="C")`, un unique support groupé donne `8`
affectations et `side_blind_schema` fusionne tout en `1` état mixte. Le même cas
garde `full` non mixte avec `4` états et `mask_multiset` non mixte avec `3`
états. Le test
`test_component_mask_quotient_negative_control_has_minimal_mixed_state`
préserve ce diagnostic.

Interprétation : les quotients qui conservent explicitement l'information de
hit local peuvent compresser nettement plus que T054, mais les plus forts
(`hit_components`, `hit_pairs`, `decision_only`) sont proches du résultat de
décision locale et ne portent pas les informations nécessaires à une composition
globale évidente. Le contrôle `side_blind_schema` confirme que supprimer les
masques rend le quotient non sound.

Conclusion : T055 donne des candidats de quotient à étudier, surtout
`mask_multiset` comme quotient non tautologique, mais ne fournit toujours pas de
DP. La prochaine question est externe au support groupé : ces quotients se
composent-ils à travers un parent PC-tree sans perdre les paires et les choix
imbriqués ?

## Tentative T056 - Collisions de contexte des quotients

Statut : diagnostic Piste C/B, hors `candidate.py`.

Hypothèse testée : un quotient local T055 peut être exact pour le hit/no-hit de
son support groupé, mais échouer comme état de composition. Le nouveau profil
`component_mask_quotient_context_collision_profile` compare deux supports
groupés qui se chevauchent. Pour une paire `(S,C)`, il fixe les choix de
`(S union C) \\ S`, calcule le quotient local sur `S`, puis mesure si ce
quotient détermine le hit/no-hit de `C`.

Contrôles :

- `assignment_signature` garde la signature complète sur `S` et doit rester à
  `0` collision ;
- `side_blind_schema` reste un contrôle négatif ;
- `full` signifie l'état de masques T054 complet, pas l'affectation complète.
  Une collision de `full` signale une contrainte ouverte entre supports, pas
  seulement une mauvaise projection.

Contre-exemple minimal régressé : `cycle_metric(5)` avec
`balanced_pc_tree(5, kind="mixed")`.

- `context_pair_count=6` ;
- `context_assignments_seen=96` ;
- `assignment_signature` : `0` collision ;
- `full` : `0` collision sur ce petit cas ;
- `mask_multiset` : `12` collisions ;
- `hit_components`, `hit_pairs`, `decision_only` et `side_blind_schema` :
  collisions positives.

Contre-exemple global régressé : sur une matrice `n=5` fournie par le sidecar
contre-exemples, deux affectations du support `((), (0,), (0,0))` ont le même
`mask_multiset=(1,2)` et le même contexte externe `(1,)=(0,1)`, mais produisent
un ordre cR `(0,1,4,3,2)` et un ordre non-cR `(0,1,3,4,2)`. L'atome
`(2,4,3,0)` sur le support voisin `((), (0,), (1,))` distingue le second. Cela
montre que le quotient peut échouer au niveau de la décision globale, pas
seulement sur une métrique de profil.

Résultat `make bench-csp-quick` après T056 :

- `192` lignes supportées, `0` mismatch des solveurs CSP expérimentaux ;
- `context_collision_assignments_seen=35728` ;
- `context_collision_pairs_profiled=1828` ;
- `context_collision_incomplete_rows=74` car le diagnostic est borné à
  `max_pairs=20` par ligne ;
- `assignment_signature` : `mixed_count=0` ;
- `full` : ratio `0.4678`, `mixed_count=190` ;
- `mask_multiset` : ratio `0.4033`, `mixed_count=856` ;
- `hit_components` : ratio `0.2137`, `mixed_count=2438` ;
- `decision_only` : ratio `0.1763`, `mixed_count=2194` ;
- `side_blind_schema` : ratio `0.1250`, `mixed_count=1334`.

Probe stress `n=8`, repeats `2`, familles
`random/cycle/non_strict/paired_farthest/permuted_cycle`,
balanced/mixed :

- `context_collision_assignments_seen=9072` ;
- `assignment_signature` : `0` collision ;
- `full` : `8` collisions ;
- `mask_multiset` : `26` collisions ;
- `hit_components` : `414` collisions ;
- `decision_only` : `354` collisions.

Conclusion : T056 réfute `mask_multiset` comme état DP autonome. Il montre aussi
que l'état de masques complet T054 peut être insuffisant face à des contraintes
ouvertes entre supports voisins. La piste C doit donc passer d'un quotient fermé
par support à une représentation d'obligations ouvertes, ou changer d'axe vers
un sous-cas prouvable.

## Tentative T057 - États de réponse ouverte

Statut : diagnostic Piste C/B, hors `candidate.py`.

Hypothèse testée : les collisions T056 peuvent être réparées si l'état local
transporte un vecteur de réponses ouvertes vers les supports voisins. Le profil
`component_mask_open_boundary_profile` énumère, pour chaque affectation locale
d'un support `S`, les réponses hit/no-hit de chaque support voisin `C` sous tous
les choix externes de `(S union C) \\ S`.

États comptés :

- `assignment_signature` : contrôle sans compression ;
- `full` et `mask_multiset` : états fermés T054/T055, avec support de base dans
  la clé ;
- `boundary_response` : seulement le vecteur de réponses ouvertes ;
- `local_boundary_response` : hit local plus réponses ouvertes ;
- `mask_multiset_plus_boundary`, `full_plus_boundary`,
  `hit_components_plus_boundary`.

Résultat minimal `cycle_metric(5)` avec `balanced_pc_tree(5, kind="mixed")` :

- `support_group_count=3`, `context_pair_count=6` ;
- `local_assignments_seen=24` ;
- `boundary_response_checks=96` ;
- `assignment_signature=24` états ;
- `mask_multiset=9` états ;
- `boundary_response=12` états ;
- `mask_multiset_plus_boundary=12` états ;
- `full_plus_boundary=12` états.

Résultat `make bench-csp-quick` :

- `192` lignes supportées, `0` mismatch ;
- diagnostic ouvert borné à `max_pairs=20`, donc `74` lignes incomplètes
  visibles ;
- `open_boundary_local_assignments_seen=6224` ;
- `open_boundary_response_checks=35728` ;
- `open_boundary_pairs_profiled=1828` ;
- `assignment_signature` : ratio `1.0000`, `6224` états ;
- `full` : ratio `0.4692`, `2920` états ;
- `mask_multiset` : ratio `0.3959`, `2464` états ;
- `boundary_response` : ratio `0.2208`, `1374` états ;
- `local_boundary_response` : ratio `0.2625`, `1634` états ;
- `mask_multiset_plus_boundary` : ratio `0.4291`, `2671` états ;
- `full_plus_boundary` : ratio `0.4770`, `2969` états.

Réparation des collisions T056 sur la réponse de bord : `mask_multiset` garde
`203` états avec plusieurs réponses de bord possibles et `full` en garde `49`.
Les états enrichis `mask_multiset_plus_boundary`, `full_plus_boundary` et
`local_boundary_response` ont `0` bucket mélangé sur ce diagnostic one-hop.
`boundary_response` seul a `0` mélange de bord, mais `260` buckets mélangent le
hit local ; il ne doit donc pas être utilisé sans le bit local.

Probe stress `n=8`, repeats `2` :

- `open_boundary_local_assignments_seen=2088` ;
- `open_boundary_response_checks=9072` ;
- `open_boundary_incomplete_rows=20` ;
- `boundary_response` : ratio `0.1518`, `317` états ;
- `local_boundary_response` : ratio `0.2126`, `444` états ;
- `mask_multiset_plus_boundary` : ratio `0.4119`, `860` états ;
- `full_plus_boundary` : ratio `0.4895`, `1022` états.

Conclusion : les obligations ouvertes one-hop donnent une compression réelle et
ne sont pas immédiatement quasi-injectives. Mais le profil est encore
énumératif, borné, et seulement one-hop. La prochaine question est de chercher
des collisions de second ordre ou de prouver une règle de composition des
vecteurs de réponses ouvertes.

## Revue externe post-T057 - CSP exact par quartets

Statut : orientation de piste, non implémentée.

La revue externe GPT 5.5 Pro fournie le 2026-05-23 recommande de ne pas réduire
la suite à T057. Pour Piste C, l'objet central proposé est un CSP exact par
quartets :

- calculer, pour chaque quartet `Q`, les types circulaires autorisés par `D` ;
- calculer les variables locales du PC-tree dont dépend le type induit sur `Q` ;
- vérifier expérimentalement que la portée effective est `0`, `1` ou `2` ;
- fusionner les contraintes par scope et résoudre par 2-SAT quand les domaines
  sont booléens, ou par DP de treewidth quand le graphe primal est petit.

Cette piste est prioritaire parce qu'elle relie plusieurs axes : T057 devient un
diagnostic de compression d'un CSP exact, le sous-cas C-only devient une
réduction 2-SAT testable, et le catalogue de relations binaires devient une
mesure de dureté potentielle.

Prochaine expérience recommandée : ajouter un rapport
`quartet_pc_scope_report(D, T)` qui, sans résoudre le CSP, liste pour chaque
quartet le scope PC-tree minimal observé, les types autorisés par `D`, et les
contraintes locales induites. Le rapport doit être comparé à l'oracle sur petits
arbres avant tout solveur.

## Tentative T058 - Portée PC-tree effective des quartets

Statut : diagnostic exact sur le scaffold supporté, hors `candidate.py`.

Changement : ajout de `quartet_type`, `quartet_allowed_types` et
`quartet_pc_scope_report`. Le rapport énumère les affectations du support
structurel `quartet_support_paths(T, Q)`, projette le quartet, calcule son type
circulaire modulo rotation/renversement, puis mesure deux portées minimales :

- portée effective de type : variables nécessaires pour déterminer le type
  circulaire réalisé ;
- portée effective d'acceptation : variables nécessaires pour déterminer si le
  type réalisé appartient aux types cR autorisés par `D`.

Invariant testé : pour chaque affectation complète, le type du quartet obtenu en
projetant le frontier complet doit coïncider avec le type obtenu depuis la seule
affectation du support. Un mismatch signifie que le support est sous-estimé.

Résultat `make bench-csp-quick` :

- `192` lignes supportées, `0` mismatch ;
- `2688` quartets profilés ;
- `21504` affectations de support inspectées ;
- `0` mismatch de projection support-local vs frontier complet ;
- support structurel conservateur : histogramme `{3: 2688}` ;
- portée effective de type : histogramme `{2: 2688}` ;
- portée effective d'acceptation : histogramme `{0: 1536, 2: 1152}` ;
- `0` quartet à portée effective type `>2` ;
- `0` quartet à portée effective acceptation `>2` ;
- `2688` quartets candidats 2-SAT sur cette gate, car les portées effectives
  d'acceptation sont booléennes.

Probe stress : `180` cas (`n=4..8`, fanout `2/3`, arbres `P/C/mixed`, familles
`random/cycle/equal/non_strict/paired_farthest/permuted_cycle`), `4536`
quartets, `0` mismatch de projection et `0` portée effective `>2`. Les arbres
`P` fanout `3` produisent des portées effectives binaires mais non booléennes :
ces lignes ne sont pas 2-SAT et doivent nourrir le futur catalogue de relations.

Limite : T058 ne prouve pas que le vrai PC-tree Hsu/McConnell général a portée
`<=2`, ni que les relations se combinent polynomialement. Le support structurel
peut rester taille `3` alors que la portée effective est `2`, donc une preuve
devra expliquer cette redondance plutôt que l'ignorer.

Prochaine action : grouper les quartets par portée effective, construire les
tables de relations, le graphe primal, et séparer trois sorties : 2-SAT booléen,
DP treewidth, relation-catalog pour domaines non booléens.

## Tentative T059 - Relations effectives de quartets

Statut : diagnostic relationnel exact sur le scaffold supporté, hors
`candidate.py`.

Changement : ajout de `quartet_effective_relation_report`. Le rapport réutilise
les projections support-local de T058, calcule pour chaque quartet la table
acceptée sur la portée effective d'acceptation, fusionne les quartets ayant le
même scope par intersection de tables, puis valide la conjonction de relations
contre `is_precircular_order_cR` sur toutes les affectations locales complètes
supportées.

Ce que le rapport matérialise :

- `quartet_relations` : table effective par quartet, avec arité, tailles de
  domaine, densité, tuples acceptés/rejetés et classe de relation ;
- `merged_relations` : relation finale par scope effectif après intersection ;
- `primal_graph` : graphe primal des scopes fusionnés, degrés, composantes,
  multiplicité d'arêtes et bornes greedy min-fill/min-degree de treewidth ;
- `row_class` : `two_sat_candidate`, `non_boolean_relation_catalog`,
  `high_arity_relation`, `incomplete` ou `relation_validation_mismatch`.

Tests ciblés ajoutés :

- cycle `n=5` balanced/mixed : relation-CSP exact, candidat 2-SAT, `0`
  mismatch de validation ;
- equal-distance C-only : toutes les contraintes fusionnent en tautologie de
  scope vide, sans arêtes primal ;
- quartet wrapping non-cR : relation constante rejetante visible, sans marquer
  `unsupported` ;
- `four_local_non_cr_core` C-only : UNSAT 2-SAT réel, pas échec de support ;
- nœud `P3` : relation unaire non booléenne cataloguée, donc pas 2-SAT ;
- trois blocs `P3` : relations binaires non booléennes cataloguées avec
  treewidth observée `3`.

Interprétation : T059 transforme le signal T058 en objet CSP vérifiable. Il ne
résout pas le problème général : la validation reste énumérative, les gros
`P` hors domaine restent unsupported, et aucune preuve de portée `<=2` pour
les vrais PC-trees Hsu/McConnell n'est encore écrite. En revanche, il fournit
un point commun pour quatre pistes indépendantes : 2-SAT booléen, DP par
treewidth, catalogue de relations non booléennes et contre-exemples de
composition.

Prochaine action : implémenter soit le sous-cas C-only/2-SAT à partir des
relations fusionnées, soit un solveur exact par DP de treewidth bornée, sans
modifier `candidate.py` tant que les obligations de preuve ne sont pas
remplies.

## Tentative T060 - Solveur 2-SAT des relations effectives

Statut : sous-cas exact expérimental sur `row_class="two_sat_candidate"`, hors
`candidate.py`.

Changement : ajout de `solve_quartet_2sat`. La fonction consomme les
`merged_relations` de `quartet_effective_relation_report`, refuse toute ligne
incomplète ou non booléenne, transforme chaque signature rejetée en clause
2-CNF, résout par graphe d'implications/SCC, puis reconstruit un témoin local et
le vérifie par `is_precircular_order_cR`.

Traduction :

- relation constante acceptante : aucune clause ;
- relation constante rejetante : clause vide, UNSAT ;
- rejet unaire `x=a` : clause `x != a` ;
- rejet binaire `(x=a, y=b)` : clause `(x != a) or (y != b)`.

Tests ajoutés :

- `cycle_metric(6)` C-only : SAT non tautologique, `12` clauses binaires,
  témoin cR vérifié ;
- equal-distance et `non_strict_large_farthest_instance(6)` C-only :
  tautologies sans clauses parasites ;
- `quasi_circular_not_circular_four_point` et `four_local_non_cr_core` C-only :
  UNSAT par clause vide, pas `unsupported` ;
- arbre mixte booléen `P` de deux blocs `C` : SAT par 2 clauses binaires ;
- nœud `P3` : refusé comme `not_two_sat_candidate`, pas converti en booléen.

Résultat `make bench-csp-quick` :

- `192` lignes supportées, `0` mismatch ;
- `0` `quartet_relation_validation_mismatches` ;
- `192` lignes 2-SAT complètes ;
- `143` SAT et `49` UNSAT par clause vide ;
- `0` incomplet et `0` échec de témoin SAT ;
- `1167` clauses, dont `1118` binaires et `49` vides.

Interprétation : T060 prouve l'encodage algorithmique du sous-cas booléen du
scaffold relationnel. Il ne prouve pas encore que tout vrai PC-tree des ordres
quasi-circulaires tombe dans ce sous-cas, ni que la portée effective `<=2` vaut
hors du scaffold testé.

Prochaine action : soit intégrer uniquement un témoin positif 2-SAT dans
`candidate.py` après garde de coût et vérification directe, soit poursuivre vers
DP treewidth pour les relations non booléennes. Ne pas utiliser UNSAT 2-SAT en
candidate avant d'avoir formalisé la suffisance du modèle relationnel et la
représentation PC-tree.

## Tentative T061 - DP treewidth des relations effectives

Statut : solveur relationnel exact à largeur bornée dans le scaffold T059, hors
`candidate.py`.

Changement : ajout de `solve_quartet_treewidth_csp`. La fonction demande les
tables complètes via `store_full_relations=True`, transforme les relations
fusionnées en facteurs, calcule un ordre d'élimination exact sous
`max_treewidth`, fait une élimination de facteurs, puis reconstruit un témoin et
le vérifie directement par `is_precircular_order_cR`.

Ce que T061 ajoute par rapport à T060 :

- les domaines non booléens, par exemple les nœuds `P3` à domaine taille `6`,
  sont acceptés si la largeur est sous cap ;
- le cap de largeur retourne `complete=False`, jamais un rejet ;
- les résultats UNSAT relationnels restent confinés au scaffold expérimental ;
- le benchmark interne expose le nombre de lignes complètes/incomplètes, la
  treewidth exacte et les échecs de témoins.

Tests ajoutés :

- matrice C-only `n=5` UNSAT sans clause vide : `solve_quartet_2sat` retourne
  `unsat_implication_scc`, pour protéger les cycles d'implications ;
- trois blocs `P3` sur `cycle_metric(9)` : `row_class` non booléen, 2-SAT
  refuse, DP SAT avec treewidth exacte `3` et témoin cR ;
- trois blocs `P3` sur `paired_farthest_matching(9, seed=7)` : DP UNSAT
  relationnel exact dans le scaffold ;
- equal-distance tautologique et `four_local_non_cr_core` constant reject ;
- `max_treewidth=2` sur le cas P3 positif : résultat incomplet
  `treewidth_cap_exceeded`.

Résultat `make bench-csp-quick` :

- `192` lignes supportées, `0` mismatch ;
- `0` `quartet_relation_validation_mismatches` ;
- `186` lignes DP complètes ;
- `137` SAT et `49` UNSAT ;
- `6` lignes incomplètes par `treewidth_cap_exceeded` ;
- `0` échec de témoin ;
- treewidth exacte maximale observée `3` sur les lignes complètes.

Interprétation : T061 fournit le premier solveur exact qui dépasse le sous-cas
booléen 2-SAT dans ce scaffold. Il ne prouve toujours pas le problème général :
la construction du CSP relationnel reste énumérative, les vrais PC-trees
Hsu/McConnell peuvent exiger une preuve séparée, et une famille
`p3_block_tree(k)` montre que la largeur du graphe primal peut croître.

Prochaine action : cataloguer la croissance de largeur sur `p3_block_tree(k)`
et décider si une intégration positive-only dans `candidate.py` mérite le coût.

## Tentative T062 - Stress de largeur `p3_block_tree(k)`

Statut : benchmark de limite de largeur, hors `candidate.py`.

Changement : ajout de `p3_block_tree(block_count)` et de
`tools/pc_csp_width_stress.py`, câblé par `make bench-width-stress`. Le rapport
construit des arbres à racine `C` portant `k` blocs `P3`, puis mesure les
relations effectives, le graphe primal, la DP treewidth et les incomplétudes
sous cap.

Résultat `make bench-width-stress` :

- `12` lignes : `k=2,3,4,5` et familles `cycle`, `paired_farthest`, `equal` ;
- `0` relation incomplète ;
- `0` mismatch de validation ;
- `11` lignes DP complètes ;
- `1` ligne incomplète : `cycle,k=5` avec `treewidth_cap_exceeded` sous cap `4` ;
- treewidth primal upper bound maximale `5` ;
- treewidth exacte maximale calculée `4` sous cap ;
- domaine maximal `6` ;
- `0` échec de témoin.

Interprétation : la portée binaire des relations ne suffit pas à garantir un
solveur polynomial. La famille `p3_block_tree(k)` montre une largeur qui croît
avec le nombre de blocs sur les cycles, tandis que les contrôles equal-distance
restent tautologiques et les paired-farthest donnent souvent des rejets
relationnels constants. C'est un stress utile pour toute future intégration
positive-only ou toute revendication FPT.

Prochaine action : mesurer si `solve_quartet_treewidth_csp` trouve des témoins
positifs réellement nouveaux pour `candidate.py` sous une garde de coût stricte,
ou basculer vers le catalogue de relations non booléennes/gadgets.

## Tentative T064 - Stress single P-node et domaine factoriel

Statut : benchmark de limite du modèle CSP/treewidth, hors `candidate.py`.

Changement : ajout de `tools/pc_single_p_domain_stress.py`, câblé par
`make bench-single-p-stress`. Le rapport prend un PC-tree star comme un seul
gros noeud `P`, donc un modèle CSP unary de treewidth `0`, puis mesure la
taille du domaine circulaire `(n-1)!/2`, les contraintes bad-side explicites et
le nombre d'ordres cR inspectés sous limite.

Gadget ajouté : `single_bad_side_quartet_instance()` donne quatre points avec
une unique paire non triviale `{0,2}` et `B_02 = {1,3}`. Elle isole une seule
contrainte `not sep(0,2;1,3)` : le star contient `3` ordres circulaires et `2`
passent cR.

Résultat `make bench-single-p-stress` :

- `30` lignes et `12` lignes ignorées car les petits gadgets ne s'appliquent
  qu'à `n=4` ou `n=5` ;
- toutes les lignes ont treewidth unary `0` ;
- domaine maximal visible `181440` à `n=10` ;
- plus grand domaine complètement énuméré `20160` à `n=9` ;
- `4` lignes `n=10` sont volontairement incomplètes sous limite `25000` ;
- plus grand nombre de contraintes bad-side non orientées `650` ;
- `cycle n=9` : `1` ordre cR sur `20160` ;
- equal-distance : tous les ordres inspectés sont cR.

Interprétation : T064 corrige une lecture trop optimiste de T061/T062. La
treewidth du graphe primal est un bon paramètre seulement avec une borne ou une
compression prouvée des domaines locaux. Pour les gros `P`, le domaine local
peut déjà contenir le problème. Une future intégration treewidth candidate doit
donc rester positive-only ou prouvée dans un sous-cas avec domaine borné.

## Tentative T065 - Catalogue de relations non booléennes P3

Statut : diagnostic CSP/complexité, hors `candidate.py`.

Changement : ajout de `tools/pc_relation_catalog.py`, câblé par
`make bench-relation-catalog`. L'outil réutilise
`quartet_effective_relation_report(..., store_full_relations=True)` sur
`p3_block_tree(k)` et extrait les relations fusionnées non booléennes avec :
taille de domaine, scopes, densités, tuples acceptés/rejetés quand petits,
hash canonique invariant par inversion de scope de même taille, treewidth,
parasites unaires/constantes, statut `relation_unsat_only` et caveat de promise.

Résultat `make bench-relation-catalog` :

- `20` lignes : `block_count=2,3`, familles `cycle`, `paired_farthest`,
  `random`, `equal`, `four_local_non_cr`, `five_local_non_cr`, avec repeats
  pour random/paired ;
- `20` lignes complètes ;
- `0` mismatch de validation ;
- `18` lignes `non_boolean_relation_catalog` et `2` lignes
  `two_sat_candidate` ;
- `38` instances de relations binaires non booléennes ;
- `27` hashes de relations binaires non booléennes distincts ;
- `12` lignes avec parasite `constant_reject` ;
- `18` lignes avec parasite unaire non booléen ;
- treewidth upper bound maximale `3` ;
- produit de domaine maximal par relation `36` ;
- densités binaires entre `0.0556` et `0.3333` ;
- `13` lignes avec `0` affectation acceptée dans le modèle relationnel.

Interprétation : T065 donne le premier catalogue lisible de relations `P3/P3`.
La diversité observée nourrit la piste gadget/dureté, mais les parasites sont
fréquents et empêchent toute conclusion NP-hard. Pour Piste C, ce rapport
confirme que "binaire" ne veut pas dire "2-SAT" : les domaines sont `6 x 6`, et
la complexité correcte reste paramétrée par `q` et `w`.

## Tentative T066 - Minage des formes de relations non booléennes

Statut : diagnostic CSP/complexité, hors `candidate.py`.

Changement : ajout de `tools/pc_relation_shape_search.py`, câblé par
`make bench-relation-shapes`. L'outil classe les profils T065 par histogrammes
de degrés, fonctionnalité, densité et tailles de domaines, puis ajoute des tags
de composabilité : `unary_gated`, `constant_blocked`, `constant_loose`,
`parasite_free`, `relation_unsat_only` et `promise_scaffold_only`.

Résultat `make bench-relation-shapes` :

- `38` instances de relations binaires non booléennes ;
- `27` hashes distincts ;
- formes observées : `sparse_partial_matching=9`,
  `partial_bijection=3`, `left_selector=5`, `right_selector=4`,
  `active_two_regular=10`, `small_domain_bridge=6`,
  `total_cover_dense=1` ;
- `0` mismatch de validation ;
- `0` `candidate_gadget_instances`, car aucun profil positif n'est encore
  parasite-free dans le contexte T065.

Interprétation : T066 rend le catalogue actionnable. Pour Piste C, ces classes
servent à choisir une représentation compacte éventuelle, mais elles ne
remplacent pas la relation exacte. Pour Piste F, elles fournissent des cibles de
gadget, mais seulement si une prochaine expérience supprime ou contrôle les
parasites.

## Tentative T067 - Composition des relations fonctionnelles

Statut : diagnostic CSP, hors `candidate.py`.

Changement : ajout de `tools/pc_relation_chain_probe.py`, câblé par
`make bench-relation-chains`. L'outil reconstruit les relations fusionnées
complètes, isole les relations non booléennes fonctionnelles, construit leurs
composantes, puis compte les affectations acceptées par plusieurs sous-systèmes
du CSP : fonctionnel seul, binaire non booléen seul, parasites seuls, et toutes
les relations.

Résultat `make bench-relation-chains` :

- `40` lignes, toutes complètes ;
- `0` mismatch de validation ;
- `31` lignes avec relations fonctionnelles ;
- `2` lignes `permutation_like` sans parasite restrictif ;
- `1` ligne `interaction_unsat` sans `constant_reject` ;
- `1` obstruction de cycle fonctionnel, mais dans une ligne déjà bloquée par
  `constant_reject`.

Interprétation : T067 expose une vraie corrélation entre contraintes dans le
CSP matérialisé, mais ne donne pas encore de solver. Pour une intégration
future, les tuples de relation ne peuvent pas être remplacés par une simple
statistique de forme ; l'interaction entre unaires et binaires doit rester
visible.

## Tentative T068 - Noyau UNSAT minimal d'interaction

Statut : diagnostic CSP matérialisé, hors `candidate.py`.

Changement : ajout de `tools/pc_relation_unsat_core_probe.py`, câblé par
`make bench-relation-unsat-cores`. L'outil reprend les lignes
`interaction_unsat`, énumère les affectations locales sous limite, puis cherche
des noyaux de relations de cardinalité minimale. Il reporte les tests de
suppression, les quartets source et les projections brutes des tuples acceptés.

Résultat observé sur le cas ciblé `five_local_non_cr` avec `p3_block_tree(2)` :

- `full_accept_count=0`, mais `binary_non_boolean_accept_count=4` et
  `parasite_accept_count=16` ;
- noyau minimal de taille `2` : l'unaire non booléenne sur `0` et la binaire
  `sparse_partial_matching` entre `0` et `1` ;
- valeurs acceptées par l'unaire sur `0` : `[0,1,3,5]` ;
- projection gauche brute de la binaire : `[2,4]` ;
- intersection vide, donc conflit unaire+binaire ;
- supprimer l'une des deux relations rend le noyau satisfaisable.

Interprétation : T068 corrige la lecture trop large de T067. L'UNSAT observé
n'est pas encore un gadget de cycle global ; c'est un conflit local entre un
parasite unaire et une relation binaire sparse. Cela reste utile pour tester les
compressions relationnelles, mais ce n'est ni un solver, ni une preuve de
dureté.

## Tentative T069 - `permutation_like` et contrôle quasi exact

Statut : diagnostic CSP matérialisé + contrôle exact petite taille, hors
`candidate.py`.

Changement : ajout de `tools/pc_permutation_like_probe.py`, câblé par
`make bench-permutation-like`. L'outil reprend les profils `permutation_like`
de `paired_farthest/P3x2`, énumère tous les ordres circulaires en `n=6`, filtre
les ordres quasi-circulaires exacts de `D`, puis compare cette famille aux
frontiers du scaffold.

Résultat `make bench-permutation-like` :

- `128` lignes, toutes complètes ;
- `0` mismatch de validation ;
- `11` lignes `permutation_like` ;
- `11` lignes `permutation_like` parasite-free ;
- `11` lignes où le scaffold `P3/P3` égale exactement les ordres quasi de `D` ;
- `0` anomalie ;
- hashes observés : `2b53bb78399e16b4`, `879a45396db9d606`,
  `8f00a6c3d8fbf547`, `95c822d2b89a3b08`.

Interprétation : dans ce sweep `n=6`, les bijections locales ne viennent pas
d'ordres hors quasi-circularité ; elles apparaissent précisément quand le
scaffold est exact pour les ordres quasi. Cela rend le signal plus propre, mais
ne prouve pas que le phénomène se compose ni que le PC-tree Hsu/McConnell serait
identique en grande taille.

## Tentative T070 - Composition multi-blocs de `permutation_like`

Statut : diagnostic CSP matérialisé, hors `candidate.py`.

Changement : ajout de `tools/pc_permutation_composition_probe.py`, câblé par
`make bench-permutation-composition`. L'outil scanne `paired_farthest` sur
`p3_block_tree(k)` pour `k=2,3,4`, extrait les arêtes `permutation_like`, leurs
composantes, les parasites restrictifs et les comptes d'affectations.

Résultat `make bench-permutation-composition` :

- `192` lignes, toutes complètes ;
- `0` mismatch ;
- `6` lignes avec une relation `permutation_like` ;
- `0` ligne avec au moins deux relations `permutation_like` ;
- `0` candidat de composition propre ;
- `max_permutation_component_edges=1` ;
- par bloc : `k=2` donne `5` bijections isolées propres, `k=3` aucune, `k=4`
  une bijection isolée bloquée par parasites.

Interprétation : T070 donne un contre-signal à la composition naïve des
bijective gadgets T069. Dans cette famille, les relations restent isolées ou
sont bloquées par constantes/unaires. Cela ne prouve pas qu'aucun gadget
multi-blocs n'existe ; cela indique seulement que `paired_farthest/P3x{k}` ne le
fournit pas directement.

## Tentative T071 - Composantes de toutes les relations non booléennes

Statut : diagnostic CSP matérialisé, hors `candidate.py`.

Changement : ajout de `tools/pc_relation_component_probe.py`, câblé par
`make bench-relation-components`. Contrairement à T070, l'outil ne filtre pas
sur `permutation_like` : il construit les composantes de graphe de toutes les
relations `binary_non_boolean_catalog` observées dans le CSP matérialisé, puis
mesure shapes, parasites, compte d'affectations de composante et compte global.

Métriques attendues : `multi_edge_component_rows`,
`parasite_free_multi_edge_rows`, `sat_parasite_free_multi_edge_rows`,
`max_component_edges`, histogrammes de shapes, et ventilation par `block_count`.

Résultat `make bench-relation-components` :

- `192` lignes, toutes complètes ;
- `0` mismatch de validation ;
- `617` relations binaires non booléennes ;
- `127` lignes avec composante multi-arêtes ;
- `0` ligne multi-arêtes parasite-free ;
- `0` ligne multi-arêtes parasite-free SAT ;
- `156` lignes avec `constant_reject` ;
- `max_component_edges=6`, `max_component_nodes=5`.

Par taille : `k=2` n'a aucune composante multi-arêtes et `5` lignes
parasite-free isolées ; `k=3` a `64/64` lignes multi-arêtes mais aucune
parasite-free ; `k=4` a `63/64` lignes multi-arêtes, toutes parasitées.

Interprétation à garder : une composante multi-arêtes sans parasite restrictif
serait un nouveau candidat de gadget. Une composante multi-arêtes bloquée par
`constant_reject` ou unaire restrictive est seulement un diagnostic de
corrélation dans le scaffold ; ce n'est pas une preuve d'impossibilité ni une
preuve de dureté.

## Tentative T021 - Repair positive-only pour paired-farthest

Statut : idée saine comme générateur expérimental vérifié, mais non intégrée à
`candidate.py`.

Idée subagent : `paired_farthest_frontier_repair_candidates(D, T)` détecterait
la structure paired-farthest, échantillonnerait des frontiers représentées,
déduirait un ordre de paires ou des deux composantes `low`, puis reconstruirait
des ordres side-by-side avec les mates. Le résultat ne serait accepté qu'après
`represents_order(T, order)` et `is_precircular_order_cR(D, order)`.

Résultats lecture seule :

- `n=6`, 80 seeds : oracle `True` 24 fois, heuristique `24/24`, aucun faux
  positif ;
- `n=8`, 80 seeds : oracle `True` 6 fois, heuristique `6/6`, aucun faux
  positif ;
- `n=10`, 80 seeds : oracle `True` 1 fois, déjà trouvé par la candidate ;
- `n=12`, 200 seeds : oracle `True` 0 fois ;
- odd `n=9/11` : rares positifs, déjà trouvés par la candidate ;
- scan crossing-filter profond jusqu'à 100k frontiers/seed : aucun gain
  grande taille observé ; `n=6 seed=21` confirme qu'un ordre où les cordes high
  croisent peut encore violer cR.

Conclusion : la fonction pourrait servir d'outil de recherche positive, mais
elle n'apporte pas de gain mesurable à la candidate actuelle et reste
échantillonnée. Ne pas l'intégrer avant d'avoir soit une borne, soit une preuve
de couverture d'un sous-cas non-star.
