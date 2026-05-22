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
