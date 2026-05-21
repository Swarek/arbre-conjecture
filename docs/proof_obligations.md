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
