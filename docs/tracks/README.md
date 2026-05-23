# Pistes de recherche

Ce dossier est le tableau de bord lisible par piste. `docs/experiment_log.md`
reste le journal chronologique global ; les fichiers ci-dessous regroupent les
idées, essais, résultats, contre-exemples et prochaines actions par axe.

Note transverse : `docs/external_analysis_digest.md` conserve une analyse GPT
5.5 Pro fournie par l'utilisateur. Elle ajoute surtout quatre rappels à ne pas
perdre : cas strict polynomial potentiel, diagnostic d'universalité séparé de
l'existence, projection locale des quartets au nœud décisif, et question des
ensembles `I_x(v)` sur les branches d'un gros nœud `P`.

## Index

| Piste | Fichier | Statut courant |
| --- | --- | --- |
| A - Contraintes locales P/C | `piste_a_local_pc_constraints.md` | Rapport `I_x(v)` implémenté comme diagnostic ; pas solver |
| B - DP sur PC-tree | `piste_b_dp_pc_tree.md` | Bad-side exact ordre fixé ; pas encore de signature compacte |
| C - SAT/CSP | `piste_c_sat_csp.md` | Nogoods bad-side divisent les atomes ; compilation encore dominante |
| D - Circular-ones / intersection | `piste_d_circular_ones.md` | Boules validées pour quasi ; arcs bad-witness naïfs réfutés |
| E - Obstructions farthest/quartets | `piste_e_farthest_quartets.md` | Farthest seul réfuté ; bad-witness one-side donne des certificats hub bas |
| F - Complexité / sous-cas | `piste_f_complexity_subcases.md` | Sous-cas universel, témoins positifs, PC-tree borné exact et certificats hub bas |

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

Le Goal courant exige au moins 50 pistes/tentatives actives documentées avant un
abandon honnête. Cette table sert de compteur lisible ; elle ne remplace pas les
gates de correction.
