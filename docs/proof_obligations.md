# Proof obligations

Pour marquer un candidat algorithme comme vraie solution, il faut remplir au
minimum les obligations suivantes :

1. Montrer que les contraintes générées sont nécessaires.
2. Montrer qu’elles sont suffisantes.
3. Montrer que l’algorithme ne manque aucun ordre représenté par le PC-arbre.
4. Montrer que le témoin renvoyé est bien représenté.
5. Montrer la complexité en fonction de `n` et `|T|`.
6. Traiter les cas non stricts et les égalités.
7. Expliquer les cas dégénérés de la condition farthest-neighbor.

Chaque point doit être classé comme théorème prouvé, conséquence directe,
conjecture, preuve expérimentale ou intuition. Tant que ces obligations ne sont
pas remplies, le solver reste une candidate expérimentale.

## État courant

### Condition farthest-neighbor brute

Statut : preuve expérimentale + contre-exemples de petite taille enregistrés.

La condition de croisement des cordes `x x'`, `y y'` avec `x' in F_x` et
`y' in F_y`, telle qu’implémentée actuellement par
`passes_farthest_crossing_condition`, ne peut pas être utilisée seule comme
critère de décision.

Limites observées :

- Non-nécessité en cas non strict : la matrice égal-distance à 4 points est
  circular Robinson pour tout ordre, mais la condition farthest brute échoue
  car tous les voisins sont farthest et créent des cordes dégénérées.
- Non-suffisance même dans un cas strict : une instance à 4 points avec toutes
  les distances hors diagonale distinctes passe la condition farthest brute pour
  l’ordre `[0, 1, 2, 3]`, mais viole la condition pre-circular cR.

Ces exemples sont verrouillés dans `tests/test_regression_counterexamples.py`.
Toute piste utilisant les farthest-neighbors doit donc préciser les cas
dégénérés, ajouter d’autres contraintes, ou restreindre explicitement le sous-cas
traité.

### Projection locale des obstructions

Statut : outil expérimental.

`measure_obstruction_support` projette les points d’un témoin cR/farthest sur les
branches des nœuds internes du PC-tree. Cela permet de mesurer si une obstruction
est visible localement dans un nœud `P` ou `C`. Cet outil ne prouve aucune
suffisance : il sert à tester les pistes A/B/C et à chercher des collisions où
deux contextes ont la même signature locale mais une validité cR différente.
