# Checkpoints

Un commit stable doit satisfaire :

- `make quick` passe ;
- `make bench-quick` écrit un rapport JSON ou documente explicitement les
  timeouts/incomplétudes ;
- `docs/experiment_log.md` décrit l’hypothèse, la commande et la conclusion ;
- aucun contre-exemple connu n’est supprimé.

## Dernier commit green

- Initial setup : `e5f0ec3` (`checkpoint: baseline research setup with
  correctness and complexity gates`).
- Statut attendu : baseline exacte `n <= 8`, placeholder incomplet au-delà.
- Validation initiale : `make quick` vert et `make bench-quick` sans timeout,
  avec runs incomplets explicitement comptés pour `n > 8`.
- Checkpoint Goal 2026-05-22 : `7da77f5` (`checkpoint: add obstruction
  diagnostics and stress families`). Diagnostics d’obstructions,
  contre-exemples farthest, familles Piste F et benchmark ciblé ajoutés.
  Validation observée : `make quick`, `make hunt-counterexamples`,
  `make check`, `make bench-quick`, `make bench-piste-f`.
- Checkpoint Prop. 4.5 : `07120e4` (`checkpoint: add prop 4.5 fixed-order
  diagnostic`). Diagnostic d’ordre fixé quasi-circulaire ajouté. Validation
  observée : `make quick`, `make check`, probe exhaustif `n <= 5` sur ordres
  quasi-circulaires sans désaccord.

Dernier commit green avant T009 : `07120e4`.

- Checkpoint T009 : `f17ad89` (`checkpoint: add prop45 nogood frontier
  experiment`). Scan Prop. 4.5 comme nogood de frontier ajouté. Validation
  observée : `make unit`, `make quick`, `make check`, `make bench-quick`, probe
  random bornée sans désaccord sur ordres quasi-circulaires.
- Checkpoint T010 : `f7aa62f` (`checkpoint: add local domain csp scaffold`).
  Scaffold CSP à domaines locaux `P/C` ajouté. Validation observée :
  `make quick`, `make check`, `make bench-quick`, probe CSP directe sans
  désaccord sur 1600 instances.
- Checkpoint T011 : `53cc4cf` (`checkpoint: compile cr quartet nogoods`).
  Nogoods compilés de quartets cR ajoutés. Validation observée : `make quick`,
  `make check`, `make bench-quick`, probe compiled-nogood sans désaccord sur
  960 instances.
- Checkpoint T012 : `9346feb` (`checkpoint: add pruned nogood backtracking`).
  Backtracking pruné par nogoods compilés ajouté. Validation observée :
  `make quick`, `make check`, `make bench-quick`, probe pruned-nogood sans
  désaccord sur 640 instances.
- Checkpoint T013 : `1b0ad1c` (`checkpoint: add csp internal benchmark`).
  Benchmark interne Piste C ajouté. Validation observée : `make quick`,
  `make check`, `make bench-csp-quick`, `make bench-quick`.
- Checkpoint T014 : `0c60de8` (`checkpoint: add bad-side dp signature
  diagnostic`). Diagnostic bad-side fixed-order Piste B ajouté. Validation
  observée : `make unit`, probe bad-side `715875` comparaisons, `make quick`,
  `make check`, `make bench-quick`.
- Checkpoint T015 : `ed52c2e` (`checkpoint: measure bad-side block
  signatures`). Métriques de signature de bloc Piste B ajoutées. Validation
  observée : `make unit`, probe signature de blocs `27` lignes, `make quick`,
  `make check`, `make bench-quick`.
- Checkpoint T016 : `eff96c1` (`checkpoint: add universal bad-witness
  subcase`). Sous-cas universel `|B(a,b)| <= 1` intégré à la candidate.
  Validation observée : `make unit`, probe large-n `33` checks, `make quick`,
  `make check`, `make hunt-counterexamples`, `make bench-quick`.
- Checkpoint T017 : `376ecea` (`checkpoint: certify sampled positive
  witnesses`). Certification des témoins positifs échantillonnés. Validation
  observée :
  `make unit`, `make quick`, `make check`, `make hunt-counterexamples`,
  `make bench-quick`, `make bench` (`0` timeout, `42` incomplets visibles).
- Checkpoint T018 : `aad8e98` (`checkpoint: add minimum-distance cycle
  witness`). Commit contenant le témoin minimum-cycle star, le
  contre-exemple régressé `n=6` montrant que le graphe minimum cycle ne suffit
  pas pour cR, et la capture Proposition 4.4 conservée dans
  `docs/source_materials/images/`. Validation observée : `make unit`,
  `make quick`, `make check`, `make hunt-counterexamples`,
  `make bench-piste-f`, `make bench-quick`, `make bench` (`0` timeout, `42`
  incomplets visibles, fit polynomial empirique `p ~= 3.25`).
- Checkpoint T019 : `1588166` (`checkpoint: certify minimum-cycle witnesses in
  represented pc trees`). Commit contenant `represents_order` non énumératif
  pour les ordres fixés du scaffold PC-tree, l'extension du témoin
  minimum-cycle aux PC-trees non-star représentés, et le contre-exemple
  régressé où un min-cycle cR non représenté ne doit pas être accepté.
  Validation observée : `make unit`, probe membership `11837` checks,
  `make quick`, `make check`, `make hunt-counterexamples`,
  `make bench-piste-f`, `make bench-quick`, `make bench` (`0` timeout, `42`
  incomplets visibles, fit polynomial empirique `p ~= 3.25`).
- Checkpoint T020 courant : commit contenant le témoin structurel
  paired-farthest pour les matrices three-level à matching maximal, et le
  contre-exemple régressé où ce témoin cR n'est pas représenté par un PC-tree
  non-star. Validation observée : `make unit`, probe `paired_farthest`
  `380` checks, `make quick`, `make check`, `make hunt-counterexamples`,
  `make bench-piste-f`, `make bench-quick`, `make bench` (`0` timeout, `42`
  incomplets visibles, fit polynomial empirique `p ~= 3.24`).
- Checkpoint T021 courant : commit contenant les régressions
  `paired_farthest` non-star `n=6`, la documentation des résultats subagents
  Piste A/B/F, et la décision de ne pas intégrer la génération side-by-side
  non bornée dans `candidate.py`. Validation observée : test ciblé
  `tests/test_regression_counterexamples.py`, `make quick`, `make bench-piste-f`.
- Checkpoint T022 courant : commit contenant
  `project_farthest_sets_to_pc_nodes` comme diagnostic Piste A/D, tests
  égal-distance et nœud `C`, et documentation de non-décision. Validation
  observée : `tests/test_local_constraints.py`, `make unit`, `make quick`,
  `make bench-quick` (`0` timeout, `0` incomplet).
- Checkpoint T023 courant : commit contenant les prédicats stricts d'ordre fixé,
  `strict_order_report`, les régressions Fig. 2.2 / égal-distance / cycle /
  témoin strict non représenté, et la documentation de non-intégration
  candidate. Validation observée : `tests/test_strict_experiments.py`,
  `make unit`, `make quick`, `make bench-quick` (`0` timeout, `0` incomplet).
