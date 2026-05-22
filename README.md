# PC-tree circular Robinson research setup

Ce dépôt prépare une boucle reproductible pour étudier le problème suivant :
décider si un PC-arbre représentant des ordres quasi-circulaires admissibles
d’un espace de dissimilarité fini contient au moins un ordre circular Robinson.

Entrée principale : une matrice symétrique `D` sur `X = {0, ..., n-1}`, à
diagonale nulle, et éventuellement un PC-arbre `T`. Sortie visée : `True/False`
et, si `True`, un ordre circulaire témoin représenté par `T`.

Le dépôt ne prétend pas résoudre le problème général. La candidate initiale est
une baseline : brute force exacte pour `n <= 8`, puis échantillonnage incomplet
documenté au-delà. Les tests servent à protéger les expériences, pas à remplacer
une preuve.

Commandes principales :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make unit
make quick
make check
make hunt-counterexamples
make bench-quick
make bench
make bench-piste-f
make acceptance
```

`make quick` lance les tests unitaires puis l’oracle exact rapide. `make check`
lance la correction forte sur petites instances. `make bench-quick` écrit un
rapport JSON dans `reports/complexity_report_quick.json`; `make bench` lance une
version plus lourde.

`make hunt-counterexamples` lance une recherche aléatoire plus longue avec
shrink. Elle est faite pour les moments où une candidate semble marcher et doit
être attaquée avant d’être considérée comme un progrès stable.

`make bench-piste-f` lance des benchmarks ciblés sur deux familles explicites :
`permuted_cycle` comme sous-cas planted-cycle, et `paired_farthest` comme famille
hard-looking à appariements farthest. Ces familles ne sont pas ajoutées au
`mixed` par défaut.

Dans `tools/pc_circular_conjecture_test.py`, la sortie `JUSTE` signifie seulement
que la candidate a été égale à l’oracle exact sur les instances générées par ce
script. Cela ne prouve pas la correction globale.

Les prochains travaux doivent remplacer la baseline par un algorithme prouvé ou
par des sous-cas clairement énoncés, en maintenant des contre-exemples,
benchmarks et obligations de preuve à jour.

Pour reprendre la boucle de recherche, lire `docs/agent_loop_guide.md`.
