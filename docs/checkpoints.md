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
- Checkpoint T010 courant : commit contenant le scaffold CSP à domaines locaux
  `P/C`; son hash est à lire avec `git log -1` et doit être reporté dans le
  compte rendu final de la session. Validation observée : `make quick`,
  `make check`, `make bench-quick`, probe CSP directe sans désaccord sur 1600
  instances.

## Rollback

Si une modification régresse et que la cause n’est pas claire :

1. noter la régression dans `docs/experiment_log.md` ;
2. inspecter `git diff` ;
3. corriger si la cause est claire ;
4. sinon revenir au dernier commit green indiqué ici.

Ne pas effacer les rapports ou contre-exemples importants pendant le rollback.