- Checkpoint T024 courant : commit contenant `strict_algorithm52_report`, un
  générateur expérimental inspiré de l'Algorithm 5.2 et filtré par les prédicats
  stricts directs, plus les régressions cycle/Fig. 2.2/random/PC-tree. Validation
  observée : `tests/test_strict_experiments.py`, probe stricte random bornée,
  `make unit`, `make quick`, `make bench-quick`.
- Checkpoint T025 courant : commit contenant `strict_ball_circular_ones_report`,
  diagnostic borné comparant boules non triviales comme arcs, quasi-circularité,
  strict quasi et strict circular, avec signatures exactes de modules par
  boules et contre-exemple random `ball_arc/quasi` non cR. Validation observée :
  `tests/test_strict_experiments.py`, probe ball/quasi random bornée,
  `make unit`, `make quick`, `make bench-quick`.
- Checkpoint T026 courant : commit contenant
  `bad_witness_arc_constraints_report`, diagnostic borné comparant la condition
  exacte one-side des mauvais témoins à deux contraintes d'arcs naïves. Il
  verrouille que `B(a,b)` arc est trop fort et que
  `B(a,b) union {a,b}` est ni nécessaire ni suffisant. Validation observée :
  `tests/test_dp_experiments.py`, `make unit`, `make quick`,
  `make bench-quick` (`0` timeout, `0` incomplet).
- Checkpoint T027 courant : commit contenant la compilation CSP bad-side par
  paire (`forbidden_bad_side_atoms`, `compile_bad_side_nogoods`,
  `solve_compiled_bad_side_nogood_csp`, `solve_pruned_bad_side_nogood_csp`).
  Les tests verrouillent l'exactitude fixed-order exhaustive `n=4`, les
  égalités, le wrapping non-cR et l'équivalence au filtre cR direct sur arbres
  supportés. Validation observée : `tests/test_sat_like_experiments.py`, probe
  fanout 3 bad-side/quartets, `make unit`, `make quick`, `make bench-csp-quick`,
  `make bench-quick`.
- Checkpoint T028 courant : commit contenant le sous-cas
  `candidate_exact_bounded_pc_tree_frontiers`. La candidate calcule une borne
  indépendante saturée sur le nombre de frontiers du PC-tree scaffold et énumère
  exactement seulement si la borne est sous `EXACT_PC_TREE_FRONTIER_LIMIT`.
  Validation observée : `tests/test_candidate.py`, probe oracle PC-tree `42`
  décisions, `make unit`, `make quick`, `make hunt-counterexamples`,
  `make check`, `make bench-quick`.
- Checkpoint T029 courant : commit contenant le sous-cas
  `candidate_exact_bounded_quasi_orders`. La candidate décide exactement une
  famille explicite `quasi_orders` seulement si elle expose une longueur fiable
  et si cette longueur est sous `EXACT_QUASI_ORDER_LIMIT`. Les familles trop
  grandes et les itérateurs non dimensionnés restent incomplets en négatif.
  Validation observée : `tests/test_candidate.py`, `make unit`, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`.
- Checkpoint T030 courant : commit contenant l'attribution `resolved_kind` des
  benchmarks `mixed`, sans changement de `candidate.py`. Le rapport de
  complexité conserve `seed`, `mixed_instance_kinds`, et les compteurs
  `resolved_kind_*`. Validation observée : tests générateurs/benchmark ciblés,
  `make unit`, `make quick`, `make check`, `make bench-quick`, `make bench`.
  Résultat observé : les `42` incomplets du benchmark fort `mixed/star` sont
  tous `random`, avec `0` timeout. `make bench-piste-f` passe aussi avec `0`
  timeout ; `paired_farthest/mixed` reste incomplet seulement pour `n=16,20`.
- Checkpoint T031 courant : commit contenant le certificat négatif héréditaire
  `candidate_small_forbidden_submatrix_obstruction` par sous-matrice 4 points,
  plus la validation cR directe du témoin paired-farthest. Validation observée :
  `tests/test_candidate.py`, `make unit`, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`,
  `make bench-piste-f`. Résultat observé : `make bench` a `0` timeout et `0`
  incomplet jusqu'à `n=100`; les `42` anciens placeholders random sont rejetés
  par obstruction 4-points.
- Checkpoint T032 courant : commit contenant le contre-exemple minimal
  `four_local_non_cr_core`, son padding large `padded_four_local_non_cr`, et
  l'extension du certificat héréditaire aux tailles `(4,5)`. Validation
  observée : tests candidats/générateurs/régressions ciblés, `make unit`,
  `make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
  `make bench`, benchmark ciblé `four_local_non_cr/star`. Résultat observé : le
  4-local seul est réfuté, mais les rejets 5-points restent sound quand le noyau
  induit est trouvé.
- Checkpoint T033 courant : commit contenant le contre-exemple minimal
  `five_local_non_cr_core`, son padding large `padded_five_local_non_cr`, le
  générateur `odd_high_cycle_plus_low_hub`, l'extension du certificat
  héréditaire aux tailles `(4,5,6)`, et le certificat structurel négatif
  `candidate_odd_high_cycle_low_hub_obstruction`. Validation observée : tests
  candidats/générateurs/régressions ciblés, `make unit`, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`,
  `make bench-piste-f`, benchmarks ciblés `five_local_non_cr/star` et
  `odd_high_cycle_plus_low_hub/star`. Résultat observé : le 5-local seul est
  réfuté ; la famille cycle haut impair plus hub bas est désormais rejetée par
  un certificat polynomial.
- Checkpoint T034 courant : commit contenant la généralisation du certificat
  cycle haut impair vers
  `candidate_non_bipartite_high_graph_low_hub_obstruction`, le générateur
  `non_bipartite_high_graph_plus_low_hub`, et les régressions associées.
  Validation observée : tests candidats/générateurs/régressions ciblés,
  `make unit`, `make quick`, `make hunt-counterexamples`, `make check`,
  `make bench-quick`, `make bench-piste-f`, `make bench`, benchmarks ciblés
  `odd_high_cycle_plus_low_hub/star` et
  `non_bipartite_high_graph_plus_low_hub/star`. Résultat observé :
  `mixed/star` garde `0` timeout et `0` incomplet jusqu'à `n=100` ; la famille
  non-cycle non-bipartie est rejetée en temps polynomial.
