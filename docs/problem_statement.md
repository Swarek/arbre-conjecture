# Problem statement

Soit `X = {0, ..., n-1}` et `D` une matrice de dissimilarité `n x n`,
symétrique, à diagonale nulle. Un ordre circulaire `beta` est une permutation de
`X` considérée modulo rotation et renversement.

Un PC-arbre `T` représente une famille compacte d’ordres circulaires :

- un nœud `P` autorise toute permutation de ses branches ;
- un nœud `C` fixe un ordre cyclique local, à renversement près ;
- les feuilles sont les éléments de `X`.

Le problème principal étudié ici est un problème d’existence :

```text
input  : D et éventuellement un PC-arbre T
output : True/False, et idéalement un ordre témoin beta si True
sens   : True ssi il existe beta représenté par T qui est circular Robinson pour D
```

Le PC-arbre fourni par Hsu/McConnell représente les ordres quasi-circulaires,
c’est-à-dire les ordres où les boules métriques sont des arcs circulaires. Le
PC-arbre seul ne suffit donc pas : la circularité Robinson dépend aussi des
valeurs de `D`, notamment des ensembles de plus lointains voisins.

Trois tâches doivent rester séparées :

- tester si un ordre donné est circular Robinson ;
- tester s’il existe un bon ordre dans le PC-arbre ;
- tester si tous les ordres du PC-arbre sont bons.

L’objectif principal de ce dépôt est la deuxième tâche, l’existence dans une
représentation compacte.
