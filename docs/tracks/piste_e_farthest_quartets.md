# Piste E - Obstructions farthest et quartets cR

## Question

Les obstructions farthest-neighbor suffisent-elles à caractériser les mauvais
ordres, ou faut-il utiliser les quartets cR exacts ?

## Résultat principal

Statut : preuve expérimentale avec contre-exemples minimaux.

La condition farthest-crossing brute n’est pas un critère de décision. Cette
condition brute n’est pas la Proposition 4.4 complète : elle ignore la clause
dégénérée non stricte mentionnée dans le papier `strongly-circular-sidma-1.pdf`.

Elle n’est pas nécessaire :

- matrice égal-distance à 4 points ;
- tout ordre est cR ;
- farthest brut échoue à cause de dégénérescences massives ;
- la condition Proposition 4.4 complète passe grâce à la clause dégénérée.

Elle n’est pas suffisante :

- exemple à 4 points avec farthest unique ;
- exemple à 4 points avec toutes les distances hors diagonale distinctes ;
- l’ordre passe farthest mais viole la condition pre-circular cR.

Artefacts :

- `tests/test_regression_counterexamples.py`;
- `docs/proof_obligations.md`;
- `docs/source_notes.md`;
- `find_precircular_cR_violation`;
- `find_farthest_crossing_violation`.
- `passes_farthest_prop_4_4_condition`.
- `find_farthest_prop_4_5_obstruction`.
- `passes_farthest_prop_4_5_order_test`.

## Données observées

Exploration exhaustive signalée par subagent :

- `n=4`, valeurs `{1,2,3}` : 405 cas `cR=True` mais `farthest=False`, 96 cas
  `cR=False` mais `farthest=True`.
- `n=5`, valeurs `{1,2,3}` : 31116 cas `cR=True` mais `farthest=False`, 24120
  cas `cR=False` mais `farthest=True`.

## Conséquence

Toute candidate basée sur farthest doit :

- traiter explicitement les égalités et dégénérescences ;
- ajouter des contraintes non-farthest ;
- ou annoncer un sous-cas strictement plus restreint.

La version Proposition 4.4 est une condition nécessaire pour un ordre cR
compatible. Elle n’est pas utilisée comme oracle global. Le prochain test utile
est de vérifier expérimentalement le couple Prop. 4.4/4.5 sur les ordres
quasi-circulaires.

## Prop. 4.5 sur ordre fixé

Statut : preuve expérimentale, ordre fixé seulement.

Le diagnostic `passes_farthest_prop_4_5_order_test` cherche l’absence de
certificat farthest du type :

- `x < x' < y < y'`, ou
- `x < y' < y < x'`,

avec `x' in F_x` et `y' in F_y`, et avec la clause non stricte qui exclut les
dégénérescences autorisées.

Résultat observé :

- aucun désaccord avec `is_precircular_order_cR` sur les ordres
  quasi-circulaires pour `n <= 5`, valeurs `{1,2,3}`;
- un test de régression exhaustif verrouille déjà le cas `n=4`;
- hors quasi-circularité, le diagnostic n’est pas suffisant et ne doit pas être
  utilisé comme oracle.

Prochaine action : utiliser ce diagnostic comme accélérateur ou générateur
d’obstructions pour le CSP/DP, sans le confondre avec l’existence dans PC-tree.

## Mauvais témoins de quartets

Statut : reformulation exacte pour ordre fixé ; contraintes d'arcs naïves
réfutées.

Pour une paire `{a,b}`, définir
`B(a,b) = {w : max(d(a,w), d(w,b)) > d(a,b)}`. Un ordre fixé est cR si et
seulement si, pour toute paire `{a,b}`, les éléments de `B(a,b)` n'apparaissent
pas sur les deux arcs ouverts séparés par `a,b`.

Le diagnostic `bad_witness_arc_constraints_report` compare cette condition
exacte à deux tentatives d'arcs indépendantes :

- `B(a,b)` arc : filtre suffisant observé, mais non nécessaire ;
- `B(a,b) union {a,b}` arc : ni nécessaire ni suffisant.

Les contre-exemples sont verrouillés dans `tests/test_dp_experiments.py`. La
suite utile n'est donc pas d'ajouter ces contraintes comme oracle, mais de les
utiliser pour produire des nogoods locaux ou des états DP qui mémorisent de
quel côté d'une paire les mauvais témoins ont déjà été vus.

T027 compile cette même obstruction comme atomes CSP : pour chaque paire
`{a,b}` et chaque couple `y,t in B(a,b)`, les orientations `(a,y,b,t)` et
`(a,t,b,y)` sont interdites. C'est une représentation plus canonique des
quartets cR : elle reste une contrainte de séparation de deux témoins, pas une
contrainte d'arc sur tout `B(a,b)`.

