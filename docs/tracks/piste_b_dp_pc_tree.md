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

## Résultats T055

Statut : exploration de quotients d'état, pas DP.

T055 compare plusieurs projections de l'état T054. Les quotients
`mask_multiset`, `hit_components`, `hit_pairs` et `decision_only` ne créent pas
d'états mixtes sur la gate rapide, tandis que le contrôle négatif
`side_blind_schema` devient massivement mixte. Cela confirme que les masques,
et pas seulement la forme du support, portent l'information locale de décision.

Lecture DP :

- `decision_only` et `hit_components` sont localement exacts, mais trop proches
  d'une table de décision du support pour constituer une signature composable ;
- `mask_multiset` est le quotient non tautologique le plus intéressant :
  ratio `0.3959` sur la gate rapide et `0.4088` sur le stress `n=8`, sans état
  mixte observé ;
- aucune de ces mesures ne prouve que deux sous-arbres avec le même quotient
  auront le même comportement face au contexte parent.

Prochaine obligation pour continuer côté DP : construire un test de composition
parent-enfant, ou produire un contre-exemple où deux affectations ayant le même
quotient local divergent après extension dans un support plus large.

## Résultats T056

Statut : contre-exemple DP contextuel, hors `candidate.py`.

T056 ajoute `component_mask_quotient_context_collision_profile`. Pour deux
supports groupés qui se chevauchent, le diagnostic fixe les choix sur
`(S union C) \\ S` et teste si un quotient local calculé sur `S` suffit à
prédire le hit/no-hit du groupe voisin `C`. C'est une approximation contrôlée
de la question parent-enfant : si le même état local et le même contexte externe
observé donnent deux réponses différentes dans `C`, alors l'état local n'est
pas composable seul.

Résultat minimal : sur `cycle_metric(5)` avec
`balanced_pc_tree(5, kind="mixed")`, `mask_multiset` a `12` collisions de
contexte sur `36` états contextuels, alors que le contrôle
`assignment_signature` a `0` collision. Le cas est régressé par
`test_component_mask_quotient_context_collision_refutes_mask_multiset_as_dp_state`.

Contre-exemple global plus fort : sur la matrice `n=5`

```text
[[0,1,2,2,3],
 [1,0,2,2,3],
 [2,2,0,1,3],
 [2,2,1,0,3],
 [3,3,3,3,0]]
```

avec `balanced_pc_tree(5, kind="C")`, deux affectations locales du support
`((), (0,), (0,0))` ont `mask_multiset=(1,2)`, `hit_components=()`,
`hit_pairs=()` et le même contexte externe `(1,)=(0,1)`. Elles induisent
pourtant les ordres canoniques `(0,1,4,3,2)` et `(0,1,3,4,2)`, respectivement
cR et non-cR. Le témoin contextuel qui distingue le second est l'atome
bad-side `(2,4,3,0)` sur le support `((), (0,), (1,))`. Le test
`test_mask_multiset_quotient_same_context_global_cr_collision_counterexample`
conserve ce cas.

Lecture DP :

- `mask_multiset` reste un classifieur local sound dans T055, mais il est
  insuffisant comme état DP autonome ;
- `hit_components`, `hit_pairs` et `decision_only` collisionnent encore plus,
  ce qui confirme qu'ils sont trop proches d'une décision locale sans mémoire
  de contexte ;
- quand l'état T054 complet `full` collisionne sur les probes agrégées, ce n'est
  pas une perte due au quotient : c'est une limite des états de masques fermés
  face aux contraintes ouvertes entre supports voisins.

Conséquence : une DP viable doit transporter plus qu'un état de masques fermé
par support. Il faut représenter des obligations ouvertes vers les supports
voisins ou garder des signatures d'affectation plus fines ; sinon le contexte
parent peut distinguer deux sous-états fusionnés.

## Résultats T057

Statut : signature ouverte one-hop mesurée, pas DP prouvée.

