# Piste D - Intersection PC-tree / circular-ones

## Question

La circularité Robinson peut-elle être reformulée comme une famille de
contraintes d’arcs ou de circular-ones à intersecter avec le PC-tree ?

## Intuition

Les ordres quasi-circulaires sont déjà décrits par des boules qui sont des arcs.
Il est tentant d’ajouter des contraintes dérivées de `D` pour éliminer les ordres
non cR sans quitter le monde PC/PQ/circular-ones.

## État courant

Statut : diagnostic borné ajouté, pas solver.

`strict_ball_circular_ones_report` teste expérimentalement la partie
quasi-circulaire attendue de la piste circular-ones : pour chaque ordre/frontier
énumérable, il vérifie que toutes les boules métriques non triviales sont des
arcs, puis compare ce signal à `is_quasi_circular_order`,
`is_strict_quasi_circular_order` et aux prédicats cR stricts.

Résultat T025 :

- sur les probes bornées, `ball_arc` coïncide avec `is_quasi_circular_order` ;
- Fig. 2.2 donne deux ordres `ball_arc/strict_quasi`, mais un seul ordre strict
  circular, donc les contraintes de boules ne décident pas cR ;
- un random `n=6 seed=7` a un unique ordre `ball_arc/quasi` sous star, mais
  aucun ordre cR, ce qui donne un faux positif non-source au-delà de Fig. 2.2 ;
- equal-distance donne tous les ordres `ball_arc/quasi/precircular` non stricts
  mais aucun ordre strict, ce qui protège les égalités ;
- le témoin strict cR non représenté par un PC-tree reste absent quand le
  rapport reçoit ce PC-tree ;
- une signature de modules par appartenance aux boules non triviales est
  exposée pour mesurer d'éventuelles contractions avant une intersection
  PC-tree/circular-ones.

Cet artefact ne construit pas encore un PC-tree de circular-ones et n'est pas
utilisé par `candidate.py`.

Résultat T026 :

`bad_witness_arc_constraints_report` teste une autre tentative circular-ones :
pour chaque paire `{a,b}`, poser
`B(a,b) = {w : max(d(a,w), d(w,b)) > d(a,b)}` et comparer trois signaux :

- `bad_witness_one_side` : `B(a,b)` est contenu dans un seul des deux arcs
  ouverts de `{a,b}` ;
- `bad_witness_set_arc` : `B(a,b)` est un arc circulaire ;
- `bad_witness_with_endpoints_arc` : `B(a,b) union {a,b}` est un arc.

La première condition est la reformulation exacte de cR pour ordre fixé déjà
portée par les quartets : une violation cR met deux mauvais témoins sur les deux
côtés de la corde `{a,b}`. Les deux autres contraintes ne donnent pas une
réduction circular-ones générale :

- `B(a,b)` arc semble suffisant pour cR, mais il est trop fort. Un
  contre-exemple `n=5` cR vérifié a `B(0,3) = {1,2}` non arc dans l'ordre
  `(0,2,4,1,3)`.
- `B(a,b) union {a,b}` arc n'est ni nécessaire ni suffisant. Equal-distance à
  `n=4` le réfute comme condition nécessaire, et une matrice carrée opposée le
  réfute comme condition suffisante.

Le rapport reste borné : si `n > max_n` ou si `frontier_limit` tronque
l'énumération, il marque `complete=False` et laisse les absences d'ordre à
`None`, jamais à `False`.

Les sources Hsu/McConnell et Hsu PC-vs-PQ sont listées dans
`docs/source_notes.md`. Elles justifient la pertinence des PC-trees pour les
arrangements circular-ones, mais l’implémentation actuelle reste un scaffold
minimal.

Complément T040 : les contraintes circular-ones locales par nœud ne suffisent
pas. Sur `even_high_cycle_plus_low_hub(7)` avec
`balanced_pc_tree(7, kind="mixed")`, toutes les frontiers représentées sont
non-cR, mais les projections locales `I_x(v)` restent compatibles à chaque nœud.
La piste viable est donc une intersection avec une contrainte circular-ones
globale auxiliaire, pas un filtre local indépendant appliqué nœud par nœud.