## Obstruction 4-locale réfutée

Statut : contre-exemple minimal enregistré.

T032 a trouvé une matrice binaire à 5 points telle que chaque sous-matrice
induite de taille 4 admet un ordre cR, mais la matrice complète n'en admet
aucun :

```text
[[0,1,1,2,2],
 [1,0,2,1,2],
 [1,2,0,1,2],
 [2,1,1,0,2],
 [2,2,2,2,0]]
```

Conséquence : les quartets cR restent l'obstruction exacte d'un ordre fixé, mais
la non-existence d'un ordre global n'est pas caractérisée par les seules
restrictions 4-points de la matrice. Les certificats héréditaires de petite
taille sont donc des rejets sound quand ils sont trouvés, pas une base
d'obstructions prouvée complète.

Artefacts : `four_local_non_cr_core`, `padded_four_local_non_cr`,
tests de régression `four_local_positive_global_negative`.

## Obstruction 5-locale réfutée

Statut : contre-exemple minimal enregistré.

T033 a trouvé une matrice binaire à 6 points telle que chaque sous-matrice
induite de taille 5 admet un ordre cR, mais la matrice complète n'en admet
aucun :

```text
[[0,1,1,1,1,1],
 [1,0,1,1,2,2],
 [1,1,0,2,1,2],
 [1,1,2,0,2,1],
 [1,2,1,2,0,1],
 [1,2,2,1,1,0]]
```

Conséquence : la hiérarchie des obstructions induites ne s'arrête pas au niveau
4 dans les expériences actuelles, et elle ne s'arrête pas non plus au niveau 5.
Les scans de petite taille restent des certificats négatifs héréditaires, pas
une caractérisation globale.

Artefacts : `five_local_non_cr_core`, `padded_five_local_non_cr`, tests de
régression `five_local_positive_global_negative`.

## Graphe haut non biparti plus hub bas

Statut : sous-cas négatif structurel prouvé, généralisant le cycle impair de
T033.

Dans une matrice binaire `low/high`, si le graphe des arêtes `high` est non
biparti et qu'il existe un hub à distance `low` de tous les autres sommets,
alors aucun ordre cR n'existe. En coupant l'ordre circulaire au hub, chaque
arête haute `{v,u}` fait de `u` un mauvais témoin pour la paire basse
`{hub,v}`. Donc tous les voisins hauts de chaque sommet `v` doivent être du
même côté de `v` dans l'ordre linéaire. En orientant chaque arête haute selon
cet ordre linéaire, chaque sommet devient source ou puits ; cela impose une
2-coloration source/puits du graphe haut. Un graphe haut non biparti contredit
cette contrainte.

Preuve expérimentale : énumération exhaustive de tous les graphes hauts
binaires avec un hub bas et `1..5` sommets non-hub ; aucun désaccord avec
l'oracle exact. Les graphes hauts bipartis testés servent de contrôles négatifs
pour le certificat.

Artefacts : `odd_high_cycle_plus_low_hub`,
`non_bipartite_high_graph_plus_low_hub`,
`candidate_non_bipartite_high_graph_low_hub_obstruction`.

## Cycle haut pair induit plus hub bas

Statut : sous-cas négatif structurel prouvé pour les cycles induits pairs de
longueur au moins `6`.

T035 montre que la frontière après T034 n'est pas "graphe haut biparti donc
positif". Avec un hub bas universel, `C4` haut est positif, mais `C6`, `C8` et
les cycles induits pairs plus longs sont négatifs.

La preuve passe par le lemme nécessaire de strong ordering du cas binaire hub
bas. Dans tout ordre cR coupé au hub, chaque sommet a ses voisins hauts d'un
seul côté ; dans une composante bipartie, cela induit des sources et puits. Les
ordres restreints aux deux parts doivent satisfaire la condition strong
ordering, sinon une paire basse manquante reçoit deux mauvais témoins sur deux
arcs opposés. Un cycle induit `C_{2r}`, `r >= 3`, viole toujours cette condition
en prenant le plus petit sommet d'une part et ses deux voisins cycliques.

Preuve expérimentale : les graphes hauts bipartis avec un hub bas et jusqu'à
`5` sommets non-hub sont tous positifs ; à `6` sommets non-hub, les `60`
négatifs sont exactement les labellisations de `C6`. `C8` plus hub est négatif
et n'a aucune obstruction induite de taille `6`, donc il échappe au scan
héréditaire `(4,5,6)`.

Artefacts : `even_high_cycle_plus_low_hub`,
`candidate_even_high_cycle_low_hub_obstruction`,
régression `test_even_high_cycle_low_hub_subcase_regression`.

