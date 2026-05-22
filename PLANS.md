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