- Checkpoint T035 courant : commit contenant le générateur
  `even_high_cycle_plus_low_hub`, le certificat négatif
  `candidate_even_high_cycle_low_hub_obstruction`, et les régressions montrant
  que `C6` plus hub bas est négatif tandis que `C8` échappe au scan
  héréditaire `(4,5,6)`. Validation observée : tests
  candidats/générateurs/régressions ciblés, `make unit`, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`,
  et benchmark ciblé `even_high_cycle_plus_low_hub/star`. Résultat observé :
  `mixed/star` reste `0` timeout et `0` incomplet jusqu'à `n=100`; la famille
  cycle haut pair induit est rejetée en temps polynomial.
- Checkpoint T036 courant : commit contenant le diagnostic borné
  `low_hub_strong_ordering_report`, sans changement de `candidate.py`. Il teste
  expérimentalement la conjecture strong-ordering du cas binaire hub bas avec
  contrôles `C4`, `C6`, `C8`, `K3,3`, matching, chain/Ferrers, tree négatif,
  cas non applicables et limite factorielle. Validation observée :
  `tests/test_local_constraints.py`, probe exhaustive diagnostic `m=6`,
  `make unit`, `make quick`. Résultat observé : le diagnostic coïncide avec
  l'oracle exact jusqu'à `m<=5` et retrouve la frontière T035 à `m=6`.
- Checkpoint T037 courant : commit contenant
  `candidate_low_hub_strong_ordering_witness`, intégré seulement comme
  certificat positif vérifié. Les générateurs
  `chain_high_graph_plus_low_hub` et
  `complete_bipartite_high_graph_plus_low_hub` couvrent deux familles
  positives large-n ; les tests verrouillent le tree négatif, le PC-tree rigide
  non représentatif et `quasi_orders=[]`. Validation observée : tests ciblés
  candidats/générateurs/local-constraints/régressions, `make unit`,
  `make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
  `make bench`, plus benchmarks ciblés chain/complete low-hub star jusqu'à
  `n=80`. Résultat observé : `mixed/star` reste `0` timeout et `0` incomplet
  jusqu'à `n=100`; les familles positives ciblées sont acceptées sans timeout.
- Checkpoint T038 courant : commit contenant
  `passes_bad_side_precircular_cR` et
  `find_bad_side_precircular_cR_violation` dans `predicates.py`, utilisés par
  `candidate.py` et `low_hub_strong_ordering_report` pour valider les ordres en
  `O(n^3)` tout en gardant les tools d'oracle sur les quadruplets. Validation
  observée : tests ciblés prédicats/DP/candidate/local-constraints,
  probe local `6058` comparaisons, probe subagent `153291` comparaisons,
  `make unit`, `make quick`, `make hunt-counterexamples`, `make check`,
  `make bench-quick`, `make bench`, et benchmarks ciblés chain/complete
  low-hub star jusqu'à `n=100`. Résultat observé : `mixed/star` reste `0`
  timeout et `0` incomplet jusqu'à `n=100`, médiane `0.0275s` à `n=100`.
- Checkpoint T039 courant : commit contenant
  `matching_high_graph_plus_low_hub`, la priorité composante-alignée de
  `low_hub_strong_ordering_report`, et la correction du diagnostic pour les
  niveaux bas `0` hors diagonale. Validation observée : tests ciblés
  local-constraints/générateurs/candidate, `make unit`, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`,
  et benchmark ciblé matching low-hub star jusqu'à `n=101`. Résultat observé :
  les matchings permutés sont trouvés au premier couple d'ordres, `mixed/star`
  reste `0` timeout et `0` incomplet jusqu'à `n=100`, médiane `0.0267s` à
  `n=100`.
- Checkpoint T040 courant : commit contenant
  `iter_low_hub_strong_ordering_witnesses`, la recherche candidate de témoin
  strong-ordering représenté par un PC-tree non-star, et la borne de frontiers
  root-aware pour ne pas sauter des énumérations exactes canoniques. Il ajoute
  les régressions matching non-star `n=18`, matching raffiné `n=10` à `720`
  frontiers réelles, et faux silence local `I_x(v)` sur `C6 + hub` raffiné.
  Validation observée : tests ciblés candidate/local-constraints, `make unit`,
  `make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
  `make bench`, et probe ciblée matching low-hub star jusqu'à `n=101`. Résultat
  observé : `mixed/star` reste `0` timeout et `0` incomplet jusqu'à `n=100`,
  médiane `0.0265s` à `n=100`.
- Checkpoint T041 courant : commit contenant
  `permuted_chain_high_graph_plus_low_hub`,
  `low_hub_ferrers_strong_ordering_report`, et l'intégration candidate du
  certificat positif Ferrers/chain low-hub. Il ajoute les régressions chaîne
  permutée large, matching non-Ferrers, et PC-tree non-star où le témoin
  Ferrers canonique est non représenté mais un autre témoin existe. Validation
  observée : tests ciblés candidate/local-constraints/generators, `make unit`,
  `make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
  `make bench`, et benchmark ciblé chaîne Ferrers permutée jusqu'à `n=101`.
  Résultat observé : `mixed/star` reste `0` timeout et `0` incomplet jusqu'à
  `n=100`, médiane `0.0287s` à `n=100`; la chaîne Ferrers permutée star a `0`
  timeout et médiane `0.2606s` à `n=101`.
- Checkpoint T042 courant : commit contenant
  `permuted_disjoint_chain_high_graph_plus_low_hub`,
  `low_hub_component_ferrers_strong_ordering_report`, et l'intégration
  candidate du certificat positif pour unions de composantes Ferrers low-hub.
  Il ajoute les régressions trois composantes permutées, matching dégénéré,
  composantes désalignées, `low=0` avec hubs multiples, non-Ferrers, et PC-tree
  non-star où le témoin component-wise est non représenté. Validation observée :
  tests ciblés candidate/local-constraints/generators, probe exact petits cas,
  `make unit`, `make quick`, `make hunt-counterexamples`, `make check`,
  `make bench-quick`, `make bench`, et benchmark ciblé disjoint-chain star
  jusqu'à `n=101`. Résultat observé : `mixed/star` reste `0` timeout et `0`
  incomplet jusqu'à `n=100`, médiane `0.0295s` à `n=100`; la disjoint-chain
  star a `0` timeout et médiane `0.2433s` à `n=101`.
- Checkpoint T043 courant : commit contenant
  `pc_tree_guided_low_hub_matching_witness_report` et l'intégration candidate du
  certificat positif matching low-hub guidé par PC-tree. Il ajoute les
  régressions non-star T040/T042 devenues positives complètes, le cas `low=0`,
  les contrôles négatifs `C6/C8/tree`, et deux limites documentées :
  split-hubs `n=6` manqué sans rejet, et frontier tardive `n=8` qui exige
  `frontier_limit=80`. Validation observée : tests ciblés
  candidate/local-constraints/generators, `make unit`, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`.
  Résultat observé : `mixed/star` reste `0` timeout et `0` incomplet jusqu'à
  `n=100`, médiane `0.0314s` à `n=100`; le certificat T043 résout les
  matchings non-star ciblés avec `frontiers_sampled=0`.
- Checkpoint T044 courant : commit contenant le test de projection frontier
  dans `pc_tree_guided_low_hub_matching_witness_report`. Le certificat accepte
  un frontier représenté dont les cordes du matching haut croisent toutes après
  suppression des hubs, puis le revalide cR et `represents_order`. Il ajoute les
  régressions split-hubs `n=6` devenu positif, split-hubs large `n=12` côté
  candidate, et non-crossing C `n=6` négatif. Validation observée : tests ciblés
  candidate/local-constraints/generators, `make quick`,
  `make hunt-counterexamples`, `make check`, `make bench-quick`, `make bench`.
  Résultat observé : `mixed/star` reste `0` timeout et `0` incomplet jusqu'à
  `n=100`, médiane `0.03139s` à `n=100`; la frontier tardive `n=8` reste une
  limite à `frontier_limit=64`.