T057 ajoute `component_mask_open_boundary_profile`. Pour chaque support groupé
`S` et affectation locale `alpha`, le diagnostic calcule le vecteur des réponses
hit/no-hit de chaque support voisin `C` qui chevauche `S`, pour chaque choix de
contexte externe `(S union C) \\ S`. Les clés d'état incluent explicitement le
support de base afin de ne pas surestimer la compression par pooling entre
supports différents.

Définition mesurée :

```text
boundary_response(S, alpha) =
  ((C, signature(beta), hit_C(alpha union beta)), ...)
```

où `beta` parcourt les choix des variables de `(S union C) \\ S`. Variantes
comptées : `boundary_response`, `local_boundary_response`,
`mask_multiset_plus_boundary`, `full_plus_boundary`, et le contrôle
`assignment_signature`.

Résultat minimal `cycle_metric(5)` / `balanced_pc_tree(5, kind="mixed")` :

- `24` affectations locales ;
- `96` checks de réponses ouvertes ;
- `assignment_signature` : `24` états ;
- `mask_multiset` : `9` états ;
- `boundary_response` : `12` états ;
- `mask_multiset_plus_boundary` : `12` états ;
- `full_plus_boundary` : `12` états.

Lecture DP :

- la réponse ouverte one-hop répare le type de collision T056 au niveau du
  support voisin mesuré ;
- elle reste beaucoup moins fine que l'affectation complète sur les petits cas,
  donc elle mérite une suite ;
- elle ne compose pas encore récursivement : rien ne prouve qu'un vecteur de
  réponses booléennes one-hop suffise pour des chaînes de supports ou pour une
  combinaison simultanée de plusieurs voisins.

Prochaine obligation : tester une collision de second ordre. Deux affectations
avec même `local_boundary_response` peuvent-elles encore diverger après
composition de deux supports voisins, ou pour la décision globale cR ?

## Revue externe post-T057

Statut : garde-fou de piste.

La revue externe GPT 5.5 Pro souligne que T057 ne doit pas devenir l'unique axe.
Pour Piste B, elle reformule la bonne cible DP comme une relation résiduelle sur
séparateur :

```text
R_P = { eta on boundary(P) : eta admet une extension interne compatible }.
```

Une signature DP est valide seulement si deux patches avec même signature ont la
même relation résiduelle. La réponse ouverte one-hop est donc un candidat
compressé, pas la relation exacte.

Prochaine expérience Piste B : comparer `local_boundary_response` à la relation
résiduelle exacte sur des patches de supports de taille `2` ou `3`. Cette
expérience doit rester une piste parmi d'autres, en parallèle du CSP exact par
quartets et du sous-cas booléen.

## R004 - Lemme d'interface P-noeud à contexte fixé

Statut : conjecture externe, non reproduite dans le dépôt.

Les notes du 2026-05-31 proposent de réparer le recollement naïf des P-noeuds
par un lemme d'interface :

```text
à ordre de branches sigma et contexte extérieur fixés, les complétions internes
valides des blocs d'un P-noeud se factorisent en produit cartésien.
```

Cette hypothèse est exactement dans le prolongement de T056/T057 : une signature
locale n'est utile que si elle détermine la relation résiduelle sur le bord. Le
lemme d'interface serait une forme de factorisation plus forte pour les
P-noeuds, mais il doit être vérifié contre les familles déjà difficiles.

Probe recommandé :

- fixer `(P, sigma, contexte)` ;
- énumérer les complétions internes admissibles de chaque bloc ;
- comparer l'ensemble global accepté au produit des relations de bloc ;
- inclure les cas T046/T075/T081/T082 et un gros `P` actif ;
- si un mismatch apparaît, le shrinker et l'ajouter aux régressions.

Même sans mismatch, la taille des relations d'interface doit être mesurée :
une factorisation exacte mais exponentielle serait utile pour la preuve, pas
forcément pour un algorithme polynomial général.

## T090 - Relation résiduelle projetée après élimination interne

Statut : preuve expérimentale bornée.

