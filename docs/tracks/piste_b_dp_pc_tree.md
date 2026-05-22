# Piste B - Programmation dynamique sur PC-tree

## Question

Existe-t-il une signature de sous-arbre qui permette de composer les frontiers
sans réénumérer toutes les permutations ?

## Intuition

La condition cR peut se lire par cordes `{x,z}` : les témoins mauvais pour une
corde ne doivent pas apparaître sur les deux arcs circulaires. Une signature de
sous-frontier pourrait résumer les témoins déjà présents sur les côtés gauche et
droit d’un bloc.

## Proposition actuelle

Statut : conjecture à falsifier.

Signature proposée par exploration :

- endpoints d’une frontier orientée `sigma` : `(sigma[0], sigma[-1])`;
- pour chaque paire globale `{x,z}`, définir `bad(x,z,w)` lorsque
  `max(D[x][w], D[w][z]) > D[x][z]`;
- enregistrer seulement les bits de présence de témoins mauvais selon leur côté
  dans le bloc.

Raison possible :

La condition cR est équivalente à interdire des témoins mauvais sur les deux arcs
pour une même corde. Des bits de côté pourraient donc se composer par `OR`.

## Plan de falsification

Pour `n <= 8` :

1. Énumérer les frontiers internes d’un même nœud.
2. Grouper deux frontiers différentes ayant la même signature.
3. Les insérer dans les mêmes contextes externes.
4. Comparer `is_precircular_order_cR(D, context + sigma)` et
   `is_precircular_order_cR(D, context + tau)`.
5. Toute différence réfute la signature.

## Tests à créer

- collisions de signature dans `src/pc_circular/solvers/dp_experiments.py`;
- comparaison à `exact_oracle_pc_tree`;
- enregistrement d’un contre-exemple minimal si collision trouvée.

## Prochaine action

Implémenter un mode expérimental `find_signature_collision` avant tout usage
dans `candidate.py`.