- Checkpoint T045 courant : commit contenant
  `exact_low_hub_matching_projection_search_report` et son intégration candidate
  bornée. Le rapport énumère paresseusement les ordres `seq + mate(seq)` avec
  hubs insérés, teste d'abord `represents_order`, puis cR, et retourne un
  négatif complet seulement si tous les candidats uniques sous la limite sont
  épuisés. Régressions ajoutées : frontier tardive `n=8` positive, rigide
  non-crossing `n=6` négatif, limite basse explicite, lazy hit `n=13`, et rejet
  candidate non-crossing `n=12`. Validation observée : tests ciblés
  candidate/local-constraints/generators, probe oracle `19` couples,
  `make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick`,
  `make bench`. Résultat observé : `mixed/star` reste `0` timeout et `0`
  incomplet jusqu'à `n=100`, médiane `0.03311s` à `n=100`.
- Checkpoint T046 courant : commit contenant
  `exact_low_hub_matching_projected_pc_tree_search_report` et son intégration
  candidate bornée avant T045. Le rapport énumère seulement les projections
  matching `seq + mate(seq)`, relève les hubs via la structure `P/C` du PC-tree
  original, puis vérifie cR et représentation. Régressions ajoutées : frontier
  tardive projetée, rigide non-crossing, limite de projections, facteur hubs,
  oracle petits PC-trees, rejet candidate avec `5` paires et `8` hubs, faux
  silence local `I_x(v)` minimal `n=5`, et contre-exemple side-only/2-SAT naïf.
  Validation observée : tests ciblés candidate/local-constraints/régressions,
  probe oracle `14` couples, `make quick`, `make hunt-counterexamples`,
  `make check`, `make bench-quick`, `make bench`. Résultat observé :
  `mixed/star` reste `0` timeout et `0` incomplet jusqu'à `n=100`, médiane
  `0.03504s` à `n=100`.
- Checkpoint T047 courant : commit contenant la compilation bad-side
  support-local hors candidate. `compile_bad_side_nogoods_support_local`
  énumère le produit des domaines de `quartet_support_paths` par atom, puis
  déduplique par signature effective de pruning. Régressions ajoutées :
  reconstructeur de projection d'atom, wrapping, égal-distance, limite de
  support, collision de canonicalisation globale, solveur pruné support-local.
  Validation observée : `tests/test_sat_like_experiments.py`, probe
  support-local `577` couples sans mismatch, `make bench-csp-quick`
  (`0` mismatch, `0` support mismatch, `0` signature mismatch), `make quick`,
  `make check`, `make bench-quick`, `make bench`. Résultat observé : le
  benchmark interne passe de `31616` nogoods atom-labellisés à `2904`
  signatures support-local, avec ratio médian `support_vs_old_scan_ratio=0.25`,
  mais la compilation support-local reste plus lente sur les très petits arbres
  du quick benchmark ; `mixed/star` reste `0` timeout et `0` incomplet jusqu'à
  `n=100`, médiane `0.03458s` à `n=100`.
- Checkpoint T048 courant : commit contenant la compilation bad-side groupée
  par support hors candidate. `compile_bad_side_nogoods_grouped_support_local`
  énumère chaque produit de domaines de support une seule fois, teste les atoms
  du groupe et déduplique par signature effective. Validation observée :
  `tests/test_sat_like_experiments.py` (`31 passed`), probe indépendant
  `130` cas sans mismatch, `make bench-csp-quick` (`192` lignes,
  `0` mismatch, `0` support mismatch, `0` grouped mismatch,
  `0` signature mismatch), `make quick`, `make check`. Résultat observé :
  produit support T047 `72256` contre produit groupé `6224`, ratio médian
  `0.11111`, mêmes `2904` signatures que T047, mais
  `total_grouped_atom_checks=72256`; le prochain progrès doit donc réduire les
  tests atom-par-atom ou prouver une borne sur la taille des groupes.
- Checkpoint T049 courant : commit contenant la variante first-hit groupée hors
  candidate. `compile_bad_side_nogoods_grouped_first_hit_support_local`
  s'arrête au premier atom violé pour chaque affectation de support, en
  conservant les mêmes signatures effectives que T048/T047. Validation
  observée : `tests/test_sat_like_experiments.py` (`39 passed`), probe
  indépendant `130` cas sans mismatch, subagent contre-exemples `220` cas sans
  mismatch, `make bench-csp-quick` (`192` lignes, `0` mismatch,
  `0` first-hit mismatch, `0` mismatch de signatures), `make quick`,
  `make check`. Résultat observé : `atom_checks` passe de `72256` à `41872` sur
  la gate CSP rapide, mais les diagnostics `atom`/`pair` deviennent des
  représentants de premier témoin et ne sont plus exhaustifs.
- Checkpoint T050 courant : commit contenant le profil first-hit hors
  candidate. Les métriques `first_hit_*` mesurent hits, no-hit, positions de
  premier hit et checks dépensés/sauvés, sans changer les signatures de pruning.
  Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`41 passed`), `make quick` (`223 passed`, puis `JUSTE`), `make check`,
  `make bench-csp-quick` (`192` lignes, `0` mismatch,
  `0` first-hit mismatch, `0` mismatch de signatures), probe par familles
  `n=4..8`, et audit subagent de non-interférence. Résultat observé :
  `3320/6224` affectations de support sont no-hit sur la gate CSP rapide et
  consomment `30520` checks ; les métriques sont dépendantes de l'ordre de scan,
  pas des invariants mathématiques.
- Checkpoint T051 courant : commit contenant
  `bad_side_grouped_support_outcome_profile` hors candidate. Le profil mesure
  hit/no-hit par support groupé, tranches unaires pures et test
  pair-side/composantes de mauvais témoins. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`44 passed`), `make bench-csp-quick` (`192` lignes, `0` mismatch,
  `0` first-hit mismatch, `profile_pair_side_split_mismatches=0`),
  `make quick` (`226 passed`, puis `JUSTE`), `make check`, et
  `make bench-quick` (`0` timeout, `0` incomplet). Résultat
  observé : le test pair-side est exact sur la gate mais plus coûteux que
  first-hit (`profile_pair_side_split_work_ratio=1.7732`) ; les tranches
  unaires couvrent `1888/3320` no-hit globalement mais `0%` sur les familles
  cycliques de la gate rapide.
- Checkpoint T052 courant : commit contenant `_witness_side_cache_key` et le
  profil cached witness-side hors candidate, plus le corpus de références sous
  `docs/references/`. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`45 passed`), `make bench-csp-quick` (`192` lignes, `0` mismatch,
  `profile_pair_side_split_mismatches=0`), `make quick` (`227 passed`, puis
  `JUSTE`), `make check`, `make bench-quick` (`40/40` runs, `0` timeout,
  `0` incomplet). Résultat observé : cache simple des
  côtés `49558` checks, ratio `1.1836x` first-hit ; modèle
  bitset-composantes `27846` checks, ratio `0.6650x`; la clé triple complète
  est protégée par un test de choix imbriqué.
- Checkpoint T053 courant : commit contenant le profil bitset/composantes réel
  hors candidate. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`49 passed`), régressions ciblées (`60 passed`), `make bench-csp-quick`
  (`192` lignes, `0` mismatch,
  `profile_pair_side_split_bitset_mismatches=0`), `make quick`
  (`232 passed`, puis `JUSTE`), `make check`, `make bench-quick`
  (`40/40` runs, `0` timeout, `0` incomplet). Résultat observé : le
  classifieur local est exact sur la gate, mais le coût réel bitset est
  `44936` checks (`1.0732x` first-hit) contre une projection théorique
  `27822` checks (`0.6645x`). `candidate.py` n'a pas été modifié.
