# Piste F - Complexité et sous-cas

## Question

Quels sous-cas semblent tractables, et quelles familles stressent les filtres
locaux ou les heuristiques de recherche ?

## Famille planted-cycle

Statut : générateur ajouté.

`permuted_cycle` construit un cycle metric puis relabellise les points. C’est un
sous-cas polynomial-looking : le graphe des distances 1 devrait révéler le cycle
planté, puis le problème se rapproche d’un test de représentation de cet ordre
par le PC-tree.

Usage :

```bash
make bench-piste-f
```

Résultat observé star :

- `n=8` : `1/2520` ordre cR valide ;
- `24/2520` ordres passent farthest, donc farthest a déjà 23 faux positifs.

## Famille paired-farthest

Statut : générateur ajouté.

`paired_farthest` crée des paires farthest uniques. C’est une famille
hard-looking parce qu’elle met une pression d’alternance sur les gros nœuds `P`.

Résultat observé star :

- `n=6` : `3/60` ordres cR valides, `4/60` ordres farthest-pass ;
- `n=8` : `12/2520` ordres cR valides, `24/2520` ordres farthest-pass.

Résultat observé mixed :

- aucun ordre cR valide dans les diagnostics `n=4,6,8` du premier benchmark.

## Artefacts

- `permuted_cycle_metric`;
- `paired_farthest_matching`;
- `instance_by_kind(..., kind="permuted_cycle")`;
- `instance_by_kind(..., kind="paired_farthest")`;
- `--diagnostics-up-to` dans `tools/pc_circular_complexity_benchmark.py`;
- `make bench-piste-f`.

## Prochaine action

Utiliser `paired_farthest` pour casser tout filtre local ou farthest-like.
Utiliser `permuted_cycle` comme sous-cas où un futur solver devrait reconnaître
un témoin caché sans brute force star.
