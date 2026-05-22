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
