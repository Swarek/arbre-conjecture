# Plans vivants

Pour toute étape longue, Codex doit créer ou mettre à jour un ExecPlan avant de
modifier l’algorithme. Un plan doit contenir :

- But.
- Hypothèse.
- Fichiers à modifier.
- Algorithme pressenti.
- Tests à exécuter.
- Risques.
- Plan de contre-exemples.
- Plan subagents, si plusieurs pistes sont explorées.
- Résultats observés.
- Décision : continuer / changer de piste / rollback.

Le plan doit rester lié au portefeuille d’hypothèses. Si une expérience réfute
une conjecture, le résultat doit produire un artefact : test, générateur,
contre-exemple minimal, lemme négatif ou entrée de journal.

Dans un Goal long, le plan doit aussi définir le critère d’arrêt : succès
mesurable, réfutation, blocage théorique, ou bascule vers une autre piste. Ne pas
laisser un Goal tourner comme une recherche ouverte sans sortie concrète.

## ExecPlan initial

But : créer le dépôt reproductible et les gates de correction/complexité.

Hypothèse : une baseline exacte sur petites tailles suffit pour démarrer la
boucle de recherche, tant qu’elle est explicitement non générale.

Fichiers à modifier : structure complète du dépôt.

Algorithme pressenti : brute force exact pour `n <= 8`, placeholder documenté
pour grandes tailles.

Tests à exécuter : `make quick`, puis `make bench-quick`.

Risques : confondre benchmark et preuve ; cacher les résultats incomplets de la
baseline grande taille.

Résultats observés : à renseigner dans `docs/experiment_log.md`.

Décision : continuer vers une première vraie piste algorithmique après le
checkpoint initial.

## ExecPlan 2026-05-22 - quartet diagnostics and first solver direction

But : produire un premier artefact de recherche utile pour remplacer la
baseline : instrumentation des violations cR/farthest sur petits ordres,
cartographie des contre-exemples, et choix d’une piste candidate pour la suite.

Hypothèse : avant d’implémenter un algorithme plus ambitieux, il faut savoir si
les violations de circular Robinson dans les frontiers PC-tree se résument par
des obstructions locales de quartets/farthest, ou si cette piste échoue déjà sur
petites instances.

Fichiers à modifier : prioritairement `src/pc_circular/predicates.py`,
`src/pc_circular/solvers/local_constraints.py`, éventuellement un outil sous
`tools/`, tests ciblés sous `tests/`, puis `docs/experiment_log.md` et
`docs/proof_obligations.md` si un lemme ou une limite devient clair.

Algorithme pressenti : ajouter des diagnostics exacts qui retournent un
quadruplet témoin pour la première violation cR et/ou une obstruction farthest
non croisée. Utiliser ces diagnostics pour comparer oracle exact, condition
farthest et contraintes locales sur familles random/cycle/block/ultrametric et
PC-trees star/balanced.

Tests à exécuter : `make quick`; si le solver change, `make
hunt-counterexamples`; si une accélération ou un nouveau mode de candidate est
intégré, `make bench-quick` puis, pour checkpoint sérieux, `make check`.

Risques : surinterpréter une condition nécessaire comme suffisante ; ignorer les
égalités ; confondre PC-tree arbitraire et PC-tree réellement issu de
Hsu/McConnell ; produire seulement un outil descriptif sans décision exploitable.

Plan de contre-exemples : générer des instances `n <= 8` où la condition
farthest diffère de `is_precircular_order_cR`, shrinker les matrices et ordres,
et enregistrer tout désaccord minimal dans les régressions ou le log.

Plan subagents : lancer jusqu’à 5 explorations indépendantes :

- Piste A : vérifier si les obstructions cR se projettent localement sur les
  branches P/C.
- Piste B : proposer une signature DP minimale et chercher une collision.
- Piste C : formuler un encodage SAT/CSP plausible sur petits PC-trees.
- Piste E : chercher activement des contre-exemples farthest-vs-cR.
- Piste F : regarder si grands P-nodes suggèrent un sous-cas polynomial ou une
  obstruction de complexité.

Résultats observés : diagnostics ajoutés pour extraire le premier quadruplet cR
violé et la première paire de cordes farthest non croisées. Projection locale des
obstructions sur les branches P/C ajoutée via `measure_obstruction_support`.
Trois contre-exemples à 4 points ont été trouvés et enregistrés :
égal-distance cR mais farthest brut échoue ; farthest unique qui passe le test
brut mais viole cR ; distances hors diagonale toutes distinctes qui passent
farthest mais violent cR. Les retours subagents convergent vers une suite fondée
sur les quadruplets cR exacts : CSP de patterns interdits ou DP avec signature
falsifiable.
Les familles `permuted_cycle` et `paired_farthest` ont été ajoutées comme stress
tests Piste F avec diagnostics exacts bornés dans le benchmark.

Décision : ne pas poursuivre la condition farthest-crossing brute comme solver
autonome. Continuer Piste E seulement comme outil de génération
d’obstructions, et comparer avec Piste C/Piste B pour ajouter les contraintes
manquantes.

## ExecPlan 2026-05-22 - Prop 4.5 fixed-order diagnostic

But : transformer les notes source `strongly-circular-sidma-1.pdf` en diagnostic
exécutable pour un ordre fixé quasi-circulaire.

Hypothèse : pour les ordres quasi-circulaires, l’absence de certificat farthest
du type Proposition 4.5 coïncide avec `is_precircular_order_cR` sur les petites
instances exhaustives. Si c’est vrai expérimentalement, ce diagnostic devient un
accélérateur et un générateur d’obstructions pour les pistes B/C, mais pas un
solver d’existence dans PC-tree.

Fichiers à modifier : `src/pc_circular/predicates.py`,
`tests/test_predicates.py`, éventuellement `docs/source_notes.md`,
`docs/tracks/piste_e_farthest_quartets.md`, `docs/proof_obligations.md` et
`docs/experiment_log.md`.

Algorithme pressenti : ajouter `find_farthest_prop_4_5_obstruction(D, order)`,
qui cherche `x, y, x' in F_x, y' in F_y` avec l’un des patterns
`x < x' < y < y'` ou `x < y' < y < x'`, en appliquant la clause non stricte
`x,x' notin F_y` et `y,y' notin F_x` quand `strict=False`.

Tests à exécuter : `make unit`, `make quick`, puis un script borné exhaustif
sur `n <= 5`, valeurs `{1,2,3}`, restreint aux ordres
`is_quasi_circular_order`.

Risques : mal interpréter les relations cycliques, appliquer le critère hors
quasi-circularité, ou confondre un test d’ordre fixé avec l’existence dans un
PC-tree.

Plan de contre-exemples : si le diagnostic diverge de `is_precircular_order_cR`
sur un ordre quasi-circulaire, enregistrer la matrice et l’ordre dans les
régressions. Chercher aussi un exemple hors quasi-circularité où le diagnostic
échoue, pour documenter la limite.

Plan subagents : pas de nouveau fanout immédiat ; les retours précédents
convergent sur cette étape locale.

Résultats observés : `find_farthest_prop_4_5_obstruction` et
`passes_farthest_prop_4_5_order_test` ajoutés. Tests unitaires ciblés ajoutés.
Probe exhaustif sur `n <= 5`, valeurs `{1,2,3}`, restreint aux ordres
quasi-circulaires : 0 désaccord avec `is_precircular_order_cR` ; `n=5` contient
`73272` ordres quasi-circulaires vérifiés.

Décision : conserver Prop. 4.5 comme diagnostic d’ordre fixé et source
d’obstructions exactes pour Piste B/C. Ne pas l’intégrer dans `candidate.py`
tant qu’il ne traite pas directement l’existence dans PC-tree.

## ExecPlan 2026-05-22 - Prop 4.5 nogood frontier scan

But : créer une première brique Piste C qui traite les obstructions Prop. 4.5
comme des nogoods expérimentaux sur les frontiers d’un PC-tree, sans modifier
la candidate générale.

Hypothèse : même si l’encodage CSP complet n’est pas encore écrit, un scanner
qui compare, frontier par frontier, `Prop. 4.5 passe` et `cR exact` donne une
mesure falsifiable : faux positifs, faux négatifs, première obstruction, et
témoin accepté. Ce rapport doit devenir le point d’entrée pour ajouter des
variables/nogoods de PC-tree au lieu d’énumérer naïvement.

Fichiers à modifier : `src/pc_circular/solvers/sat_like_experiments.py`, un test
unitaire dédié, `docs/tracks/piste_c_sat_csp.md`, `docs/experiment_log.md`,
éventuellement `docs/proof_obligations.md` et `docs/tracks/README.md`.

Algorithme pressenti : énumérer un ensemble borné ou complet d’ordres représentés
par `quasi_orders` ou `pc_tree`, filtrer optionnellement les ordres non
quasi-circulaires, appliquer `passes_farthest_prop_4_5_order_test`, puis
comparer à `is_precircular_order_cR` pour compter les désaccords. Retourner un
rapport structuré et une fonction de recherche de témoin Prop. 4.5.

Tests à exécuter : `make unit`, `make quick`; comme la candidate ne change pas,
`make hunt-counterexamples` n’est pas obligatoire mais un test exhaustif borné
doit vérifier qu’aucun désaccord n’est introduit sur les cas `n=4` déjà couverts.

Risques : présenter une énumération de frontiers comme un vrai CSP ; appliquer
Prop. 4.5 sans précondition quasi-circulaire ; confondre l’absence de désaccord
expérimental avec une preuve.

Plan de contre-exemples : enregistrer dans le rapport le premier faux positif et
le premier faux négatif ; si un désaccord apparaît sur ordre quasi-circulaire,
l’ajouter aux régressions et basculer Piste E avant toute intégration solver.

Plan subagents : 5 subagents exploratoires sont lancés en parallèle sur Pistes
B/C/E/F et audit documentaire ; ils ne modifient pas les fichiers et doivent
rapporter des risques ou prochaines expériences indépendantes.

Résultats observés : `prop45_nogood_frontier_report` et
`prop45_nogood_frontier_search` ajoutés dans `sat_like_experiments.py`. Les
tests vérifient un rejet de l’ordre quasi-circulaire non-cR à 4 points, un témoin
cycle-metric sur star tree, et l’absence de désaccord Prop. 4.5 vs cR sur les
657 matrices `n=4` à valeurs `{1,2,3}` ayant au moins un ordre quasi-circulaire.
Une probe random bornée `n=6..8` n’a trouvé aucun désaccord sur `35068` ordres
quasi-circulaires. `make unit`, `make quick`, `make check` et
`make bench-quick` passent. Les subagents confirment que la suite doit être un
moteur CSP à domaines locaux avec source `cr` directe avant compression
Prop. 4.5, et que le benchmark devra mieux séparer décisions complètes et runs
incomplets.

Décision : continuer Piste C, mais ne pas intégrer ce filtre dans
`candidate.py`. Prochaine étape recommandée : `build_local_domains` /
`frontier_from_assignment` pour petits nœuds `P/C`, avec refus `unsupported`
plutôt qu’une réponse négative sur grands domaines.

## ExecPlan 2026-05-22 - local-domain CSP scaffold

But : passer du scan de frontiers à un premier moteur CSP expérimental où les
variables sont les choix locaux des nœuds internes du PC-tree.

Hypothèse : pour des PC-trees dont tous les nœuds `P` ont un degré borné, on
peut énumérer les affectations de domaines locaux, reconstruire exactement les
frontiers représentées, puis filtrer par nogoods cR directs. Cela ne prouve pas
encore une complexité utile, mais valide la représentation CSP avant toute
compression Prop. 4.5 ou DP.

Fichiers à modifier : `src/pc_circular/solvers/sat_like_experiments.py`,
`tests/test_sat_like_experiments.py`, `docs/tracks/piste_c_sat_csp.md`,
`docs/experiment_log.md`, `docs/proof_obligations.md` et
`docs/tracks/README.md`.

Algorithme pressenti : traverser le PC-tree avec des chemins de nœuds comme
variables. Domaine d’un `C` : ordre forward et reverse de ses enfants. Domaine
d’un `P` : toutes les permutations des enfants si le degré est `<= max_p_degree`,
sinon statut `unsupported`. Une affectation complète reconstruit une frontier
linéaire ; sa forme canonique doit coïncider avec `enumerate_frontiers`. Le
solver expérimental `source="cr"` accepte exactement les affectations dont la
frontier vérifie `is_precircular_order_cR`.

Tests à exécuter : `make unit`, `make quick`, `make check`. Pour la recherche de
contre-exemples, comparer CSP `source="cr"` à `enumerate_frontiers` +
`is_precircular_order_cR` sur plusieurs petits arbres balanced/mixed et familles
random/cycle/block/ultrametric.

Risques : faire passer une énumération d’affectations pour un algorithme compact
; rater les duplications de frontiers dues aux symétries ; retourner `False` sur
un grand `P` au lieu de `unsupported`; mélanger source cR directe et Prop. 4.5.

Plan de contre-exemples : si les frontiers d’affectations diffèrent de
`enumerate_frontiers`, enregistrer l’arbre et l’affectation. Si `source="cr"`
diffère du filtre exact, ajouter un test de régression. Tester explicitement un
gros `P` pour vérifier `unsupported`.

Plan subagents : pas de nouveau fanout dans ce patch ; les subagents précédents
ont déjà fourni l’API et les risques. Un fanout pourra reprendre après T010 pour
falsifier une signature DP ou attaquer le benchmark.

Résultats observés : `build_local_domains`, `frontier_from_assignment`,
`iter_local_assignments`, `assignment_frontier_report`, `solve_nogood_csp` et
`accepted_frontiers_by_csp` ajoutés. Les tests vérifient que les frontiers issues
des affectations égalent `enumerate_frontiers`, que `source="cr"` égale le
filtre exact cR sur un arbre mixed, et qu’un star `P` de degré 5 avec
`max_p_degree=3` retourne `unsupported` sans décision négative. Probe bornée :
`1600` instances `n=4..7`, arbres balanced/mixed, huit familles, aucun désaccord.

Décision : continuer Piste C. La couche variable/frontier est validée comme
scaffold expérimental, mais elle énumère encore toutes les affectations. La
prochaine étape doit compiler des nogoods de quartets cR sur supports de
variables et mesurer le pruning ; ne pas intégrer dans `candidate.py`.

## ExecPlan 2026-05-22 - compiled cR quartet nogoods

But : transformer le CSP local en un artefact plus proche d’un vrai solveur :
des nogoods explicites issus de quartets cR interdits, projetés sur les variables
locales qui déterminent l’ordre cyclique du quartet.

Hypothèse : pour un quartet fixé, les choix locaux des nœuds internes où les
quatre labels sont séparés entre au moins deux branches déterminent son ordre
relatif. En projetant chaque violation cR sur ces variables, on obtient des
nogoods qui rejettent exactement les mêmes frontiers que `source="cr"` sur les
petits arbres supportés. Si cette projection sur-rejette ou sous-rejette, le
dépôt doit enregistrer un contre-exemple.

Fichiers à modifier : `src/pc_circular/solvers/sat_like_experiments.py`,
`tests/test_sat_like_experiments.py`, `docs/tracks/piste_c_sat_csp.md`,
`docs/experiment_log.md`, `docs/proof_obligations.md`,
`docs/tracks/README.md`, `docs/checkpoints.md`.

Algorithme pressenti : générer tous les atoms ordonnés `(x,y,z,t)` dont
l’inégalité pre-circular cR échoue. Pour chaque atom, calculer son support de
variables dans le PC-tree. Énumérer les affectations supportées et enregistrer
la projection de celles où l’atom apparaît dans l’ordre cyclique. Résoudre par
matching de ces signatures de nogoods au lieu de recalculer l’inégalité cR à
chaque frontier. Mesurer nombre d’atoms, nogoods uniques, tailles de support et
désaccords éventuels avec le filtre exact.

Tests à exécuter : `make unit`, `make quick`, `make check`; probe bornée sur
petits arbres balanced/mixed et familles variées pour comparer
`solve_compiled_nogood_csp` à `accepted_frontiers_by_csp(source="cr")`.

Risques : un support trop petit sur-rejette ; un support trop grand ne compresse
pas ; les frontiers équivalentes par rotation/renversement peuvent produire des
assignations dupliquées ; le résultat reste énumératif car la compilation
actuelle inspecte les affectations complètes.

Plan de contre-exemples : comparer le solveur compilé au filtre cR direct sur
familles `random/cycle/block/ultrametric/equal/non_strict/paired_farthest/
permuted_cycle`, arbres balanced/mixed, `n <= 7`. En cas de désaccord, enregistrer
`D`, `T`, l’atom, le nogood et la frontier fautive dans les régressions.

Plan subagents : un subagent lecture seule relit les risques de support de
variables et les tests de contre-exemples. L’intégration reste locale dans le
thread principal.

Résultats observés : `forbidden_cr_atoms`, `quartet_support_paths`,
`compile_cr_nogoods` et `solve_compiled_nogood_csp` ajoutés. Les tests couvrent
les supports imbriqués, un support artificiellement trop petit qui change la
projection d’un quartet, un atom qui wrappe autour de la coupure linéaire, le
statut `unsupported` pour gros `P`, et l’égalité avec le CSP cR direct sur petit
arbre. Probe bornée : `960` instances `n=4..7`, arbres balanced/mixed, huit
familles, aucun désaccord ; `153512` nogoods uniques produits.

Décision : continuer Piste C mais ne pas intégrer dans `candidate.py`. La
projection de support semble correcte expérimentalement ; le prochain obstacle
est la taille des nogoods et l’absence de pruning avant énumération complète.
Prochaine étape : backtracking avec signatures partielles et rapport de
croissance des nogoods/supports.

## ExecPlan 2026-05-22 - pruned nogood backtracking

But : utiliser les nogoods compilés pour pruner les affectations partielles dès
qu’un support de nogood est entièrement assigné, et mesurer si ce pruning réduit
l’espace exploré par rapport à l’énumération complète.

Hypothèse : même si la compilation de nogoods reste énumérative, un backtracking
qui vérifie les signatures à chaque variable peut rejeter des sous-arbres avant
construction de frontier. Sur petits PC-trees supportés, les frontiers acceptées
doivent rester exactement celles de `solve_compiled_nogood_csp` et du filtre cR
direct.

Fichiers à modifier : `src/pc_circular/solvers/sat_like_experiments.py`,
`tests/test_sat_like_experiments.py`, `docs/tracks/piste_c_sat_csp.md`,
`docs/experiment_log.md`, `docs/proof_obligations.md`,
`docs/tracks/README.md`, `docs/checkpoints.md`.

Algorithme pressenti : indexer les nogoods par leur dernière variable selon
l’ordre de backtracking. À chaque choix de domaine, vérifier seulement les
nogoods nouvellement complets ; si l’un matche, couper cette branche. À une
feuille non coupée, reconstruire la frontier, dédupliquer, et revalider avec
`is_precircular_order_cR` pour détecter tout faux positif/faux négatif. Reporter
`nodes_visited`, `branches_pruned`, `leaf_assignments_seen`, frontiers uniques
et taux de pruning.

Tests à exécuter : `make unit`, `make quick`, `make check`; probe bornée
comparant backtracking pruné, solveur compilé et CSP cR direct sur arbres
balanced/mixed et familles variées.

Risques : le pruning ne réduit rien si les supports sont trop grands ; un index
de nogood mal calculé peut sous-rejeter ; les métriques peuvent être trompeuses
si elles ne distinguent pas compilation énumérative et solve backtracking.

Plan de contre-exemples : comparer les ensembles acceptés à `source="cr"` sur
`n <= 7`; si désaccord, enregistrer la matrice, l’arbre, l’affectation partielle
et le nogood impliqué. Tester aussi une instance sans nogood pour vérifier que
le pruned solver accepte tout ce que cR accepte.

Plan subagents : pas de nouveau fanout ; la tranche est mécanique et issue du
retour T011. Un fanout redeviendra utile après les métriques de pruning pour
choisir entre Piste B et Piste F.

Résultats observés : `solve_pruned_nogood_csp` ajouté. Les nogoods sont indexés
par la dernière variable de leur support, et chaque branche est coupée dès que
la signature interdite est complète. Tests ajoutés : cycle metric avec pruning
strictement positif, et equal-distance sans atoms cR donc sans pruning. Probe
bornée : `640` instances `n=4..7`, arbres balanced/mixed, huit familles, aucun
désaccord avec le filtre cR direct ; `4284` branches prunées, `7396` feuilles
visitées sur `19200` affectations complètes possibles.

Décision : continuer à instrumenter Piste C, mais ne pas intégrer dans
`candidate.py`. Le pruning post-compilation est réel sur la probe, cependant la
compilation reste énumérative. Prochaine étape : benchmark interne séparant coût
de compilation, coût de solve et explosion des nogoods/supports par famille.

## ExecPlan 2026-05-22 - CSP internal benchmark

But : mesurer objectivement si Piste C progresse ou si la compilation des
nogoods explose déjà sur petits arbres supportés.

Hypothèse : un benchmark séparant compilation, solve pruné et filtre direct
permettra de savoir si le backtracking pruné réduit assez les feuilles pour
justifier la suite, ou si l’explosion des nogoods doit faire basculer vers Piste
B/F.

Fichiers à modifier : `src/pc_circular/solvers/sat_like_experiments.py`,
`tools/pc_csp_internal_benchmark.py`, `tests/test_csp_internal_benchmark.py`,
`Makefile`, `docs/tracks/piste_c_sat_csp.md`, `docs/experiment_log.md`,
`docs/proof_obligations.md`, `docs/tracks/README.md`, `docs/checkpoints.md`.

Algorithme pressenti : exposer une fonction qui lance le solve pruné depuis une
compilation déjà construite, puis créer un outil JSON qui mesure séparément
`compile_seconds`, `solve_seconds`, `direct_seconds`, `unique_nogoods`,
`full_assignment_space`, `leaf_assignments_seen`, `branches_pruned` et les
désaccords de validation. Le target Makefile `bench-csp-quick` reste borné à
petits `n`.

Tests à exécuter : `make unit`, `make quick`, `make check`, `make bench-csp-quick`
et `make bench-quick`.

Risques : benchmark trop lent ; rapport trop optimiste parce que la compilation
reste énumérative ; PC-trees unsupported cachés dans les agrégats.

Plan de contre-exemples : l’outil doit enregistrer tout mismatch entre solve
pruné et filtre direct. Si un mismatch apparaît, le transformer en régression
avant toute suite algorithmique.

