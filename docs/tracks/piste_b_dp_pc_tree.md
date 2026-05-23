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

## Résultats T038

Statut : la caractérisation bad-side d'un ordre fixé est promue en prédicat
central exact, mais pas en DP compacte.

Artefacts :

- `find_bad_side_precircular_cR_violation` dans `predicates.py` retourne une
  paire `{a,b}` et deux mauvais témoins placés sur les deux arcs ;
- `passes_bad_side_precircular_cR` donne le test booléen exact en `O(n^3)` ;
- `candidate.py` utilise ce prédicat pour valider les témoins déjà produits ou
  énumérés ;
- les tools de correction gardent le test de quadruplets comme oracle
  indépendant.

Validation :

- exhaustif `n=4`, valeurs `{1,2,3}`, `2187` comparaisons dans les tests ;
- probes locales et subagents : `153291` comparaisons ordre fixé sans
  désaccord ;
- égal-distance confirme que l'inégalité stricte `>` est nécessaire ;
- wrapping par rotations/renversements et cas "deux témoins mauvais du même
  côté" sont en régression.

Conclusion : T038 accélère fortement le test d'un ordre fixé et les validations
de témoins, mais ne résout pas encore la question DP : il faut toujours produire
ou représenter un ordre. La prochaine tentative Piste B doit exploiter cette
forme pour réduire le support des états, pas seulement accélérer l'énumération.

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

## Résultats T046

Statut : étape intermédiaire vers DP, mais encore énumérative.

`exact_low_hub_matching_projected_pc_tree_search_report` peut être vu comme une
intersection PC-tree x langage apparié où les hubs sont epsilon : le langage
demande une projection `seq + mate(seq)`, et le releveur vérifie que cette
projection se parse en blocs compatibles avec les nœuds `P/C`.

Le subagent Piste B recommande que la vraie DP transporte au minimum :

- la phase `A/B` du premier et du dernier endpoint d'un bloc ;
- les endpoints frontières ;
- les paires ouvertes dont le mate est hors sous-arbre ;
- l'ordre relatif ou une contrainte PC/PQ sur ces paires ouvertes ;
- l'orientation exposée de chaque paire ;
- le statut hubs-only comme epsilon.

Exactitude attendue : polynomial seulement si le nombre de paires ouvertes par
arête du scaffold est borné ou si les contraintes d'ordre exposées restent
laminaires/PC-tree-représentables. Sinon, l'ordre des paires ouvertes peut
dégénérer vers l'énumération factorielle de T046.

Contre-exemple de signature trop faible : deux blocs peuvent exposer les mêmes
ensembles de paires mais des ordres opposés. Le cas rigide
`C(0,1,2,3,4,6,5,7)` splitte chaque paire côté A/B mais désynchronise les mates,
donc une signature par ensembles ou booléens de côté accepte à tort.

## Résultats T047

Statut : clarification d'une collision de canonicalisation, pas nouvelle DP.

Le sidecar Piste B trouve une collision si l'on demande que la signature de
support prédise l'identité exacte de l'atom orienté après
`canonical_circular_order(frontier_complet)`. Dans
`balanced_pc_tree(5, kind="mixed")`, deux affectations qui ne diffèrent que par
un choix hors support de l'atom `(0,2,3,4)` ont la même projection brute sur les
quatre labels, mais la canonicalisation globale change l'orientation visible
parce que le label hors atom `1` détermine le renversement canonique.

Conclusion : pour Piste B/C, l'objet stable n'est pas `(atom, signature)` mais
la signature de pruning. Cette collision est verrouillée par
`test_support_local_atom_identity_is_not_stable_under_global_canonicalization`.
Toute future DP doit éviter de baser son état sur une orientation canonique
globale influencée par des labels déjà supprimés.

## Résultats T048

Statut : signal pour une future DP, pas encore une signature suffisante.

Le regroupement par support montre que de nombreux atoms bad-side partagent les
mêmes variables locales du PC-tree. Sur le benchmark CSP rapide, le produit de
supports passe de `72256` à `6224` quand on compte chaque support distinct une
seule fois.

Limite DP : l'implémentation groupée teste encore chaque atom du groupe pour
chaque affectation de support, donc `atom_checks=72256`. Une vraie signature DP
devrait factoriser ces atoms en contraintes plus compactes sur un même support
ou prouver que la taille des groupes reste bornée dans les instances
quasi-circulaires.

## Résultats T049

Statut : optimisation de table de support, pas DP compacte.

First-hit remplace, pour une affectation de support fixée, la liste complète des
atoms violés par le booléen "au moins un atom bad-side du groupe apparaît". Cela
préserve les signatures effectives utilisées par `_nogood_matches`.

Limite DP : la table "affectation mauvaise" est encore construite par scan
séquentiel des atoms, et les diagnostics d'atom/pair deviennent incomplets. Le
contre-exemple minimal `n=4` ajouté aux tests montre que les signatures restent
identiques alors que `atoms_with_nogoods` et `pairs_with_nogoods` diminuent.
Une vraie DP doit donc porter une contrainte de support agrégée, pas les
représentants first-hit.