T090 ajoute `tools/pc_boundary_residual_projection_probe.py`. Il prend la
relation exacte des complétions internes acceptées autour d'un focus `P`, puis
cache au moins une branche et mesure la relation résiduelle restante sur le
bord. C'est le modèle minimal d'une composition de patch où des variables
internes ont été éliminées.

Résultat observé :

- `P2x4` sparse two-level : `20000` cas, aucune projection de bord d'arité
  minimale `>2` ;
- `P2x5` sparse two-level : `20000` cas, aucune projection de bord d'arité
  minimale `>2` ;
- contrôle binaire reproduit l'égalité de deux branches après projection ;
- random multi-niveaux `P2x4`, `500` essais : aucune projection de bord
  non triviale.

Lecture DP : ce résultat ne prouve pas qu'une relation binaire de séparateur
suffit, mais il ferme une variante simple du contre-argument "l'élimination
interne crée immédiatement une arité 3" dans les familles testées. La prochaine
attaque DP doit introduire un contexte extérieur non fixé ou plusieurs patches
dont les contextes restent variables.

## T093 - Ordre local insuffisant pour les obligations ouvertes

Statut : lemme négatif expérimental.

T093 ajoute `make bench-partial-context-lab`. Le rapport groupe les frontiers
par `(P-node, obligation same_side, ordre local de branches)` et cherche les
groupes mixtes : même ordre local, même obligation, mais satisfaction différente
selon les ordres internes ou le contexte.

Résultat clé : le témoin `single_bad_side_quartet_instance()` sur
`P(P(0,1),P(2,3))` donne déjà un groupe mixte à la racine. L'ordre local des
branches est `(0,1)` dans les deux cas, mais `(0,1,3,2)` satisfait
`same_side(0,2;1,3)` et `(0,1,2,3)` le viole.

Benchmark borné : `120` lignes complètes, `1223` groupes mixtes
support-boundary, `0` groupe mixte fully-visible. Lecture DP : les contraintes
fermées en cordes de branches sont bien locales dans ce sweep, mais les
obligations ouvertes demandent une vraie relation de séparateur. La prochaine
étape DP doit donc définir cette relation et mesurer sa composabilité.

## T094 - Signature visible insuffisante comme état DP

Statut : diagnostic implémenté, garde-fou DP.

T094 ajoute `make bench-separator-signature-lab`. La signature testée raffine
l'ordre local de branches par l'ordre des rôles visibles `endpoint/witness`
dans chaque branche touchée par une obligation `same_side`.

Résultat positif local : cette signature distingue le témoin minimal T093 à la
racine de `P(P(0,1),P(2,3))`.

Résultat négatif global borné :

- `120` lignes complètes ;
- `branch_order_mixed_group_count=1434` ;
- `separator_signature_mixed_group_count=1957` ;
- `support_boundary_separator_mixed_group_count=1428` ;
- `fully_visible_separator_mixed_group_count=0`.

Lecture DP : la signature visible n'est pas une congruence de composition. Elle
peut même scinder un groupe mixte grossier en plusieurs groupes mixtes plus
fins. Les exemples restants ont des rôles absents du nœud courant ; une vraie
relation de séparateur doit donc représenter la relation entre les rôles visibles
et les côtés/contextes extérieurs, pas seulement l'ordre visible interne.

## T095 - Ladder de contexte et insertion extérieure

Statut : diagnostic implémenté, garde-fou DP.

T095 ajoute `make bench-context-signature-ladder`. Le rapport compare quatre
niveaux de signature pour une obligation ouverte :

1. T094 visible par branche ;
2. ordre global des rôles visibles ;
3. ordre global visible plus ordre des rôles absents ;
4. ordre complet des quatre rôles avec localisation branche/extérieur.

Résultat borné :

- `t094_visible_per_branch` : `2048` groupes mixtes ;
- `visible_global` : `1861` groupes mixtes ;
- `visible_global_plus_missing_order` : `1793` groupes mixtes ;
- `full_context_order` : `0` groupe mixte.