Plan subagents : pas de fanout immédiat ; cette tranche produit le signal qui
décidera si un fanout Piste B/F devient prioritaire.

Résultats observés : `solve_pruned_nogood_csp_from_compilation` ajouté pour
séparer compilation et solve. `tools/pc_csp_internal_benchmark.py` et
`make bench-csp-quick` ajoutés. Le benchmark rapide produit
`reports/csp_internal_benchmark_quick.json` avec `192` lignes, `0` mismatch,
compilation médiane `~0.00104s`, solve pruné médian `~0.000284s`, filtre direct
médian `~0.000307s`, `31616` nogoods uniques, `1280` branches prunées, `2208`
feuilles visitées sur `5760` affectations possibles.

Décision : Piste C reste correcte expérimentalement, mais la compilation
énumérative domine déjà le solve sur petites tailles. Ne pas intégrer dans
`candidate.py`. La prochaine itération doit soit trouver une compilation
non-énumérative, soit basculer vers Piste B/F avec cette limite documentée.

## ExecPlan 2026-05-23 - bad-side fixed-order DP signature

But : établir un invariant exact pour un ordre circulaire fixé qui reformule la
condition pre-circular cR en termes de paires d'extrémités et de témoins mauvais
sur les deux arcs. L'objectif immédiat est un diagnostic Piste B, pas un solver
d'existence dans un PC-tree.

Hypothèse : pour une paire `{a,b}` et un témoin `w`, définir
`bad(a,b,w)` par `max(D[a][w], D[w][b]) > D[a][b]`. Un ordre viole cR ssi il
existe une paire `{a,b}` telle que l'un des deux arcs entre `a` et `b` contient
un témoin mauvais et l'autre arc contient aussi un témoin mauvais. Si l'invariant
est exact, il peut servir de base à une future signature DP.

Fichiers à modifier : `src/pc_circular/solvers/dp_experiments.py`,
`tests/test_dp_experiments.py`, `docs/tracks/piste_b_dp_pc_tree.md`,
`docs/experiment_log.md`, `docs/proof_obligations.md`,
`docs/tracks/README.md`, `docs/checkpoints.md`.

Algorithme pressenti : pour chaque paire non ordonnée `{a,b}`, calculer les deux
arcs ouverts dans l'ordre circulaire. Chercher un témoin `w` de chaque côté avec
`bad(a,b,w)`. Si les deux côtés existent, retourner un certificat qui se lit
comme un quadruplet cyclique `(a, w_left, b, w_right)`. Sinon l'ordre passe le
diagnostic.

Tests à exécuter : `make unit`, un probe exhaustif `n=4` valeurs `{1,2,3}` sur
tous les ordres, un probe random borné `n<=6`, `make quick`, `make check`, puis
`make bench-quick` pour conserver le checkpoint même si `candidate.py` ne change
pas.

Risques : erreur d'orientation des deux arcs ; mauvais traitement des égalités
dans le strict `>` ; croire que l'invariant d'ordre fixé suffit déjà pour
l'existence PC-tree ; signature DP future possiblement explosive parce qu'elle
reste indexée par toutes les paires globales.

Plan de contre-exemples : comparer systématiquement le diagnostic à
`is_precircular_order_cR` sur petits ordres exhaustifs et matrices aléatoires.
Si un désaccord apparaît, enregistrer `D`, l'ordre et le certificat dans les
régressions avant toute autre extension.

Plan subagents : trois explorateurs lecture seule tournent en parallèle :
preuve/cas d'égalité de l'invariant, chasse de contre-exemples, et projection
vers une signature DP ou circular-ones. L'intégration reste locale.

Résultats observés : diagnostic ajouté dans `dp_experiments.py` avec
`is_bad_witness`, `bad_witnesses_by_pair`, `bad_side_signature`,
`find_bad_side_cr_violation` et `passes_bad_side_cr_test`. Tests unitaires
ajoutés pour égal-distance, exemple quatre points non cR, cycle metric,
égalités strictes, exhaustif `n=4` et random `n=5,6`. Probe principal :
exhaustif `n=4,5`, valeurs `{1,2,3}`, puis random `n=6,7`, `715875`
comparaisons sans désaccord. Un subagent contre-exemple a aussi rapporté
`926775` comparaisons sans désaccord sur familles variées `n=6..9`.
Gates : `make unit`, `make quick`, `make check`, `make bench-quick` verts.

Décision : continuer Piste B comme invariant fixed-order prouvé par réécriture
et validé expérimentalement. Ne pas intégrer dans `candidate.py` avant une
signature de sous-arbre testée ; prochaine étape : chercher collisions de
signature ou mesurer l'explosion `#signatures / #frontiers`.

## ExecPlan 2026-05-23 - block signature collision metrics

But : transformer le diagnostic bad-side fixed-order en expérience falsifiable
sur des sous-frontiers contiguës, afin de savoir si une DP PC-tree peut compacter
les états ou si la signature devient quasi injective.

Hypothèse : une sous-frontier orientée peut exposer une signature minimale
composée des endpoints, des masques `inside/external` et des masques
`inside/inside`. Si deux sous-frontiers ont la même signature mais divergent
dans un même contexte externe pour `is_precircular_order_cR`, la signature est
réfutée. Si le ratio `#signatures / #frontiers` est proche de `1` sur les
familles stress, la piste DP compacte est suspecte même sans collision.

Fichiers à modifier : `src/pc_circular/solvers/dp_experiments.py`,
`tests/test_dp_experiments.py`, `docs/tracks/piste_b_dp_pc_tree.md`,
`docs/experiment_log.md`, `docs/proof_obligations.md`,
`docs/tracks/README.md`, `docs/checkpoints.md`.

Algorithme pressenti : pour un bloc `sigma` et un univers global, calculer :

- `endpoints = (sigma[0], sigma[-1])`;
- `EI_mask[a,e]` pour `a` dans le bloc et `e` hors bloc : bit gauche/droite
  selon l'existence d'un témoin mauvais interne de chaque côté de `a`;
- `II_mask[x,z]` pour deux labels internes : bits selon l'existence de témoins
  mauvais sur les deux arcs internes induits par `sigma`.

Grouper les frontiers par signature, reporter nombre de signatures, ratio,
plus gros bucket et rejets forcés. Ajouter aussi un chercheur de collision qui
teste deux frontiers de même signature dans les mêmes contextes externes.

Tests à exécuter : `make unit`, probes bornés sur familles `random`,
`paired_farthest`, `cycle`, `equal` avec blocs de taille `4..6`, puis
`make quick`, `make check`, `make bench-quick`.

Risques : l'expérience mesure une signature candidate, pas toutes les DP
possibles ; un ratio élevé n'est pas une preuve de dureté ; les contextes
testés peuvent manquer une collision ; les masques `II` autour des bords du bloc
peuvent être interprétés avec une mauvaise orientation.

Plan de contre-exemples : le chercheur doit accepter une signature volontairement
faible pour vérifier qu'il détecte bien une collision connue. Ensuite utiliser
la signature candidate sur petites familles ; toute collision réelle sera ajoutée
comme régression durable.

Plan subagents : deux explorateurs lecture seule tournent en parallèle :
validation de la définition de signature et recherche de collisions/mesures
indépendantes. L'intégration reste locale.