- Checkpoint T054 courant : commit contenant la mesure de cardinalité des états
  de masques hors candidate. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`49 passed`), `make bench-csp-quick` (`192` lignes, `0` mismatch,
  `component_mask_state_mismatches=0`), probe stress `n=8` (`30` lignes,
  `0` mismatch), `make quick` (`232 passed`, puis `JUSTE`), `make check`,
  `make bench-quick` (`40/40` runs, `0` timeout, `0` incomplet). Résultat
  observé : `2920` états pour `6224` affectations (`0.4692`), bucket moyen
  `2.1315`, bucket max `4`; quotient exact mais faible, pas DP compacte.
  `candidate.py` n'a pas été modifié.
- Checkpoint T055 courant : commit contenant les quotients d'états de masques
  hors candidate. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`50 passed`), `make bench-csp-quick` (`192` lignes, `0` mismatch),
  probe stress `n=8` (`30` lignes, `0` mismatch), `make quick`
  (`233 passed`, puis `JUSTE`), `make check` (`JUSTE`), `make bench-quick`
  (`40/40` runs, `0` timeout, `0` incomplet). Résultat observé :
  `mask_multiset` compresse à `0.3959` sur la gate rapide sans état mixte,
  tandis que `side_blind_schema` descend à `0.1250` mais produit `358` états
  mixtes ; le cas minimal `cycle_metric(4)`/`balanced_pc_tree(4, kind="C")`
  est régressé. Aucun changement dans `candidate.py`.
- Checkpoint T056 courant : commit contenant le diagnostic de collisions de
  contexte des quotients hors candidate. Validation observée :
  `tests/test_regression_counterexamples.py tests/test_sat_like_experiments.py
  tests/test_csp_internal_benchmark.py` (`64 passed`),
  `make bench-csp-quick` (`192` lignes, `0` mismatch), probe stress `n=8`
  (`20` lignes, `0` mismatch), `make quick` (`236 passed`, puis `JUSTE`),
  `make check` (`JUSTE`), `make bench-quick` (`40/40` runs, `0` timeout,
  `0` incomplet). Résultat observé : `mask_multiset` a `856` collisions de
  contexte sur la gate CSP rapide et un contre-exemple global `n=5` avec même
  `mask_multiset=(1,2)` mais décisions cR différentes est régressé. Les
  collisions de `full` montrent que les états de masques fermés ne suffisent
  pas comme états DP autonomes. Aucun changement dans `candidate.py`.
- Checkpoint T057 courant : commit contenant le diagnostic de réponses ouvertes
  one-hop hors candidate. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`54 passed`), `make bench-csp-quick` (`192` lignes, `0` mismatch,
  `74` lignes incomplètes visibles sur le profil ouvert borné), probe stress
  `n=8` (`20` lignes, `0` mismatch), `make quick` (`238 passed`, puis
  `JUSTE`), `make check` (`JUSTE`), `make bench-quick` (`40/40` runs,
  `0` timeout, `0` incomplet). Résultat observé :
  `mask_multiset_plus_boundary` supprime les buckets à réponses de bord
  mélangées mesurés tout en gardant un ratio `0.4291` sur la gate CSP rapide ;
  `local_boundary_response` est plus compressé (`0.2625`) mais reste seulement
  one-hop et non prouvé récursif. Aucun changement dans `candidate.py`.
- Checkpoint T058 courant : commit contenant le diagnostic de portée PC-tree par
  quartets hors candidate. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`61 passed`), `make bench-csp-quick` (`192` lignes, `0` mismatch,
  `quartet_scope_projection_mismatches=0`), `make quick` (`245 passed`, puis
  `JUSTE`), `make check` (`JUSTE`) et `make bench-quick` (`40/40` runs, `0`
  timeout, `0` incomplet). Résultat observé : sur la gate CSP rapide, les `2688`
  quartets ont un support structurel conservateur de taille `3`, mais une
  portée effective de type toujours `2` et une portée effective d'acceptation
  `0` ou `2`; aucun changement dans `candidate.py`.
- Checkpoint T059 courant : commit contenant le rapport de relations effectives
  de quartets hors candidate. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`67 passed`), `make bench-csp-quick` (`192` lignes supportées, `0`
  mismatch, `quartet_relation_validation_mismatches=0`), `make quick`
  (`251 passed`, puis `JUSTE`), `make check` (`JUSTE`) et
  `make bench-quick` (`40/40` runs, `0` timeout, `0` incomplet). Résultat
  observé : le CSP relationnel fusionné valide exactement le filtre cR sur le
  scaffold supporté, expose un graphe primal/treewidth, distingue le sous-cas
  2-SAT des domaines non booléens `P3`, et ne modifie pas `candidate.py`.
- Checkpoint T060 courant : commit contenant le solveur 2-SAT des relations
  effectives booléennes hors candidate. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`73 passed`), `make bench-csp-quick` (`192` lignes supportées, `0`
  mismatch, `quartet_relation_validation_mismatches=0`, `192` lignes 2-SAT
  complètes, `143` SAT, `49` UNSAT par clause vide, `0` échec de témoin),
  `make quick` (`257 passed`, puis `JUSTE`), `make check` (`JUSTE`) et
  `make bench-quick` (`40/40` runs, `0` timeout, `0` incomplet). Résultat
  observé : le sous-cas booléen du CSP relationnel est résolu par 2-SAT dans
  le scaffold supporté ; les domaines non booléens restent refusés comme
  `not_two_sat_candidate` et `candidate.py` n'a pas été modifié.
- Checkpoint T061 courant : commit contenant le solveur DP/treewidth des
  relations effectives hors candidate. Validation observée :
  `tests/test_sat_like_experiments.py tests/test_csp_internal_benchmark.py`
  (`78 passed`), `make bench-csp-quick` (`192` lignes supportées, `0`
  mismatch, `quartet_relation_validation_mismatches=0`, `186` lignes DP
  complètes, `137` SAT, `49` UNSAT, `6` incomplètes par cap de treewidth,
  `0` échec de témoin), `make quick` (`262 passed`, puis `JUSTE`),
  `make check` (`JUSTE`) et `make bench-quick` (`40/40` runs, `0` timeout,
  `0` incomplet). Résultat observé : les domaines non booléens `P3` sont
  résolus dans le scaffold quand la treewidth exacte est sous cap ; les caps
  restent incomplets et `candidate.py` n'a pas été modifié.
- Checkpoint T062 courant : commit contenant le générateur `p3_block_tree(k)`
  et le benchmark de stress de largeur. Validation observée :
  `tests/test_pc_tree_frontiers.py tests/test_sat_like_experiments.py
  tests/test_csp_internal_benchmark.py` (`89 passed`),
  `make bench-width-stress` (`12` lignes, `0` mismatch de validation,
  `11` lignes DP complètes, `1` incomplète par `treewidth_cap_exceeded`,
  treewidth upper bound max `5`, `0` échec de témoin),
  `make quick` (`264 passed`, puis `JUSTE`), `make check` (`JUSTE`) et
  `make bench-quick` (`40/40` runs, `0` timeout, `0` incomplet). Résultat
  observé : `p3_block_tree(k)` rend la largeur de T061 visible comme paramètre
  limitant ; `candidate.py` n'a pas été modifié.
