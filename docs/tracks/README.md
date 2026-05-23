# Pistes de recherche

Ce dossier est le tableau de bord lisible par piste. `docs/experiment_log.md`
reste le journal chronologique global ; les fichiers ci-dessous regroupent les
idées, essais, résultats, contre-exemples et prochaines actions par axe.

Note transverse : `docs/external_analysis_digest.md` conserve une analyse GPT
5.5 Pro fournie par l'utilisateur. Elle ajoute surtout quatre rappels à ne pas
perdre : cas strict polynomial potentiel, diagnostic d'universalité séparé de
l'existence, projection locale des quartets au nœud décisif, et question des
ensembles `I_x(v)` sur les branches d'un gros nœud `P`.

Note transverse 2026-05-23 : `docs/external_reviews/gpt55_bad_side_quartet_strategy_2026-05-23.md`
conserve la revue externe centree bad-side/quartets. Elle est explicitement
routee vers plusieurs pistes : bad-side fixed-order, CSP de quartets, 2-SAT,
treewidth, circular-ones/universalite, gadgets non booleens et collisions T057.
Elle ne remplace ni les tests ni les obligations de preuve.

## Index

| Piste | Fichier | Statut courant |
| --- | --- | --- |
| A - Contraintes locales P/C | `piste_a_local_pc_constraints.md` | Rapport `I_x(v)` implémenté comme diagnostic ; pas solver |
| B - DP sur PC-tree | `piste_b_dp_pc_tree.md` | Bad-side exact ordre fixé ; pas encore de signature compacte |
| C - SAT/CSP | `piste_c_sat_csp.md` | Solveurs 2-SAT puis DP treewidth des relations effectives hors candidate |
| D - Circular-ones / intersection | `piste_d_circular_ones.md` | Boules validées pour quasi ; arcs bad-witness naïfs réfutés |
| E - Obstructions farthest/quartets | `piste_e_farthest_quartets.md` | Farthest seul réfuté ; bad-witness one-side donne des certificats hub bas |
| F - Complexité / sous-cas | `piste_f_complexity_subcases.md` | Permutation-like parasite-free et interaction UNSAT observées dans le scaffold |

## Règle d’édition

Pour chaque itération non triviale, mettre à jour :

- le fichier de piste concerné ;
- `docs/experiment_log.md` pour la chronologie ;
- `docs/proof_obligations.md` si un résultat touche une preuve, une limite ou
  une conjecture ;
- les tests/régressions si un contre-exemple est découvert.

Chaque fichier de piste doit séparer : théorème prouvé, conséquence directe,
conjecture, preuve expérimentale, intuition et prochaine action.

## Tentatives documentées