Résultats observés : `block_bad_side_signature`,
`forced_bad_side_pairs_in_block`, `block_signature_bucket_report` et
`find_signature_collision` ajoutés dans `dp_experiments.py`. Les masques
`inside/inside` ont été corrigés pour être relatifs au bord du bloc :
`between` versus `through-boundary`. Tests ajoutés pour masques
`inside/external`, rapport de buckets, collision détectée avec une signature
volontairement faible, collision endpoints-only, et absence de collision sur
égal-distance. Probe borné sur blocs de taille `4,5,6`, familles
`equal/cycle/block/random/paired_farthest`, `27` lignes : `equal` compresse
(`ratio` jusqu'à `0.0417` à `k=6`), `block` compresse partiellement
(`0.5667..0.8333` dans la probe), mais `cycle`, `random` et
`paired_farthest` restent quasi injectifs (`ratio` environ `0.95..1.0`) avec
beaucoup de frontiers déjà forcément rejetées.

Décision : la signature candidate est cohérente et falsifiable, mais trop
globale pour suggérer une DP compacte telle quelle. Continuer Piste B seulement
si une signature moins indexée par paires globales est proposée ; sinon basculer
vers Piste F ou un sous-cas polynomial.

## ExecPlan 2026-05-23 - universal bad-witness subcase

But : ajouter un premier sous-cas large-n prouvé à `candidate.py` sans affaiblir
l'oracle ni cacher les limites générales : si chaque paire `{a,b}` a au plus un
témoin mauvais global, tout ordre circulaire est circular Robinson.

Hypothèse : pour `B(a,b) = {w : max(D[a][w], D[w][b]) > D[a][b]}`, si
`|B(a,b)| <= 1` pour toute paire, aucun ordre circulaire ne peut placer deux
témoins mauvais sur les deux arcs opposés d'une même paire. Par le lemme T014,
aucune violation cR n'est possible. Le cas constant hors diagonale est inclus
car tous les ensembles `B(a,b)` sont vides.

Fichiers à modifier : `src/pc_circular/predicates.py`,
`src/pc_circular/pc_tree.py`, `src/pc_circular/solvers/candidate.py`, tests
ciblés, `docs/tracks/piste_f_complexity_subcases.md`,
`docs/experiment_log.md`, `docs/proof_obligations.md`,
`docs/tracks/README.md`, `docs/checkpoints.md`, éventuellement `README.md`.

Algorithme pressenti : ajouter un prédicat
`has_at_most_one_bad_witness_per_pair(D)` et un constructeur
`sample_frontier(T)` qui renvoie une frontier valide sans énumération. Dans
`candidate.solve`, avant le placeholder grande taille, retourner `exists=True`,
`complete=True` et un témoin représenté pour les instances du sous-cas ; si
`quasi_orders` est fourni, consommer seulement le premier ordre et renvoyer
`False` complet si la famille est vide.

Tests à exécuter : `make unit`, probe `n=9..30` sur star/balanced/mixed
vérifiant témoin cR et représenté, `make quick`, `make check`,
`make hunt-counterexamples`, `make bench-quick`.

Risques : retourner un ordre qui n'est pas représenté par le PC-tree ; traiter
une famille `quasi_orders` vide comme non vide ; présenter un sous-cas suffisant
comme caractérisation générale ; ne pas documenter que les autres grandes
tailles restent placeholder.

Plan de contre-exemples : tester arbres star/balanced/mixed pour `n>8`, un
itérable `quasi_orders=[]`, un premier `quasi_order` explicite, une matrice
constante, une matrice `constant + une arête haute`, et une matrice presque
constante avec une seule distance basse pour vérifier que le placeholder reste
marqué incomplet.

Plan subagents : deux explorateurs lecture seule : preuve/risques du sous-cas
constant, et recherche d'un autre sous-cas sûr adjacent. L'intégration reste
locale ; le second subagent a proposé le critère plus large `|B(a,b)| <= 1`.

Résultats observés : prédicats `is_constant_off_diagonal` et
`has_at_most_one_bad_witness_per_pair` ajoutés, `sample_frontier` ajouté, et
`candidate.py` renvoie maintenant `complete=True` avec solver
`candidate_universal_bad_witness_bound_all_orders` sur le sous-cas. Tests
unitaires ajoutés pour constant, `constant + une arête haute`,
`quasi_orders=[]`, premier `quasi_order`, et faux ami avec une arête basse.
Probe large-n : `33` checks sur star/balanced/mixed, `n=9..30`, témoins cR et
représentés/structurellement échantillonnés ; le faux ami reste placeholder
incomplet.

Décision : continuer avec ce sous-cas prouvé intégré à la candidate. Il améliore
la complétude grande taille pour une famille non stricte, mais ne résout pas le
cas général.

## ExecPlan 2026-05-23 - certify sampled positive witnesses

But : améliorer la sémantique de `candidate.py` sans changer l'oracle : un ordre
échantillonné qui vérifie `is_precircular_order_cR` est un certificat positif
d'existence, même si la recherche n'est pas exhaustive pour les réponses
négatives.

Hypothèse : pour un `pc_tree`, les ordres produits par `enumerate_frontiers`
sont représentés ; pour `quasi_orders`, l'ordre vient de la famille fournie ;
pour l'absence de PC-tree, tout ordre circulaire sur `0..n-1` est admissible.
Donc une réponse `exists=True` accompagnée d'un ordre cR valide est complète
comme preuve d'existence. En revanche, l'absence de témoin dans l'échantillon ne
prouve toujours pas `False`.

Fichiers à modifier : `src/pc_circular/solvers/candidate.py`,
`tests/test_candidate.py`, `docs/experiment_log.md`, `docs/checkpoints.md`,
`docs/proof_obligations.md`, `docs/tracks/README.md`, éventuellement
`README.md`.

Algorithme pressenti : dans la boucle large-n de `candidate.solve`, si un ordre
échantillonné passe `is_precircular_order_cR`, renvoyer `complete=True`,
`solver="candidate_validated_sampled_witness"` et une note expliquant que le
témoin prouve l'existence. Garder `complete=False` pour les retours négatifs
après échantillonnage.

Tests à exécuter : `make unit`, probe `make bench-quick` pour mesurer les runs
incomplets, `make quick`, `make check`, `make hunt-counterexamples`, puis
`make bench-quick`.

Risques : confondre "preuve positive d'existence" avec "algorithme décisionnel
complet" ; retourner `complete=True` pour un témoin qui ne vient pas vraiment de
la famille représentée ; oublier que les réponses négatives restent
placeholders.

Plan de contre-exemples : tester un grand cycle metric sur `star` où le témoin
naturel suffit, un grand cas non cR échantillonné où le résultat doit rester
incomplet, et les gates oracle sur `n <= 8`.

Plan subagents : pas de fanout ; c'est une clarification de certificat positif
locale et directement testable.

Résultats observés : `candidate.py` renvoie maintenant
`candidate_validated_sampled_witness` avec `complete=True` lorsqu'un ordre
échantillonné est cR. Les retours négatifs après échantillonnage conservent
`complete=False`. Tests ajoutés pour un grand cycle metric `star` certifié
positif et pour une famille `quasi_orders` qui ne contient qu'un mauvais ordre,
où le résultat reste incomplet. `make unit` : `59 passed`. `make bench-quick` :
`0` timeout, `0` run incomplet, les grandes tailles mixed/star passent par
`candidate_validated_sampled_witness` sauf les sous-cas universels déjà prouvés.
`make bench` : `0` timeout jusqu'à `n=100`, `42` runs incomplets visibles, fit
polynomial empirique `p ~= 3.25`, les incomplets correspondant aux réponses
négatives du placeholder.

Décision : conserver cette clarification de certificat positif. Elle améliore
les benchmarks sans changer l'oracle ni faire passer un `False` non justifié
pour complet.

## ExecPlan 2026-05-23 - minimum-distance cycle witness

But : ajouter une recherche positive structurée pour la famille planted-cycle :
si le graphe des distances minimales positives est un cycle simple, reconstruire
l'ordre cyclique candidat et l'accepter seulement s'il est vérifié cR et
représenté.

Hypothèse : dans les métriques de cycle permutées, les arêtes de distance
minimale forment exactement le cycle planté. Pour un PC-tree `star`, tout ordre
est représenté ; sans PC-tree, tout ordre circulaire sur `0..n-1` est admissible.
Donc le cycle reconstruit peut fournir un témoin positif complet. Pour les
PC-trees non-star, l'étape reste désactivée tant qu'on n'a pas de test de
représentation non énumératif fiable.

Fichiers à modifier : `src/pc_circular/solvers/candidate.py`,
`tests/test_candidate.py`, `docs/tracks/piste_f_complexity_subcases.md`,
`docs/experiment_log.md`, `docs/proof_obligations.md`,
`docs/tracks/README.md`, `docs/checkpoints.md`.

Algorithme pressenti : calculer les arêtes de distance minimale positive. Si
chaque sommet a degré 2 et le graphe est connexe, parcourir le cycle depuis le
plus petit label avec un choix déterministe du voisin suivant. Vérifier ensuite
`is_precircular_order_cR(D, order)`. Accepter seulement si `pc_tree is None` ou
si le PC-tree est un star de feuilles, car la représentation est alors certaine.

Tests à exécuter : `make unit`, probe sur `permuted_cycle/star` grandes tailles,
`make quick`, `make check`, `make hunt-counterexamples`, `make bench-piste-f`,
`make bench-quick`.

Risques : le graphe des distances minimales peut être un cycle simple sans que
les distances restantes satisfassent cR ; d'où la vérification cR obligatoire.
Pour un PC-tree non-star, le cycle reconstruit peut ne pas être représenté ;
d'où désactivation hors star/None. Le cas `n <= 3` est déjà couvert par brute
force/universel.

Plan de contre-exemples : chercher des matrices où le graphe minimum est un
cycle simple mais le cycle échoue cR ; vérifier que la candidate ne les accepte
pas. Tester `permuted_cycle` grande taille, `paired_farthest`, `random` et un
PC-tree balanced où le témoin structurel doit être ignoré.

Plan subagents : deux explorateurs lecture seule : preuve/risques du témoin
cycle-minimum et recherche de faux positifs.

Résultats observés : `candidate.py` ajoute
`candidate_minimum_distance_cycle_witness`. La branche reconstruit le cycle du
graphe des distances minimales positives, puis accepte seulement après
`is_precircular_order_cR`. Elle est désactivée pour les PC-trees non-star.
Subagent preuve/risques : accepter seulement comme certificat positif
star/None ; vérifier directement cR ; ajouter un garde non-star. Subagent
contre-exemples : matrice `n=6` où le graphe minimum est le cycle
`(0,1,2,3,4,5)` mais l'ordre viole cR, donc le test fixed-order est
indispensable. Tests ajoutés : témoin `permuted_cycle` grande taille sur star,
non-utilisation sur balanced non-star, et régression du faux positif minimum
cycle. Les documents sources locaux sont aussi conservés dans
`docs/source_materials/`, y compris la capture Proposition 4.4.

Validation observée : `make unit` : `62 passed`; `make quick` : `62 passed`,
`JUSTE`; `make check` : `JUSTE`; `make hunt-counterexamples` : `JUSTE`;
`make bench-piste-f` : `0` timeout, `0` incomplet pour
`permuted_cycle/star`, et `candidate_minimum_distance_cycle_witness` pour tous
les `n > 8`; `paired_farthest` reste incomplet en grande taille (`60`
incomplets star, `40` incomplets mixed), ce qui garde la famille stress utile ;
`make bench-quick` : `0` timeout, `0` incomplet. `make bench` : `0` timeout,
`42` incomplets visibles jusqu'à `n=100`, fit polynomial empirique
`p ~= 3.25`.

Décision : conserver comme certificat positif borné, pas comme critère de
décision général. Continuer ensuite sur une piste qui attaque les cas négatifs
incomplets, notamment `paired_farthest` et PC-trees non-star.

## ExecPlan 2026-05-23 - non-enumerative PC-tree membership for witnesses

But : promouvoir les certificats positifs hors PC-tree star quand un ordre
candidat est déjà connu et vérifié cR, en ajoutant un test exact de
représentation d'une frontier par le scaffold PC-tree sans énumérer toutes les
frontiers.

Hypothèse : dans le scaffold actuel, une frontier linéaire représentée par un
nœud interne est exactement une concaténation de blocs contigus correspondant à
ses enfants ; pour `P`, l'ordre des blocs est arbitraire, et pour `C`, il est
forward ou reverse. Pour un ordre circulaire au root, il suffit de tester les
rotations des deux orientations. Cela donne un test de membership sûr pour un
ordre témoin fixé.

Fichiers à modifier : `src/pc_circular/pc_tree.py`,
`src/pc_circular/solvers/candidate.py`, `tests/test_pc_tree_frontiers.py`,
`tests/test_candidate.py`, `docs/tracks/piste_f_complexity_subcases.md`,
`docs/experiment_log.md`, `docs/proof_obligations.md`,
`docs/tracks/README.md`, `docs/checkpoints.md`.

Algorithme pressenti : ajouter un parseur récursif `represents_order_fast` ou
améliorer `represents_order` quand `limit is None`. Le parseur valide la
permutation de labels, découpe la séquence en runs de labels appartenant au même
enfant, rejette si un enfant apparaît dans plusieurs runs, vérifie l'ordre
local `P/C`, puis recurse dans les chunks. Au root, tester toutes les rotations
de l'ordre et de son renversé. Dans `candidate.py`, remplacer le garde
star-only du témoin minimum-cycle par "pas de PC-tree, ou ordre représenté par
ce test exact".

Tests à exécuter : `make unit`, probe comparant membership rapide à
`enumerate_frontiers` sur arbres small star/balanced/mixed, probe large-n
`permuted_cycle` sur star/balanced/mixed, `make quick`, `make check`,
`make hunt-counterexamples`, `make bench-piste-f`, `make bench-quick`, et si
vert `make bench`.

Risques : une rotation de root pourrait être acceptée à tort dans un sous-nœud ;
d'où restriction des rotations au root seulement. Une canonicalisation
circulaire pourrait masquer un ordre linéaire non représenté ; d'où comparaison
contre l'énumération exacte sur petits arbres. Pour les grands PC-trees
non-star, un `False` du membership ne prouve rien sur l'existence générale.

Plan de contre-exemples : chercher un ordre qui traverse deux fois le même
sous-arbre et doit être rejeté ; tester des rotations/renversements valides ;
tester un C-node avec ordre enfant non forward/reverse ; comparer exhaustivement
aux frontiers énumérées pour `n <= 8`.

Plan subagents : trois explorateurs lecture seule : preuve/risques du parseur
PC-tree, attaque du témoin minimum-cycle + membership, et mesure sur
`permuted_cycle` avec PC-trees balanced/mixed.

Résultats observés : `represents_order` garde l'ancien diagnostic borné quand
`limit` est fourni, mais utilise maintenant un parseur exact non énumératif
quand `limit is None`. `candidate_minimum_distance_cycle_witness` accepte un
témoin minimum-cycle pour un PC-tree non-star seulement si ce parseur confirme
la représentation ; le test de représentation est fait avant le check cR pour
éviter un coût élevé sur les non-hits. Subagents : l'explorateur membership a
confirmé l'invariant par induction et signalé le piège des rotations internes
de `C`; l'explorateur contre-exemples a fourni un cas `n=6` où le min-cycle est
cR mais non représenté et où l'oracle PC-tree répond `False`; l'explorateur
benchmark a mesuré que `permuted_cycle` aléatoire est presque jamais représenté
par balanced/mixed au-delà de `n=10`.

Validation observée : `make unit` : `70 passed`; probe membership vs
énumération : `11837` checks sans désaccord ; probe grande taille
`cycle/mixed` : témoin représenté et cR pour `n=10,14,20,40,80` ;
`make quick` : `70 passed`, `JUSTE`; `make check` : `JUSTE`;
`make hunt-counterexamples` : `JUSTE`; `make bench-piste-f` :
`cycle/mixed` et `permuted_cycle/star` ont `0` timeout et `0` incomplet,
`paired_farthest` reste incomplet grande taille (`60` star, `40` mixed) ;
`make bench-quick` : `0` timeout et `0` incomplet ; `make bench` : `0`
timeout jusqu'à `n=100`, `42` incomplets visibles, fit polynomial empirique
`p ~= 3.25`.

Décision : conserver l'extension comme certificat positif sûr pour ordre fixé
représenté. Elle améliore les PC-trees non-star quand le cycle est compatible
avec les blocs du scaffold, sans résoudre les cas négatifs ni les vrais
PC-trees Hsu/McConnell.

## ExecPlan 2026-05-23 - paired-farthest structural witness

But : attaquer la famille `paired_farthest` qui reste incomplète en grande
taille, en reconstruisant depuis `D` un témoin positif pour le sous-cas
structurel "matching farthest unique + deux cliques low-distance + neutre
éventuel".

Hypothèse : si les distances positives ont trois niveaux `low < mid < high`,
si les arêtes `high` forment un matching parfait sur tous les sommets sauf
éventuellement un neutre, et si les arêtes `low` sur les sommets appariés
forment deux cliques disjointes de même taille, alors l'ordre
`A_0, ..., A_{m-1}, mate(A_0), ..., mate(A_{m-1})` avec le neutre à la fin
est cR par la caractérisation bad-side. La candidate ne doit l'accepter qu'après
`represents_order` si un PC-tree est fourni ; le check cR direct est remplacé
par l'obligation de preuve documentée pour éviter le coût `O(n^4)`.

Fichiers à modifier : `src/pc_circular/solvers/candidate.py`,
`tests/test_candidate.py`, `docs/tracks/piste_f_complexity_subcases.md`,
`docs/experiment_log.md`, `docs/proof_obligations.md`,
`docs/tracks/README.md`, `docs/checkpoints.md`.

Algorithme pressenti : détecter les trois niveaux positifs ; construire le
matching des arêtes maximales ; identifier au plus un neutre sans arête
maximale ; retirer le neutre ; vérifier que les arêtes minimales induisent
exactement deux composantes cliques de même taille ; vérifier que chaque mate
maximal est dans l'autre composante et que les distances restantes valent
`mid`. Construire l'ordre avec une composante triée par label, puis les mates
dans le même ordre, puis le neutre. Tester représentation si `pc_tree` est
fourni.

Tests à exécuter : `make unit`, probes `paired_farthest` star/balanced/mixed
sur seeds et tailles grandes, `make quick`, `make check`,
`make hunt-counterexamples`, `make bench-piste-f`, `make bench-quick`, et si
vert `make bench`.

Risques : optimiser uniquement la famille générée ; à mitiger en documentant
le sous-cas structurel en termes de distances, pas de nom de générateur, et en
gardant la vérification cR/représentation comme seule raison d'accepter.
Autre risque : les cas `m=1` ou dégénérés à deux niveaux ; ils restent couverts
par brute force `n <= 8` et le sous-cas universel.

Plan de contre-exemples : perturber une distance `mid` en `low` ou `high` et
vérifier que le détecteur ne prétend pas au sous-cas ; vérifier avec
`quasi_orders` fourni que la branche ne contourne pas une famille explicite ;
tester PC-tree mixed où le témoin reconstruit est souvent non représenté.

Plan subagents : trois explorateurs lecture seule : caractérisation
paired-farthest, taux de représentation par PC-tree, attaque de faux positifs
du détecteur structurel.

Résultats observés : `_paired_farthest_order` détecte les matrices three-level
à matching farthest maximal, reconstruit les deux cliques low-distance, et
renvoie l'ordre side-by-side avec les mates synchronisés. La candidate accepte
ce témoin seulement quand `quasi_orders is None` et quand il est représenté par
le PC-tree éventuel. Le sous-cas est documenté comme preuve bad-side, donc la
branche évite le check cR `O(n^4)` sur grandes tailles positives.

Validation observée : `make unit` : `75 passed`; probe `paired_farthest` :
`380` checks, solver `candidate_paired_farthest_matching_witness` jusqu'à
`n=100` en `~0.0056s`; `make quick` : `75 passed`, `JUSTE`; `make check` :
`JUSTE`; `make hunt-counterexamples` : `JUSTE`; `make bench-piste-f` :
`paired_farthest/star` passe à `0` timeout et `0` incomplet avec la nouvelle
branche pour tous les `n > 8`, tandis que `paired_farthest/mixed` garde `40`
incomplets ; `make bench-quick` : `0` timeout et `0` incomplet ; `make bench` :
`0` timeout jusqu'à `n=100`, `42` incomplets visibles, fit polynomial
empirique `p ~= 3.24`.

Décision : conserver comme sous-cas positif prouvé pour star et pour tout
PC-tree qui représente le témoin canonique. Ne pas conclure négatif quand le
témoin n'est pas représenté ; les subagents ont trouvé de petits cas non-star
où un autre ordre représenté peut exister.

## ExecPlan 2026-05-23 - paired-farthest non-star counterexamples

But : comprendre pourquoi `paired_farthest/mixed` reste incomplet après le
témoin canonique T020, et produire des artefacts durables avant d'intégrer une
nouvelle branche candidate.

Hypothèse : pour un PC-tree non-star, l'ordre paired-farthest canonique
`A, mate(A)` peut ne pas être représenté, mais il peut exister un autre ordre
représenté et cR. Une recherche positive basée seulement sur les cordes `high`
qui se croisent risque d'être trop faible.

Fichiers à modifier : `tests/test_regression_counterexamples.py`,
`docs/tracks/piste_f_complexity_subcases.md`,
`docs/tracks/piste_a_local_pc_constraints.md`,
`docs/tracks/piste_b_dp_pc_tree.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`,
`docs/proof_obligations.md`.

Algorithme pressenti : ne pas modifier `candidate.py` dans cette tentative.
Ajouter les contre-exemples minimaux et documenter les résultats subagents.
Tester localement une reconstruction d'ordres side-by-side dérivés de
frontiers représentées, mais la garder hors candidate tant que la version
grande taille n'est pas bornée et prouvée.

Tests à exécuter : test ciblé `tests/test_regression_counterexamples.py`,
`make quick`, puis `make bench-piste-f` si les régressions passent.

Risques : transformer une heuristique qui marche sur `n=6/8` en faux solver ;
confondre condition nécessaire "cordes high croisées" et cR ; oublier que les
nœuds balanced/mixed du scaffold fanout 2 rendent `P` et `C` localement
équivalents.

Plan de contre-exemples : intégrer le cas positif minimal `n=6 seed=1` où le
témoin canonique est non représenté mais l'oracle PC-tree est `True`, et le cas
`n=6 seed=21` où les cordes farthest passent mais cR échoue. Garder le cas
`n=4 seed=5` déjà enregistré comme faux positif de représentation.

Plan subagents : cinq explorateurs lecture seule. Piste A projette les
ensembles `I_x(v)` ; Piste B teste des signatures DP compactes ; Piste C
cherche une extension CSP minimale ; Piste E/F shrinke `paired_farthest`
non-star ; sources relit les PDF vendorizés et les obligations.

Résultats observés : avant modification, `make quick` passe (`75 passed`,
`JUSTE`). Les six PDF demandés et la capture Proposition 4.4 sont déjà
versionnés dans `docs/source_materials/` avec hashes listés. Probe locale :
une génération naïve d'ordres side-by-side depuis rotations de frontiers
récupère tous les positifs oracle observés sur `paired_farthest` `n=6/8`, mais
elle devient trop coûteuse si non bornée en grande taille. Version bornée :
peu de hits au-delà de `n=10`, temps déjà ~`0.25s` pour `n=40` sur seulement
16 candidats.

Décision : intégrer seulement les régressions et la documentation. La prochaine
tentative utile doit soit prouver une famille d'ordres représentés
paired-farthest non-star, soit basculer vers un diagnostic local/CSP qui produit
des obstructions sans prétendre décider l'existence.

## ExecPlan 2026-05-23 - farthest set projection diagnostic

But : ajouter un outil expérimental Piste A/D qui projette les ensembles de plus
lointains voisins sur les branches de chaque nœud PC-tree, afin de guider les
obstructions locales sans modifier `candidate.py`.

Hypothèse : les ensembles `I_x(v) = {i : B_i intersecte F_x}` peuvent signaler
des contraintes locales utiles, en particulier violations d'intervalle sur
nœuds `C`, non-laminarité sur gros `P`, ou échec d'un test circular-ones exact
à petit degré. Les itérations précédentes montrent déjà que ces signaux ne sont
pas suffisants pour décider l'existence.

Fichiers à modifier : `src/pc_circular/solvers/local_constraints.py`,
`tests/test_local_constraints.py`, `docs/tracks/piste_a_local_pc_constraints.md`,
`docs/tracks/README.md`, `docs/experiment_log.md`, `docs/checkpoints.md`,
éventuellement `docs/proof_obligations.md`.

Algorithme pressenti : pour chaque nœud interne, calculer les labels de chaque
branche, puis pour chaque point `x` projeter `F_x` sur les indices de branches.
Rapporter histogramme des tailles, ensembles propres non triviaux, violations
laminaires, violations d'intervalle dans l'ordre local déclaré, et compatibilité
circular-ones par brute force seulement si le degré est borné (`<= 8`).

Tests à exécuter : test ciblé `tests/test_local_constraints.py`, probe sur
familles `equal/cycle/random/paired_farthest` en `star` et `mixed`,
`make unit`, `make quick`, puis `make bench-quick` si aucun rapport lourd n'est
généré.

Risques : surinterpréter le diagnostic comme critère nécessaire/suffisant ;
rejeter à tort les cas non stricts égal-distance par laminarité ; ne rien voir
sur les arbres binaires où beaucoup de projections sont singletons.

Plan de contre-exemples : verrouiller dans les tests le cas égal-distance star,
où la laminarité échoue alors que tous les ordres sont cR, et un nœud `C` où un
point a projection `{0,2}` non intervalle dans l'ordre déclaré.

Plan subagents : deux explorateurs lecture seule en parallèle. L'un vérifie la
forme minimale du diagnostic et les tests pertinents. L'autre prépare le sous-cas
strict pour décider si la prochaine itération doit basculer vers Piste F.

Résultats observés : `project_farthest_sets_to_pc_nodes` ajouté dans
`local_constraints.py` avec rapport par nœud, tailles de branches,
`projection_size`, statut circular-ones et témoin d'ordre de branches quand
compatible. Tests ajoutés pour égal-distance/star non laminaire mais
circular-ones compatible, et pour une violation d'intervalle déclarée sur nœud
`C`. Probe `n=8` :
`equal/star` signale `laminar=28`, `random/star` signale `laminar=8`,
`interval=6`, `circular_ones_false=1`, tandis que `random/mixed` et
`paired_farthest/mixed` sont muets sur le scaffold binaire. `make unit` :
`77 passed`; `make quick` : `77 passed`, `JUSTE`; `make bench-quick` : `0`
timeout, `0` incomplet, dernier `n=20` via sous-cas universel et témoins
échantillonnés. Subagent strict : l'Algorithm 5.2 doit être transcrit dans un
module expérimental avant toute intégration candidate, car une probe naïve rate
`cycle_metric(6)` et produit des mismatches `n=4`.

Décision : conserver comme diagnostic Piste A/D. Ne pas modifier `candidate.py`.
La prochaine itération peut basculer vers le sous-cas strict ou vers une famille
de contraintes circular-ones avec preuve locale plus forte.

## ExecPlan 2026-05-23 - strict fixed-order predicates

But : préparer le sous-cas strict avec des définitions directes testables avant
de tenter Algorithm 5.2 ou une intégration dans `candidate.py`.

Hypothèse : les conditions strictes d'ordre fixé du papier peuvent être ajoutées
comme prédicats expérimentaux sûrs : `scR` remplace `>=` par `>` dans la
formule pre-circular, `sqcR` utilise `d(x,z) > min(d(y,z), d(t,z))`, et le
strict circular Robinson fixed-order se teste par arcs strictement Robinson.
Ces prédicats ne génèrent pas encore les ordres stricts de façon polynomiale.

Fichiers à modifier : `src/pc_circular/predicates.py`,
`src/pc_circular/solvers/strict_experiments.py`,
`tests/test_strict_experiments.py`, `docs/tracks/piste_f_complexity_subcases.md`,
`docs/tracks/README.md`, `docs/experiment_log.md`, `docs/checkpoints.md`,
`docs/proof_obligations.md`.

Algorithme pressenti : implémenter les prédicats directs pour ordre fixé et un
rapport `strict_order_report(D, pc_tree=None, max_n=8)` qui énumère exactement
les ordres seulement pour petites tailles. Ne pas modifier `candidate.py`.

Tests à exécuter : tests stricts ciblés, probe exhaustive `n=4` valeurs
`{1,2,3}` pour vérifier strict circular => strict pre-circular => strict quasi,
régression d'un témoin strict non représenté par PC-tree, `make unit`,
`make quick`, puis `make bench-quick` si la candidate est inchangée.

Risques : confondre les prédicats fixed-order avec un algorithme de génération
d'ordres stricts ; nommer "strict quasi" une condition autre que `sqcR` ;
laisser les égalités passer par erreur ; intégrer trop tôt une transcription
naïve de l'Algorithm 5.2.

Plan de contre-exemples : tests sur égal-distance pour rejeter les égalités ;
cycle metric pour vérifier un positif strict ; exhaustif `n=4` pour les
implications ; `max_n` pour empêcher une énumération cachée grande taille.

Plan subagents : deux explorateurs lecture seule. L'un vérifie les définitions
strictes fixed-order et les pièges d'égalités. L'autre cherche des familles et
matrices utiles pour les tests/régressions strictes.

Résultats observés : ajout de `is_strict_robinson_linear`,
`is_strict_precircular_order_cR`, `is_strict_quasi_circular_order`,
`is_strict_circular_robinson_order` et des fonctions de violation associées
dans `predicates.py`. Ajout de `strict_order_report` dans
`solvers/strict_experiments.py`, exact seulement pour `n <= max_n` et incomplet
au-delà. Tests ajoutés : égal-distance rejeté en strict, `cycle_metric(6)`
unique strict modulo renversement, Fig. 2.2 strict quasi mais non strict
pre-circular dans l'ordre `(0,1,2,3)`, ordre corrigé `(0,1,3,2)` strict
circular, témoin strict cR non représenté par PC-tree avec oracle PC-tree
`False`, et équivalence exhaustive `n=4` entre strict pre-circular et définition
stricte par arcs sur `2187` couples matrice-ordre. Subagents : définitions
strictes directes confirmées, Fig. 2.2 et témoin strict non représenté
recommandés comme régressions prioritaires. `make unit` : `85 passed`;
`make quick` : `85 passed`, `JUSTE`; `make bench-quick` : `0` timeout, `0`
incomplet.

Décision : conserver comme base expérimentale Piste F. Ne pas intégrer dans
`candidate.py` tant que la génération des ordres stricts (Algorithm 5.2 ou
équivalent) n'est pas prouvée exhaustive et testée contre l'oracle PC-tree.

## ExecPlan 2026-05-23 - Algorithm 5.2 strict candidates

But : transformer la lecture de l'Algorithm 5.2 en générateur expérimental
d'ordres candidats stricts, filtrés par les prédicats fixed-order de T023,
sans modifier `candidate.py`.

Hypothèse : en générant les ordres issus de la partition `N/F` de l'Algorithm
5.2 pour tous les choix `x` et `x' in F_x`, puis en vérifiant directement
`sqcR`/strict circular, on récupère les un ou deux ordres compatibles stricts
observés en petit `n`. Les sorties non vérifiées restent de simples candidats.

Fichiers à modifier : `src/pc_circular/solvers/strict_experiments.py`,
`tests/test_strict_experiments.py`, `docs/source_notes.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/proof_obligations.md`, `docs/experiment_log.md`, `docs/checkpoints.md`.

Algorithme pressenti : implémenter `strict_algorithm52_report(D, pc_tree=None)`
avec `J(x,y) = {u : d(x,y) > max(d(x,u), d(u,y))} union {x,y}`. Pour le cas
`N cap F != empty`, construire les ordres `Sort(x, X1) ++ ReverseSort(x, X2)`.
Pour le cas disjoint, calculer les partitions `J(x,z)` et `J(x',y)`, générer
les deux orientations possibles de chaque segment afin d'éviter le faux rejet
observé sur `cycle_metric(6)`, puis filtrer par les prédicats stricts. Limiter
le nombre de candidats produits et marquer `complete=False` si la limite est
atteinte.

Plan de contre-exemples : comparer aux ordres exacts de `strict_order_report`
sur Fig. 2.2, `cycle_metric(6)`, equal-distance, témoin strict non représenté
par PC-tree, exhaustif `n=4` valeurs `{1,2,3}`, et probes random `n=5`.

Plan subagents : cinq explorateurs lecture seule en parallèle : transcription
source Algorithm 5.2, matrices strictes minimales, artefact CSP/PC-tree strict,
signature DP stricte, et lien modules/circular-ones.

Tests à exécuter : tests stricts ciblés, probe exhaustive `n=4`, `make unit`,
`make quick`, `make bench-quick`. Si `candidate.py` reste inchangé, pas de
`make hunt-counterexamples` obligatoire, mais garder une probe dédiée contre
les ordres stricts exacts.

Risques : surinterpréter un générateur filtré comme preuve de complétude ;
confondre ordre strict quasi et strict circular ; exploser sur des égalités
non strictes ; accepter un témoin non représenté par le PC-tree.

Résultats observés : `strict_algorithm52_report` ajouté dans
`strict_experiments.py`. Le rapport génère des candidats inspirés de
l'Algorithm 5.2 pour tous les choix `x, x' in F_x`, filtre par représentation
PC-tree si fournie, puis vérifie `strict_quasi`, `strict_precircular` et
`strict_circular` par les prédicats directs. Pour éviter le faux rejet de la
transcription naïve T022 sur `cycle_metric(6)`, le cas `N cap F = empty`
génère les deux orientations possibles des segments `N` et `F` avant filtrage.
Tests ajoutés : cycle strict positif, Fig. 2.2 avec deux ordres `sqcR` mais un
seul strict circular, random `n=5` seed `33` strict positif non couvert par les
témoins minimum-cycle/paired-farthest existants, garde PC-tree non représenté,
et exhaustif `n=4` valeurs `{1,2,3}` comparé aux ordres stricts exacts. Probe
locale : cycles `n=4..7`, equal-distance et random `n=5/6` seeds `0..199` sans
désaccord entre les ordres stricts exacts et les ordres vérifiés du rapport.

Décision : conserver comme artefact expérimental T024. Ne pas intégrer dans
`candidate.py` : la complétude est vérifiée expérimentalement sur petits cas,
mais pas encore prouvée pour l'existence dans un PC-tree compact ni pour les
cas non stricts.

## ExecPlan 2026-05-23 - ball circular-ones strict diagnostic

But : tester la piste D en ajoutant un rapport borné qui compare, sur les
ordres/frontiers énumérables, la contrainte "toutes les boules sont des arcs" à
`is_quasi_circular_order`, `strict_quasi` et `strict_circular`.

Hypothèse : la famille des boules propres fournit le bon pont circular-ones
pour générer les ordres quasi-circulaires candidats. Sur les petits cas stricts,
les ordres dont toutes les boules sont arcs doivent coïncider avec
`is_quasi_circular_order`; en revanche Fig. 2.2 doit rappeler que ce n'est pas
une décision cR.

Fichiers à modifier : `src/pc_circular/solvers/strict_experiments.py`,
`tests/test_strict_experiments.py`, `docs/tracks/piste_d_circular_ones.md`,
`docs/tracks/README.md`, `docs/proof_obligations.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : construire toutes les boules propres non triviales
`B_r(x) = {y : D[x][y] <= r}` pour les rayons observés hors diagonale. Pour un
ordre donné, tester `is_arc(order, B)` pour chaque boule. Le rapport énumère
`all_circular_orders(n)` ou les frontiers de `pc_tree` tant que `n <= max_n`,
compte `ball_arc`, `quasi`, `strict_quasi`, `strict_precircular`,
`strict_circular`, signale le premier mismatch ball/quasi, et calcule une
signature de module par vecteur d'appartenance aux boules.

Plan de contre-exemples : Fig. 2.2 doit avoir deux ordres `ball_arc/strict_quasi`
mais un seul strict circular ; equal-distance doit être ball/quasi/cR non strict
mais pas strict ; le témoin strict non représenté doit rester absent avec le
PC-tree `C`; l'exhaustif `n=4` valeurs `{1,2,3}` doit chercher un mismatch
ball/quasi.

Plan subagents : trois explorateurs lecture seule : invariants
circular-ones/balles, contre-exemples petits, et API PC-tree/CSP bornée.

Tests à exécuter : tests stricts ciblés, probe exhaustive `n=4` ball/quasi,
`make unit`, `make quick`, `make bench-quick`.

Risques : traiter les boules triviales comme signal artificiel ; confondre
quasi-circularité par boules avec circular Robinson ; croire que le rapport
énumératif est un algorithme scalable ; oublier que l'absence de strict witness
ne réfute pas un ordre non strict cR.

Résultats observés : `strict_ball_circular_ones_report` ajouté dans
`strict_experiments.py`. Il énumère les ordres ou frontiers quand `n <= max_n`,
construit les boules métriques non triviales, compte les ordres où toutes ces
boules sont des arcs, compare à `is_quasi_circular_order`, `strict_quasi`,
`strict_precircular` et `strict_circular`, puis fournit une signature de modules
par appartenance exacte aux boules non triviales. Le rapport expose aussi
`counts`, `exists`, `order_source`, `incomplete_reasons` et un sanity check de
représentation PC-tree. Tests ajoutés : `cycle_metric(6)` donne un seul ordre
ball/quasi/strict ; Fig. 2.2 donne deux ordres ball/quasi mais un seul strict
circular ; equal-distance garde tous les ordres non stricts mais aucun strict ;
un random `n=6 seed=7` verrouille un ordre quasi/ball non cR ;
`cycle_metric(4)` verrouille que les modules sont groupés par signature exacte,
pas par poids ; le témoin strict non représenté reste absent avec PC-tree ;
les labels PC-tree invalides sont rejetés, un arbre imbriqué n'a pas de
mismatch de représentation, et `n=9` est marqué incomplet. Probe locale :
cycles `n=4..7`, equal-distance et
random `n=5/6` seeds `0..199` sans mismatch ball/quasi.

Décision : conserver comme diagnostic Piste D. La contrainte de boules confirme
la génération quasi-circulaire sur petits cas, mais ne décide pas cR et reste
énumérative dans ce scaffold. Ne pas intégrer dans `candidate.py`.

## ExecPlan 2026-05-23 - bad-witness arc constraints diagnostic

But : tester la piste D/E en transformant les mauvais témoins cR
`B(a,b) = {w : max(d(a,w), d(w,b)) > d(a,b)}` en contraintes d'arcs
diagnostiques, sans modifier `candidate.py`.

Hypothèse : pour un ordre fixé, la condition exacte est que chaque `B(a,b)`
reste sur un seul des deux arcs ouverts délimités par `a,b`. En revanche les
contraintes plus simples "`B(a,b)` est un arc" et "`B(a,b) union {a,b}` est un
arc" devraient être des approximations falsifiables, utiles pour éviter une
fausse réduction circular-ones.

Fichiers à modifier : `src/pc_circular/solvers/dp_experiments.py`,
`tests/test_dp_experiments.py`, `docs/tracks/piste_d_circular_ones.md`,
`docs/tracks/piste_e_farthest_quartets.md`, `docs/tracks/README.md`,
`docs/proof_obligations.md`, `docs/experiment_log.md`,
`docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : ajouter `bad_witness_arc_constraints_report(D,
pc_tree=None, max_n=8, frontier_limit=None)`. Le rapport énumère tous les
ordres circulaires ou les frontiers PC-tree tant que `n <= max_n`, refuse les
labels PC-tree invalides, marque `complete=False` si `frontier_limit` est
atteint, et produit des comptes séparés pour `bad_witness_one_side`,
`bad_witness_set_arc`, `bad_witness_with_endpoints_arc`,
`precircular`, `strict_precircular` et `strict_circular`. Si le rapport est
incomplet, une absence de témoin reste `None`, jamais `False`.

Plan de contre-exemples : chercher exhaustivement en `n=4` valeurs `{1,2,3}`
et par random/shrink en `n=5/6` des faux positifs/faux négatifs pour les deux
contraintes naïves. Verrouiller les exemples minimaux dans
`tests/test_dp_experiments.py`; vérifier que `bad_witness_one_side` reste
équivalent à `is_precircular_order_cR` sur l'exhaustif `n=4`.

Plan subagents : trois explorateurs lecture seule : définitions et risques
d'une contrainte d'arc, recherche de contre-exemples petits, et API PC-tree
bornée compatible avec les rapports Piste D existants.

Tests à exécuter : tests DP ciblés, probe de contre-exemples bornée,
`make unit`, `make quick`, `make bench-quick`. `make check` n'est pas requis si
`candidate.py` reste inchangé, mais `make quick` doit rester vert.

Risques : appeler "arc" une condition de côté et la vendre comme réduction
circular-ones ; interpréter une énumération tronquée comme une décision ;
traiter les égalités avec `>=` au lieu de `>` ; confondre cR non strict et
strict circular.

Résultats observés : `bad_witness_arc_constraints_report` ajouté dans
`dp_experiments.py`, avec énumération bornée des ordres/frontiers, gestion
`complete=False` pour `n > max_n` et `frontier_limit`, et champs séparés
`counts`, `exists`, témoins de violation et mismatches. Les subagents ont
confirmé la reformulation exacte one-side pour ordre fixé et fourni des
contre-exemples minimaux : `B(a,b)` arc est trop fort (`n=5`, ordre
`(0,2,4,1,3)`, cR vrai mais `B(0,3)={1,2}` non arc) ; `B(a,b) union {a,b}` est
ni nécessaire (equal-distance `n=4`) ni suffisant (matrice carrée opposée).
Tests ajoutés dans `tests/test_dp_experiments.py`, dont l'équivalence
one-side/cR sur l'exhaustif `n=4`.

Décision : conserver T026 comme résultat négatif utile Piste D/E. Ne pas
intégrer dans `candidate.py`. La suite doit utiliser `B(a,b)` arc seulement
comme filtre/nogood suffisant expérimental, ou construire un état DP/CSP qui
mémorise le côté des mauvais témoins sans sur-rejeter les ordres cR.

## ExecPlan 2026-05-23 - bad-side pair nogood CSP compilation

But : tester Piste B/C après T026 en compilant des nogoods CSP à partir des
paires `{a,b}` et des mauvais témoins situés sur deux côtés, plutôt qu'à partir
de tous les quartets cR ordonnés.

Hypothèse : les atomes bad-side
`(a, y, b, t)` et `(a, t, b, y)` pour `y,t in B(a,b)` capturent exactement les
violations cR d'un ordre fixé, mais avec moins d'atomes que
`forbidden_cr_atoms`. Cela peut réduire la compilation/pruning expérimental sans
prouver encore un solveur compact.

Fichiers à modifier : `src/pc_circular/solvers/sat_like_experiments.py`,
`tests/test_sat_like_experiments.py`, `docs/tracks/piste_b_dp_pc_tree.md`,
`docs/tracks/piste_c_sat_csp.md`, `docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/README.md`, `docs/proof_obligations.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : ajouter `forbidden_bad_side_atoms(D)` qui génère pour
chaque paire `{a,b}` les deux orientations de chaque couple de mauvais témoins.
Ajouter `compile_bad_side_nogoods(D,T)` en réutilisant le support
`quartet_support_paths`, puis `solve_compiled_bad_side_nogood_csp` et
`solve_pruned_bad_side_nogood_csp` qui réutilisent le solveur pruné existant.
Tous les témoins acceptés restent validés par `is_precircular_order_cR`.

Plan de contre-exemples : exhaustif `n=4` valeurs `{1,2,3}` pour vérifier que
les atomes bad-side détectent exactement les ordres non cR ; comparaison avec
`forbidden_cr_atoms` sur equal-distance, cycle, random et Fig. 2.2 ; tests sur
PC-tree balanced/mixed ; vérifier que les égalités ne créent pas d'atomes.

Plan subagents : trois explorateurs lecture seule : API/tests et pièges
d'égalité, familles de comparaison/pruning, et formulation preuve/limites pour
les obligations.

Tests à exécuter : `tests/test_sat_like_experiments.py`, probe bornée de counts
bad-side vs quartets, `make unit`, `make quick`, `make bench-csp-quick` si la
compilation CSP est touchée, puis `make bench-quick`.

Risques : croire que moins d'atomes implique complexité polynomiale ; compiler
encore par énumération complète ; oublier des rotations/orientations cycliques ;
produire un faux négatif sur les cas non stricts en utilisant `>=`.

Résultats observés : `forbidden_bad_side_atoms`,
`compile_bad_side_nogoods`, `solve_compiled_bad_side_nogood_csp` et
`solve_pruned_bad_side_nogood_csp` ajoutés dans `sat_like_experiments.py`.
Tests ajoutés : équivalence exhaustive `n=4` des atomes bad-side avec
`not cR`, equal-distance sans atomes/nogoods, wrapping non-cR minimal,
équivalence avec le filtre cR direct sur arbre mixed, comparaison de taille
avec les quartets ordonnés, et solveur pruné bad-side. Probe T027 :
`equal6_mixed` donne `0` atome/nogood ; `wrap4_c` donne `6/12` atomes et
`2/4` nogoods ; `cycle8_mixed_f3` donne `416/832` atomes et `1178/2356`
nogoods ; `paired8_1008_mixed_f3` donne `168/336` atomes et `796/1592`
nogoods. Tous les probes ont `validation_fp/fn = 0`.

Décision : conserver comme simplification CSP Piste B/C/E. Le résultat divise
les objets compilés par deux dans les probes, mais la compilation reste
énumérative et le pruning observé ne prouve pas de nouvelle borne. Ne pas
intégrer dans `candidate.py`.

## ExecPlan 2026-05-23 - bounded exact PC-tree candidate subcase

But : intégrer un sous-cas exact dans `candidate.py` pour les PC-trees dont le
nombre de frontiers représentées est borné par un petit seuil explicite, même
si `n > 8`.

Hypothèse : certains PC-trees fournis ont peu de frontiers malgré une grande
taille `n` (par exemple un nœud `C` quasi rigide). Dans ce cas, énumérer toutes
les frontiers représentées et vérifier `is_precircular_order_cR` donne une
décision complète justifiée. Si l'upper bound dépasse le seuil, la candidate ne
conclut pas et retombe sur ses certificats positifs/placeholder existants.

Fichiers à modifier : `src/pc_circular/solvers/candidate.py`,
`tests/test_candidate.py`, `docs/tracks/piste_f_complexity_subcases.md`,
`docs/tracks/piste_c_sat_csp.md`, `docs/tracks/README.md`,
`docs/proof_obligations.md`, `docs/experiment_log.md`,
`docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : ajouter un upper bound récursif borné sur le nombre de
frontiers linéaires du scaffold PC-tree : produit des enfants, facteur
`degree!` pour `P`, facteur `2` pour `C`, avec saturation à
`EXACT_PC_TREE_FRONTIER_LIMIT + 1`. Si le bound est au plus la limite, appeler
`enumerate_frontiers(pc_tree, canonical=True)` sans limite, tester chaque ordre,
et retourner une décision complète `True` avec témoin ou `False` sans témoin.
Ne pas utiliser cette branche quand `quasi_orders` explicite est fourni.

Plan de contre-exemples : C-tree rigide `n>8` positif (`cycle_metric`) ;
C-tree rigide `n>8` négatif contenant le contre-exemple 4 points étendu ;
star/gros P-node dont l'upper bound dépasse la limite et ne doit pas retourner
un faux `False` complet ; garde contre `quasi_orders` explicite.

Plan subagents : deux explorateurs lecture seule : preuve/tests de la branche
bounded PC-tree et fixtures `n>8` positives/négatives.

Tests à exécuter : tests candidate ciblés, `make unit`, `make quick`,
`make hunt-counterexamples` parce que `candidate.py` change, `make bench-quick`
et si possible `make check`.

Risques : sous-estimer le nombre de frontiers ; conclure `False` après une
énumération tronquée ; bypasser une famille `quasi_orders` explicite ; ralentir
les benchmarks star en essayant d'énumérer un gros P-node ; confondre scaffold
PC-tree et vrai PC-tree Hsu/McConnell.

Résultats observés : `EXACT_PC_TREE_FRONTIER_LIMIT`,
`_pc_tree_frontier_upper_bound` et
`candidate_exact_bounded_pc_tree_frontiers` ajoutés dans `candidate.py`.
La branche est placée après les certificats positifs rapides
minimum-cycle/paired-farthest et avant l'échantillonnage. Résultat positif
verrouillé : C-tree rigide `n=9` avec métrique plateau-cycle, aucun shortcut
minimum-cycle/paired-farthest, témoin naturel cR. Résultat négatif verrouillé :
C-tree rigide `n=9` avec contre-exemple quatre points étendu, unique frontier
non cR. Garde gros `P` verrouillé : star `n=9` sur la même matrice a un témoin
cR hors des 64 premiers échantillons, donc la candidate reste
`candidate_large_n_placeholder` et `complete=False`.
Probe locale : 42 décisions de la nouvelle branche comparées à
`exact_oracle_pc_tree` sur arbres rigides/one-P `n=9..11`, familles
cycle/equal/paired/random, sans désaccord.

Décision : intégrer dans `candidate.py` comme sous-cas exact borné. Ce n'est
pas une solution générale : la limite évite toute énumération explosive et les
grands espaces restent incomplets.

## ExecPlan 2026-05-23 - finite quasi-orders exact candidate subcase

But : intégrer un sous-cas exact pour les appels où `quasi_orders` est une
famille finie explicite et assez petite, au lieu de n'en échantillonner que les
premiers ordres pour `n > 8`.

Hypothèse : si l'utilisateur fournit directement une famille finie d'ordres
admissibles, la candidate peut décider exactement l'existence cR dans cette
famille en testant chaque ordre par `is_precircular_order_cR`, tant que la
taille est sous une limite explicite. Ce sous-cas ne dit rien sur les PC-trees
compacts ni sur les familles trop grandes/non dimensionnées.

Fichiers à modifier : `src/pc_circular/solvers/candidate.py`,
`tests/test_candidate.py`, `docs/proof_obligations.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : ajouter `EXACT_QUASI_ORDER_LIMIT`. Si
`quasi_orders is not None`, expose `len(quasi_orders)`, et que cette taille est
au plus la limite, itérer sur toute la famille, valider chaque ordre, tester cR,
et retourner une décision complète positive au premier témoin ou négative après
avoir tout testé. Si la famille n'a pas de longueur fiable ou dépasse la limite,
retomber sur l'échantillonnage existant sans conclure négativement.

Plan de contre-exemples : liste `quasi_orders` avec un seul mauvais ordre
`n=10`, qui doit maintenant être un `False` complet ; liste avec 64 mauvais
ordres puis un témoin cR, que l'ancien sampling aurait ratée ; liste trop
grande dont le témoin est hors budget, qui doit rester `complete=False` ; un
itérateur non dimensionné qui doit rester soumis au placeholder.

Plan subagents : deux explorateurs lecture seule : revue de correction/API du
sous-cas fini et audit des incomplets benchmark restants.

Tests à exécuter : `tests/test_candidate.py`, `make unit`, `make quick`,
`make hunt-counterexamples`, `make check`, `make bench-quick`. Lancer
`make bench` seulement si l'itération touche les benchmarks `pc_tree=star`.

Risques : confondre une famille explicite finie avec un PC-tree compact ;
consommer un itérateur non réitérable ; retourner `False` complet après une
énumération tronquée ; bypasser les certificats positifs existants dans les cas
où `quasi_orders` n'est pas fourni ; faire croire que cela réduit les incomplets
du benchmark `mixed/star`, alors que celui-ci passe par `pc_tree` et non par
`quasi_orders`.

Résultats observés : `candidate_exact_bounded_quasi_orders` ajouté. Le sous-cas
valide toute famille `quasi_orders` `Sized` de taille
`<= EXACT_QUASI_ORDER_LIMIT`, retourne un témoin complet si trouvé, et retourne
un négatif complet seulement après avoir inspecté toute la famille. Tests
verrouillés : famille vide non universelle devient négatif complet ; liste finie
mauvais seul `n=10` devient négatif complet ; liste avec 64 mauvais ordres puis
témoin cR trouve le témoin ; liste trop grande et itérateur non dimensionné
restent `candidate_large_n_placeholder` si le sampling manque le témoin ;
`quasi_orders` garde la priorité sur `pc_tree`.
Validation : `tests/test_candidate.py` `24 passed`, `make unit` `115 passed`,
`make quick` `115 passed` puis `JUSTE`, `make hunt-counterexamples` `JUSTE`,
`make check` `JUSTE`, `make bench-quick` `0` timeout et `0` incomplet.

Décision : intégrer comme sous-cas exact API. Ne pas le présenter comme progrès
sur les benchmarks `pc_tree=star` : ceux-ci n'utilisent pas `quasi_orders`.
Prochaine cible : `paired_farthest/mixed` ou attribution par sous-famille des
placeholders `mixed/star`.

## ExecPlan 2026-05-23 - mixed benchmark placeholder attribution

But : rendre les placeholders du benchmark `mixed/star` exploitables en
attribuant chaque run `mixed` à sa sous-famille effective (`random`, `cycle`,
`block`, `ultrametric`, `equal`, `non_strict`).

Hypothèse : les `42` incomplets du rapport fort ne sont pas uniformément
répartis entre les sous-familles. Une attribution reproductible permettra de
viser le prochain certificat sur la bonne famille au lieu d'optimiser à l'aveugle
sur `mixed`.

Fichiers à modifier : `src/pc_circular/generators.py`,
`tools/pc_circular_complexity_benchmark.py`, `tests/test_generators.py`,
un test benchmark dédié si une fonction `run_benchmark` est exposée,
`docs/experiment_protocol.md`, `docs/tracks/README.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/experiment_log.md`,
`docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : extraire la liste stable `MIXED_INSTANCE_KINDS` et
ajouter `instance_by_kind_with_metadata`. Pour un `kind != mixed`, la
métadonnée `resolved_kind` vaut le kind demandé. Pour `mixed`, tirer exactement
le même choix qu'avant avec `rng.choice(MIXED_INSTANCE_KINDS)`, générer
l'instance résolue, puis retourner `{"requested_kind": "mixed",
"resolved_kind": subkind}`. Le benchmark utilisera cette API et ajoutera aux
rows JSON : counts d'instances par sous-famille, incomplets par sous-famille,
timeouts par sous-famille, et solvers par sous-famille.

Plan de contre-exemples : vérifier qu'à seed identique, `instance_by_kind(...,
kind="mixed")` produit la même matrice que la nouvelle API ; vérifier que les
counts par sous-famille somment aux repeats ; lancer `bench-quick` et idéalement
`bench` pour confirmer que le nombre total d'incomplets reste visible et que
leur attribution est lisible.

Plan subagents : deux explorateurs lecture seule : revue des risques
reproductibilité/JSON et analyse préparatoire de `paired_farthest/mixed` pour
T031.

Tests à exécuter : tests générateurs ciblés, test benchmark ciblé si ajouté,
`make unit`, `make quick`, `make bench-quick`, puis `make bench` si le temps
reste raisonnable. `make hunt-counterexamples` n'est pas requis car
`candidate.py` ne change pas.

Risques : changer la distribution RNG de `mixed`; casser les rapports JSON
existants ; rendre les rapports trop volumineux ; confondre diagnostic de
benchmark et preuve ; croire qu'une attribution résout les incomplets au lieu de
seulement guider T031.

Résultats observés : ajout de `MIXED_INSTANCE_KINDS` et
`instance_by_kind_with_metadata`, qui préserve à seed identique la matrice
produite par `instance_by_kind(..., kind="mixed")`. Le benchmark expose
maintenant une fonction `run_benchmark`, ajoute `seed` et `mixed_instance_kinds`
au rapport, puis agrège par `resolved_kind` :
`resolved_kind_counts`, `successful_runs_by_resolved_kind`,
`timeouts_by_resolved_kind`, `incomplete_runs_by_resolved_kind`,
`exists_true_by_resolved_kind`, `solver_counts_by_resolved_kind`, et
`diagnostics_sample_metadata` quand les diagnostics exacts sont actifs.
Validation : tests générateurs/benchmark ciblés `7 passed`, `make unit`
`119 passed`, `make quick` `119 passed` puis `JUSTE`, `make bench-quick`
`0` timeout et `0` incomplet, `make check` `JUSTE`, `make bench` `0` timeout
et `42` incomplets visibles, `make bench-piste-f` `0` timeout.

Résultat benchmark fort T030 : avec seed `20260521`, les `42` incomplets
`mixed/star` sont tous attribués à `resolved_kind="random"`. Les sous-familles
`cycle`, `block`, `ultrametric`, `equal` et `non_strict` n'ont aucun placeholder
dans ce rapport fort.

Résultat ciblé `paired_farthest/mixed` après T028/T030 : `n=10` et `n=12` sont
maintenant complets par `candidate_exact_bounded_pc_tree_frontiers`; les
incomplets restants de cette famille ciblée sont `n=16` et `n=20`, tous via
`candidate_large_n_placeholder`.

Décision : conserver comme instrumentation de complexité. T030 ne résout pas le
problème d'existence, mais transforme les placeholders `mixed/star` en signal
exploitable : le prochain effort benchmark général doit viser `random`, tandis
que `paired_farthest/mixed` reste une famille ciblée séparée pour T031.

## ExecPlan 2026-05-23 - hereditary small obstruction certificate

But : réduire les incomplets `random/star` du benchmark principal par un
certificat négatif héréditaire sound, sans prétendre résoudre le cas général.

Hypothèse : si une sous-matrice induite de petite taille, en pratique 4 points,
n'admet aucun ordre circular Robinson, alors la matrice complète n'admet aucun
ordre circular Robinson. Les randoms du benchmark fort devraient contenir très
vite une telle obstruction.

Fichiers à modifier : `src/pc_circular/solvers/candidate.py`,
`tests/test_candidate.py`, éventuellement `tests/test_regression_counterexamples.py`
si un contre-exemple minimal utile est isolé, `docs/proof_obligations.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : ajouter une recherche bornée de sous-ensembles de taille
4. Pour chaque sous-ensemble, construire la sous-matrice induite et la tester
exactement par la baseline brute-force sur 4 labels. Si aucune ordre cR n'existe
sur cette sous-matrice, retourner `exists=False`, `complete=True`, avec les
labels du certificat. Si aucune obstruction n'est trouvée avant la limite de
recherche, ne conclure rien et continuer vers le sampling incomplet.

Plan de contre-exemples : vérifier que `cycle_metric` et les sous-cas positifs
ne déclenchent pas le certificat ; vérifier qu'une matrice random `n=10`
certifiée négative contient bien une sous-matrice 4 points sans ordre cR ;
comparer contre oracle exact sur petits `n` via `make check` ; lancer
`make hunt-counterexamples` car `candidate.py` change ; mesurer `make bench`
pour vérifier que les placeholders `random` deviennent des rejets complets.

Plan subagents : deux explorateurs lecture seule : preuve de soundness/API et
probe random/star pour estimer la limite de sous-ensembles nécessaire.

Tests à exécuter : `tests/test_candidate.py`, `make unit`, `make quick`,
`make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`.

Risques : confondre absence d'obstruction trouvée avec absence globale ; rendre
un rejet complet après une recherche tronquée ; coût trop élevé si on parcourt
tous les 4-subsets à grand `n` ; oublier que le certificat est indépendant du
PC-tree mais ne prouve rien si aucune obstruction n'est trouvée ; présenter un
benchmark random comme preuve de correction globale.

Résultats observés : ajout de `SMALL_FORBIDDEN_SUBMATRIX_ORDER = 4`,
`SMALL_FORBIDDEN_SUBMATRIX_LIMIT = 4096`, et
`candidate_small_forbidden_submatrix_obstruction` dans `candidate.py`. Le
certificat retourne `False complete=True` seulement après avoir trouvé une
sous-matrice induite sans ordre cR exact ; sinon il ne conclut rien. Le témoin
paired-farthest est aussi revérifié directement par
`is_precircular_order_cR` avant acceptation positive.

Tests ajoutés : random `n=10` seed `0` rejeté par obstruction 4-points,
obstruction explicite
`[[0,2,1,2],[2,0,3,3],[1,3,0,3],[2,3,3,0]]` étendue à `n=9`, et garde positif
`cycle_metric(10)` toujours accepté par le témoin minimum-cycle.

Validation : `tests/test_candidate.py` `27 passed`, `make unit` `122 passed`,
`make quick` `122 passed` puis `JUSTE`, `make hunt-counterexamples` `JUSTE`,
`make check` `JUSTE`, `make bench-quick` `0` timeout et `0` incomplet,
`make bench` `0` timeout et `0` incomplet jusqu'à `n=100`,
`make bench-piste-f` `0` timeout.

Résultat benchmark fort T031 : les `42` anciens placeholders `random` sont tous
classés par `candidate_small_forbidden_submatrix_obstruction`; le rapport
`reports/complexity_report.json` garde `0` incomplet et un fit polynomial
empirique `p ~= 3.22`.

Décision : intégrer comme certificat négatif héréditaire. Ce n'est pas une
preuve générale : la recherche est bornée et l'absence d'obstruction trouvée ne
prouve rien. Le prochain effort peut soit chercher des familles sans petites
obstructions où l'existence reste ouverte, soit reprendre `paired_farthest/mixed`
pour réduire les incomplets ciblés `n=16,20`.

## ExecPlan 2026-05-23 - five-point hereditary obstruction stress

But : attaquer le certificat 4-points T031 en cherchant une famille où toutes
les sous-matrices 4-points sont cR mais où la matrice complète ne l'est pas,
puis intégrer seulement un progrès sound si cette famille donne un certificat
héréditaire plus fort.

Hypothèse : la non-existence cR n'est pas caractérisée par les seules
obstructions induites de taille 4. Si un contre-exemple 5-points existe, la
même preuve d'hérédité permet d'ajouter un certificat négatif induit de taille 5
sans prétendre à une caractérisation globale.

Fichiers à modifier : `src/pc_circular/solvers/candidate.py`,
`src/pc_circular/generators.py`, `tests/test_candidate.py`,
`tests/test_regression_counterexamples.py`, `docs/proof_obligations.md`,
`docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : remplacer le scan 4-points unique par un scan borné de
tailles `(4, 5)`. Pour chaque taille, tester les sous-matrices induites par la
baseline exacte de petite taille. Retourner `False complete=True` uniquement si
une sous-matrice inspectée est prouvée sans ordre cR. Si la limite est atteinte
sans obstruction, continuer vers les branches incomplètes.

Plan de contre-exemples : exhaustif `n=5`, valeurs `{1,2}`, pour trouver une
matrice globalement non-cR dont toutes les restrictions 4-points sont cR ;
étendre cette matrice à `n=9` par des points à distance constante et vérifier
que le scan 4-points ne voit rien ; verrouiller que le scan 5-points rejette la
famille par certificat héréditaire ; vérifier que les positifs cycle restent
acceptés et que les gates oracle ne régressent pas.

Plan subagents : trois explorateurs lecture seule : recherche indépendante de
contre-exemples 4-local/global, analyse des incomplets `paired_farthest/mixed`,
et statut théorique/artefact recommandé pour les obstructions héréditaires.

Tests à exécuter : tests candidats/régressions ciblés, `make unit`,
`make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
et un benchmark ciblé sur la nouvelle famille si elle est ajoutée aux
générateurs.

Risques : croire que le scan `(4,5)` est une caractérisation ; ralentir les cas
où aucune obstruction petite n'existe ; masquer une incomplétude candidate par
un benchmark qui ne contient que des obstructions induites ; ajouter une famille
de générateur qui échoue pour `n < 5` sans le documenter.

Résultats observés : probe exhaustive `n=5`, valeurs `{1,2}`, a trouvé après
236 matrices un noyau binaire globalement non-cR dont toutes les restrictions
4-points sont cR :
`[[0,1,1,2,2],[1,0,2,1,2],[1,2,0,1,2],[2,1,1,0,2],[2,2,2,2,0]]`.
Le même noyau apparaît dans l'exhaustif `{1,2,3}`. Le padding avec distance `2`
du noyau vers les nouveaux points et distance `1` entre nouveaux points préserve
les restrictions 4-points positives dans les tests `n=6,7,8,9,10,12,20`.

Changements intégrés : ajout de `four_local_non_cr_core` et
`padded_four_local_non_cr` dans `generators.py`; ajout de régressions montrant
que le noyau est globalement négatif mais 4-local positif ; extension de
`candidate_small_forbidden_submatrix_obstruction` aux tailles configurées
`(4,5)`. Les scans d'obstructions sont placés après l'échantillonnage, car un
témoin positif directement vérifié suffit déjà à prouver l'existence.

Validation : tests candidats/générateurs/régressions ciblés `39 passed`,
`make unit` `127 passed`, `make quick` `127 passed` puis `JUSTE`,
`make hunt-counterexamples` `JUSTE`, `make check` `JUSTE`, `make bench-quick`
`0` timeout et `0` incomplet, `make bench` `0` timeout et `0` incomplet,
benchmark ciblé `four_local_non_cr/star` `0` timeout et `0` incomplet.

Résultat benchmark ciblé : pour tailles `5,6,8,9,10,12,20,40`, répétitions `3`,
les cas `n <= 8` sont exacts par brute force et les cas `n > 8` sont rejetés par
`candidate_small_forbidden_submatrix_obstruction` avec obstruction d'ordre 5.

Décision : conserver comme progrès sound et comme contre-exemple durable à la
caractérisation 4-locale. Ne pas conclure à une base finie d'obstructions :
les tailles `(4,5)` sont seulement deux certificats héréditaires bornés.

## ExecPlan 2026-05-23 - six-point k-local obstruction probe

But : tester si la hiérarchie des obstructions induites continue : chercher une
matrice à 6 points globalement non-cR dont toutes les sous-matrices induites de
taille 5 sont cR.

Hypothèse : les certificats de tailles `(4,5)` ne caractérisent pas non plus la
non-existence globale. Si un noyau 6-points existe, il doit devenir un
contre-exemple durable et éventuellement un certificat héréditaire taille 6,
mais seulement si le coût reste compatible avec les gates.

Fichiers à modifier : d'abord `PLANS.md` seulement. Si une obstruction utile est
trouvée : `src/pc_circular/generators.py`, `tests/test_regression_counterexamples.py`,
`tests/test_candidate.py`, `docs/proof_obligations.md`,
`docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, et possiblement
`src/pc_circular/solvers/candidate.py` si l'intégration taille 6 est sound et
raisonnablement rapide.

Algorithme pressenti : probe exhaustive `n=6`, valeurs `{1,2}`, en filtrant les
matrices dont toutes les 5-sous-matrices sont positives puis en testant l'oracle
global. Si l'exhaustif est trop lent ou négatif, utiliser recherche random et
local search sur valeurs `{1,2,3}` avec score `nombre de 5-sous-matrices cR`
moins pénalité si la matrice globale devient positive.

Plan de contre-exemples : si un noyau est trouvé, vérifier toutes les
restrictions 5-points par oracle exact, vérifier que le noyau complet est
négatif, puis chercher un padding à grandes tailles qui ne crée pas
d'obstruction 4/5 plus petite. Si aucun noyau n'est trouvé, documenter la borne
exhaustive et ne pas modifier la candidate.

Plan subagents : trois explorateurs lecture seule : recherche indépendante de
noyau 6-local ; coût/placement d'un éventuel scan 6-points dans `candidate.py` ;
stratégie de génération/shrink pour les obstructions k-locales.

Tests à exécuter : probes bornées, puis si modification code : tests ciblés,
`make unit`, `make quick`, `make hunt-counterexamples`, `make check`,
`make bench-quick`, et benchmark ciblé de la nouvelle famille.

Risques : intégrer taille 6 sans nécessité ; ralentir fortement les cas
incomplets ; confondre absence de noyau `{1,2}` avec théorème ; ajouter une
famille artificielle qui ne teste pas le PC-tree compact ; oublier que les
obstructions induites sont négatives seulement.

Résultats observés : l'exhaustif `n=6`, valeurs `{1,2}`, a trouvé après `237`
matrices un noyau globalement non-cR dont toutes les restrictions 5-points sont
cR :
`[[0,1,1,1,1,1],[1,0,1,1,2,2],[1,1,0,2,1,2],[1,1,2,0,2,1],[1,2,1,2,0,1],[1,2,2,1,1,0]]`.
Le padding par sommets bas universels préserve les restrictions 5-points
positives sur les tailles testées et donne une obstruction induite de taille 6.

Résultat structurel : les subagents ont identifié ce noyau comme un cycle haut
impair plus un hub bas universel. Pour chaque sommet du cycle, le hub impose que
ses deux voisins hauts soient du même côté dans tout ordre cR ; en orientant les
arêtes du cycle selon l'ordre linéaire autour du hub, chaque sommet devrait être
source ou puits. Une alternance source/puits est impossible sur un cycle impair.

Changements intégrés : ajout de `five_local_non_cr_core`,
`padded_five_local_non_cr` et `odd_high_cycle_plus_low_hub` dans
`generators.py`; extension du certificat induit borné aux tailles `(4,5,6)` ;
ajout du certificat structurel
`candidate_odd_high_cycle_low_hub_obstruction` dans `candidate.py`, qui rejette
les graphes hauts formés d'un cycle impair connecté et d'au moins un hub bas
universel.

Validation : tests candidats/générateurs/régressions ciblés `46 passed`,
`make unit` `134 passed`, `make quick` `134 passed` puis `JUSTE`,
`make hunt-counterexamples` `JUSTE`, `make check` `JUSTE`, `make bench-quick`
`0` timeout et `0` incomplet, `make bench` `0` timeout et `0` incomplet,
`make bench-piste-f` `0` timeout. Benchmarks ciblés : `five_local_non_cr/star`
`0` timeout et `0` incomplet ; `odd_high_cycle_plus_low_hub/star` passe de
placeholders `n>=10` à `candidate_odd_high_cycle_low_hub_obstruction` avec `0`
timeout et `0` incomplet sur tailles `6,8,10,12,20,40`.

Décision : intégrer. Contrairement au scan 6-points seul, le certificat
odd-cycle donne une famille paramétrique négative avec preuve simple et coût
faible. Garder le scan 6-points comme certificat héréditaire borné, mais ne pas
présenter `(4,5,6)` comme caractérisation.

## ExecPlan 2026-05-23 - non-bipartite high graph with low hub

But : généraliser le certificat T033 du cycle haut impair vers tout graphe haut
non biparti avec hub bas universel, sans affaiblir les oracles ni masquer les
cas incomplets restants.

Hypothèse : dans une matrice binaire `low/high`, un hub bas universel et un
graphe des arêtes hautes non biparti suffisent à interdire tout ordre cR. Le
cycle impair n'était que le premier cas non biparti trouvé par la recherche
d'obstructions 5-locales.

Fichiers à modifier : `src/pc_circular/solvers/candidate.py`,
`src/pc_circular/generators.py`, `tests/test_candidate.py`,
`tests/test_generators.py`, `tests/test_regression_counterexamples.py`,
`docs/proof_obligations.md`, `docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `README.md`, `PLANS.md`.

Algorithme pressenti : scanner les deux valeurs positives `low < high`,
construire le graphe haut, vérifier qu'il existe au moins un sommet isolé
servant de hub bas, puis tester la bipartition du sous-graphe haut non isolé.
Si ce graphe n'est pas biparti, retourner `False complete=True` par certificat
négatif. Ne pas énumérer les cycles impairs.

Plan de contre-exemples : tester exhaustivement tous les graphes hauts binaires
avec un hub bas et jusqu'à 5 sommets non-hub ; verrouiller des contrôles
bipartis qui ne doivent pas déclencher ; ajouter une famille non-cycle
`non_bipartite_high_graph_plus_low_hub` avec triangle haut et branches.

Plan subagents : deux sidecars lecture seule. Le premier vérifie la preuve et
les préconditions exactes ; le second propose les familles de stress et
interprète l'impact benchmark attendu.

Tests à exécuter : tests candidats/générateurs/régressions ciblés, `make unit`,
`make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
`make bench-piste-f`, `make bench`, benchmarks ciblés sur
`odd_high_cycle_plus_low_hub/star` et
`non_bipartite_high_graph_plus_low_hub/star`.

Risques : appliquer le certificat à plus de deux niveaux de distance sans
preuve ; rejeter des graphes hauts bipartis ; croire que ce sous-cas négatif
résout les cas `paired_farthest/mixed` ou le problème PC-tree général.

Résultats observés : les subagents valident la preuve source/puits. En coupant
au hub `h`, chaque arête haute `{v,u}` fait de `u` un mauvais témoin pour la
paire basse `{h,v}` ; tous les voisins hauts de `v` doivent donc être du même
côté de `v`. Orienter les arêtes hautes selon l'ordre linéaire force chaque
sommet à être source ou puits, donc force une bipartition. Un graphe haut non
biparti contredit cette condition.

Validation observée : exhaustif local des graphes hauts avec un hub bas jusqu'à
5 sommets non-hub, aucun désaccord oracle ; `pytest -q
tests/test_candidate.py tests/test_generators.py
tests/test_regression_counterexamples.py` `49 passed`; `make unit`
`137 passed`; `make quick` `137 passed` puis `JUSTE`;
`make hunt-counterexamples` `JUSTE`; `make check` `JUSTE`;
`make bench-quick` `0` timeout et `0` incomplet ; `make bench-piste-f` `0`
timeout ; `make bench` `0` timeout et `0` incomplet jusqu'à `n=100`.

Résultats benchmark ciblés : `odd_high_cycle_plus_low_hub/star` et
`non_bipartite_high_graph_plus_low_hub/star`, tailles `6,8,10,12,20,40`,
répétitions `3`, tous `0` timeout et `0` incomplet ; à `n=40`, médianes
respectives environ `0.00053s` et `0.00052s` via
`candidate_non_bipartite_high_graph_low_hub_obstruction`.

Décision : intégrer comme sous-cas négatif polynomial prouvé. Continuer ensuite
vers les limites du binaire hub : graphes hauts bipartis, plus de deux niveaux
de distance, ou liens avec les choix locaux d'un gros nœud `P`.

## ExecPlan 2026-05-23 - even high cycle with low hub

But : attaquer le cas laissé ouvert par T034 : matrices binaires `low/high`
avec hub bas universel et graphe haut biparti. Chercher d'abord un
contre-exemple ou un sous-cas négatif prouvé, sans prétendre caractériser tous
les graphes bipartis.

Hypothèse : la bipartition du graphe haut n'est pas suffisante. Un cycle haut
induit pair de longueur au moins `6` avec hub bas devrait être impossible,
alors que `C4` reste positif. Ce serait une famille bipartie négative qui
échappe aux scans d'obstructions induites de tailles `(4,5,6)` dès `C8`.

Fichiers à modifier : si l'hypothèse survit aux probes,
`src/pc_circular/generators.py`, `src/pc_circular/solvers/candidate.py`,
`tests/test_candidate.py`, `tests/test_generators.py`,
`tests/test_regression_counterexamples.py`, puis
`docs/proof_obligations.md`, `docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md` et `PLANS.md`.

Algorithme pressenti : détecter les matrices à exactement deux distances
positives où le graphe haut est formé d'un unique cycle pair de taille au moins
`6` plus au moins un hub isolé. Retourner `False complete=True` seulement dans
ce sous-cas structurel. Garder T034 pour tous les graphes hauts non bipartis.

Plan de contre-exemples : énumérer tous les graphes hauts avec un hub bas
jusqu'à `6` sommets non-hub ; vérifier que les négatifs bipartis de taille `6`
coïncident avec les `C6` induits ; vérifier que `C8` plus hub est négatif mais
non détecté par les scans `(4,5,6)` ; ajouter des régressions durables.

Plan subagents : trois sidecars lecture seule. Un vérifie la preuve/structure
du cas biparti, un cherche des contre-exemples exhaustifs ou random, et un
prépare l'intégration minimale candidate/générateurs/benchmarks.

Tests à exécuter : tests ciblés candidats/générateurs/régressions, `make unit`,
`make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
benchmark ciblé `even_high_cycle_plus_low_hub/star`, et `make bench` si la
candidate change.

Risques : généraliser à des graphes bipartis arbitraires sans preuve ; confondre
cycle induit et cycle avec cordes ; intégrer un rejet négatif alors que seul le
cas exact cycle-plus-hubs est prouvé ; oublier que les petits `C6` sont déjà
capturés par brute force ou scan 6-points.

Résultats observés : probes locales et subagents confirment que les graphes
hauts bipartis avec hub bas ne sont pas tous positifs. Exhaustif avec `m`
sommets non-hub : pour `m <= 5`, tous les graphes hauts bipartis sont positifs
à l'oracle exact ; pour `m = 6`, il y a `5117` positifs et `60` négatifs, et
les `60` négatifs sont exactement les labellisations de `C6`. Probes ciblées :
`C4 + hub` positif, `C6 + hub` négatif, `C8 + hub` négatif, `K3,3 + hub`
positif. Le sous-cas général plausible devient "graphe haut avec strong
ordering", mais il n'est pas intégré.

Changements intégrés : ajout de `even_high_cycle_plus_low_hub` dans
`generators.py`; ajout de
`candidate_even_high_cycle_low_hub_obstruction` dans `candidate.py`, limité aux
graphes hauts exactement cycle pair induit de longueur au moins `6` plus hubs
isolés ; tests ciblés et régressions. La preuve documentée utilise le lemme
nécessaire de strong ordering pour le cas binaire hub bas, puis le fait qu'un
cycle induit `C_{2r}`, `r >= 3`, ne peut pas satisfaire ce strong ordering.

Validation observée : `pytest -q tests/test_candidate.py tests/test_generators.py
tests/test_regression_counterexamples.py` `54 passed`; `make unit`
`142 passed`; `make quick` `142 passed` puis `JUSTE`;
`make hunt-counterexamples` `JUSTE`; `make check` `JUSTE`;
`make bench-quick` `0` timeout et `0` incomplet ; `make bench` `0` timeout et
`0` incomplet jusqu'à `n=100`, fit polynomial empirique `p ~= 3.24`.
Benchmark ciblé `even_high_cycle_plus_low_hub/star`, tailles
`7,9,11,13,21,41,61,81`, répétitions `10` : `0` timeout, `0` incomplet ; à
`n=81`, médiane `0.00248s`.

Décision : intégrer comme sous-cas négatif polynomial étroit. Ne pas intégrer la
caractérisation strong-ordering complète avant d'avoir un détecteur/witness
robuste, des contrôles positifs `K_{p,q}`/chain/matching, et une preuve de
représentation PC-tree pour les témoins positifs.

## ExecPlan 2026-05-23 - strong ordering low-hub diagnostic

But : tester la conjecture issue de T035 sans l'intégrer à la candidate :
dans une matrice binaire `low/high` avec hub bas universel, l'existence d'un
ordre cR sous star pourrait coïncider avec l'existence d'un strong ordering du
graphe haut privé des hubs.

Hypothèse : après retrait des hubs bas, le graphe haut doit être un bipartite
permutation graph. Un strong ordering fournit le témoin naturel
`hub, A-order, B-order`; une absence de strong ordering expliquerait les
obstructions `C6`, `C8` et le tree négatif trouvé par subagent.

Fichiers à modifier : `src/pc_circular/solvers/local_constraints.py` ou un
module expérimental proche, `tests/test_local_constraints.py` ou un test dédié,
`docs/proof_obligations.md`, `docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : pour les petites tailles seulement, détecter les deux
niveaux `low/high` et les hubs isolés du graphe haut, énumérer les bipartitions
et les permutations des deux parts sous une limite explicite, puis tester la
condition strong ordering. Vérifier le témoin construit par
`is_precircular_order_cR`. Le rapport doit marquer `complete=False` si les
permutations dépassent la limite.

Plan de contre-exemples : comparer strong-ordering vs oracle exact pour tous
les graphes hauts avec hub bas jusqu'à `m=6` sommets non-hub, puis sur random
`m=7,8` avec budgets bornés. Contrôles : `C4` positif, `C6`/`C8` négatifs,
`K3,3` positif, matching positif, chain/Ferrers positif, tree négatif.

Plan subagents : deux sidecars lecture seule. Un cherche des mismatches
strong-ordering/oracle ; l'autre audite l'intégration minimale hors candidate.

Tests à exécuter : tests ciblés du module expérimental, `make unit`,
`make quick`. Pas de `make hunt-counterexamples` obligatoire si `candidate.py`
n'est pas modifié, mais lancer un probe exhaustif dédié et documenté.

Risques : coût factoriel ; mauvais traitement des composantes isolées ;
confondre un diagnostic complet borné avec un algorithme polynomial ; oublier
que les témoins positifs doivent encore être représentés par le PC-tree avant
toute intégration future dans `candidate.py`.

Résultats observés : `low_hub_strong_ordering_report` ajouté dans
`local_constraints.py` comme diagnostic borné hors `candidate.py`. Il détecte
les cas non applicables, les graphes hauts non bipartis, les limites
factorielles, et vérifie directement le témoin `hubs + A + B` lorsqu'un strong
ordering est trouvé. Les contrôles unitaires couvrent `C4`, `C6`, `C8`,
`K3,3`, matching, chain/Ferrers, un tree négatif, les cas non binaires, sans
hub, et limite atteinte.

Probe exhaustive : pour tous les graphes hauts avec hub bas et `m=6` sommets
non-hub, le diagnostic donne `5117` strong-ordering positifs, `60` graphes
bipartis sans strong ordering, et `27591` graphes non bipartis. Cela recoupe la
frontière T035. Le test unitaire compare aussi strong-ordering à l'oracle exact
pour tous les graphes hauts jusqu'à `m=5`.

Validation observée : `pytest -q tests/test_local_constraints.py` `12 passed`;
`make unit` `149 passed`; `make quick` `149 passed` puis `JUSTE`.

Décision : conserver comme diagnostic expérimental et comme candidat de
caractérisation du cas star/all-orders binaire hub bas. Ne pas intégrer dans
`candidate.py` avant une preuve écrite, un détecteur polynomial plutôt que
factoriel, et un garde de représentation PC-tree pour les témoins positifs.

## ExecPlan 2026-05-23 - bounded low-hub strong-ordering witness

But : transformer T036 en progrès de candidate sans prétendre décider les
négatifs : utiliser le diagnostic strong-ordering uniquement comme générateur
de témoin positif vérifié.

Hypothèse : si `low_hub_strong_ordering_report` trouve un ordre
`hubs + A + B`, et si cet ordre est vérifié cR puis représenté par le PC-tree
fourni, alors `exists=True complete=True` est sound. Si le diagnostic ne trouve
rien, atteint sa limite, ou si le témoin n'est pas représenté, la candidate ne
doit pas conclure négativement.

Fichiers à modifier : `src/pc_circular/solvers/candidate.py`,
`src/pc_circular/generators.py`, `tests/test_candidate.py`,
`tests/test_generators.py`, `tests/test_regression_counterexamples.py`,
`docs/proof_obligations.md`, `docs/tracks/piste_f_complexity_subcases.md`,
`docs/tracks/piste_e_farthest_quartets.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : appeler `low_hub_strong_ordering_report` avec une limite
bornée après les certificats négatifs hub bas et avant les scans exacts
quasi/PC-tree. Si `strong_ordering_exists=True` et `witness_order_is_cr=True`,
vérifier la représentation par `represents_order` quand `pc_tree` est fourni,
puis retourner un certificat positif. Tous les autres statuts retournent `None`.

Plan de contre-exemples : contrôles positifs star/all-orders `K_{p,q}`,
chain/Ferrers et matching ; contrôles négatifs `C6`, `C8`, tree négatif qui ne
doivent pas devenir des faux positifs ; contrôle PC-tree non-star où le témoin
strong-ordering existe mais n'est pas représenté.

Plan subagents : deux sidecars lecture seule. Un audite les risques de faux
positif et le placement dans `solve`; l'autre propose les familles et
benchmarks ciblés.

Tests à exécuter : tests candidats/générateurs/régressions ciblés, `make unit`,
`make quick`, `make hunt-counterexamples`, `make check`, benchmark ciblé sur
`chain_high_graph_plus_low_hub/star`, `make bench-quick`, et `make bench` si la
branche change des runs grande taille.

Risques : coût factoriel caché ; accepter un ordre non représenté ; confondre
échec du diagnostic avec non-existence ; faire dépendre la candidate d'une
conjecture non prouvée autrement que par la vérification directe du témoin.

Résultats observés : intégration de
`candidate_low_hub_strong_ordering_witness` comme certificat strictement
positif. La candidate appelle le diagnostic borné seulement quand
`quasi_orders is None`, accepte uniquement un `witness_order` de forme valide,
vérifié par `is_precircular_order_cR`, puis représenté par `represents_order`
si un PC-tree est fourni. Les familles
`chain_high_graph_plus_low_hub` et
`complete_bipartite_high_graph_plus_low_hub` ont été ajoutées pour tester des
positifs low-hub de grande taille.

Validation ciblée : `pytest -q tests/test_candidate.py tests/test_generators.py
tests/test_local_constraints.py tests/test_regression_counterexamples.py`
donne `72 passed`. Benchmarks ciblés `chain_high_graph_plus_low_hub/star` et
`complete_bipartite_high_graph_plus_low_hub/star`, tailles
`5,6,8,10,12,16,20,40,80`, répétitions `10` : `0` timeout, `0` incomplet ;
à `n=80`, médianes respectives `1.7726s` et `1.8263s`, toutes via
`candidate_low_hub_strong_ordering_witness`.

Validation gates : `make unit` `155 passed`; `make quick` `155 passed` puis
`JUSTE`; `make hunt-counterexamples` `JUSTE`; `make check` `JUSTE`;
`make bench-quick` `0` timeout, `0` incomplet ; `make bench` `0` timeout,
`0` incomplet jusqu'à `n=100`, médiane `2.0845s`, p95 `2.1490s`,
fit polynomial empirique `p ~= 3.25`.

Décision : conserver dans `candidate.py` comme témoin positif vérifié, pas
comme caractérisation du cas low-hub. L'échec du diagnostic, l'atteinte de la
limite factorielle ou l'absence de représentation PC-tree restent incomplets.
Prochaine étape : prouver ou réfuter la suffisance du strong ordering, puis
remplacer l'énumération factorielle par une reconnaissance polynomial-time ou
isoler des sous-cas positifs plus étroits comme matching/chain avec preuve.

## ExecPlan 2026-05-23 - fast bad-side fixed-order predicate

But : accélérer les validations de témoins dans `candidate.py` sans changer le
problème décidé : promouvoir la reformulation bad-side exacte d'un ordre fixé
comme prédicat central `O(n^3)`, en gardant l'oracle fort comme comparaison
indépendante via le prédicat de quadruplets existant.

Hypothèse : pour un ordre circulaire fixé, la condition pre-circular/cR est
équivalente au fait qu'aucune paire `{a,b}` n'a de mauvais témoins sur les deux
arcs ouverts entre `a` et `b`. Un mauvais témoin `w` vérifie
`max(d(a,w), d(w,b)) > d(a,b)`. Cette reformulation est déjà expérimentée en
Piste B ; l'intégrer dans `predicates.py` permet de valider les témoins
large-n plus vite.

Fichiers à modifier : `src/pc_circular/predicates.py`,
`src/pc_circular/solvers/candidate.py`,
`src/pc_circular/solvers/local_constraints.py`, `tests/test_predicates.py`,
`tests/test_candidate.py` si nécessaire, `docs/proof_obligations.md`,
`docs/tracks/piste_b_dp_pc_tree.md`, `docs/tracks/piste_f_complexity_subcases.md`,
`docs/tracks/README.md`, `docs/experiment_log.md`, `docs/checkpoints.md`,
`PLANS.md`.

Algorithme pressenti : ajouter `find_bad_side_precircular_cR_violation` et
`passes_bad_side_precircular_cR` dans `predicates.py`. Le prédicat parcourt les
paires de positions d'un ordre, cherche un mauvais témoin sur chaque arc ouvert
et retourne une violation `(a,y,b,t)` si les deux côtés sont non vides. Utiliser
ce prédicat dans la candidate pour valider les témoins et les ordres
échantillonnés ; ne pas modifier l'oracle exact des outils tant que les tests
d'équivalence sont la garde.

Plan de contre-exemples : comparer au test de quadruplets sur exhaustif `n=4`
valeurs `{1,2,3}`, random `n=5..7`, familles equal-distance, cycle,
quasi-non-cR, low-hub chain/complete/matching, et ordres PC-tree non
représentés. Si un désaccord apparaît, l'ajouter en régression et ne pas
intégrer à la candidate.

Plan subagents : trois sidecars lecture seule. Un audite la preuve et les cas
non stricts ; un cherche des contre-exemples par scripts temporaires ; un
audite les lignes candidate/local_constraints et les benchmarks de performance.

Tests à exécuter : `pytest -q tests/test_predicates.py tests/test_dp_experiments.py
tests/test_candidate.py tests/test_local_constraints.py`, probe d'équivalence
random bornée, benchmarks ciblés low-hub chain/complete avant/après,
`make unit`, `make quick`, `make hunt-counterexamples`, `make check`,
`make bench-quick`; `make bench` si la candidate change ses validations
large-n.

Risques : déplacer trop tôt un prédicat expérimental dans le cœur ; modifier
l'oracle au lieu de garder une comparaison indépendante ; perdre les détails de
diagnostic de `find_precircular_cR_violation`; oublier que la stricte
inégalité `>` dans mauvais témoin est nécessaire pour les égalités.

Résultats observés : `find_bad_side_precircular_cR_violation` et
`passes_bad_side_precircular_cR` ont été ajoutés dans `predicates.py`.
`candidate.py` et `low_hub_strong_ordering_report` utilisent ce prédicat pour
valider les témoins, tandis que `is_precircular_order_cR` et les tools
d'oracle restent sur la définition par quadruplets. Les tests ajoutés couvrent
exhaustif `n=4`, égal-distance, rotations/renversements avec wrapping, et un
cas où deux mauvais témoins sont du même côté et ne doivent pas être rejetés.

Preuve/contre-exemples : les subagents ont confirmé la preuve directe et n'ont
trouvé aucun désaccord. Probe local : `6058` comparaisons ordre fixé sans
mismatch. Probe subagent indépendant : `153291` comparaisons, incluant
exhaustif `n=4`, random `n=5..7`, familles exactes `n=4..8`, et échantillons
`n=9,10,12`, sans mismatch. La variante `>=` a été réfutée immédiatement sur
égal-distance, confirmant le besoin du `>` strict.

Validation ciblée : `pytest -q tests/test_predicates.py
tests/test_dp_experiments.py tests/test_candidate.py tests/test_local_constraints.py`
donne `83 passed`. Benchmarks ciblés, tailles `20,40,80,100`, répétitions `5` :
`chain_high_graph_plus_low_hub/star` passe à médiane `0.2485s` à `n=100`,
`complete_bipartite_high_graph_plus_low_hub/star` à `0.3284s`, `0` timeout et
`0` incomplet. Le micro-benchmark subagent estime l'ancien chemin quadruplets à
`4.306s` et `4.456s` à `n=100` sur ces deux familles.

Validation gates : `make unit` `159 passed`; `make quick` `159 passed` puis
`JUSTE`; `make hunt-counterexamples` `JUSTE`; `make check` `JUSTE`;
`make bench-quick` `0` timeout, `0` incomplet ; `make bench` `0` timeout,
`0` incomplet jusqu'à `n=100`, médiane `0.0275s`, p95 `0.0362s`, fit
polynomial empirique `p ~= 1.73`.

Décision : intégrer comme accélérateur exact d'ordre fixé et comme validation
candidate. Ce n'est pas un solveur d'existence PC-tree : il accélère seulement
les ordres déjà produits ou énumérés. Garder l'oracle par quadruplets comme
comparaison indépendante dans les tools. Prochaine étape : utiliser ce gain
pour tester plus agressivement la reconnaissance strong-ordering low-hub ou les
familles matching/PC-tree non-star.

## ExecPlan 2026-05-23 - permuted low-hub matching witness

But : ajouter un stress positif low-hub indépendant de chain/complete et rendre
le diagnostic strong-ordering capable de trouver immédiatement le témoin d'un
graphe haut matching même lorsque les labels sont permutés.

Hypothèse : dans une matrice binaire `low/high` avec hubs bas et graphe haut
formé d'un matching, l'ordre `hubs, A_1..A_m, B_1..B_m`, où les paires
`A_i B_i` sont les arêtes du matching dans le même ordre de composantes, est cR.
Plus généralement, pour des composantes biparties disjointes, essayer les deux
parts concaténées composante par composante est une priorité sûre car tout
témoin reste vérifié par le prédicat fixed-order exact.

Fichiers à modifier : `src/pc_circular/solvers/local_constraints.py`,
`src/pc_circular/generators.py`, `tests/test_local_constraints.py`,
`tests/test_generators.py`, `tests/test_candidate.py` si nécessaire,
`docs/proof_obligations.md`, `docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : conserver l'énumération bornée comme fallback, mais
ajouter aux priorités de `low_hub_strong_ordering_report` un couple
`(A_order, B_order)` construit en concaténant les parts de chaque composante
bipartie dans le même ordre après application des flips. Pour un matching,
cela aligne automatiquement les mates, donc le premier ordre testé suffit même
si les labels sont mélangés.

Plan de contre-exemples : tester un matching low-hub volontairement désaligné
par labels où l'ordre trié échoue ; vérifier que `max_permutation_pairs=1`
trouve tout de même le témoin ; tester `max_permutation_pairs=0` comme limite ;
contrôler que `C6/C8` et le tree négatif restent rejetés ; comparer à l'oracle
exact sur petits matchings et à `make hunt-counterexamples`.

Plan subagents : deux sidecars lecture seule. Un audite la preuve du matching
et les risques de priorité composante ; un cherche des contre-exemples rapides
sur graphes bipartis low-hub multi-composantes où la nouvelle priorité pourrait
masquer une limite ou changer un statut.

Tests à exécuter : tests ciblés générateurs/local-constraints/candidate,
benchmark ciblé `matching_high_graph_plus_low_hub/star` jusqu'à `n=101`,
`make unit`, `make quick`, `make hunt-counterexamples`, `make check`,
`make bench-quick`; `make bench` si `candidate.py` change ou si les rapports
forts doivent être rafraîchis.

Risques : confondre priorité de recherche et preuve de complétude ; exploser en
`2^components` avant d'atteindre un témoin ; accepter un témoin non représenté
par un PC-tree ; suradapter aux labels naturels au lieu de tester une version
permutée.

Résultats observés : `matching_high_graph_plus_low_hub` ajouté comme famille
positive indépendante. `low_hub_strong_ordering_report` essaie maintenant en
priorité l'ordre composante-aligné puis son renversement, avant les priorités
triées et l'énumération factorielle. Les tests ciblés
`tests/test_local_constraints.py tests/test_generators.py tests/test_candidate.py`
donnent `68 passed`. Le benchmark ciblé
`matching_high_graph_plus_low_hub/star`, tailles `5,7,9,11,21,41,81,101`,
répétitions `10`, timeout `2s`, donne `0` timeout et `0` incomplet ; à
`n=101`, médiane `0.1810s`, p95 `0.1852s`. Les gates fortes restent vertes :
`make unit` donne `163 passed`, `make quick` donne `163 passed` puis `JUSTE`,
`make hunt-counterexamples` et `make check` donnent `JUSTE`, `make bench-quick`
donne `0` timeout et `0` incomplet, et `make bench` donne `0` timeout et `0`
incomplet jusqu'à `n=100`, médiane `0.0267s`, p95 `0.0366s`, fit polynomial
empirique `p ~= 1.72`.

Résultats subagents : l'audit preuve confirme que, pour un matching haut avec
hubs bas, l'ordre `hubs, A_1..A_m, B_1..B_m` aligne les mates et satisfait la
condition bad-side. La recherche de contre-exemples confirme l'absence de faux
positif observé et mesure `2400/2400` matchings permutés trouvés au premier
essai, mais rappelle l'incomplétude générale : avec `max_permutation_pairs=1`,
seuls `1542/5117` graphes positifs strong-ordering à `m=6` sont trouvés.

Corrections associées : le diagnostic prend maintenant en compte les distances
basses `0` hors diagonale au lieu de les ignorer, avec une régression triangle
haut non biparti `low=0`. Les tests rappellent aussi qu'une petite limite de
permutations doit rester `unsupported_permutation_limit`, pas `False`, même
quand un témoin existe plus loin.

Décision : conserver T039 comme amélioration de priorité et stress positif
matching, pas comme preuve générale du cas strong-ordering. Prochaine étape :
soit prouver la suffisance strong-ordering pour le cas binaire hub bas complet,
soit remplacer l'énumération factorielle par une reconnaissance polynomiale de
graphe biparti à strong ordering, en gardant les tests `C6/C8`, tree négatif,
low-zero et positifs retardés comme garde-fous.

## ExecPlan 2026-05-23 - represented low-hub strong-ordering witness search

But : corriger un trou positif non-star du diagnostic low-hub : le premier
témoin strong-ordering peut ne pas être représenté par le PC-tree, alors qu'un
autre témoin strong-ordering représenté existe.

Hypothèse : dans le cas binaire low-hub, une recherche bornée de témoins
strong-ordering filtrés par `represents_order(T, order)` peut certifier des
positifs PC-tree non-star sans affaiblir les rejets ni prétendre à la
complétude. Un témoin accepté reste sound parce qu'il est vérifié par
`passes_bad_side_precircular_cR` puis par `represents_order`.

Fichiers à modifier : `src/pc_circular/solvers/local_constraints.py`,
`src/pc_circular/solvers/candidate.py`, `tests/test_candidate.py`,
`tests/test_local_constraints.py` si un helper public est ajouté,
`tests/test_regression_counterexamples.py` si le cas devient une régression
durable, `docs/proof_obligations.md`, `docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : extraire de `low_hub_strong_ordering_report` un itérateur
borné qui parcourt les témoins strong-ordering prioritaires puis factoriels,
sans s'arrêter au premier témoin non représenté. La candidate l'utilise
seulement quand `pc_tree` est fourni : elle teste chaque témoin par le prédicat
fixed-order exact et par `represents_order`; si aucun témoin représenté n'est
trouvé avant la limite, le résultat reste incomplet.

Plan de contre-exemples : construire un matching low-hub `n=18` avec PC-tree
racine `C` contenant deux gros blocs `P` pour les deux parts. Le PC-tree
représente un ordre cR avec une composante flipped, mais pas le premier témoin
du diagnostic ; la candidate actuelle retourne placeholder après 64 samples.
Vérifier aussi que `C6/C8` et le tree négatif ne deviennent pas de faux
positifs, que les petites limites restent `unsupported`, et que les gates oracle
ne changent pas.

Plan subagents : cinq sidecars lecture seule. Un audite la preuve de suffisance
low-hub strong-ordering, un cherche des contre-exemples PC-tree non-star, un
évalue l'option CSP/nogoods, un analyse les projections locales A/D, un classe
les sous-cas F encore sûrs. L'intégration reste dans le rollout principal.

Tests à exécuter : tests ciblés candidate/local-constraints, `make unit`,
`make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`, et
benchmark ciblé sur le nouveau cas non-star si un générateur dédié est ajouté.
`make bench` si `candidate.py` change.

Risques : faire exploser la recherche factorielle ; accepter un témoin hors
PC-tree ; transformer une limite de recherche en faux négatif ; dupliquer trop
de logique entre rapport diagnostic et itérateur de témoins.

Résultats observés : un premier contre-exemple positif non-star a été construit
avec `matching_high_graph_plus_low_hub(18)` et un PC-tree racine `C` à deux
gros blocs `P`. Avant T040, la candidate retournait
`candidate_large_n_placeholder` après `64` samples ; après l'ajout de
`iter_low_hub_strong_ordering_witnesses`, elle trouve un témoin représenté
après `761` couples de permutations. Un second contre-exemple subagent à
`n=10` a montré que `_pc_tree_frontier_upper_bound` surestimait les frontiers
canoniques d'une racine circulaire (`4097` contre `720` réels) ; la borne est
maintenant root-aware et permet l'énumération exacte bornée de ce cas. Le
contre-exemple local `I_x(v)` silencieux sur `even_high_cycle_plus_low_hub(7)`
avec `balanced_pc_tree(7, kind="mixed")` est régressé.

Résultats subagents : l'audit proof-side fournit une preuve bad-side de la
suffisance de tout strong ordering donné pour le témoin `hubs,A,B`. Le sidecar
CSP recommande un rapport non-star hors candidate, car la compilation reste
énumérative. Le sidecar A/D fournit le faux silence local `I_x(v)`. Le sidecar
F recommande T041 sur le sous-cas chain/Ferrers permuté. Le sidecar
contre-exemples fournit le cas `n=10` ci-dessus.

Validation : tests ciblés `tests/test_candidate.py tests/test_local_constraints.py`
donnent `59 passed`. `make unit` donne `167 passed`. `make quick` donne
`167 passed` puis `JUSTE`. `make hunt-counterexamples` et `make check` donnent
`JUSTE`. `make bench-quick` donne `0` timeout et `0` incomplet ; à `n=20`,
médiane `0.000983s`, p95 `0.001069s`. `make bench` donne `0` timeout et `0`
incomplet jusqu'à `n=100`; à `n=100`, médiane `0.0265s`, p95 `0.0363s`, fit
polynomial empirique `p ~= 1.72`. Probe ciblée matching low-hub/star T040 :
`0` timeout et `0` incomplet jusqu'à `n=101`, médiane `0.1812s`.

Décision : intégrer T040 comme double progrès : (1) recherche positive
strong-ordering représentée dans les PC-trees non-star, toujours bornée et
validée ; (2) borne de frontiers canoniques root-aware pour ne pas rater des
petits PC-trees exacts. Ne pas transformer l'absence de témoin strong-ordering
représenté en rejet. Prochaine piste recommandée : T041
`permuted_chain_high_graph_plus_low_hub` ou rapport CSP non-star diagnostique.

## ExecPlan 2026-05-23 - permuted Ferrers low-hub witness

But : intégrer un certificat positif polynomial pour les matrices binaires
low-hub dont le graphe haut privé des hubs est un graphe biparti chain/Ferrers,
y compris après permutation des labels.

Hypothèse : si une bipartition du graphe haut a des voisinages emboîtés dans
une part, alors trier cette part par voisinages décroissants et l'autre part
dans l'ordre Ferrers opposé donne un strong ordering. Par le lemme bad-side
T040, `hubs, A_order, B_order` est cR. La candidate ne peut accepter ce témoin
que s'il est aussi représenté par le PC-tree.

Fichiers à modifier : `src/pc_circular/solvers/local_constraints.py`,
`src/pc_circular/solvers/candidate.py`, `src/pc_circular/generators.py`,
`tests/test_local_constraints.py`, `tests/test_candidate.py`,
`tests/test_generators.py`, `docs/proof_obligations.md`,
`docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : ajouter `low_hub_ferrers_strong_ordering_report`.
Détecter les matrices à deux niveaux hors diagonale avec hubs bas, bipartir le
graphe haut, exiger une seule composante non-hub, trier une part par inclusion
décroissante de voisinages, trier l'autre par inclusion/degré croissant, puis
vérifier `_has_strong_ordering` et `passes_bad_side_precircular_cR`. Intégrer
dans `candidate.py` seulement comme témoin positif vérifié.

Plan de contre-exemples : tester `permuted_chain_high_graph_plus_low_hub` aux
tailles `15,17,21,41,81,101`; vérifier les petites tailles contre brute force ;
contrôler que matching low-hub reste non-Ferrers et continue via T039/T040 ;
contrôler `C6/C8`, le tree négatif, low `0`, plusieurs hubs, non-binaire, sans
hub, PC-tree non-star non représentatif, et `quasi_orders=[]`.

Plan subagents : quatre sidecars lecture seule. Un audite la preuve Ferrers et
l'ordre des parts, un cherche des contre-exemples/ties/dégénérescences, un
mesure l'échec factoriel actuel sur chain permuté, un propose la documentation
des obligations de preuve.

Tests à exécuter : tests ciblés local-constraints/candidate/generators,
benchmark ciblé `permuted_chain_high_graph_plus_low_hub/star` jusqu'à `n=101`,
`make unit`, `make quick`, `make hunt-counterexamples`, `make check`,
`make bench-quick`, `make bench` puisque `candidate.py` change.

Risques : confondre Ferrers suffisant et strong-ordering général ; accepter un
témoin non représenté ; utiliser le rejet Ferrers comme faux négatif ; mauvais
ordre de la seconde part sous labels permutés ou égalités de voisinage.

Résultats observés : avant T041, `permuted_chain_high_graph_plus_low_hub`
relabellisé seed `0` saturait la limite `100000` de l'itérateur
strong-ordering dès `n=15`, alors que le premier témoin factoriel arrive après
`11,594,305` couples (`n=17` : `1,161,812,121`, `n=21` :
`4,429,285,415,150`). Le détecteur Ferrers évite cette explosion et accepte les
tailles `15,17,21,41,81,101` avec `checked_permutation_pairs=0`. Le benchmark
ciblé `permuted_chain_high_graph_plus_low_hub/star`, tailles
`9,11,15,17,21,41,81,101`, répétitions `10`, timeout `2s`, donne `0` timeout
et `0` incomplet ; à `n=101`, médiane `0.2606s`, p95 `0.2677s`.

Résultats subagents : l'audit preuve valide l'ordre Ferrers comme
strong-ordering quand l'inclusion réelle des voisinages est vérifiée. La
recherche de contre-exemples ne trouve pas de faux positif Ferrers, mais ajoute
deux garde-fous : un témoin Ferrers peut être cR mais non représenté par un
PC-tree non-star alors qu'un autre témoin représenté existe ; un tri par degrés
seulement échoue déjà sur un matching low-hub `n=5`. Le code verrouille donc
`represents_order` puis continue l'itérateur, et vérifie l'inclusion des
voisinages plutôt qu'un critère de degré.

Validation : tests ciblés `tests/test_candidate.py tests/test_local_constraints.py
tests/test_generators.py` donnent `76 passed`. `make unit` donne `171 passed`.
`make quick` donne `171 passed` puis `JUSTE`. `make hunt-counterexamples` et
`make check` donnent `JUSTE`. `make bench-quick` donne `0` timeout et `0`
incomplet ; à `n=20`, médiane `0.00112s`, p95 `0.00122s`. `make bench` donne
`0` timeout et `0` incomplet jusqu'à `n=100`; à `n=100`, médiane `0.0287s`,
p95 `0.0360s`, fit polynomial empirique `p ~= 1.76`.

Décision : intégrer T041 comme certificat positif polynomial pour le sous-cas
Ferrers/chain low-hub permuté. Garder explicitement les limites : Ferrers est
suffisant mais pas nécessaire, l'ordre Ferrers canonique peut ne pas être
représenté par un PC-tree non-star, et tout échec du détecteur reste
non-conclusif. Prochaine piste recommandée : rapport CSP non-star hors
candidate ou extension positive aux graphes bipartis permutation/strong-ordering
sans énumération factorielle.

## ExecPlan 2026-05-23 - component Ferrers low-hub witness

But : étendre le certificat positif low-hub au cas où le graphe haut privé des
hubs est une union disjointe de composantes biparties chain/Ferrers, y compris
après permutation des labels.

Hypothèse : si chaque composante non-hub admet un ordre Ferrers local
`A_c,B_c`, alors concaténer les composantes dans le même ordre côté `A` et côté
`B` donne un strong ordering global. Par le lemme bad-side T040, l'ordre
`hubs, A_1,...,A_k, B_1,...,B_k` est cR. Comme pour T041, la candidate ne peut
accepter qu'après validation cR directe et contrôle `represents_order` si un
PC-tree est fourni.

Fichiers à modifier : `src/pc_circular/solvers/local_constraints.py`,
`src/pc_circular/solvers/candidate.py` si un nouveau rapport est séparé,
`src/pc_circular/generators.py`, `tests/test_local_constraints.py`,
`tests/test_candidate.py`, `tests/test_generators.py`,
`docs/proof_obligations.md`, `docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : ajouter un générateur
`permuted_disjoint_chain_high_graph_plus_low_hub`. Ajouter un rapport positif
polynomial qui bipartit chaque composante, essaie les deux orientations
Ferrers, vérifie l'emboîtement des voisinages dans la composante, concatène les
ordres component-wise, puis vérifie `_has_strong_ordering` et
`passes_bad_side_precircular_cR`. Ne jamais utiliser l'échec de ce rapport
comme rejet.

Plan de contre-exemples : tester les tailles `13,17,21,31,41,81,101` où la
candidate actuelle échoue dès `n=17`; varier nombre de composantes, tailles
impaires, labels permutés, plusieurs hubs, `low=0`, PC-tree star et PC-tree
non-star qui ne représente pas le premier témoin. Vérifier que graphes non
Ferrers, cycles hauts pairs/impairs et tree négatif restent non acceptés par ce
certificat.

Plan subagents : jusqu'à cinq sidecars lecture seule. Un audite la preuve
component-wise, un cherche des contre-exemples/ties/PC-tree non-star, un mesure
l'explosion actuelle et les benchmarks ciblés, un compare avec la piste CSP/BPG
pour la suite, un audite les risques de documentation et d'obligations.

Tests à exécuter : tests ciblés candidate/local-constraints/generators,
benchmark ciblé `permuted_disjoint_chain_high_graph_plus_low_hub/star` jusqu'à
`n=101`, `make unit`, `make quick`, `make hunt-counterexamples`, `make check`,
`make bench-quick`; `make bench` si `candidate.py` change.

Risques : concaténer les composantes dans des ordres incompatibles côté `A` et
`B`; accepter un témoin non représenté par un PC-tree non-star ; confondre
union de composantes Ferrers avec reconnaissance générale des graphes bipartis
permutation ; transformer un échec de certificat en faux négatif.

Résultats observés : avant T042, la famille
`permuted_disjoint_chain_high_graph_plus_low_hub` seed `0` échouait par limite
factorielle dès `n=17` sur PC-tree star : `unsupported_permutation_limit` à
`100000` couples, puis `candidate_large_n_placeholder`. À `n=13`, le premier
témoin arrivait déjà après environ `79k` couples. Le nouveau rapport trouve le
témoin component-wise avant l'itérateur avec `checked_permutation_pairs=0`.
Benchmark ciblé star, tailles `13,17,21,31,41,81,101`, répétitions `10`,
timeout `2s` : `0` timeout et `0` incomplet ; à `n=101`, médiane `0.2433s`,
p95 `0.2454s`, fit polynomial empirique `p ~= 3.12`.

Résultats subagents : l'audit preuve valide l'argument component-wise à
condition que les composantes soient concaténées dans le même ordre côté `A` et
côté `B`; deux arêtes disjointes désalignées donnent déjà une violation. La
recherche de contre-exemples fournit un cas non-star `n=9` où le témoin
component-wise est cR mais non représenté, alors que la candidate trouve un
autre témoin représenté après `326` couples. Elle fournit aussi un cas limite
matching non-star `n=17` où un témoin représenté est connu mais la candidate
reste incomplète, ce qui motive une future intersection PC-tree/component-wise.
Le sidecar CSP confirme que T042 reste strictement plus faible qu'une
reconnaissance bipartite permutation/strong-ordering générale.

Validation : tests ciblés `tests/test_candidate.py tests/test_local_constraints.py
tests/test_generators.py` donnent `86 passed`. `make unit` donne `181 passed`.
`make quick` donne `181 passed` puis `JUSTE`. `make hunt-counterexamples` et
`make check` donnent `JUSTE`. `make bench-quick` donne `0` timeout et `0`
incomplet ; à `n=20`, médiane `0.00111s`, p95 `0.00123s`. `make bench` donne
`0` timeout et `0` incomplet jusqu'à `n=100`; à `n=100`, médiane `0.0295s`,
p95 `0.0359s`, fit polynomial empirique `p ~= 1.76`.

Décision : intégrer T042 comme certificat positif polynomial pour les unions
disjointes de composantes chain/Ferrers low-hub, en gardant les limites :
ce n'est pas une reconnaissance bipartite permutation générale, un témoin
component-wise non représenté ne prouve rien, et un échec du rapport reste
non conclusif. Prochaine piste recommandée : intersection PC-tree avec les
ordres component-Ferrers/strong-ordering, ou rapport polynomial expérimental
bipartite permutation hors candidate.

## ExecPlan 2026-05-23 - PC-tree guided matching witness

But : réduire la limite non-star laissée par T042 sur les matchings low-hub,
où un témoin représenté existe mais le témoin component-wise canonique n'est pas
représenté et l'itérateur factoriel peut manquer le bon ordre.

Hypothèse : dans un graphe haut matching avec hubs bas, tout ordre
`hubs, A_1,...,A_m, B_1,...,B_m` alignant les mates dans le même ordre est cR.
Si le PC-tree expose déjà un segment contigu contenant exactement un endpoint
de chaque paire, on peut lire ce segment dans un frontier représenté, placer les
mates en face dans le même ordre, puis vérifier directement cR et
`represents_order`. C'est un certificat positif guidé par le PC-tree, pas un
test complet d'intersection.

Fichiers à modifier : `src/pc_circular/solvers/local_constraints.py`,
`src/pc_circular/solvers/candidate.py`, `tests/test_local_constraints.py`,
`tests/test_candidate.py`, `docs/proof_obligations.md`,
`docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : ajouter un rapport
`pc_tree_guided_low_hub_matching_witness_report`. Détecter le sous-cas binaire
low-hub matching, prendre `sample_frontier(T)` et un petit nombre de frontiers
canoniques bornés, chercher des segments circulaires de longueur `m` contenant
exactement un endpoint de chaque paire, construire `hubs, mates(segment),
segment` et l'ordre inverse, puis accepter seulement si
`passes_bad_side_precircular_cR` et `represents_order(T, order)` sont vrais.

Plan de contre-exemples : tester le matching non-star `n=17` de T042, le
matching non-star `n=18` déjà régressé, des star controls, un PC-tree où le
segment lu ne donne pas de témoin représenté, les négatifs `C6/C8/tree`, `low=0`
et plusieurs hubs. Ajouter une régression pour tout cas où un témoin guidé est
cR mais non représenté.

Plan subagents : sidecars lecture seule. Un audite la soundness du segment
matching, un cherche des contre-exemples PC-tree où le segment heuristic est
insuffisant ou trompeur, un mesure le gain sur les cas non-star T040/T042, un
propose la documentation et les limites.

Tests à exécuter : tests ciblés candidate/local-constraints, probe exact petits
matchings PC-tree si possible, `make unit`, `make quick`,
`make hunt-counterexamples`, `make check`, `make bench-quick`; `make bench` si
`candidate.py` change.

Risques : confondre segment trouvé dans un frontier avec preuve de complétude ;
oublier que les hubs doivent rester un bloc représenté ; accepter un ordre non
représenté ; masquer l'incomplétude quand aucun segment utile n'est trouvé.

Résultats observés : le rapport guidé PC-tree résout les deux cas non-star
ciblés sans énumération de frontiers. Sur le cas T042 `n=17` racine `C/P/C`,
la candidate passe de placeholder incomplet à
`candidate_low_hub_pc_tree_guided_matching_witness`, avec `templates_checked=1`,
`frontiers_sampled=0`, `segments_checked=10`. Sur le cas T040 `n=18` racine
`C/P/P`, elle passe du témoin trouvé après `761` couples de permutations à un
témoin guidé avec `templates_checked=1`, `frontiers_sampled=0`,
`segments_checked=3`. Les probes `star/mixed` matchings `n=9,11,13,17`, cinq
seeds, gardent des incomplets mixed visibles (`5/20`) et ne transforment pas
l'échec du rapport en rejet.

Résultats subagents : l'audit soundness valide le certificat si le graphe haut
est bien un matching low-hub et si l'ordre construit est revalidé par
`passes_bad_side_precircular_cR` et `represents_order`. La recherche de
contre-exemples trouve deux limites durables : un cas split-hubs `n=6` où un
témoin représenté existe mais T043 ne le trouve pas, et un cas `n=8` où
`frontier_limit=64` échoue alors que `80` trouve un témoin. Ces limites sont
ajoutées aux tests pour empêcher toute lecture négative du statut incomplet.

Validation : tests ciblés `tests/test_candidate.py tests/test_local_constraints.py
tests/test_generators.py` donnent `91 passed`. `make unit` donne `186 passed`.
`make quick` donne `186 passed` puis `JUSTE`. `make hunt-counterexamples` et
`make check` donnent `JUSTE`. `make bench-quick` donne `0` timeout et `0`
incomplet ; à `n=20`, médiane `0.00118s`, p95 `0.00132s`. `make bench` donne
`0` timeout et `0` incomplet jusqu'à `n=100`; à `n=100`, médiane `0.0314s`,
p95 `0.0369s`, fit polynomial empirique `p ~= 1.80`.

Décision : intégrer T043 comme certificat positif guidé PC-tree pour matchings
low-hub, pas comme solveur d'intersection. Le rapport est sample-first et borné ;
absence de segment/témoin représenté reste `strong_ordering_exists=None` et ne
devient jamais un rejet. Prochaine piste recommandée : formaliser une vraie
intersection PC-tree/ordres matching ou component-Ferrers, notamment pour les
hubs séparés et les frontiers tardives.

## ExecPlan 2026-05-23 - projected frontier matching witness

But : traiter une limite explicite de T043 sur les matchings low-hub avec hubs
séparés. Dans ces cas, le frontier représenté lui-même peut être cR même si la
construction T043 `hubs, A, B` n'est pas représentée.

Hypothèse : pour une matrice binaire `low/high` avec hubs bas et graphe haut
matching, un ordre circulaire est cR dès que, après suppression des hubs, toutes
les cordes du matching haut se croisent deux à deux. Les hubs peuvent alors être
intercalés arbitrairement. C'est une conséquence du lemme bad-side, à vérifier
directement dans le code avant tout retour positif.

Fichiers à modifier : `src/pc_circular/solvers/local_constraints.py`,
`src/pc_circular/solvers/candidate.py`, `tests/test_local_constraints.py`,
`tests/test_candidate.py`, `docs/proof_obligations.md`,
`docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : factoriser l'analyse binaire low-hub matching déjà faite
par T043, ajouter un prédicat de projection "toutes les arêtes du matching se
croisent dans le frontier sans hubs", puis tester `sample_frontier(T)` et des
frontiers canoniques bornées. Si un frontier représenté passe la projection, le
retourner directement après `passes_bad_side_precircular_cR` et
`represents_order`. Garder T043 comme fallback de construction segmentaire.

Plan de contre-exemples : verrouiller le cas split-hubs `n=6` de T043 comme
positif complet ; tester `low=0`, plusieurs hubs, C6/C8/tree non matching,
frontier tardive `n=8`, petits PC-trees matching contre oracle exact, et des
ordres où les cordes ne croisent pas toutes pour éviter un faux positif.

Plan subagents : cinq sidecars lecture seule. Un audite le lemme bad-side avec
hubs arbitraires ; un cherche des faux positifs ou positifs manqués sur petits
PC-trees ; un mesure l'impact benchmark/probes T043 ; un explore si la
condition de projection peut devenir une vraie intersection PC-tree non bornée ;
un prépare la checklist documentation/preuve.

Tests à exécuter : tests ciblés candidate/local-constraints, probes exactes
petits matchings PC-tree, `make unit`, `make quick`,
`make hunt-counterexamples`, `make check`, `make bench-quick`; `make bench` si
`candidate.py` change.

Risques : croire que la projection matching donne une caractérisation pour des
graphes hauts non matching ; accepter un frontier sans revérification cR ;
masquer la borne `frontier_limit` ; dupliquer la logique T043 au lieu de la
factoriser proprement.

Résultats observés : le rapport T044 teste maintenant la projection matching
avant la construction segmentaire T043. Le split-hubs `n=6` passe de
`no_pc_tree_guided_matching_witness_found` à
`pc_tree_projected_matching_frontier_found` avec `projected_frontiers_checked=1`
et `segments_checked=0`. Une régression candidate `n=12` avec deux gros blocs
`P` et hubs séparés est maintenant positive complète par
`candidate_low_hub_pc_tree_guided_matching_witness`, alors que le témoin
component-Ferrers canonique n'est pas représenté. Le cas non-crossing rigide
`n=6` reste négatif exact, et le cas frontier tardive `n=8` reste une limite :
à `frontier_limit=64`, aucun témoin n'est trouvé.

Résultats subagents : l'audit preuve classe le lemme comme théorème dans le
sous-cas binaire low-hub matching, avec nécessité et suffisance de croisement
des cordes après suppression des hubs. Le sidecar intersection rappelle que
l'API `PCNode` actuelle ne fournit pas d'opération d'intersection non bornée ;
T044 reste donc une recherche de frontiers bornée, et une vraie décision
compacte demanderait pruning des hubs puis synchronisation de deux moitiés
`seq + mate(seq)` par DP/CSP.

Validation : tests ciblés `tests/test_local_constraints.py tests/test_candidate.py
tests/test_generators.py` donnent `94 passed`. `make quick` donne `189 passed`
puis `JUSTE`. `make hunt-counterexamples` et `make check` donnent `JUSTE`.
Probe exact petits matchings `n=5..8` : split-hubs positif au premier frontier,
non-crossing C négatif, frontier tardive toujours incomplète à `64`.
`make bench-quick` donne `0` timeout et `0` incomplet ; à `n=20`, médiane
`0.00120s`, p95 `0.00136s`, fit polynomial empirique `p ~= 1.85`. `make bench`
donne `0` timeout et `0` incomplet jusqu'à `n=100`; à `n=100`, médiane
`0.03139s`, p95 `0.03742s`, fit polynomial empirique `p ~= 1.79`.

Décision : intégrer T044 comme amélioration positive du certificat matching
low-hub. Le résultat prouvé porte sur un ordre fixé/projeté ; l'existence dans
un PC-tree compact reste bornée par les frontiers inspectées. Prochaine piste :
diagnostic exact petit `seq + mate(seq)` après pruning des hubs, puis tentative
DP/CSP d'intersection non bornée si les états restent petits.

## ExecPlan 2026-05-23 - exact bounded matching projection search

But : dépasser la dépendance T044 aux frontiers inspectées en énumérant
directement, lorsque c'est petit, tous les ordres circular Robinson possibles du
sous-cas matching low-hub : projections `seq + mate(seq)` et placements des
hubs dans les interstices.

Hypothèse : dans le sous-cas binaire low-hub matching prouvé par T044, les
ordres cR sont exactement les ordres dont la projection non-hub est
`seq, mate(seq)` à rotation/renversement près. Si le nombre de projections et
placements de hubs est sous une limite explicite, on peut décider exactement
l'existence dans un PC-tree du scaffold en testant `represents_order` sur tous
ces candidats. Au-dessus de la limite, le rapport reste incomplet.

Fichiers à modifier : `src/pc_circular/solvers/local_constraints.py`,
`src/pc_circular/solvers/candidate.py`, `tests/test_local_constraints.py`,
`tests/test_candidate.py`, `docs/proof_obligations.md`,
`docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : ajouter un rapport
`exact_low_hub_matching_projection_search_report`. Détecter le sous-cas
low-hub matching ; calculer la borne
`2^m * m! * h! * C(h+2m-1,2m-1)` ; si elle dépasse
`max_candidate_orders`, ne pas couper avant d'avoir essayé : énumérer
paresseusement les orientations et permutations des paires, insérer les hubs
dans les `2m` interstices, dédupliquer modulo rotation/renversement, tester
d'abord `represents_order`, puis accepter le premier ordre qui passe aussi
`passes_bad_side_precircular_cR`. Si le nombre réel de candidats uniques atteint
`max_candidate_orders`, retourner `candidate_limit_exceeded`. Si tous les
candidats sont épuisés, retourner un négatif complet pour ce sous-cas.

Plan de contre-exemples : tester le non-crossing rigide `n=6`, la frontier
tardive `n=8`, des PC-trees petits contre `exact_oracle_pc_tree`, des limites
de candidats, `low=0`, hubs multiples, et des cas où T044/T043 trouvent déjà un
témoin pour vérifier que le nouveau rapport ne contredit pas les certificats
positifs existants.

Plan subagents : sidecars lecture seule. Un audite la complétude de
l'énumération `seq + mate(seq)` avec hubs ; un cherche un faux négatif contre
l'oracle PC-tree sur petits matchings ; un mesure si le rapport résout des
placeholders mixed ou seulement des cas déjà couverts ; un évalue les risques de
complexité/limite ; un prépare la checklist documentaire.

Tests à exécuter : tests ciblés local-constraints/candidate, probes exactes
petits matchings PC-tree, `make unit`, `make quick`,
`make hunt-counterexamples`, `make check`, `make bench-quick`; `make bench` si
`candidate.py` change.

Risques : explosion combinatoire déguisée ; conclure négatif alors que
l'énumération n'a pas été complète ; doublons modulo rotation qui masquent une
erreur de couverture ; accepter un ordre non représenté ; généraliser le
résultat hors matching low-hub.

Résultats observés : le rapport exact borné trouve le cas frontier tardive
`n=8` que T044/T043 manquait à `frontier_limit=64`, avec témoin représenté et
cR. Il rejette complètement un rigide non-crossing `n=6`, et la candidate
rejette complètement un cas non-crossing `n=12` dont la borne PC-tree générale
dépasse `4096`, avec `21120` candidats uniques testés, `0` ordre représenté et
`0` check cR payé grâce à l'ordre `represents_order` avant cR. La correction
lazy évite un faux blocage sur une borne brute lâche : un cas `n=13` avec borne
brute `>100000` est trouvé sous `100000` candidats uniques.

Résultats subagents : l'audit preuve confirme que l'énumération
`seq + mate(seq)` plus placements arbitraires des hubs est complète pour le
sous-cas binaire low-hub matching, modulo rotation/renversement. Les probes
sidecars donnent `0` mismatch sur plusieurs centaines de couples petits
`(D,T)` et `59040` ordres fixés. Les mesures recommandent de garder
`EXACT_LOW_HUB_MATCHING_PROJECTION_LIMIT = 100000`, de tester `represents_order`
avant cR, et de présenter T045 comme diagnostic exact borné : il ne résout pas
les placeholders mixed `n=17` et n'améliore pas T040/T042 déjà couverts par
T043.

Validation : tests ciblés `tests/test_local_constraints.py tests/test_candidate.py
tests/test_generators.py` donnent `99 passed`. `make quick` donne `194 passed`
puis `JUSTE`. `make hunt-counterexamples` et `make check` donnent `JUSTE`.
Probe oracle local : `19` couples petits matching/PC-tree sans mismatch avec
`exact_oracle_pc_tree`. `make bench-quick` donne `0` timeout et `0` incomplet ;
à `n=20`, médiane `0.00126s`, p95 `0.00143s`, fit polynomial empirique
`p ~= 1.85`. `make bench` donne `0` timeout et `0` incomplet jusqu'à `n=100` ;
à `n=100`, médiane `0.03311s`, p95 `0.03756s`, fit polynomial empirique
`p ~= 1.81`.

Décision : intégrer T045 comme sous-cas exact borné après T044/T043 et seulement
quand le PC-tree n'est pas déjà sous la borne exacte générale. Un retour
`exists=False, complete=True` est autorisé uniquement si l'énumération des
candidats uniques est réellement épuisée ; `candidate_limit_exceeded` reste
incomplet. Prochaine piste : transformer cette énumération en DP/CSP
d'intersection `seq + mate(seq)` ou chercher un contre-exemple minimal à toute
règle locale de synchronisation.

## ExecPlan 2026-05-23 - hub-projected matching PC-tree lift

But : réduire la limite combinatoire T045 en séparant deux questions dans le
sous-cas binaire low-hub matching : existence d'une projection high-vertices
`seq + mate(seq)`, puis relèvement exact de cette projection dans le PC-tree
original avec les hubs placés par la structure de l'arbre.

Hypothèse : pour ce sous-cas, les hubs peuvent être ignorés dans la condition
cR, mais pas dans la représentation PC-tree. Si l'on peut relever exactement une
projection high-vertices vers un frontier complet représenté, on peut décider
plus de cas que T045 lorsque les placements de hubs font exploser
`h! * C(h+2m-1,2m-1)`. Un échec complet sur toutes les projections
`seq + mate(seq)` donne un négatif exact pour ce sous-cas ; un dépassement de
limite reste incomplet.

Fichiers à modifier : `src/pc_circular/solvers/local_constraints.py`,
`src/pc_circular/solvers/candidate.py`, `tests/test_local_constraints.py`,
`tests/test_candidate.py`, `docs/proof_obligations.md`,
`docs/tracks/piste_c_sat_csp.md`,
`docs/tracks/piste_e_farthest_quartets.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/tracks/README.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `PLANS.md`.

Algorithme pressenti : ajouter un releveur récursif
`_lift_projection_frontier` qui, pour une projection linéaire donnée et un
ensemble de labels projetés, construit un frontier complet représenté ou
échoue. Sur un nœud `P`, les enfants non vides doivent apparaître comme des
blocs contigus dans la projection ; les enfants hubs-only peuvent être insérés
sans changer la projection. Sur un nœud `C`, l'ordre des enfants non vides doit
être compatible avec l'ordre local forward/reverse après suppression des
enfants hubs-only. Au niveau racine, essayer rotations et renversements de la
projection. Énumérer seulement les projections `2^m * m!` dédupliquées modulo
rotation/renversement, relever, puis vérifier directement
`passes_bad_side_precircular_cR` et `represents_order` avant tout retour
positif.

Plan de contre-exemples : comparer le releveur à une énumération exhaustive des
frontiers sur petits PC-trees avec hubs multiples ; chercher les cas où la
projection est représentable après suppression des hubs mais non relevable dans
l'arbre original ; tester non-crossing rigide, frontier tardive, gros hubs avec
peu de paires, nœuds `C` avec enfants hubs-only intercalés, `low=0`, et des
PC-trees où certains ordres marchent mais d'autres non.

Plan subagents : cinq sidecars lecture seule. Piste B audite l'état DP possible
du releveur ; Piste C cherche une formulation CSP/nogoods de la même
projection ; Piste A cherche un contre-exemple à une règle locale P/C naïve ;
Piste E/F attaque la candidate par probes non-star/non stricts ; complexité
classe les sous-cas prouvés versus bornés et recommande l'intégration suivante.

Tests à exécuter : tests ciblés local-constraints/candidate, probes exhaustives
petits PC-trees contre `enumerate_frontiers` et `exact_oracle_pc_tree`,
`make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`; si
`candidate.py` change, lancer aussi `make bench`.

Risques : le relèvement projection -> frontier complet peut être trop faible si
la rotation racine est mal traitée ; un enfant projeté en deux morceaux doit
être rejeté ; les hubs-only dans un nœud `C` ne doivent pas donner une liberté
de placement inexistante ; l'énumération reste factorielle en nombre de paires
et ne doit pas être présentée comme un algorithme général.

Résultats observés : `exact_low_hub_matching_projected_pc_tree_search_report`
ajouté. Le releveur trouve le cas frontier tardive `n=8`, rejette le rigide
non-crossing `n=6`, transforme le rejet candidate rigide `n=12` en recherche
sur `192` projections avec `0` ordre relevé, et rejette un stress `5` paires +
`8` hubs sans énumérer les placements de hubs. Probe oracle local :
`14` couples matching/PC-tree sans mismatch. Deux contre-exemples de méthode ont
été ajoutés aux régressions : `P(P(1,3),P(2,4),0)` est négatif malgré des
projections locales `I_x(v)` silencieuses, et une projection side-split rigide
montre qu'une 2-SAT par côté des endpoints est trop faible.

Résultats subagents : Piste A fournit le contre-exemple minimal `n=5` aux
règles locales `I_x(v)`. Piste B recommande une future DP qui transporte l'ordre
des paires ouvertes et confirme que T046 est une étape utile mais encore
factorielle. Piste C recommande des nogoods 4-aires/support-local et fournit le
contre-exemple side-only `C(0,1,2,3,4,6,5,7)`. Piste complexité classe T046
comme exact borné, pas polynomial, et recommande de supprimer à terme la limite
`2^m*m!`. Le sidecar E/F a été fermé après timeout sans livrable exploitable.

Validation : tests ciblés `tests/test_local_constraints.py tests/test_candidate.py
tests/test_regression_counterexamples.py` donnent `102 passed`. `make quick`
donne `202 passed`, puis `JUSTE`. `make hunt-counterexamples` et `make check`
donnent `JUSTE`. `make bench-quick` écrit le rapport avec `0` timeout,
`0` incomplet ; à `n=20`, médiane `0.001331s`, p95 `0.001514s`, fit polynomial
empirique `p ~= 1.91`. `make bench` écrit le rapport fort avec `0` timeout,
`0` incomplet jusqu'à `n=100` ; à `n=100`, médiane `0.03504s`,
p95 `0.04181s`, fit polynomial empirique `p ~= 1.82`.

Décision : intégrer T046 comme amélioration exacte bornée avant T045 complète,
car elle enlève le facteur des hubs sans affaiblir la correction. Ne pas marquer
le sous-cas comme polynomial : la prochaine piste doit remplacer l'énumération
des projections par une DP/CSP support-local ou produire un contre-exemple à
cette compression.

## ExecPlan 2026-05-23 - support-local bad-side nogood compilation

But : réduire le coût dominant de la Piste C en compilant les nogoods bad-side
par produit des domaines du support local d'un atom, au lieu d'énumérer toutes
les affectations complètes du PC-tree pour découvrir les mêmes signatures.

Hypothèse : `quartet_support_paths(T, atom)` contient exactement les variables
dont les choix déterminent l'ordre cyclique relatif des quatre labels de
`atom`. Pour un PC-tree supporté, on peut donc énumérer seulement
`prod(|domain(v)| : v in support)` pour chaque atom bad-side et produire les
mêmes nogoods que `compile_bad_side_nogoods`, qui parcourt l'espace complet.
Si cette équivalence tient sur petits arbres, cela donne une brique CSP plus
compacte et falsifiable, sans l'intégrer encore comme solver général.

Fichiers à modifier : `src/pc_circular/solvers/sat_like_experiments.py`,
`tests/test_sat_like_experiments.py`, `tools/pc_csp_internal_benchmark.py` si
la métrique doit être exposée, `docs/tracks/piste_c_sat_csp.md`,
`docs/tracks/piste_b_dp_pc_tree.md`, `docs/proof_obligations.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `docs/tracks/README.md`,
`PLANS.md`.

Algorithme pressenti : ajouter un reconstructeur de l'ordre projeté des labels
d'un atom depuis une affectation partielle sur son support. Compiler les nogoods
bad-side en itérant, pour chaque atom, le produit des domaines des chemins de
support ; si l'atom apparaît dans l'ordre projeté, enregistrer la signature
support comme nogood. Réutiliser ensuite `solve_pruned_nogood_csp_from_compilation`
pour valider que les frontiers acceptées coïncident avec le CSP direct exact.
La compilation garde un statut incomplet si une limite de produits de support
est atteinte ou si un nœud `P` est unsupported.

Plan de contre-exemples : comparer les nogoods support-local aux nogoods
énumérés complets sur arbres nested, wrapping, balanced/mixed et familles
random/cycle/equal/matching low-hub ; chercher faux positifs/faux négatifs via
`solve_pruned_nogood_csp_from_compilation(validate_against_direct=True)` ; tester
spécifiquement les cas où le support omet un nœud nested et ceux où la
canonicalisation circulaire pourrait inverser l'orientation.

Plan subagents : sidecars lecture seule. Piste C audite l'équivalence support
local vs compilation complète ; Piste B cherche une collision de signature de
support ; Piste A/E génère des contre-exemples de quartet/nœud nested ; Piste F
mesure si la métrique est un vrai progrès ou seulement un déplacement de coût.

Tests à exécuter : tests ciblés `tests/test_sat_like_experiments.py`, probes
bornées contre `accepted_frontiers_by_csp`, `make quick`,
`make hunt-counterexamples` si le solveur public change ou si un nouveau
certificat est intégré, `make bench-csp-quick` pour la métrique interne.

Risques : l'ordre projeté d'un atom peut dépendre d'une rotation/reversal
globale non capturée ; un support calculé trop petit peut produire un faux
nogood ; un produit de supports par atom peut être plus cher que l'espace
complet quand il y a beaucoup d'atomes ; ce travail reste expérimental et ne
doit pas devenir un rejet dans `candidate.py`.

Résultats observés : ajout de
`compile_bad_side_nogoods_support_local`,
`compile_cr_nogoods_support_local` et
`solve_support_local_bad_side_nogood_csp`. Les nogoods support-local sont
dédupliqués par signature effective de pruning, pas par identité orientée
d'atom. Tests ciblés `tests/test_sat_like_experiments.py` : `26 passed`.
Probe borné : `577` couples famille/tree sans mismatch de signatures ni de
solveur contre le CSP direct. `make bench-csp-quick` : `192` lignes, `0`
mismatch, `0` mismatch de signatures, médiane compile complète `0.00104s`,
médiane compile support-local `0.00276s`, médiane solve support-local
`0.000120s`, ratio médian `support_product_total / (full_assignment_space *
atoms) = 0.25`, `2904` signatures support-local contre `31616` nogoods
atom-labellisés complets. `make quick` final donne `209 passed`, puis `JUSTE`.
`make check` donne `JUSTE`. `make bench-quick` garde `0` timeout et `0`
incomplet ; à `n=20`, médiane `0.001340s`, p95 `0.001529s`, fit polynomial
empirique `p ~= 1.90`. `make bench` garde `0` timeout et `0` incomplet jusqu'à
`n=100` ; à `n=100`, médiane `0.03458s`, p95 `0.03771s`, fit polynomial
empirique `p ~= 1.81`.

Résultats subagents : Piste C valide l'approche seulement au niveau signatures
et recommande explicitement de ne pas comparer `(atom, signature)`. Piste B
trouve une collision canonique où un label hors atom change l'orientation de
`canonical_circular_order(frontier_complet)` ; ce cas est ajouté en test. Piste
contre-exemples exécute `1491` cas `n=4..7` sans mismatch de signatures seules
ni mismatch solveur, tout en confirmant `1271` mismatches stricts
`(atom, signature)`. Piste complexité montre que T047 est asymptotiquement
meilleur quand l'ancien coût pertinent est `full_assignment_space * atoms`, mais
pas toujours plus rapide sur petits arbres.

Décision : conserver T047 comme artefact Piste C hors `candidate.py`. Il réduit
fortement le nombre de signatures de pruning et donne une métrique plus honnête
du coût de compilation, mais il ne prouve pas encore un solveur compact général :
si le nombre d'atoms domine, la somme des produits de support peut rester
élevée. Prochaine étape : compiler les supports par classes/signatures
d'atom ou chercher une borne structurelle sur `support_product_total`.

## ExecPlan 2026-05-23 - grouped support-local bad-side compilation

But : tester si l'étape T047 peut être renforcée en énumérant chaque support
local une seule fois, au lieu de répéter le même produit de domaines pour tous
les atoms qui partagent ce support.

Hypothèse : pour les nogoods bad-side, beaucoup d'atoms partagent le même
`quartet_support_paths`. Si l'on groupe ces atoms par support, une affectation
du support peut être projetée une seule fois par atom du groupe et produire les
mêmes signatures de pruning que T047. Le coût de produit devient
`sum_unique_support_products`, plus lisible que `sum_support_products`, même si
le coût de test des atoms dans chaque groupe reste à mesurer.

Fichiers à modifier : `src/pc_circular/solvers/sat_like_experiments.py`,
`tests/test_sat_like_experiments.py`, `tools/pc_csp_internal_benchmark.py`,
`docs/tracks/piste_c_sat_csp.md`, `docs/proof_obligations.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `docs/tracks/README.md`,
`PLANS.md`.

Algorithme pressenti : ajouter
`compile_bad_side_nogoods_grouped_by_support`. Construire les atoms bad-side,
calculer leur support, grouper par tuple de chemins. Pour chaque groupe,
énumérer le produit des domaines une seule fois ; pour chaque affectation de ce
support, tester les atoms du groupe avec
`_project_atom_order_from_support_assignment`, puis enregistrer la signature
quand au moins un atom apparaît. Le rapport doit exposer
`support_group_count`, `grouped_support_product_total`,
`atom_checks`, `effective_signature_count` et comparer ces métriques à T047
dans le benchmark interne. Aucune intégration dans `candidate.py`.

Plan de contre-exemples : comparer les signatures du compilateur groupé avec
`compile_bad_side_nogoods_support_local` et `compile_bad_side_nogoods` sur
wrapping, nested, equal-distance, random, cycle, paired-farthest et matching
low-hub ; valider le solveur pruné contre `accepted_frontiers_by_csp`; tester
une limite basse pour vérifier que le statut incomplet ne produit pas de rejet.

Plan subagents : sidecars lecture seule si besoin. Piste C vérifie la
soundness de la déduplication par groupe ; Piste F mesure si le ratio
`grouped_support_product_total / support_product_total` est réellement utile ;
Piste B cherche une collision due à un support groupé trop large ou trop petit.

Tests à exécuter : tests ciblés `tests/test_sat_like_experiments.py`, probe
borné de signatures groupées, `make bench-csp-quick`, puis `make quick` et
`make check` si le code expérimental reste isolé.

Risques : le groupement peut réduire les produits énumérés sans réduire le
coût total si `atom_checks` domine ; une limite sur groupes doit rester
incomplète, jamais négative ; l'atom stocké dans un nogood reste seulement
diagnostique comme en T047.

Résultats observés : le compilateur groupé a été ajouté sous le nom
`compile_bad_side_nogoods_grouped_support_local`, avec le solveur expérimental
`solve_grouped_support_local_bad_side_nogood_csp`. Les tests ciblés
`tests/test_sat_like_experiments.py` donnent `31 passed`. Le probe indépendant
multi-familles `n=4..7` donne `130` cas, `0` mismatch de signatures,
`0` mismatch solveur groupé vs support-local, `0` mismatch contre le CSP cR
direct ; produit support T047 `50048` contre produit groupé `4128`, ratio
`0.08248`. `make bench-csp-quick` donne `192` lignes, `0` mismatch,
`0` support mismatch, `0` grouped mismatch, `0` signature mismatch, produit
support total `72256`, produit groupé total `6224`, ratio médian
`0.11111`, `total_grouped_atom_checks=72256`, et mêmes `2904` signatures que
T047. Le gain mesuré est donc sur l'énumération des produits de support, pas
encore sur les tests atom-par-atom. `make quick` donne `214 passed`, puis
`JUSTE`; `make check` donne `JUSTE`.

Résultats subagents : audit Piste C sans faux positif/faux négatif évident,
avec recommandation d'ajouter des tests de signatures seules, limite et
unsupported ; Piste F mesure des collisions massives de support avec gains de
produit `8x..43x` jusqu'à `n=10`, mais signale que `atom_checks` reste égal au
coût support-local T047 ; Piste contre-exemples exécute `84` cas généraux et
`18` cas low-hub matching sans mismatch, avec ratio produit groupé de
`0.007706` sur la première série et `0.046384` sur low-hub.

Décision : conserver T048 comme compression structurelle Piste C hors
`candidate.py`. C'est un progrès métrique net sur `sum_unique_support_products`,
mais pas encore un solveur compact : la prochaine tentative doit factoriser les
tests d'atom dans un même groupe de support ou prouver une borne sur la taille
des groupes.

## ExecPlan 2026-05-23 - first-hit grouped support compilation

But : tester si T048 peut réduire le coût `atom_checks` sans perdre de nogood en
s'arrêtant au premier atom violé pour une affectation de support.

Hypothèse : pour un support fixé et une affectation de ses variables, la
signature de pruning est entièrement déterminée par l'affectation. Si au moins
un atom bad-side du groupe apparaît, cette signature est déjà un nogood
suffisant ; les autres atoms violés par la même affectation sont diagnostiques
mais redondants pour le pruning. On peut donc compiler les mêmes signatures que
T048 avec moins de tests d'atoms.

Fichiers à modifier : `src/pc_circular/solvers/sat_like_experiments.py`,
`tests/test_sat_like_experiments.py`, `tools/pc_csp_internal_benchmark.py`,
`docs/tracks/piste_c_sat_csp.md`, `docs/tracks/piste_b_dp_pc_tree.md`,
`docs/tracks/piste_f_complexity_subcases.md`, `docs/proof_obligations.md`,
`docs/experiment_log.md`, `docs/checkpoints.md`, `docs/tracks/README.md`,
`PLANS.md`.

Algorithme pressenti : factoriser `_compile_nogoods_by_grouped_supports` avec
un paramètre interne `stop_after_first_hit`. Ajouter un compilateur public
expérimental `compile_bad_side_nogoods_grouped_first_hit_support_local` et un
solveur associé. Quand un atom du groupe apparaît pour une affectation de
support, enregistrer la signature puis arrêter le scan des atoms de ce groupe
pour cette affectation. Exposer `stopped_after_first_hit`,
`atom_checks_if_exhaustive` et `atom_checks_saved_by_first_hit`.

Plan de contre-exemples : comparer les signatures first-hit à T048 et T047 sur
random, cycle, block, ultrametric, equal, non-strict, paired-farthest,
permuted-cycle et matching low-hub ; valider le solveur pruné contre
`accepted_frontiers_by_csp(source="cr")`; tester wrapping, limite basse et
unsupported ; chercher explicitement un cas où plusieurs atoms partagent une
signature mais où le premier atom choisi changerait l'ensemble des signatures.

Plan subagents : Piste C audite la soundness de l'arrêt au premier hit ; Piste
contre-exemples lance des probes signatures/solveur sur familles diverses ;
Piste F mesure le gain d'`atom_checks` et cherche les familles où il est nul ;
Piste B vérifie que l'optimisation ne crée pas une fausse signature DP trop
faible.

Tests à exécuter : tests ciblés `tests/test_sat_like_experiments.py`, probe
multi-familles, `make bench-csp-quick`, `make quick`, `make check`. Pas de
`make hunt-counterexamples` requis sauf si `candidate.py` est modifié, ce qui
n'est pas prévu.

Risques : les métriques `atoms_with_nogoods`, `pairs_with_nogoods` et
`atom_hits` deviennent des compteurs de premiers hits, pas une énumération
complète des violations ; il faut documenter ce changement pour éviter une
interprétation sémantique trop forte. L'optimisation peut être faible si la
plupart des affectations de support ne violent aucun atom.

Résultats observés : ajout de
`compile_bad_side_nogoods_grouped_first_hit_support_local` et
`solve_grouped_first_hit_support_local_bad_side_nogood_csp`, sans changement de
`candidate.py`. Tests ciblés `tests/test_sat_like_experiments.py` :
`39 passed`. `make bench-csp-quick` : `192` lignes, `0` mismatch,
`0` support/grouped/first-hit mismatch, `0` mismatch de signatures ; mêmes
`2904` signatures que T047/T048 ; `total_grouped_atom_checks=72256`,
`total_first_hit_atom_checks=41872`, gain `30384` checks. Probe indépendant
multi-familles `n=4..7` : `130` cas, `0` mismatch de signatures,
`0` mismatch contre le CSP cR direct ; `grouped_atom_checks=49760`,
`first_hit_atom_checks=24168`, gain `25592`, ratio sauvegardé `0.5143`.
Subagents : audit soundness validant l'équivalence existentielle des signatures
mais pas les diagnostics exhaustifs ; Piste B fournit un cas minimal où les
signatures restent identiques mais `atoms_with_nogoods` et `pairs_with_nogoods`
diminuent ; contre-exemples couvre `220` cas sans mismatch et observe
`356612 -> 82052` atom checks ; complexité mesure `160` cas jusqu'à `n=8` avec
`48888/87328` checks économisés, soit `56.0%`. `make quick` final :
`222 passed`, puis `JUSTE`; `make check` final : `JUSTE`.

Décision : conserver T049 comme optimisation expérimentale sound au niveau des
signatures de pruning. Cela améliore réellement le coût atom-par-atom de T048,
mais ne donne toujours pas de borne polynomiale générale : il faut ensuite
caractériser les cas sans hit rapide ou compiler les groupes de support sans
scanner une liste d'atoms.