Lecture DP : connaître séparément l'ordre visible et l'ordre des rôles absents
ne suffit pas. Il faut connaître où le contexte extérieur s'insère par rapport
au bloc visible. Le mode `full_context_order` élimine les mixtes parce qu'il
encode presque directement le type du quartet, donc il sert de borne haute
diagnostique, pas d'état DP. La prochaine expérience doit chercher une relation
plus abstraite de positions/côtés extérieurs possibles.

## T096 - Relation de gaps et taille d'interface

Statut : diagnostic implémenté, garde-fou DP.

T096 ajoute `make bench-context-gap-relation`. Le rapport encode le contexte
extérieur d'une obligation ouverte par des gaps cycliques entre les rôles
visibles au P-nœud, puis mesure la relation
`visible_state -> set(gap_patterns)`.

Résultat borné :

- `gap_state_mixed_group_count=0` sur `120` lignes complètes ;
- `visible_missing_mixed_group_count=1730`, donc T095 était bien trop faible ;
- `gap_relation_bucket_count=2359499` ;
- `nontrivial_gap_relation_bucket_count=3008` ;
- `max_gap_patterns_per_visible_state=4`.

Lecture DP : la bonne information locale ressemble maintenant à une relation de
positions d'insertion du contexte extérieur. Elle décide les obligations isolées
du sweep, mais sa composition n'est pas testée. Si plusieurs patches font croître
ces ensembles de gaps, on retombe sur une relation résiduelle complète ; si leur
taille reste bornée ou structurée, c'est une piste DP réelle.

## T097 - Produit des marges de gaps insuffisant

Statut : lemme négatif expérimental, garde-fou DP.

T097 ajoute `make bench-context-gap-composition`. Pour chaque obligation
`same_side` projetée sur plusieurs nœuds `P`, le rapport fixe l'état visible de
chaque projection, collecte les tuples de patterns de gaps observés, puis les
compare au produit cartésien des marges locales.

Résultat borné :

- `120` lignes complètes ;
- `2487` projections ouvertes ;
- `880` tuples de projections ;
- `2040` relations visibles jointes ;
- `1120` cas où le produit des marges ajoute des tuples impossibles ;
- `false_product_tuple_count=2240` ;
- `max_product_size=4` et `max_actual_relation_size=2`.

Lecture DP : une DP qui stocke seulement les relations T096 séparément par
projection perd des corrélations. Le prochain objet DP doit être une relation
résiduelle jointe sur le séparateur, ou une factorisation prouvée plus fine que
le produit naïf. Le résultat ne borne pas encore la taille de cette relation
jointe et ne justifie aucune intégration dans `candidate.py`.

## T098 - Closure binaire des relations de gaps

Statut : diagnostic implémenté, preuve expérimentale bornée.

T098 ajoute `make bench-context-gap-arity`. Le rapport prend des tuples de trois
projections ouvertes d'une même obligation, fixe l'état visible joint, puis
compare :

1. le produit des marges ;
2. la closure par toutes les projections binaires ;
3. la relation jointe réellement observée.

Résultat borné :

- `124` lignes complètes ;
- `120` lignes du sweep standard, qui ne produisent pas de tuples à trois
  projections ouvertes ;
- `4` lignes du stress `nested_bad_side_ladder` ;
- `875` relations jointes testées ;
- toutes ont besoin d'au moins une contrainte binaire
  (`product_false_case_count=875`) ;
- aucune n'exige plus que les projections binaires
  (`higher_order_case_count=0`) ;
- `max_product_size=64`, `max_actual_relation_size=4`,
  `max_pairwise_closure_size=4`.

Lecture DP : ce stress ne valide pas une DP binaire générale, mais il oriente le
prochain modèle : transporter un graphe de relations binaires entre projections
de gaps peut être strictement plus pertinent qu'une relation jointe arbitraire.
Le prochain contre-test doit chercher une vraie arité `3`, ou bien construire un
prototype de composition binaire et essayer de le casser.