- Checkpoint R002/T063 courant : commit contenant le recadrage documentaire de
  la revue GPT 5.5 Pro bad-side/quartets après critique utilisateur. Validation
  observée : `make quick` (`264 passed`, puis `JUSTE`). Aucun changement
  algorithmique ni modification de `candidate.py`.
- Checkpoint R003/T064 courant : commit contenant le benchmark single `P`-node
  et la revue red-team sur la taille de domaine. Validation observée :
  test ciblé single-P (`1 passed`), tests ciblés
  `tests/test_csp_internal_benchmark.py tests/test_pc_tree_frontiers.py`
  (`13 passed`), `make bench-single-p-stress` (`30` lignes,
  `treewidth_zero_rows=30`, `max_domain_size=181440`), `make quick`
  (`265 passed`, puis `JUSTE`) et `make bench-quick` (`40/40` runs, `0`
  timeout, `0` incomplet). `candidate.py` n'a pas été modifié.
- Checkpoint T065 courant : commit contenant le catalogue de relations non
  booléennes entre blocs `P3`. Validation observée : test ciblé relation
  catalog (`1 passed`), `make bench-relation-catalog` (`20` lignes complètes,
  `0` mismatch, `38` relations binaires non booléennes, `27` hashes distincts),
  tests ciblés `tests/test_csp_internal_benchmark.py` (`4 passed`),
  `make quick` (`266 passed`, puis `JUSTE`) et `make bench-quick` (`40/40`
  runs, `0` timeout, `0` incomplet). `candidate.py` n'a pas été modifié.
- Checkpoint T066 courant : commit contenant le minage des formes de profils
  relationnels non booléens entre nœuds `P`. Validation observée : test ciblé
  shape search (`1 passed`), `make bench-relation-shapes` (`38` profils
  binaires non booléens, `27` hashes, `0` mismatch,
  `candidate_gadget_instances=0`), tests ciblés
  `tests/test_csp_internal_benchmark.py` (`5 passed`), `make quick`
  (`267 passed`, puis `JUSTE`) et `make bench-quick` (`40/40` runs,
  `0` timeout, `0` incomplet). Résultat observé : formes structurées mais
  aucun gadget positif sans parasite restrictif. `candidate.py` n'a pas été
  modifié.
- Checkpoint T067 courant : commit contenant le diagnostic de composition des
  relations fonctionnelles non booléennes. Validation observée : test ciblé
  chain probe (`1 passed`), `make bench-relation-chains` (`40` lignes
  complètes, `0` mismatch, `2` relations `permutation_like` sans parasite
  restrictif, `1` ligne `interaction_unsat`), tests ciblés
  `tests/test_csp_internal_benchmark.py` (`6 passed`), `make quick`
  (`268 passed`, puis `JUSTE`) et `make bench-quick` (`40/40` runs,
  `0` timeout, `0` incomplet). `candidate.py` n'a pas été modifié.
- Checkpoint T068 courant : commit contenant la minimisation du noyau
  `interaction_unsat`. Validation observée : test ciblé unsat-core
  (`1 passed`), tests ciblés `tests/test_csp_internal_benchmark.py`
  (`7 passed`), `make bench-relation-unsat-cores` (`40` lignes complètes,
  `0` mismatch, `1` ligne `interaction_unsat`, `min_core_size=2`),
  `make quick` (`269 passed`, puis `JUSTE`) et `make bench-quick` (`40/40`
  runs, `0` timeout, `0` incomplet). Résultat observé : le noyau minimal est un
  conflit local entre une unaire non booléenne et une binaire
  `sparse_partial_matching`; `candidate.py` n'a pas été modifié.
- Checkpoint T069 courant : commit contenant le contrôle promise-aware borné
  des profils `permutation_like`. Validation observée : test ciblé
  permutation-like (`1 passed`), `make bench-permutation-like` (`128` lignes
  complètes, `0` mismatch, `11` profils `permutation_like`, `11`
  parasite-free, `0` anomalie), tests ciblés
  `tests/test_csp_internal_benchmark.py` (`8 passed`), `make quick`
  (`270 passed`, puis `JUSTE`) et `make bench-quick` (`40/40` runs,
  `0` timeout, `0` incomplet). Résultat observé : en `n=6`, les profils
  bijectifs parasite-free coïncident avec l'exactitude quasi-circulaire du
  scaffold ; `candidate.py` n'a pas été modifié.
- Checkpoint T070 courant : commit contenant le probe de composition multi-blocs
  des profils `permutation_like`. Validation observée : test ciblé composition
  (`1 passed`), `make bench-permutation-composition` (`192` lignes complètes,
  `0` mismatch, `6` lignes `permutation_like`, `0` candidat de composition),
  tests ciblés `tests/test_csp_internal_benchmark.py` (`9 passed`),
  `make quick` (`271 passed`, puis `JUSTE`) et `make bench-quick` (`40/40`
  runs, `0` timeout, `0` incomplet). Résultat observé : les bijections restent
  isolées en `k=2`, disparaissent en `k=3`, ou sont bloquées par parasites en
  `k=4`; `candidate.py` n'a pas été modifié.
- Checkpoint T071 courant : commit contenant le probe de composantes de toutes
  les relations binaires non booléennes. Validation observée : test ciblé
  component probe (`1 passed`), `make bench-relation-components` (`192` lignes
  complètes, `0` mismatch, `617` relations binaires non booléennes, `127`
  lignes multi-arêtes, `0` multi-arête parasite-free,
  `max_component_edges=6`), tests ciblés `tests/test_csp_internal_benchmark.py`
  (`10 passed`), `make quick` (`272 passed`, puis `JUSTE`) et
  `make bench-quick` (`40/40` runs, `0` timeout, `0` incomplet). Résultat
  observé : les réseaux non booléens existent hors `permutation_like`, mais
  restent tous bloqués par parasites dans `paired_farthest/P3x{k}` ;
  `candidate.py` n'a pas été modifié.
- Checkpoint T072 courant : commit contenant le probe des conflits
  `sparse_partial_matching`. Validation observée : test ciblé sparse
  (`1 passed`), `make bench-sparse-matching` (`40` lignes complètes,
  `0` mismatch, `21` relations sparse, `10` conflits projection/unaire vides,
  `3` composantes sparse binaires insatisfiables, `28` lignes avec
  `constant_reject`), tests ciblés `tests/test_csp_internal_benchmark.py`
  (`11 passed`), `make quick` (`273 passed`, puis `JUSTE`) et
  `make bench-quick` (`40/40` runs, `0` timeout, `0` incomplet). Résultat
  observé : le noyau T068 est confirmé comme conflit unaire+binaire local ;
  les composantes binaires sparse restent contaminées par constantes ;
  `candidate.py` n'a pas été modifié.
