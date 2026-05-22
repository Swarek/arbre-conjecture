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
- Checkpoint T019 courant : commit contenant `represents_order` non énumératif
  pour les ordres fixés du scaffold PC-tree, l'extension du témoin
  minimum-cycle aux PC-trees non-star représentés, et le contre-exemple
  régressé où un min-cycle cR non représenté ne doit pas être accepté.
  Validation observée : `make unit`, probe membership `11837` checks,
  `make quick`, `make check`, `make hunt-counterexamples`,
  `make bench-piste-f`, `make bench-quick`, `make bench` (`0` timeout, `42`
  incomplets visibles, fit polynomial empirique `p ~= 3.25`).

## Rollback

Si une modification régresse et que la cause n’est pas claire :

1. noter la régression dans `docs/experiment_log.md` ;
2. inspecter `git diff` ;
3. corriger si la cause est claire ;
4. sinon revenir au dernier commit green indiqué ici.

Ne pas effacer les rapports ou contre-exemples importants pendant le rollback.