| ID | Date | Piste | Résultat | Artefact |
| --- | --- | --- | --- | --- |
| T001 | 2026-05-21 | Setup | Harnais initial créé | `make quick`, `make bench-quick` |
| T002 | 2026-05-22 | Goal workflow | Boucle contre-exemple-first définie | `make hunt-counterexamples` |
| T003 | 2026-05-22 | A/E | Farthest brut réfuté comme solver | régressions 4 points |
| T004 | 2026-05-22 | A | Projection locale des obstructions ajoutée | `measure_obstruction_support` |
| T005 | 2026-05-22 | F | Familles `permuted_cycle` et `paired_farthest` ajoutées | `make bench-piste-f` |
| T006 | 2026-05-22 | E/D | Sources PDF intégrées ; Prop. 4.4 séparée de la condition farthest brute | `docs/source_notes.md` |
| T007 | 2026-05-22 | Sources | PDF de référence conservés dans le repo | `docs/source_materials/` |
| T008 | 2026-05-22 | E | Prop. 4.5 testée sur ordres quasi-circulaires petits | `passes_farthest_prop_4_5_order_test` |
| T009 | 2026-05-22 | C | Prop. 4.5 mesurée comme filtre nogood sur frontiers énumérées | `prop45_nogood_frontier_report` |
| T010 | 2026-05-22 | C | Domaines locaux `P/C` et CSP cR direct expérimentaux | `solve_nogood_csp(source="cr")` |
| T011 | 2026-05-22 | C | Nogoods compilés de quartets cR sur supports locaux | `compile_cr_nogoods` |
| T012 | 2026-05-22 | C | Backtracking pruné par signatures de nogoods complètes | `solve_pruned_nogood_csp` |
| T013 | 2026-05-22 | C | Benchmark interne compile/solve/direct/pruning | `make bench-csp-quick` |
| T014 | 2026-05-23 | B | cR fixed-order reformulé par mauvais témoins sur deux arcs | `passes_bad_side_cr_test` |
| T015 | 2026-05-23 | B | Signature de bloc mesurée ; compression faible hors égal-distance | `block_signature_bucket_report` |
| T016 | 2026-05-23 | F | Sous-cas `|B(a,b)| <= 1` intégré à la candidate | `candidate_universal_bad_witness_bound_all_orders` |
| T017 | 2026-05-23 | Candidate | Témoins positifs échantillonnés marqués complets | `candidate_validated_sampled_witness` |
| T018 | 2026-05-23 | F/Sources | Témoin minimum-cycle star ajouté ; faux positif `n=6` régressé ; capture Prop. 4.4 vendored | `candidate_minimum_distance_cycle_witness` |
| T019 | 2026-05-23 | F/D | Membership PC-tree non énumératif pour certifier les témoins minimum-cycle non-star | `represents_order` |
| T020 | 2026-05-23 | F/E | Témoin paired-farthest structurel ajouté ; garde représentation PC-tree régressé | `candidate_paired_farthest_matching_witness` |
| T021 | 2026-05-23 | A/B/F | Paired-farthest non-star : canonique incomplet, high-cross insuffisant, diagnostics locaux/DP non décisifs | régressions `paired_farthest` `n=6` |
| T022 | 2026-05-23 | A/D/F | Projection des farthest sets ajoutée ; sous-cas strict préparé mais non intégré | `project_farthest_sets_to_pc_nodes` |
| T023 | 2026-05-23 | F | Prédicats stricts d'ordre fixé et rapport strict borné ajoutés ; pas d'intégration candidate | `strict_order_report` |
| T024 | 2026-05-23 | F | Générateur Algorithm 5.2 strict filtré ; récupère les ordres stricts exacts sur probes bornées | `strict_algorithm52_report` |
| T025 | 2026-05-23 | D/F | Diagnostic boules non triviales comme contraintes circular-ones ; ball_arc égale quasi sur probes | `strict_ball_circular_ones_report` |
| T026 | 2026-05-23 | D/E | Contraintes d'arcs bad-witness testées : one-side exact, `B` arc trop fort, `B union endpoints` invalide | `bad_witness_arc_constraints_report` |
| T027 | 2026-05-23 | B/C/E | Nogoods bad-side par paire compilés ; mêmes frontiers cR, moitié moins d'atomes/nogoods sur probes | `compile_bad_side_nogoods` |
| T028 | 2026-05-23 | F/C | Sous-cas PC-tree à frontiers bornées intégré à la candidate ; décisions exactes n>8 quand l'espace est petit | `candidate_exact_bounded_pc_tree_frontiers` |
| T029 | 2026-05-23 | F/API | Sous-cas `quasi_orders` fini borné intégré ; décision exacte relative à la famille explicite | `candidate_exact_bounded_quasi_orders` |
| T030 | 2026-05-23 | F/Benchmark | Attribution des placeholders `mixed/star` par sous-famille ; les 42 incomplets forts sont tous `random` | `resolved_kind_*` benchmark JSON |
| T031 | 2026-05-23 | F/E | Certificat négatif héréditaire par sous-matrice 4 points ; `make bench` passe à 0 incomplet | `candidate_small_forbidden_submatrix_obstruction` |
| T032 | 2026-05-23 | E/F | Contre-exemple 5-points à la caractérisation 4-locale ; certificat héréditaire étendu aux tailles 4 et 5 | `four_local_non_cr_core` |
| T033 | 2026-05-23 | E/F | Contre-exemple 6-points à la caractérisation 5-locale ; cycle haut impair plus hub bas certifié négatif | `candidate_odd_high_cycle_low_hub_obstruction` |
| T034 | 2026-05-23 | E/F | Certificat cycle impair généralisé à tout graphe haut non biparti avec hub bas | `candidate_non_bipartite_high_graph_low_hub_obstruction` |
| T035 | 2026-05-23 | E/F | Les graphes hauts bipartis ne suffisent pas ; cycle haut pair induit `>=6` certifié négatif | `candidate_even_high_cycle_low_hub_obstruction` |
| T036 | 2026-05-23 | E/F | Diagnostic strong-ordering borné pour le cas binaire hub bas ; pas intégré à la candidate | `low_hub_strong_ordering_report` |
| T037 | 2026-05-23 | E/F | Diagnostic strong-ordering intégré seulement comme témoin positif vérifié et représenté | `candidate_low_hub_strong_ordering_witness` |
| T038 | 2026-05-23 | B/F | Test fixed-order bad-side exact promu en prédicat `O(n^3)` pour accélérer les validations candidate | `passes_bad_side_precircular_cR` |
| T039 | 2026-05-23 | E/F | Matching low-hub permuté ajouté ; priorité composante-alignée et garde `low=0` pour le diagnostic strong-ordering | `matching_high_graph_plus_low_hub` |
| T040 | 2026-05-23 | E/F/A/D | Recherche de témoin strong-ordering représenté dans PC-tree non-star ; faux silence local `I_x(v)` régressé | `iter_low_hub_strong_ordering_witnesses` |
| T041 | 2026-05-23 | E/F | Sous-cas chain/Ferrers low-hub permuté formalisé comme certificat positif vérifié | `permuted_chain_high_graph_plus_low_hub` |
| T042 | 2026-05-23 | E/F | Union de composantes chain/Ferrers low-hub certifiée positive component-wise | `low_hub_component_ferrers_strong_ordering_report` |
| T043 | 2026-05-23 | E/F | Témoin matching low-hub guidé par PC-tree ; limites split-hubs/frontier-limit régressées | `pc_tree_guided_low_hub_matching_witness_report` |
| T044 | 2026-05-23 | E/F | Projection frontier matching low-hub ; hubs séparés traités si un frontier croisé est inspecté | `pc_tree_projected_matching_frontier_found` |
| T045 | 2026-05-23 | E/F/C | Recherche exacte bornée des projections matching low-hub ; négatifs complets seulement sous limite explicite | `exact_low_hub_matching_projection_search_report` |
| T046 | 2026-05-23 | B/C/E/F/A | Relèvement PC-tree des projections matching low-hub sans énumérer les placements de hubs ; contre-exemples aux règles locales/2-SAT naïves | `exact_low_hub_matching_projected_pc_tree_search_report` |
| T047 | 2026-05-23 | C/B/F | Compilation bad-side support-local ; mêmes signatures de pruning que la compilation complète sur probes, coût déplacé vers `sum_support_products` | `compile_bad_side_nogoods_support_local` |
| T048 | 2026-05-23 | C/B/F | Compilation bad-side groupée par support ; même signatures que T047, produit support rapide réduit mais `atom_checks` inchangé | `compile_bad_side_nogoods_grouped_support_local` |
| T049 | 2026-05-23 | C/B/F | Variante first-hit : mêmes signatures que T048, `atom_checks` réduit, diagnostics atoms/pairs volontairement non exhaustifs | `compile_bad_side_nogoods_grouped_first_hit_support_local` |
| T050 | 2026-05-23 | C/B/F | Profil first-hit : le coût restant est dominé par les affectations no-hit, pas seulement par les hits tardifs | métriques `first_hit_*` |
| T051 | 2026-05-23 | C/B/F | Profil support hit/no-hit : pair-side exact sur la gate, mais tranches unaires et recomputation par composantes insuffisantes comme compression | `bad_side_grouped_support_outcome_profile` |
| T052 | 2026-05-23 | C/B/F | Cache des côtés par support triple : cache simple encore trop cher, modèle bitset-composantes prometteur | `_witness_side_cache_key` |
| T053 | 2026-05-23 | C/B/F | Profil bitset/composantes réel : exact mais encore plus cher que first-hit en coût réel ; la projection reste prometteuse | `_pair_side_bitset_outcome` |
| T054 | 2026-05-23 | C/B/F | Cardinalité des états de masques : quotient local exact mais faible, environ facteur 2 seulement | `component_mask_state_*` |
| T055 | 2026-05-23 | C/B/F | Quotients d'états de masques : quelques quotients locaux compressent mieux, mais les contrôles sans masques deviennent mixtes | `component_mask_quotients` |
| T056 | 2026-05-23 | B/C/F | Collisions de contexte : `mask_multiset` et même l'état de masques complet ne sont pas des états DP autonomes | `component_mask_quotient_context_collision_profile` |
| T057 | 2026-05-23 | B/C/F | Signature d'obligations ouvertes one-hop : compression visible mais diagnostic borné et encore non récursif | `component_mask_open_boundary_profile` |
| R001 | 2026-05-23 | B/C/D/E/F | Revue externe globale post-T057 re-routée vers cinq pistes, pas seulement collision T057 | `docs/external_reviews/gpt55_global_strategy_2026-05-23.md` |
| R002 | 2026-05-23 | B/C/D/E/F | Revue externe bad-side/quartets recadrée après critique utilisateur : T057 reste une piste, pas le plan unique | `docs/external_reviews/gpt55_bad_side_quartet_strategy_2026-05-23.md` |
| T058 | 2026-05-23 | C/F/E | Rapport de portée PC-tree par quartets : support conservateur taille 3, portée effective observée `<=2` sur la gate | `quartet_pc_scope_report` |
| T059 | 2026-05-23 | C/F/E | Relations effectives de quartets fusionnées : validation cR, graphe primal, 2-SAT booléen et catalogue non booléen séparés | `quartet_effective_relation_report` |
| T060 | 2026-05-23 | C/F | Solveur 2-SAT exact sur les relations effectives booléennes ; SAT/UNSAT et témoins vérifiés hors candidate | `solve_quartet_2sat` |
| T061 | 2026-05-23 | C/F | DP/treewidth exacte bornée sur relations effectives, incluant les domaines non booléens `P3` | `solve_quartet_treewidth_csp` |
| T062 | 2026-05-23 | C/F | Stress `p3_block_tree(k)` ajouté ; largeur croissante et cap incomplet visibles dans un JSON | `make bench-width-stress` |
| R003 | 2026-05-23 | C/F | Revue red-team : treewidth faible ne suffit pas si le domaine `P` est factoriel | `docs/external_reviews/gpt55_red_team_domain_warning_2026-05-23.md` |
| T064 | 2026-05-23 | C/F | Stress single `P`-node : treewidth `0`, domaine `(n-1)!/2`, énumération bornée visible | `make bench-single-p-stress` |
| T065 | 2026-05-23 | F/C | Catalogue de relations non booléennes `P3` : diversité et parasites visibles | `make bench-relation-catalog` |
| T066 | 2026-05-23 | F/C | Minage des formes de relations non booléennes : classes structurées mais aucun gadget parasite-free | `make bench-relation-shapes` |
| T067 | 2026-05-23 | F/C | Composition fonctionnelle : `permutation_like` sans parasite restrictif et interaction UNSAT | `make bench-relation-chains` |
| T068 | 2026-05-23 | F/C | Noyau UNSAT minimal d'interaction : conflit unaire plus `sparse_partial_matching`, diagnostic matérialisé seulement | `make bench-relation-unsat-cores` |
| T069 | 2026-05-23 | F/C | Contrôle promise-aware borné : `permutation_like` parasite-free seulement quand `P3/P3` égale les ordres quasi exacts en `n=6` | `make bench-permutation-like` |

Le Goal courant exige au moins 50 pistes/tentatives actives documentées avant un
abandon honnête. Cette table sert de compteur lisible ; elle ne remplace pas les
gates de correction.
