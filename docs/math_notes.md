# Math notes

Une dissimilarité finie est une matrice `D` symétrique, à diagonale nulle et à
valeurs non négatives. Aucune inégalité triangulaire n’est supposée.

Un ordre circulaire est une permutation de `X` modulo rotation et renversement.
Un arc est un sous-ensemble contigu dans cet ordre circulaire, en autorisant le
passage par la coupure.

Un ordre est quasi-circulaire pour `D` lorsque toute boule
`B(x,r) = {y : d(x,y) <= r}` est un arc circulaire. Le PC-arbre de Hsu/McConnell
compacte précisément les ordres quasi-circulaires admissibles.

Un ordre est circular Robinson si les distances respectent la monotonie
circulaire attendue. Dans ce dépôt, le test exact d’un ordre utilise la condition
pre-circular/circular Robinson : pour tout `x ≺ y ≺ z ≺ t`,

```text
d(x,z) >= min(max(d(x,y), d(y,z)), max(d(x,t), d(t,z))).
```

Un PC-tree contient des nœuds `P` et `C`. Un nœud `P` autorise une permutation
arbitraire des branches. Un nœud `C` fixe un ordre cyclique local à renversement
près. Les feuilles sont les points de `X`.

Pour chaque point `x`, `F_x` désigne l’ensemble de ses plus lointains voisins.
Une caractérisation utile dit que, pour tout `x,y`, `x' in F_x`, `y' in F_y`,
les cordes `xx'` et `yy'` doivent alterner/croiser dans l’ordre circulaire, sauf
cas dégénérés non stricts.

Conséquences algorithmiques :

- tester un ordre donné est facile par énumération des quadruplets cycliques ;
- tester l’existence dans un PC-arbre compact est le cœur du problème ;
- les égalités et grands ensembles `F_x` ne doivent pas être balayés comme des
cas stricts ordinaires ;
- un benchmark positif ne remplace pas la preuve de nécessité et suffisance.
