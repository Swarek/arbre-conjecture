# Pistes de recherche

Ce dossier est le tableau de bord lisible par piste. `docs/experiment_log.md`
reste le journal chronologique global ; les fichiers ci-dessous regroupent les
idées, essais, résultats, contre-exemples et prochaines actions par axe.

## Index

| Piste | Fichier | Statut courant |
| --- | --- | --- |
| A - Contraintes locales P/C | `piste_a_local_pc_constraints.md` | Diagnostic utile ajouté ; pas solver |
| B - DP sur PC-tree | `piste_b_dp_pc_tree.md` | Signature proposée ; à falsifier |
| C - SAT/CSP | `piste_c_sat_csp.md` | Scaffold domaines locaux ajouté ; non compact |
| D - Circular-ones / intersection | `piste_d_circular_ones.md` | Non testée expérimentalement |
| E - Obstructions farthest/quartets | `piste_e_farthest_quartets.md` | Farthest seul réfuté ; cR quartets restent centraux |
| F - Complexité / sous-cas | `piste_f_complexity_subcases.md` | Deux familles stress ajoutées |

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

Le Goal courant exige au moins 50 pistes/tentatives actives documentées avant un
abandon honnête. Cette table sert de compteur lisible ; elle ne remplace pas les
gates de correction.