Complément T075 : `make bench-frontier-obstructions` confirme ce diagnostic sur
un sweep borné. Les `494` frontiers non-cR profilées sont toutes dans des lignes
où le rapport local `I_x(v)` est silencieux, et le premier quartet cR interdit
utilise toujours `3` supports PC-tree. Les variantes d'arc de mauvais témoins
restent seulement diagnostiques : `B(a,b) union {a,b}` échoue comme prédicat
nécessaire sur les lignes cR, et `B(a,b)` arc produit encore quelques mismatchs
sur cycles. La conclusion reste qu'il faut une contrainte globale de projection
ou une relation de séparateur, pas une circular-ones locale indépendante.

Complément T078 : la reformulation clean-side par seuil remplace la vue
`B(a,b)` par son complément
`C_ab = N_{d(a,b)}[a] intersect N_{d(a,b)}[b]`. Pour un ordre fixé, la condition
cR devient : pour toute paire `{a,b}`, au moins un des deux arcs ouverts entre
`a` et `b` est contenu dans `C_ab`. Le probe `make bench-threshold-roundness`
compare cette condition à bad-side et à la définition par quadruples. Résultat
observé : `53` lignes, `6072` ordres vérifiés, `0` mismatch, `0` troncature.

Interprétation : T078 donne une meilleure porte vers les seuils imbriqués,
round-order et projection-adjacence. Il ne transforme pas encore cR en
circular-ones standard, car la contrainte porte sur un arc choisi entre deux
endpoints, pas sur la consécutivité globale de `C_ab`.

Complément T079 : `make bench-cr-pc-representability` teste si l'ensemble
complet des ordres cR d'une matrice est lui-même représentable par un `PCNode`
du scaffold. Le learner énumère exactement les familles du scaffold jusqu'à
`n=6` sous cap `50000` familles par sous-ensemble. Résultat observé :
`39` lignes complètes, `0` incomplète, `19` représentables, `10` cibles vides
et `10` contre-exemples informatifs. Le premier contre-exemple non vide/non
total apparaît en `n=5` sur `paired_farthest`, avec exactement deux ordres cR :
`(0,1,3,2,4)` et `(0,1,4,3,2)`.

Interprétation : la route "l'ensemble des ordres cR est directement un PCNode"
est réfutée pour le scaffold du dépôt. Il reste possible qu'un PC-tree
Hsu/McConnell non enraciné plus fidèle représente cette famille ; T079 ne doit
donc pas être vendu comme théorème externe.

## Risques

- Les contraintes cR peuvent ne pas être exprimables comme contraintes d’arcs
  indépendantes.
- Des contraintes valables localement peuvent ne pas capturer les corrélations
  globales entre choix PC-tree.

## Prochaine action

Deux suites raisonnables :

- construire réellement le PC-tree/circular-ones des boules et l'intersecter
  avec le PC-tree donné, au lieu d'énumérer les frontiers ;
- tester si les familles de contraintes `C_ab` par seuil sont représentables
  par une structure round-order ou simultaneous PC/PQ-ordering imbriquée ;
- comparer le contre-exemple T079 à un modèle PC-tree non enraciné plus fidèle
  avant de conclure sur la PC-représentabilité générale ;
- exploiter `B(a,b)` arc comme filtre positif suffisant ou obstruction locale,
  sans l'utiliser comme caractérisation, puis chercher les corrélations
  supplémentaires qui restaurent la condition exacte one-side dans un PC-tree.

Complément revue externe post-T057 : si le CSP exact par quartets confirme que
les contraintes ont portée `<= 2`, alors le sous-cas où tous les choix locaux
effectifs sont booléens doit être traité comme une piste 2-SAT prioritaire.
Cette piste est distincte d'une vraie intersection circular-ones : elle passe
par les types de quartets cR, pas seulement par les boules métriques.