## Strong ordering low-hub

Statut : suffisance prouvée pour le témoin `hubs, A, B` quand un strong
ordering est donné ; intégration candidate seulement comme témoin positif
vérifié et représenté.

`low_hub_strong_ordering_report` teste bornément si le graphe haut privé des
hubs admet un strong ordering. Ce diagnostic explique les certificats T034/T035
dans un langage commun : graphe non biparti impossible ; graphe biparti sans
strong ordering impossible dans les probes ; strong ordering trouvé donne le
témoin naturel `hubs, A, B`, qui est cR par le lemme bad-side et reste vérifié
ensuite par le prédicat fixed-order exact.

Résultat T036 : exhaustif oracle jusqu'à `5` sommets non-hub sans mismatch ;
sur tous les graphes à `6` sommets non-hub, le diagnostic retrouve `5117`
strong-ordering, `60` bipartis sans strong ordering, et `27591` non bipartis.
Les contrôles incluent `C4`, `C6`, `C8`, `K3,3`, matching, chain/Ferrers et un
tree négatif.

Limite : le rapport est factoriel et marqué incomplet si la limite de
permutations est atteinte. Il ne prouve pas encore l'existence dans un PC-tree
compact, car un témoin positif doit aussi être représenté.

Résultat T037 : `candidate_low_hub_strong_ordering_witness` accepte uniquement
un ordre produit par ce diagnostic après vérification directe cR et contrôle
`represents_order` si un PC-tree est fourni. Les échecs du diagnostic, les
limites de permutations et les témoins non représentés restent incomplets. Les
contrôles ajoutés couvrent chain/Ferrers, complete-bipartite, tree négatif,
PC-tree rigide non représentatif et `quasi_orders=[]`.

Résultat T039 : la famille `matching_high_graph_plus_low_hub` force un stress
positif indépendant de chain/complete. Le diagnostic essaie maintenant en
priorité les composantes biparties alignées côté `A` et côté `B`, ce qui trouve
les matchings permutés au premier essai tout en gardant la vérification directe
du témoin. Régressions ajoutées : matchings permutés multi-seed,
matchings avec plusieurs hubs, triangle haut avec `low=0`, et positif qui reste
`unsupported_permutation_limit` sous petite limite. Ce résultat ne prouve pas la
complétude : un scan subagent trouve seulement `1542/5117` positifs
strong-ordering à `m=6` avec `max_permutation_pairs=1`.

Résultat T040 : `iter_low_hub_strong_ordering_witnesses` parcourt plusieurs
témoins strong-ordering au lieu de s'arrêter au premier témoin global. La
candidate l'utilise pour trouver un témoin représenté par le PC-tree. Régression
ajoutée : un matching low-hub `n=18` avec racine `C` et deux gros blocs `P`
représente un ordre cR, mais pas le premier témoin strong-ordering ; avant T040,
la candidate restait placeholder après `64` samples, après T040 elle trouve un
témoin représenté après `761` couples testés. Les limites restent explicites :
si la borne de permutations est atteinte, l'absence de témoin représenté reste
incomplète.

Résultat T041 : `low_hub_ferrers_strong_ordering_report` reconnaît le sous-cas
chain/Ferrers par inclusion des voisinages du graphe haut, construit directement
un strong ordering et laisse `candidate.py` accepter seulement le témoin vérifié
cR et représenté. C'est un certificat positif polynomial pour ce sous-cas, pas
un rejet : matching low-hub reste volontairement non-Ferrers et passe par les
autres témoins. Un contre-exemple non-star est ajouté côté candidate : le
témoin Ferrers canonique peut être non représenté, donc la recherche doit
continuer vers un autre témoin représenté.

Résultat T042 : `low_hub_component_ferrers_strong_ordering_report` étend le
certificat positif aux unions disjointes de composantes chain/Ferrers. Les
composantes sont concaténées dans le même ordre côté `A` et côté `B`, puis le
témoin est revalidé par bad-side et par `represents_order`. Deux arêtes
disjointes désalignées forment une régression de limite : l'ordre des
composantes est une condition nécessaire de cette preuve. Les cas non-star où
le témoin component-wise n'est pas représenté restent une recherche incomplète,
pas un rejet.

## Prochaine action

Utiliser les témoins `find_precircular_cR_violation` comme source principale
d’obstructions. Pour low-hub, chercher une réduction polynomial-time de
reconnaissance strong-ordering générale ou un diagnostic d'intersection PC-tree
plus compact. Prochaine option raisonnable : intersecter le PC-tree avec les
ordres component-Ferrers/strong-ordering, ou préparer hors candidate une
reconnaissance bipartite permutation avec témoin.