## T099 - Arité binaire avec plusieurs obligations

Statut : diagnostic implémenté, preuve expérimentale bornée.

T099 ajoute `make bench-context-gap-multi-arity`. Contrairement à T098, les
tuples de projections peuvent venir de plusieurs obligations `same_side`
distinctes. Le rapport teste si la relation jointe est reconstruite par les
projections binaires.

Résultat borné :

- `23` lignes, dont `14` atteignent le cap de tuples ;
- `172211` tuples de projections ;
- `493440` relations visibles ;
- `122513` cas où les marges unaires suffisent ;
- `370927` cas où une contrainte binaire est nécessaire et suffisante ;
- `0` cas d'arité `>=3` ;
- `max_actual_relation_size=16`.

Lecture DP : le signal binaire résiste à un mélange de plusieurs obligations,
mais le cap de tuples et le scaffold non promise-aware empêchent toute preuve.
La prochaine étape utile est soit un générateur plus agressif pour chercher une
arity `>=3`, soit un prototype de propagation de relations binaires de gaps
dont on pourra mesurer la taille et les collisions.

## T100 - Stress largeur 4 pour l'interface binaire de gaps

Statut : preuve expérimentale bornée, garde-fou DP.

T100 ajoute `make bench-context-gap-high-arity`. Il compare le même diagnostic
multi-obligations aux tailles de tuple `3` et `4`. L'intérêt DP est simple :
si une relation de quatre projections a une closure binaire strictement plus
large que la relation réelle, alors une DP à seules arêtes de compatibilité de
gaps serait insuffisante dans ce scaffold.

Résultat borné :

- `22` lignes agrégées, dont `18` atteignent le cap de tuples ;
- tuple size `4` : `31001` tuples de projections et `79813` relations
  visibles ;
- total tuple sizes `3/4` : `149290` relations visibles ;
- `product_false_case_count=123508`, donc les marges unaires restent
  insuffisantes ;
- `binary_sufficient_case_count=123508` ;
- `higher_order_case_count=0` ;
- `max_product_size=256`, `max_actual_relation_size=8`.

Lecture DP : le résultat renforce l'idée d'une interface binaire de gaps, mais
ne la prouve pas. Les caps augmentent avec la largeur `4`, donc la suite ne
doit pas seulement augmenter les combinaisons ; elle doit soit construire une
famille adversariale ciblant l'arité `>=3`, soit essayer une propagation binaire
réelle et chercher ses collisions.

## T101 - Échantillonnage adversarial de tuples de gaps

Statut : preuve expérimentale bornée, garde-fou DP.

T101 ajoute `make bench-context-gap-random-arity`. Contrairement à T100, le
probe ne prend pas seulement les premiers tuples sous cap : il tire des tuples
de projections ouvertes aléatoirement dans l'espace complet, avec tailles `4`
et `5`, puis refait le test relation réelle vs closure binaire.

Résultat borné :

- `56` lignes ;
- `32730` tuples échantillonnés dans un espace déclaré de `1680626925`
  combinaisons ;
- `111193` relations visibles ;
- `product_false_case_count=99865` ;
- `binary_sufficient_case_count=99865` ;
- `higher_order_case_count=0` ;
- `max_product_size=1024`, `max_actual_relation_size=8`.

Lecture DP : l'hypothèse "relation de gaps déterminée par les projections
binaires" résiste aussi à un échantillonnage randomisé de tuples plus larges.
Mais le résultat reste très loin d'une preuve : aucune borne de taille, aucune
composition prouvée, aucune garantie promise-aware. La suite doit arrêter les
simples sweeps d'arité et passer à un modèle constructif ou à une famille
adversariale explicitement conçue.

## T102 - Propagation binaire locale de gaps

Statut : prototype de diagnostic DP, preuve expérimentale bornée.

T102 ajoute `make bench-context-gap-binary-components`. Le probe choisit des
ensembles de `6` et `8` projections ouvertes, fixe les états visibles joints
observés dans les frontiers, puis compare la relation réelle de gaps à la
closure produite par toutes les contraintes binaires entre projections.

