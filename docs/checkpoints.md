# Checkpoints

Un commit stable doit satisfaire :

- `make quick` passe ;
- `make bench-quick` écrit un rapport JSON ou documente explicitement les
  timeouts/incomplétudes ;
- `docs/experiment_log.md` décrit l’hypothèse, la commande et la conclusion ;
- aucun contre-exemple connu n’est supprimé.

## Dernier commit green

- Initial setup : hash à reporter depuis `git log` après création du checkpoint
  initial.
- Statut attendu : baseline exacte `n <= 8`, placeholder incomplet au-delà.
- Validation initiale : `make quick` vert et `make bench-quick` sans timeout,
  avec runs incomplets explicitement comptés pour `n > 8`.
- Checkpoint Goal 2026-05-22 : à reporter après commit. Diagnostics
  d’obstructions, contre-exemples farthest, familles Piste F et benchmark ciblé
  ajoutés. Validation observée : `make quick`, `make hunt-counterexamples`,
  `make check`, `make bench-quick`, `make bench-piste-f`.
- Checkpoint Prop. 4.5 : à reporter après commit. Diagnostic d’ordre fixé
  quasi-circulaire ajouté. Validation observée : `make quick`, `make check`,
  probe exhaustif `n <= 5` sur ordres quasi-circulaires sans désaccord.

## Rollback

Si une modification régresse et que la cause n’est pas claire :

1. noter la régression dans `docs/experiment_log.md` ;
2. inspecter `git diff` ;
3. corriger si la cause est claire ;
4. sinon revenir au dernier commit green indiqué ici.

Ne pas effacer les rapports ou contre-exemples importants pendant le rollback.
