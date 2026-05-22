# Piste B - Programmation dynamique sur PC-tree

## Question

Existe-t-il une signature de sous-arbre qui permette de composer les frontiers
sans réénumérer toutes les permutations ?

## Intuition

La condition cR peut se lire par cordes `{x,z}` : les témoins mauvais pour une
corde ne doivent pas apparaître sur les deux arcs circulaires. Une signature de
sous-frontier pourrait résumer les témoins déjà présents sur les côtés gauche et
droit d’un bloc.

## Diagnostic fixed-order bad-side

Statut : conséquence directe pour ordre fixé, preuve expérimentale renforcée par
tests exhaustifs petits.

Pour une paire `{a,b}` et un témoin `w`, définir :

```text
bad(a,b,w) := max(D[a][w], D[w][b]) > D[a][b]
```

Alors un ordre circulaire fixé viole la condition pre-circular cR ssi il existe
une paire `{a,b}` telle qu'un des deux arcs ouverts entre `a` et `b` contient un
témoin mauvais, et l'autre arc ouvert contient aussi un témoin mauvais.

Raison : la violation cR pour un quadruplet cyclique `a, y, b, t` est exactement

```text
D[a][b] < min(max(D[a][y], D[y][b]), max(D[a][t], D[t][b]))
```

ce qui équivaut à `bad(a,b,y)` et `bad(a,b,t)`, avec `y` et `t` situés sur les
deux arcs opposés. La réciproque donne le même quadruplet cyclique. Le `>` strict
traite les égalités : un témoin avec valeur égale à `D[a][b]` ne crée pas de
violation.

Artefact : `src/pc_circular/solvers/dp_experiments.py` contient
`find_bad_side_cr_violation`, `passes_bad_side_cr_test` et
`bad_side_signature`.

Limite : ce diagnostic concerne un ordre complet fixé. Il ne décide pas encore
l'existence dans un PC-tree compact.

## Proposition de signature DP

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

## Résultats T014

Tests ajoutés :

- égal-distance non strict : aucun témoin mauvais ;
- exemple `quasi_circular_not_circular_four_point` : certificat
  `(0, 1, 2, 3)` retrouvé ;
- cycle metric naturel : aucun certificat ;
- égalités strictes : `max(...) == D[a][b]` n'est pas mauvais ;
- exhaustif `n=4`, valeurs `{1,2,3}`, tous les ordres ;
- random borné `n=5,6`, tous les ordres.

Probe hors tests principal : exhaustif `n=4,5`, valeurs `{1,2,3}`, puis random
`n=6,7`, sans désaccord sur `715875` ordres/matrices comparés.

Probe subagent contre-exemples : exhaustif `n=4,5`, puis familles
`random/cycle/permuted_cycle/block/ultrametric/equal/non_strict/
paired_farthest/mixed` pour `n=6..9`, `926775` comparaisons, `0` désaccord.
La seule variante réfutée est `bad >= D[a][b]` : elle rejette à tort les cas
égal-distance.

Retour subagents :

- preuve fixed-order confirmée ;
- risque DP principal : une signature naïve par paires globales expose jusqu'à
  `3^Theta(n^2)` états ;
- expérience suivante recommandée : chercher des collisions de signatures de
  sous-frontiers ou mesurer le ratio `#signatures / #frontiers` sur arbres
  balanced et familles `random` / `paired_farthest`.

## Prochaine action

Implémenter un mode expérimental `find_signature_collision` avant tout usage
dans `candidate.py`.