Résultat borné :

- `21765` ensembles de projections échantillonnés ;
- `88103` cas visibles ;
- `product_false_case_count=87533` ;
- `binary_sufficient_case_count=87533` ;
- `higher_order_case_count=0` ;
- `product_capped_case_count=0` ;
- `frontier_truncated_rows=0` ;
- `visible_cases_with_restrictive_edges=87533` ;
- `max_product_size=16384`, `max_closure_size=8`,
  `max_actual_relation_size=8`.

Lecture DP : ce résultat est le signal le plus fort jusqu'ici pour une
interface de gaps binaire dans les scaffolds testés : les cas non triviaux ont
de nombreuses arêtes restrictives, mais aucun tuple admis par la closure
binaire et absent des frontiers n'est observé. La limite reste majeure : T102 ne
compose pas encore des sous-arbres, ne prouve pas de borne de taille, et ne
travaille pas sous le promise Hsu/McConnell `T=T(D)`.

## T103 - Jointure de composants de gaps

Statut : garde-fou DP, lemme négatif expérimental.

T103 ajoute `make bench-context-gap-join-decomposition`. Le probe choisit une
union de projections ouvertes, la décompose en deux côtés avec overlap
(`4:4:2` ou `5:5:2`), puis compare :

1. la relation globale réelle des gaps ;
2. les deux relations exactes projetées sur les côtés ;
3. leur jointure naturelle sur l'overlap.

Résultat borné :

- `22400` décompositions échantillonnées ;
- `90833` cas visibles ;
- `nontrivial_component_case_count=89429` ;
- `exact_join_case_count=80562` ;
- `false_join_case_count=10271` ;
- `false_join_tuple_count=25104` ;
- `cross_edge_repaired_case_count=10271` ;
- `cross_edge_unrepaired_case_count=0` ;
- `binary_higher_order_case_count=0` ;
- `join_capped_case_count=0`, `frontier_truncated_rows=0`.

Lecture DP : T103 casse le modèle trop faible "deux patchs exacts se recollent
par petit overlap". Les fausses jointures montrent que des compatibilités
transverses entre left-only et right-only sont nécessaires. Le fait que toutes
les fausses jointures soient réparées par les arêtes binaires transverses garde
ouverte une DP par graphe de contraintes binaires de gaps, mais pas une DP par
overlaps fixes naïfs.

## T104 - Cycle de parité ciblé pour les gaps

Statut : contre-signal expérimental pour l'interface binaire de gaps.

T104 ajoute `make bench-context-gap-parity-cycle`. L'expérience arrête
l'échantillonnage uniforme de T101/T102 et cible les familles
high-cycle/low-hub, où les obligations `same_side(0,v; prev,next)` forment
naturellement un cycle. Le probe compare deux modes :

- `current_gap`, la signature utilisée dans les expériences précédentes ;
- `gap_with_distance`, qui garde en plus la distance cyclique des rôles
  manquants dans leur gap.

Résultat borné :

- `8` lignes complètes ;
- `54` projections ciblées cycle ;
- `2880` cas visibles ;
- `product_capped_case_count=0`, `frontier_truncated_rows=0` ;
- `higher_order_case_count=76`, dont `12` sous `gap_with_distance` ;
- `min_higher_order_projection_count=4` ;
- `pairwise_false_tuple_count=92`.

Lecture DP : T104 fournit le premier contre-signal ciblé contre la conjecture
"les relations exactes de gaps sont toujours 2-décomposables" dans les
scaffolds testés. Une partie du signal est un artefact possible de quotient
(`current_gap` sur `cycle_pair_p`), mais le mode enrichi `gap_with_distance`
produit encore un higher-order sur `mixed/odd_high_cycle_low_hub`. La prochaine
étape doit donc shrinker ce cas et le comparer à des signatures plus exactes,
avant de conclure sur la nécessité d'une relation résiduelle d'arité supérieure.