- Checkpoint T073 courant : commit contenant le probe de suppression des
  constantes pour les noyaux binaires `sparse_partial_matching`. Validation
  observée : test ciblé sparse binary core (`1 passed`),
  `make bench-sparse-binary-cores` (`40` lignes complètes, `0` mismatch,
  `3` composantes sparse zéro, `0` ligne sparse zéro sans `constant_reject`,
  `3` composantes avec projection partagée vide, `max_zero_component_edges=2`),
  tests ciblés `tests/test_csp_internal_benchmark.py` (`12 passed`),
  `make quick` (`274 passed`, puis `JUSTE`) et `make bench-quick` (`40/40`
  runs, `0` timeout, `0` incomplet). Résultat observé : les noyaux sparse
  binaires sont des conflits de projections partagées, mais restent tous
  accompagnés de `constant_reject` dans ce sweep ; `candidate.py` n'a pas été
  modifié.

- Checkpoint T074 courant : commit contenant le probe de couverture
  positive-only des solveurs de quartets et la réparation 2-SAT pour domaines
  non booléens inactifs. Validation observée : tests ciblés (`2 passed`),
  `make bench-quartet-coverage` (`80` lignes complètes, `0` mismatch,
  `14` positives treewidth validées, `0` nouveau témoin positif,
  `0` échec de témoin, `max_treewidth_exact=5`), smoke `k=6`
  (`4` lignes, `0` nouveau positif), tests ciblés élargis (`91 passed`),
  `make quick` (`276 passed`, puis `JUSTE`) et `make bench-quick` (`40/40`
  runs, `0` timeout, `0` incomplet). Résultat observé : intégration
  positive-only non justifiée pour l'instant ; `candidate.py` n'a pas été
  modifié.

- Checkpoint T075 courant : commit contenant le probe de supports exacts des
  obstructions de frontiers. Validation observée : test ciblé local
  (`1 passed`), `make bench-frontier-obstructions` (`40` lignes complètes,
  `0` troncature, `624` frontiers, `494` non-cR, `494` non-cR avec projections
  locales silencieuses, `494` obstructions multi-niveaux profilées,
  `support_path_count_histogram={"3": 494}`), tests locaux
  `tests/test_local_constraints.py` (`43 passed`), `make quick`
  (`277 passed`, puis `JUSTE`) et `make bench-quick` (`40/40` runs,
  `0` timeout, `0` incomplet). `candidate.py` n'a pas été modifié.

- Checkpoint T076 courant : commit contenant l'audit strict Algorithm 5.2
  contre énumération exacte bornée. Validation observée : test ciblé audit
  (`1 passed`), `make bench-strict-algorithm52` (`360` lignes complètes,
  `0` ligne incomplète, `0` mismatch, `0` ordre strict quasi/pre-circular/cR
  manqué, `138` lignes positives strict circular exactes,
  `0` limite candidate atteinte), tests stricts complets (`23 passed`),
  `make quick` (`279 passed`, puis `JUSTE`) et `make bench-quick` (`40/40`
  runs, `0` timeout, `0` incomplet). `candidate.py` n'a pas été modifié.

- Checkpoint T077 courant : commit contenant le probe de couverture
  positive-only stricte large-n. Validation observée : test ciblé coverage
  (`1 passed`), `make bench-strict-positive-coverage` (`708` lignes,
  `204` témoins stricts validés, `0` nouveau positif vs candidate,
  `40` lignes candidate incomplètes, `0` limite strict candidate,
  `0` échec de validation de témoin, `152` lignes avec stricts non représentés,
  `max_strict_seconds ~= 2.14s`), tests stricts complets (`24 passed`),
  `make quick` (`280 passed`, puis `JUSTE`) et `make bench-quick` (`40/40`
  runs, `0` timeout, `0` incomplet). `candidate.py` n'a pas été modifié.

- Checkpoint T078 courant : commit contenant la reformulation clean-side par
  seuil pour ordre fixé. Validation observée : `tests/test_predicates.py`
  (`20 passed`), `make bench-threshold-roundness` (`53` lignes, `6072` ordres
  vérifiés, `0` mismatch vs bad-side et cR directe, `0` troncature,
  `max_seconds ~= 0.0307`), `make quick` (`283 passed`, puis `JUSTE`) et
  `make bench-quick` (`40/40` runs, `0` timeout, `0` incomplet).
  `candidate.py` n'a pas été modifié.

- Checkpoint T079 courant : commit contenant le learner borné de
  PC-représentabilité scaffold des ordres cR. Validation observée :
  `tests/test_pc_tree_learning.py` (`9 passed`),
  `make bench-cr-pc-representability` (`39` lignes complètes, `0` incomplète,
  `19` représentables, `10` cibles vides, `10` contre-exemples informatifs,
  premier contre-exemple en `n=5 paired_farthest`, `max_seconds ~= 0.6084`),
  `make quick` (`292 passed`, puis `JUSTE`) et `make bench-quick` (`40/40`
  runs, `0` timeout, `0` incomplet).
  `candidate.py` n'a pas été modifié.

- Checkpoint T080 courant : commit contenant l'audit non enraciné du
  contre-exemple T079. Validation observée : `tests/test_unrooted_pc_tree.py`
  (`4 passed`), `make bench-unrooted-pc-representability` (`3` lignes
  complètes, `0` incomplète, `2` représentables, `t079_complete=True`,
  `t079_representable=False`, `893` candidats inspectés, `93` familles
  distinctes, `max_seconds ~= 1.0228`), `make quick` (`296 passed`, puis `JUSTE`) et `make bench-quick` (`40/40`
  runs, `0` timeout, `0` incomplet). `candidate.py` n'a pas été modifié.

- Checkpoint T081 courant : commit contenant le probe de profondeur locale des
  obstructions cR induites. Validation observée :
  `tests/test_local_obstructions.py` (`7 passed`),
  `make bench-local-obstruction-depth` (`71` lignes, `64` complètes,
  `34` négatives, `11` négatives de profondeur au moins `5`,
  `max_min_negative_subset_size=6`, `0` négative invisible sous cap décidée
  seulement par oracle global), `make quick` (`303 passed`, puis `JUSTE`) et
  `make bench-quick` (`40/40` runs, `0` timeout, `0` incomplet).
  `candidate.py` n'a pas été modifié.

- Checkpoint T082 courant : commit contenant le probe chirotope same-side
  high-girth et le document de transmission chercheur
  `docs/research_handoff_2026-05-23.md`. Validation observée :
  `tests/test_cyclic_order_sat.py`
  (`7 passed`), `make bench-chirotope-high-girth` (`140` lignes,
  `140` complètes, `90` négatives, `2` candidates high-girth,
  `0` mismatch oracle, `max_min_negative_subset_size=6`,
  `max_checked_orders=20160`), `make quick` (`310 passed`, puis `JUSTE`) et
  `make bench-quick` (`40/40` runs, `0` timeout, `0` incomplet).
  `candidate.py` n'a pas été modifié.

- Checkpoint R004 courant : commit contenant le triage documentaire des notes
  externes du 2026-05-31 et le screenshot manuscrit vendorisé. Validation
  observée avant modification : `make quick` (`310 passed`, puis `JUSTE`) ;
  validation finale : `rtk make quick` (`310 passed`, puis `JUSTE`).
  Modification documentaire seulement ; `candidate.py`, l'oracle et les tests
  ne sont pas modifiés.

