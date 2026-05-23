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

## Résultats T015

Statut : preuve expérimentale d'une limite de compacité pour cette signature.

Artefacts ajoutés :

- `block_bad_side_signature` : signature de bloc orienté avec endpoints,
  masques `inside/external` et masques `inside/inside` ;
- `forced_bad_side_pairs_in_block` : paires déjà mauvaises sur les deux côtés du
  bloc ;
- `block_signature_bucket_report` : métriques `#signatures / #frontiers`,
  plus gros bucket et frontiers forcées ;
- `find_signature_collision` : cherche deux frontiers de même signature qui
  divergent dans un même contexte externe.

Probe borné sur blocs de taille `4,5,6`, univers `n=6,7,8`, familles
`equal/cycle/block/random/paired_farthest` :

- `equal` compresse fortement : ratio `0.5`, `0.1667`, puis `0.0417` ;
- `cycle` est déjà injectif sur ces blocs : ratio `1.0` ;
- `block` compresse partiellement : ratios observés `0.5667..0.8333` ;
- `random` est quasi injectif : ratios observés `0.95..1.0` ;
- `paired_farthest` est quasi injectif : ratios observés `0.9944..1.0` ;
- aucune collision réelle trouvée dans les contextes testés ;
- les collisions avec signature volontairement faible et endpoints-only sont
  détectées, donc le chercheur de collisions est opérationnel.
- probe subagent indépendante : collisions de signature simples trouvées, mais
  aucune collision sémantique sur `37924` checks de même contexte ; ratios
  équilibrés `random` dans `0.936121..1.0` et `paired_farthest` dans
  `0.949627..1.0`.

Interprétation :

Cette signature est utile pour comprendre les contraintes, mais elle est trop
fine sur les familles stress. Elle ressemble davantage à une réénumération
encodée qu'à une compression DP exploitable.

## Prochaine action

Ne pas intégrer cette signature dans `candidate.py`. La suite Piste B doit soit
proposer une signature moins globale, soit être mise en pause au profit de
Piste F/sous-cas. Une expérience raisonnable restante est de chercher un
sous-cas où les masques se factorisent, par exemple degré PC-tree borné ou
familles laminaire/equal-block.

## Résultats T027

Statut : reformulation CSP exacte pour ordre fixé, pas compression DP.

Les nogoods bad-side par paire reprennent directement le diagnostic T014 :
pour chaque `{a,b}`, deux témoins mauvais `y,t` séparés par les endpoints
créent les atomes interdits `(a,y,b,t)` et `(a,t,b,y)`. Cette forme évite les
quartets numériques redondants mais conserve le même support de quatre labels.

Observation : sur les probes bornées, cette forme divise par deux les atomes et
nogoods par rapport aux quartets ordonnés, mais ne diminue pas le nombre de
branches prunées dans le backtracking post-compilation. L'information reste
quartet-like et la compilation est encore découverte par énumération complète.

Conclusion : T027 clarifie l'état exact "mauvais témoins par paire" et fournit
une meilleure représentation pour Piste C, mais ne débloque pas encore une
signature DP compacte. Pour Piste B, la prochaine avancée doit réduire le
support ou prouver une factorisation par structure de PC-tree.

## Résultats T021

Statut : résultat négatif expérimental sur signatures compactées.

Hypothèse testée par subagent : remplacer `block_bad_side_signature` par des
agrégats plus compacts, par exemple endpoints + `bad_any`, `forced_only`,
histogrammes de masques ou compteurs de paires forcées.

Métriques sur P-node star-block `n=8`, bloc de taille `6`, `720`
sous-frontiers :

- `cycle` : signature complète `720/720`, histogramme `0.597`, `bad_any`
  `0.042` ;
- `random` : complète `672/720`, forced `0.906`, histogramme `0.450` ;
- `paired_farthest` : complète `716/720`, forced `0.817`, histogramme
  `0.686` ;
- `equal` : complète `30/720`, seule famille franchement compressible.

Contre-exemple de compression non sûre :

- famille `paired_farthest`, `n=8`, seed `1008` ;
- bloc `(0,1,2,3,4)`, contexte `(7,5,6)` ;
- signature `forced_only` identique et aucune paire forcée ;
- frontier `(1,2,0,4,3)` donne cR `True` ;
- frontier `(1,2,4,0,3)` donne cR `False`, violation sur quadruplet
  `(4,0,5,6)`.

Conclusion : les agrégats compressent, mais perdent l'information de côté ou
l'identité fine des témoins mauvais sur les familles stress. Continuer Piste B
seulement avec une structure supplémentaire prouvable : degré borné, familles
laminaires/equal-block, ou sous-cas strict.
