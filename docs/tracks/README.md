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
| B - DP sur PC-tree | `piste_b_dp_pc_tree.md` | Signatures compactées réfutées sur familles stress |
| C - SAT/CSP | `piste_c_sat_csp.md` | Benchmark interne ajouté ; compilation encore dominante |
| D - Circular-ones / intersection | `piste_d_circular_ones.md` | Non testée expérimentalement |
| E - Obstructions farthest/quartets | `piste_e_farthest_quartets.md` | Farthest seul réfuté ; cR quartets restent centraux |
| F - Complexité / sous-cas | `piste_f_complexity_subcases.md` | Sous-cas universel + témoins positifs intégrés ; Algorithm 5.2 strict en diagnostic |

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

Le Goal courant exige au moins 50 pistes/tentatives actives documentées avant un
abandon honnête. Cette table sert de compteur lisible ; elle ne remplace pas les
gates de correction.