- Checkpoint T083 courant : commit contenant la projection bad-side complète
  sur les nœuds PC et le probe R004 correspondant. Validation observée :
  compilation Python de `local_constraints.py` et
  `pc_bad_side_projection_probe.py` réussie, tests ciblés
  `tests/test_local_constraints.py` et `tests/test_regression_counterexamples.py`
  (`58 passed`), `make bench-r004-bad-side-projections` (`130` lignes,
  `112` complètes, `18` tronquées par limite de frontiers, `0` troncature
  d'obligations, `82` lignes farthest silencieuses mais bad-side actives,
  `77` lignes multi-niveaux, `max_obligation_count=378`) et `make quick`
  (`313 passed`, puis `JUSTE`). `candidate.py` n'a pas été modifié.

- Checkpoint T084 courant : commit contenant le test empirique largeur 4 des
  P-nœuds. Validation observée : compilation Python de
  `width4_experiments.py` et `pc_pnode_width4_probe.py` réussie, tests ciblés
  `tests/test_width4_experiments.py` (`6 passed`),
  `make bench-pnode-width4` (`103` lignes, `103` complètes, `35` lignes avec
  nœud testé, `0` nœud réfuté, `0` nœud unsupported,
  `max_frontiers_seen=20160`, `max_missing_order_count=0`) et `make quick`
  (`319 passed`, puis `JUSTE`). `candidate.py` n'a pas été modifié.

- Checkpoint T085 courant : commit contenant le probe du gadget manuscrit 4
  blocs x 2 feuilles. Validation observée : tests ciblés
  `tests/test_handwritten_gadget_probe.py` (`3 passed`),
  `make bench-handwritten-gadget` (`730` lignes, `730` positives pour le `P`
  libre, `416` lignes où un `C` fixé devient négatif,
  `256` lignes où `C=ABCD` est négatif, `196` lignes farthest silencieuses mais
  bad-side actives, `max_root_four_branch_obligation_count=6`) et `make quick`
  (`322 passed`, puis `JUSTE`). `candidate.py` n'a pas été modifié.

- Checkpoint T086 courant : commit contenant le probe d'interface P-nœud à
  ordre de branches fixé. Validation observée : compilation Python de
  `interface_experiments.py` et `pc_pnode_interface_probe.py` réussie, tests
  ciblés `tests/test_interface_experiments.py` (`3 passed`),
  `make bench-pnode-interface` (`9` lignes, `9` complètes, `8` factorisées,
  `1` réfutée, `max_false_product_count=2`,
  `max_minimal_coupling_support_size=2`) et `make quick` (`325 passed`, puis
  `JUSTE`). `candidate.py` n'a pas été modifié.

- Checkpoint T087 courant : commit contenant le probe d'interface P-nœud avec
  contexte extérieur explicite. Validation observée : compilation Python de
  `interface_experiments.py` et `pc_pnode_context_interface_probe.py` réussie,
  tests ciblés `tests/test_interface_experiments.py` (`6 passed`),
  `make bench-pnode-context-interface` (`5` lignes, `5` complètes,
  `4` factorisées, `1` réfutée, `max_false_product_count=2`,
  `max_minimal_coupling_support_size=2`) et `make quick` (`328 passed`, puis
  `JUSTE`). `candidate.py` n'a pas été modifié.

- Checkpoint T088 courant : commit contenant le probe d'arité des relations
  résiduelles d'interface. Validation observée : compilation Python de
  `interface_experiments.py` et `pc_residual_interface_probe.py` réussie, tests
  ciblés `tests/test_residual_interface_probe.py` et
  `tests/test_interface_experiments.py` (`8 passed`),
  `make bench-residual-interface` (`24157` cas two-level complets,
  `2514` relations non triviales, histogramme d'arité minimale
  `{1: 24103, 2: 54}`, `0` cas au-delà du binaire) et `make quick`
  (`330 passed`, puis `JUSTE`). `candidate.py` n'a pas été modifié.

- Checkpoint T089 courant : commit contenant le stress d'interfaces
  résiduelles plus riches. Validation observée : compilation Python de
  `pc_residual_interface_stress_probe.py` réussie, tests ciblés
  `tests/test_residual_interface_stress_probe.py`,
  `tests/test_residual_interface_probe.py` et
  `tests/test_interface_experiments.py` (`10 passed`),
  `make bench-residual-interface-stress` (`P2x4`: `5000` essais,
  `384` relations non triviales, histogramme `{1: 4981, 2: 19}` ;
  `P3x3`: `1500` essais, `198` relations non triviales, histogramme
  `{1: 1478, 2: 22}` ; `0` cas au-delà du binaire) et `make quick`
  (`332 passed`, puis `JUSTE`). `candidate.py` n'a pas été modifié.

- Checkpoint T090 courant : commit contenant le probe de projection de relation
  résiduelle sur variables de bord après branches cachées. Validation observée :
  compilation Python de `pc_boundary_residual_projection_probe.py` réussie,
  tests ciblés `tests/test_boundary_residual_projection_probe.py`
  (`2 passed`), `make bench-boundary-residual-projection` (`P2x4` :
  `20000` cas, histogramme de bord `{1: 9315, 2: 168}` ; `P2x5` :
  `20000` cas, histogramme de bord `{1: 37708, 2: 792}` ; random
  multi-niveaux `P2x4` : `500` essais sans projection non triviale ;
  `0` cas au-delà du binaire) et `make quick` (`334 passed`, puis `JUSTE`).
  `candidate.py` n'a pas été modifié.

- Checkpoint T091 courant : commit contenant le lab circle/interlacement des
  contraintes `same_side` pleinement visibles sur P-nœuds. Validation observée :
  compilation Python de `circle_graph_experiments.py` et
  `pc_circle_graph_lab_probe.py` réussie, tests ciblés
  `tests/test_circle_graph_experiments.py` (`4 passed`),
  `make bench-circle-graph-lab` (`120` lignes, `120` complètes,
  `80` lignes avec P-nœuds, `35` lignes avec contraintes locales,
  `0` ordre cR projeté manquant localement, `17` lignes localement UNSAT,
  `25` supersets locaux tous vacus, `0` superset contraint,
  `max_forbidden_chord_pair_count=140`) et `make quick` (`338 passed`, puis
  `JUSTE`).
  `candidate.py` n'a pas été modifié.

- Checkpoint T092 courant : commit contenant le lab des obligations bad-side
  partielles autour de T091. Validation observée : compilation Python de
  `partial_obligation_experiments.py` et `pc_partial_obligation_lab_probe.py`
  réussie, tests ciblés `tests/test_partial_obligation_experiments.py`
  (`3 passed`), `make bench-partial-obligation-lab` (`120` lignes,
  `120` complètes, `80` lignes avec P-nœuds, `0` ligne
  `global_not_contained`, `52` nœuds en superset local vacu, `52/52` avec
  information partielle ou multi-niveau, `0` superset local contraint,
  `max_non_chord_obligation_count=159`) et `make quick` (`341 passed`, puis
  `JUSTE`).
  `candidate.py` n'a pas été modifié.

## Rollback

Si une modification régresse et que la cause n’est pas claire :

1. noter la régression dans `docs/experiment_log.md` ;
2. inspecter `git diff` ;
3. corriger si la cause est claire ;
4. sinon revenir au dernier commit green indiqué ici.

Ne pas effacer les rapports ou contre-exemples importants pendant le rollback.
