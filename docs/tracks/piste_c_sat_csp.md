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