## Résultats T050

Statut : profil d'implémentation utile pour orienter la DP.

Les métriques T050 montrent que le coût restant de first-hit se divise en deux :
hits tardifs et affectations sans hit. Sur `make bench-csp-quick`, les no-hit
représentent `3320/6224` affectations de support et consomment `30520` checks.

Conséquence DP : une table par support qui dit seulement "hit existe" est
insuffisante si elle est encore construite par scan. Le bon objet serait une
contrainte agrégée capable de décider directement qu'au moins un atom du groupe
apparaît, ou de certifier qu'aucun ne peut apparaître, pour une affectation de
support donnée.

## Résultats T051

Statut : hypothèse DP clarifiée, pas encore compression.

Le diagnostic pair-side/composantes transforme chaque support groupé en graphes
`G(S,a,b)` dont les sommets sont les mauvais témoins de la paire `{a,b}` et les
arêtes les couples de témoins qui produisent un atom du support `S`. Pour une
affectation locale, un hit existe ssi une composante de `G(S,a,b)` a des témoins
sur les deux côtés de `{a,b}`.

Ce résultat donne une signature DP candidate plus structurée que la liste
d'atoms : transporter les composantes de témoins et leurs côtés exposés. Mais le
profil T051 montre que recalculer ces côtés par affectation coûte plus cher que
le first-hit actuel sur la gate rapide (`pair_side_split_work_ratio=1.7732`).

Conséquence DP : il faut factoriser le calcul des côtés lui-même, probablement
par sous-arbre ou par paire endpoint, sinon le passage atom -> composante ne
suffit pas.

## Résultats T052

Statut : brique de signature DP, pas encore solver.

Le cache T052 valide expérimentalement que le côté d'un mauvais témoin `w`
relativement à `{a,b}` est déterminé par la signature du support minimal du
triple `(a,b,w)`. Cela donne un atome d'état DP plus local que le support
quartet complet.

Limite : le cache simple réduit les recalculs de côtés mais reste à `1.1836x`
du coût first-hit sur la gate rapide. Le signal positif vient du modèle
bitset-composantes (`0.6650x`) : une DP prometteuse devrait transporter des
masques de côtés par composante de témoins plutôt que recalculer ou rescanner
les témoins.

Contre-exemple à une signature trop faible : si on omet les choix imbriqués du
support triple, deux affectations peuvent avoir le même choix root mais placer
le témoin sur des côtés opposés.

## Résultats T053

Statut : brique DP locale exacte pour un support groupé, pas état DP suffisant.

Le profil bitset réel confirme que, pour une affectation de support fixée, la
donnée suivante est suffisante pour classifier les atoms bad-side du groupe :
pour chaque paire `{a,b}` et chaque composante group-local de mauvais témoins,
un masque binaire des côtés occupés. Le groupe hit ssi un masque vaut `0b11`.

Ce que cette signature préserve :

- les labels de la paire endpoint ;
- l'appartenance à une composante de témoins ;
- les choix imbriqués du support nécessaire à chaque côté ;
- le fait qu'une composante, et non seulement la paire globale, occupe deux
  côtés.

Ce qu'elle perd :

- l'ordre des témoins dans une composante ;
- les côtés exacts après agrégation par OR ;
- les corrélations entre supports groupés différents ;
- la représentabilité globale d'un frontier.

Conséquence DP : les masques de composantes sont un bon atome d'état local, mais
pas une signature globale. T053 ajoute aussi un contre-exemple de perte
d'identité sur paired-farthest `n=6` : deux blocs proches changent la validité
cR même si une signature trop grossière ne garderait que les mêmes types de
masques. Toute DP doit donc garder les labels/paires et non seulement des
profils de couleurs anonymes.

## Résultats T054

Statut : test de compression d'état, pas DP.

T054 compte les états distincts
`((pair, component, side_mask), ...)` par support groupé. Les résultats sont
cohérents avec l'interprétation T053 : l'état local est exact (`0` état mixte,
`0` mismatch contre le scan atomique), mais il ne compresse qu'environ par deux.

Sur la gate CSP rapide :

- `2920` états pour `6224` affectations, ratio `0.4692` ;
- bucket moyen `2.1315`, bucket max `4` ;
- les stress `random`, `permuted_cycle` et `paired_farthest` restent dans la
  bande `0.45..0.50`.

Conséquence DP : ce quotient est trop faible pour annoncer une DP compacte. Il
reste utile comme métrique de falsification : si un futur état plus abstrait
descend nettement sous ce ratio sans créer d'états mixtes, il pourra devenir
intéressant. Mais une preuve devra encore montrer que les états se composent à
travers les frontières du PC-tree sans reconstruire les frontiers ni revisiter
tous les témoins.
