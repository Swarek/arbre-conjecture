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

Cette condition brute est distincte de la Proposition 4.4 de
`strongly-circular-sidma-1.pdf`, qui inclut une clause dégénérée non stricte.
Le prédicat expérimental `passes_farthest_prop_4_4_condition` encode cette
version séparément.

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

Observation expérimentale initiale : sur les ordres quasi-circulaires exhaustifs
testés en petit `n`, la version Proposition 4.4 n’a pas montré de faux négatif
cR. Cela reste une vérification expérimentale, pas une preuve interne au dépôt.

### Proposition 4.5 sur ordre quasi-circulaire fixé

Statut : preuve expérimentale, précondition quasi-circularité explicite.

`find_farthest_prop_4_5_obstruction` cherche un certificat farthest d’échec cR
du type décrit dans `strongly-circular-sidma-1.pdf`. Sur tous les ordres
quasi-circulaires exhaustifs testés pour `n <= 5`, valeurs `{1,2,3}`, l’absence
d’un tel certificat coïncide avec `is_precircular_order_cR`.

Limites :

- ce résultat concerne un ordre fixé ;
- il dépend de la précondition quasi-circularité ;
- il ne décide pas encore l’existence d’un bon ordre dans un PC-tree compact.

### Projection locale des obstructions

Statut : outil expérimental.

`measure_obstruction_support` projette les points d’un témoin cR/farthest sur les
branches des nœuds internes du PC-tree. Cela permet de mesurer si une obstruction
est visible localement dans un nœud `P` ou `C`. Cet outil ne prouve aucune
suffisance : il sert à tester les pistes A/B/C et à chercher des collisions où
deux contextes ont la même signature locale mais une validité cR différente.

### Prop. 4.5 comme nogood de frontier

Statut : preuve expérimentale / scaffold Piste C.

`prop45_nogood_frontier_report` compare, sur des frontiers énumérées, le filtre
`find_farthest_prop_4_5_obstruction is None` au prédicat exact
`is_precircular_order_cR`. Avec `require_quasi=True`, les ordres hors
précondition quasi-circulaire sont sautés explicitement.

Ce rapport vérifie une compatibilité d’ordre fixé et fournit des faux positifs
ou faux négatifs si la compatibilité échoue. Il ne satisfait pas encore les
obligations 2, 3 et 5 : il ne donne ni encodage compact de PC-tree, ni preuve de
suffisance globale, ni complexité polynomiale.

### CSP à domaines locaux P/C

Statut : conséquence directe expérimentale / scaffold Piste C.

`build_local_domains` associe une variable à chaque nœud interne supporté :
permutation de branches pour `P`, orientation forward/reverse pour `C`.
`frontier_from_assignment` reconstruit la frontier linéaire d’une affectation
complète, et `solve_nogood_csp(source="cr")` accepte une affectation si la
frontier canonique vérifie `is_precircular_order_cR`.

Obligations couvertes dans le périmètre expérimental :

- obligation 3 partielle : sur les arbres supportés testés, les frontiers issues
  des affectations coïncident avec `enumerate_frontiers` ;
- obligation 4 partielle : tout témoin renvoyé vient d’une affectation locale et
  est donc représenté par construction dans ce scaffold ;
- correction du filtre `source="cr"` : conséquence directe du prédicat exact
  d’ordre fixé, pas un nouveau théorème.

Limites restantes :

- pas de pruning compact ni de preuve de complexité ;
- un nœud `P` de degré supérieur à `max_p_degree` est `unsupported`, jamais une
  preuve de non-existence ;
- `source="prop45"` reste soumis à la précondition quasi-circulaire et ne doit
  pas être utilisé comme rejet global.

### Nogoods compilés de quartets cR

Statut : preuve expérimentale / scaffold Piste C.

`compile_cr_nogoods` part des quartets ordonnés qui violent l’inégalité cR et
projette chaque occurrence sur les variables locales calculées par
`quartet_support_paths`. Ce support inclut les nœuds internes où les quatre
labels sont répartis dans au moins deux branches, puis descend récursivement dans
les branches contenant au moins deux labels du quartet.

Obligations partiellement couvertes :

- nécessité des atoms : conséquence directe de la définition pre-circular cR ;
- représentation du témoin : comme T010, tout témoin accepté vient d’une
  affectation locale ;
- exactitude expérimentale du support : tests et probes n’ont trouvé ni
  sur-rejet ni sous-rejet sur petits arbres supportés.

Limites restantes :

- la compilation actuelle énumère les affectations complètes pour découvrir les
  signatures, donc elle ne prouve aucune borne polynomiale ;
- le nombre de nogoods peut être grand, et doit être mesuré avant toute
  intégration candidate ;
- la suffisance globale pour un PC-tree Hsu/McConnell compact reste non prouvée.

### Backtracking pruné par nogoods

Statut : preuve expérimentale / optimisation de scaffold Piste C.

`solve_pruned_nogood_csp` utilise les nogoods compilés pour couper une branche
dès que toutes les variables du support d’un nogood sont assignées et matchent
la signature interdite. Les feuilles survivantes sont reconstruites en frontiers
et revalidées par `is_precircular_order_cR`.

Ce que cela apporte :

- preuve expérimentale que les nogoods compilés peuvent être utilisés avant la
  construction de toutes les frontiers ;
- métriques séparant branches prunées, feuilles visitées, affectations complètes
  possibles et frontiers acceptées.

Limites restantes :

- la compilation des nogoods reste énumérative ;
- le pruning dépend de l’ordre des variables et peut être faible si les supports
  sont profonds ou larges ;
- aucune borne en `n` et `|T|` n’est prouvée.

### Benchmark interne CSP/nogoods

Statut : preuve expérimentale / mesure de limite.

`tools/pc_csp_internal_benchmark.py` mesure séparément compilation, solve pruné
post-compilation et filtre cR direct. Le benchmark rapide T013 montre déjà que
la compilation peut dominer le solve pruné, et que le nombre de nogoods uniques
peut être élevé même pour `n <= 7`.

Conséquence expérimentale : Piste C ne peut pas être promue en candidate générale
tant que la compilation reste fondée sur l’énumération complète des
affectations. La prochaine obligation est soit de prouver/implémenter une
compilation non énumérative, soit de basculer vers une signature DP ou un
sous-cas polynomial.

### Caractérisation bad-side d'un ordre fixé

Statut : conséquence directe pour ordre fixé + prédicat central exact depuis
T038.

Pour une paire `{a,b}` et un point `w` distinct des endpoints, définir
`bad(a,b,w)` par :

```text
max(D[a][w], D[w][b]) > D[a][b]
```

Pour un ordre circulaire fixé, la condition pre-circular cR est équivalente à
l'absence d'une paire `{a,b}` dont chacun des deux arcs ouverts contient au moins
un témoin mauvais. En effet, une violation cR est un quadruplet cyclique
`a, y, b, t` tel que les deux maxima de côté sont strictement supérieurs à
`D[a][b]`; réciproquement, deux mauvais témoins sur les deux arcs donnent ce
quadruplet.

Ce que cela couvre :

- obligation 1 fixed-order : les témoins mauvais sur deux arcs sont nécessaires,
  directement par réécriture de l'inégalité cR ;
- obligation 2 fixed-order : ils sont suffisants pour un ordre complet fixé ;
- obligation 6 fixed-order : les égalités sont traitées par le `>` strict, donc
  `max(...) == D[a][b]` ne crée pas d'obstruction.

Limites restantes :

- aucune décision d'existence dans un PC-tree compact ;
- aucune preuve que la signature de sous-arbre issue de cet invariant reste de
  taille polynomiale ;
- les obligations 3, 4 et 5 restent ouvertes pour une vraie candidate générale.

Preuve expérimentale T014 : tests unitaires et probe exhaustif `n=4,5`, valeurs
`{1,2,3}`, puis random `n=6,7`, sans désaccord avec
`is_precircular_order_cR` sur `715875` comparaisons. Un probe subagent
indépendant a ajouté des familles `random/cycle/permuted_cycle/block/
ultrametric/equal/non_strict/paired_farthest/mixed` jusqu'à `n=9`, sans
désaccord sur `926775` comparaisons. La variante non stricte `>=` est
explicitement exclue, car elle rejette les égal-distance.

Conséquence T038 : `passes_bad_side_precircular_cR` et
`find_bad_side_precircular_cR_violation` sont maintenant dans `predicates.py`.
La candidate les utilise pour valider les témoins produits ou énumérés en
`O(n^3)` au lieu de scanner les quadruplets. Les tools de correction gardent
`is_precircular_order_cR` comme oracle indépendant par quadruplets.

Preuve expérimentale T038 : tests exhaustifs `n=4`, rotations/renversements,
égal-distance, cas avec deux mauvais témoins sur le même arc, probe local
`6058` comparaisons et probe subagent `153291` comparaisons, sans désaccord.
La complexité observée de `make bench` sur `mixed/star` descend à une médiane
`0.0275s` à `n=100`, sans timeout ni incomplet.

### Signature bad-side de bloc

Statut : outil expérimental / limite de compacité observée.

`block_bad_side_signature` applique l'invariant bad-side à une sous-frontier
orientée supposée contiguë. La signature conserve :

- les endpoints du bloc ;
- les masques `inside/external`, indiquant si des témoins mauvais internes sont
  à gauche, à droite, ou des deux côtés d'un label interne face à un endpoint
  externe ;
- les masques `inside/inside`, avec un bit `between` et un bit
  `through-boundary`, indiquant si les témoins mauvais internes sont entre les
  deux endpoints du bloc ou sur le côté qui rejoint le contexte externe.

Ce que cela couvre :

- obligation 1 expérimentale : les masques enregistrent des obstructions
  nécessaires issues directement de la caractérisation fixed-order ;
- obligation 6 expérimentale : les égalités restent gouvernées par le `>` strict
  hérité de `is_bad_witness`.

Limites :

- cette signature n'est pas prouvée suffisante pour composer des sous-arbres ;
- elle n'établit aucune complexité polynomiale ;
- la probe T015 montre qu'elle devient quasi injective sur `cycle`, `random` et
  `paired_farthest`, donc elle ne constitue pas en l'état une compression DP.

Preuve expérimentale T015 : sur blocs de taille `4,5,6`, familles
`equal/cycle/block/random/paired_farthest`, aucune collision réelle n'a été
trouvée dans les contextes testés, mais le ratio `#signatures / #frontiers` vaut
souvent `0.95..1.0` hors égal-distance et block partiel. Le chercheur de
collisions détecte bien des collisions lorsque la signature est volontairement
affaiblie ou réduite aux endpoints. Une probe subagent indépendante a trouvé des
collisions de signature simples mais aucune collision sémantique sur `37924`
checks de même contexte, ce qui suggère une signature cohérente mais peu
compressive.

### Sous-cas universel par nombre de témoins mauvais

Statut : théorème prouvé pour ce sous-cas + intégré à la candidate.

Pour chaque paire `{a,b}`, poser :

```text
B(a,b) = {w != a,b : max(D[a][w], D[w][b]) > D[a][b]}
```

Si `|B(a,b)| <= 1` pour toute paire, alors tout ordre circulaire est circular
Robinson. Par la caractérisation bad-side d'un ordre fixé, une violation cR
demanderait une paire `{a,b}` avec un témoin mauvais sur chacun des deux arcs
ouverts, donc au moins deux témoins mauvais globaux pour cette paire.

Ce que cela couvre :

- obligation 1 : le critère utilise une condition suffisante issue directement
  de l'inégalité cR ;
- obligation 2 dans le sous-cas : tout ordre représenté est accepté, donc la
  suffisance est immédiate ;
- obligation 3 dans le sous-cas : aucun ordre représenté n'est manqué, puisque
  tous sont cR ;
- obligation 4 dans le sous-cas PC-tree : `sample_frontier` produit une frontier
  représentée par construction ;
- obligation 5 dans le sous-cas : le test du critère est `O(n^3)` et la
  construction du témoin PC-tree est `O(|T|)` ;
- obligation 6 : les égalités sont traitées par le `>` strict dans la définition
  de témoin mauvais.

Limites :

- c'est seulement une condition suffisante pour "tous les ordres sont cR", pas
  une caractérisation de l'existence générale ;
- si le critère échoue, la candidate retombe sur le placeholder grande taille ;
- les familles planted-cycle, paired-farthest et PC-tree généraux restent
  ouvertes.

Preuve expérimentale T016 : tests unitaires, probe `n=9..30` sur
star/balanced/mixed avec `33` checks, et faux ami à arête basse vérifié hors
sous-cas.

### Graphe haut non biparti avec hub bas

Statut : certificat négatif prouvé pour ce sous-cas + intégré à la candidate.

`candidate_non_bipartite_high_graph_low_hub_obstruction` traite les matrices à
deux distances positives `low < high` dont le graphe des arêtes `high` contient
au moins une composante non bipartie et au moins un sommet isolé. Un sommet
isolé dans le graphe haut est à distance `low` de tous les autres sommets ; on
l'appelle hub bas.

Preuve :

- fixer un hub bas `h` et couper tout ordre circulaire supposé cR en `h` ;
- fixer une arête haute `{v,u}` du graphe haut ;
- la paire `{h,v}` a distance `low` ;
- `u` est un témoin mauvais pour `{h,v}`, car
  `max(d(h,u), d(u,v)) = high > low` ;
- dans tout ordre cR, tous les voisins hauts de `v` doivent donc être du même
  côté de `v` dans l'ordre linéaire obtenu après la coupure en `h` ;
- orienter chaque arête haute selon cet ordre linéaire force chaque sommet du
  graphe haut à être source ou puits ;
- chaque arête va d'une source vers un puits, donc le graphe haut devrait être
  biparti ;
- si le graphe haut est non biparti, contradiction.

Ce que cela couvre :

- obligation 1 : le certificat utilise la caractérisation bad-side exacte d'un
  ordre fixé ;
- obligation 2 négative : l'impossibilité d'alternance prouve qu'aucun ordre
  complet ne peut être cR ;
- obligation 3 : aucun ordre représenté par le PC-tree n'est manqué, car aucun
  ordre complet n'existe ;
- obligation 5 : la détection inspecte les deux valeurs de distance et le graphe
  `high`, donc elle est polynomiale en `n`.

Limites :

- le certificat exige exactement deux niveaux de distance positive dans
  l'implémentation courante ;
- il ne traite pas les matrices à plus de deux niveaux, ni les encodages où le
  niveau bas hors diagonale vaut `0` ;
- il ne conclut rien quand le graphe haut est biparti, même si l'instance peut
  être négative pour une autre raison ;
- il est négatif seulement et ne fournit aucun témoin positif.

### Cycle haut pair induit avec hub bas

Statut : certificat négatif prouvé pour le sous-cas exact cycle + hubs,
intégré à la candidate.

`candidate_even_high_cycle_low_hub_obstruction` traite les matrices à deux
distances positives `low < high` dont le graphe des arêtes `high` est formé
d'un cycle induit pair connecté de longueur au moins `6`, plus au moins un hub
isolé dans ce graphe. Le cas `C4` est explicitement exclu : il admet des ordres
cR.

Preuve :

- dans toute matrice binaire avec hub bas `h`, couper un ordre cR supposé en
  `h` ;
- pour chaque sommet `v`, tous ses voisins hauts doivent être du même côté de
  `v`, sinon la paire basse `{h,v}` a des mauvais témoins sur les deux arcs ;
- dans une composante haute bipartie, cela donne une bipartition source/puits ;
- en restreignant l'ordre linéaire aux sources `A` et aux puits `B`, on obtient
  une condition de strong ordering nécessaire : si `a_i < a_k`, `b_j < b_l`,
  et si les arêtes croisées `a_i b_l`, `a_k b_j` sont hautes, alors les deux
  arêtes droites `a_i b_j`, `a_k b_l` doivent aussi être hautes. Sinon la paire
  basse manquante a les deux arêtes croisées comme mauvais témoins sur des arcs
  opposés ;
- un cycle induit `C_{2r}` avec `r >= 3` n'a pas de strong ordering. Prendre le
  plus petit sommet `a_p` de sa part `A`. Ses deux voisins cycliques sont
  `b_{p-1}` et `b_p`. Si `b_{p-1} < b_p`, les arêtes croisées
  `a_p b_p` et `a_{p-1} b_{p-1}` forceraient la corde `a_{p-1} b_p`, absente
  dans un cycle induit de longueur au moins `6`. Le cas symétrique
  `b_p < b_{p-1}` force de même la corde `a_{p+1} b_{p-1}` ;
- donc aucun ordre cR ne peut exister.

Ce que cela couvre :

- obligation 1 : le certificat dérive de la condition bad-side exacte d'un
  ordre fixé ;
- obligation 2 négative : l'absence de strong ordering pour les cycles induits
  pairs de longueur `>=6` prouve la non-existence globale ;
- obligation 3 : aucun ordre représenté par le PC-tree n'est manqué, car aucun
  ordre complet n'existe ;
- obligation 5 : la détection scanne les deux valeurs de distance et vérifie
  degré `2` + connexité du graphe haut, donc coût polynomial en `n`.

Limites :

- le certificat ne traite que le graphe haut exactement cycle induit plus hubs ;
- il ne rejette pas les graphes bipartis arbitraires, car `K_{3,3}` plus hub
  est positif dans les probes malgré ses cycles pairs non induits ;
- le lemme de strong ordering suggère une caractérisation plus large du cas
  binaire hub bas, mais cette caractérisation complète n'est pas encore
  intégrée ni prouvée dans le dépôt ;
- les encodages avec niveau bas hors diagonale `0` restent hors de la détection
  actuelle.

### Strong ordering du graphe haut avec hub bas

Statut : suffisance du témoin strong-ordering prouvée pour le sous-cas binaire
hub bas ; reconnaissance et compatibilité PC-tree encore bornées. T037/T040 en
intègrent seulement la direction positive vérifiée comme générateur de témoin ;
ce n'est pas un théorème de caractérisation complète du problème PC-tree.

Pour une matrice binaire `low/high` avec au moins un hub bas universel, T035
suggère la conjecture suivante sous star/all-orders : il existe un ordre cR si
et seulement si le graphe des arêtes `high`, privé des hubs bas, admet un
strong ordering de graphe biparti. Un strong ordering est une bipartition
`A,B` avec deux ordres linéaires tels que, pour `a_i < a_k` et `b_j < b_l`, les
arêtes croisées `a_i b_l` et `a_k b_j` forcent aussi les arêtes droites
`a_i b_j` et `a_k b_l`.

Conséquence prouvée partielle côté nécessité :

- nécessité locale : dans tout ordre cR coupé en un hub bas, chaque sommet a
  tous ses voisins hauts du même côté. Cela oriente les arêtes hautes d'une
  composante bipartie de sources vers puits ;
- une violation du strong ordering produit une paire basse avec deux mauvais
  témoins sur deux arcs opposés, donc viole la condition bad-side d'ordre fixé.

Suffisance prouvée pour un strong ordering donné :

- pour une paire à distance `high`, aucun témoin mauvais n'existe ;
- pour deux hubs, aucun témoin mauvais n'existe ;
- pour `hub, a_i`, les seuls témoins mauvais sont dans `N(a_i) subset B`, donc
  ils sont tous sur un seul arc de l'ordre `hubs, A_order, B_order`; de même
  pour `hub, b_j` ;
- pour deux sommets d'une même part, tous les témoins mauvais sont dans l'autre
  part, qui est contiguë, donc ils sont encore sur un seul arc ;
- pour une paire basse croisée `a_i, b_j` non arête, le strong ordering force
  les voisinages `N(b_j)` dans `A` et `N(a_i)` dans `B` à être des intervalles.
  Les deux configurations qui placeraient des témoins mauvais sur les deux arcs
  donneraient deux arêtes croisées et forceraient l'arête droite `a_i b_j`,
  contradiction ;
- donc aucune paire basse n'a de mauvais témoins sur les deux arcs. Par le
  lemme bad-side d'ordre fixé, `hubs, A_order, B_order` est cR. Les égalités et
  le cas `low=0` restent couverts par le `>` strict du témoin mauvais.

Conséquence directe utilisée par la candidate T037/T040 :

- si le diagnostic produit un ordre, que `candidate.py` valide sa forme, que
  `passes_bad_side_precircular_cR(D, order)` est vrai, et que `represents_order(T,
  order)` est vrai quand un PC-tree est fourni, alors retourner `exists=True`
  est sound indépendamment de la conjecture strong-ordering ;
- T040 parcourt plusieurs témoins strong-ordering pour trouver un témoin
  représenté par le PC-tree au lieu de s'arrêter au premier témoin global ;
- aucun statut négatif du diagnostic n'est utilisé comme rejet complet, et une
  limite de permutations reste un résultat incomplet.

Preuve expérimentale T036 :

- contrôles positifs : `C4 + hub`, `K3,3 + hub`, matching, chain/Ferrers ;
- contrôles négatifs : `C6 + hub`, `C8 + hub`, tree haut
  `(1,2),(1,5),(2,3),(2,4),(3,6),(4,7)` plus hub ;
- exhaustif `m <= 5` non-hub : le diagnostic strong-ordering coïncide avec
  l'oracle exact ;
- exhaustif diagnostic `m=6` : `5117` strong-ordering trouvés, `60` graphes
  bipartis sans strong ordering, `27591` graphes non bipartis.

Preuve expérimentale T037 :

- chain/Ferrers et complete-bipartite low-hub sous star sont acceptés jusqu'à
  `n=80` dans les benchmarks ciblés, toujours après vérification directe du
  témoin ;
- le tree négatif T036, un PC-tree rigide ne représentant pas le témoin et
  `quasi_orders=[]` restent des contrôles de non-contournement ;
- `make check`, `make hunt-counterexamples` et `make bench` restent verts.

Preuve expérimentale T039 :

- matching low-hub permuté : `matching_high_graph_plus_low_hub/star` est accepté
  avec `0` timeout et `0` incomplet jusqu'à `n=101`, après validation directe du
  témoin ;
- les matchings permutés multi-seed et les matchings avec plusieurs hubs sont
  trouvés au premier couple d'ordres grâce à la priorité composante-alignée ;
- le cas `low=0` est explicitement régressé par un triangle haut non biparti,
  pour éviter de confondre distances nulles hors diagonale et absence de niveau
  bas ;
- une petite limite de permutations reste documentée comme incomplète même sur
  certains positifs.

Preuve expérimentale T040 :

- un PC-tree non-star à `n=18` avec deux gros blocs `P` représente un témoin
  matching low-hub cR, mais pas le premier témoin strong-ordering global ;
- avant T040, la candidate restait `candidate_large_n_placeholder` après les
  `64` samples ; après T040, elle trouve un témoin représenté après `761`
  couples de permutations contrôlés par la limite ;
- le benchmark ciblé matching/star reste inchangé qualitativement : `0`
  timeout et `0` incomplet jusqu'à `n=101` dans la probe T040.

Conséquence partielle prouvée T039 :

- pour un graphe haut matching, choisir une orientation de chaque composante
  arête et l'ordre `hubs, A_1..A_m, B_1..B_m` place, pour toute paire basse, les
  éventuels mauvais témoins hauts sur un seul arc ; les paires hautes n'ont pas
  de mauvais témoin. Ce lemme couvre le sous-cas matching mais ne caractérise pas
  tous les graphes bipartis à strong ordering.

Obligations ouvertes avant théorème général :

- prouver la nécessité complète du strong ordering pour tous les cas binaires
  hub bas, ou documenter un contre-exemple ;
- remplacer l'énumération bornée/factorielle par un algorithme polynomial de
  reconnaissance ou documenter précisément la borne ;
- vérifier la représentation PC-tree de tout témoin positif, ce qui est fait par
  la candidate mais pas encore par un algorithme complet de recherche ;
- séparer star/all-orders et existence dans un PC-tree arbitraire ;
- traiter en preuve les cas où le niveau bas hors diagonale vaut `0` et les cas
  dégénérés avec plusieurs hubs ; le code les teste mais cela ne remplace pas un
  argument général ;
- expliquer pourquoi les matrices avec plus de deux niveaux hors diagonale
  sortent du sous-cas.

### Sous-cas chain/Ferrers high graph avec hub bas

Statut : théorème prouvé pour un certificat positif ; sous-cas suffisant, pas
caractérisation complète.

Dans une matrice binaire `low/high` avec au moins un hub bas, si le graphe haut
privé des hubs est biparti Ferrers/chain, alors ses voisinages peuvent être
ordonnés par inclusion. En triant une part par voisinages décroissants et
l'autre dans l'ordre Ferrers opposé, on obtient un strong ordering. Par le
lemme bad-side T040, l'ordre `hubs, A_order, B_order` est circular Robinson.

Ce que cela couvre :

- obligation 1/2 positive : le strong ordering construit donne un témoin cR par
  le lemme bad-side ;
- obligation 4 : `candidate.py` accepte seulement si l'ordre est représenté par
  `represents_order(T, order)` quand un PC-tree est fourni ;
- obligation 5 dans ce sous-cas : bipartition, test d'inclusion des voisinages,
  construction de l'ordre et validation directe sont polynomiaux ; le coût
  dominant reste la validation fixed-order `passes_bad_side_precircular_cR` en
  `O(n^3)` dans la candidate ;
- obligation 6 : les égalités du cas binaire non strict, y compris `low=0`
  hors diagonale, restent gouvernées par le `>` strict des mauvais témoins.

Limites :

- le critère n'est pas nécessaire : les matchings low-hub et d'autres graphes
  strong-ordering positifs ne sont pas forcément Ferrers ;
- sur PC-tree non-star, un témoin Ferrers non représenté ne prouve pas
  `exists=False` ;
- les matrices non binaires, sans hub bas, ou avec graphe haut non Ferrers
  restent hors sous-cas ;
- aucun échec de reconnaissance Ferrers ne doit être converti en rejet.

Preuve expérimentale T041 :

- `permuted_chain_high_graph_plus_low_hub/star` est accepté après permutation
  des labels jusqu'à `n=101` dans le benchmark ciblé, avec `0` timeout et `0`
  incomplet ;
- `matching_high_graph_plus_low_hub` est régressé comme positif non-Ferrers :
  le détecteur Ferrers ne doit pas devenir un critère nécessaire ;
- un contre-exemple PC-tree non-star montre que le témoin Ferrers construit
  peut être cR mais non représenté alors qu'un autre témoin représenté existe ;
  `candidate.py` doit donc continuer la recherche après un témoin positif non
  représenté, jamais conclure `False`.

### Sous-cas union de composantes chain/Ferrers high graph avec hub bas

Statut : théorème prouvé pour un certificat positif ; sous-cas suffisant, pas
caractérisation complète.

Dans une matrice binaire `low/high` avec hubs bas, supposons que le graphe haut
privé des hubs ait des composantes biparties `C_1,...,C_k`, et que chaque
composante admette un ordre Ferrers local `A_c,B_c`. En concaténant les
composantes dans le même ordre côté `A` et côté `B`, tout couple d'arêtes
croisées entre deux composantes distinctes devient impossible : l'ordre côté
`A` impose `p <= q` tandis que l'ordre côté `B` impose `q <= p`, donc les deux
arêtes croisées viennent de la même composante. Le strong ordering local donne
alors les deux arêtes droites. Par le lemme bad-side T040, l'ordre
`hubs, A_1,...,A_k, B_1,...,B_k` est circular Robinson.

Ce que cela couvre :

- obligations 1/2 positives : le strong ordering component-wise est suffisant
  pour obtenir un témoin cR par le lemme bad-side ;
- obligation 4 : `candidate.py` accepte seulement si l'ordre est représenté par
  `represents_order(T, order)` quand un PC-tree est fourni ;
- obligation 5 dans ce sous-cas : bipartition, reconnaissance Ferrers locale,
  concaténation et validation directe sont polynomiales ; la validation
  fixed-order `passes_bad_side_precircular_cR` reste le coût dominant du
  scaffold ;
- obligation 6 : `low=0`, hubs multiples et égalités binaires restent traités
  par le `>` strict des mauvais témoins ; les singletons sans arête haute sont
  des hubs, pas des composantes privées.

Limites :

- le critère n'est pas nécessaire : il existe des graphes bipartis
  strong-ordering positifs connectés qui ne sont pas Ferrers ;
- l'ordre des composantes doit être le même côté `A` et côté `B`; deux arêtes
  disjointes désalignées suffisent à créer une violation ;
- sur PC-tree non-star, un témoin component-wise non représenté ne prouve pas
  `exists=False` ;
- aucun échec `not_component_ferrers_high_graph` ne doit être converti en
  rejet.

Preuve expérimentale T042 :

- `permuted_disjoint_chain_high_graph_plus_low_hub/star` est accepté après
  permutation des labels jusqu'à `n=101`, avec `0` timeout et `0` incomplet ;
- un cas non-star `n=9` verrouille que la candidate continue après un témoin
  component-wise cR mais non représenté ;
- un cas matching non-star `n=17` documente une limite restante : un témoin
  représenté est connu, mais la candidate peut rester incomplète si la recherche
  factorielle ne l'atteint pas.

### Témoin matching low-hub guidé par PC-tree

Statut : conséquence directe / certificat positif sound ; pas une intersection
complète PC-tree/strong-ordering.

Dans une matrice binaire `low/high` avec hubs bas et graphe haut matching, tout
ordre `hubs, A_1,...,A_m, B_1,...,B_m` alignant les paires mates dans le même
ordre est cR par le lemme bad-side : les paires hautes n'ont pas de mauvais
témoin, les paires basses dans un même côté ont leurs mauvais témoins mates sur
un seul arc, et les paires croisées non mates ont leurs deux mauvais témoins sur
un même arc grâce à l'ordre aligné.

T043 ne prouve pas que le PC-tree contient un tel ordre. Il cherche seulement,
dans `sample_frontier(T)` puis dans un nombre borné de frontiers canoniques, un
segment avec exactement un endpoint de chaque paire. Chaque ordre construit est
accepté seulement après validation `passes_bad_side_precircular_cR` et
`represents_order(T, order)`.

Ce que cela couvre :

- obligation 1/2 positive : le témoin matching aligné est cR ;
- obligation 4 : le témoin renvoyé est contrôlé par `represents_order` ;
- obligation 6 : `low=0` et hubs multiples restent sound grâce au `>` strict
  des mauvais témoins ;
- obligation de séparation : l'échec du rapport reste incomplet, jamais une
  preuve de non-existence.

Limites :

- sous-cas matching seulement, pas graphes bipartis strong-ordering généraux ;
- les hubs peuvent devoir être séparés dans un ordre représenté ; T043 force un
  bloc de hubs et peut donc manquer des positifs ;
- la recherche de frontiers est bornée par `frontier_limit` ;
- un segment dans un frontier représenté ne suffit pas : l'ordre reconstruit
  peut être cR mais non représenté, d'où le garde obligatoire.

Preuve expérimentale T043 :

- le cas non-star T042 `n=17` devient positif complet avec `frontiers_sampled=0`
  et `segments_checked=10` ;
- le cas non-star T040 `n=18` devient positif complet avec `frontiers_sampled=0`
  et `segments_checked=3` ;
- un contre-exemple split-hubs `n=6` et un cas de limite `n=8` sont régressés
  pour documenter que T043 reste incomplet.

### Témoins positifs échantillonnés

Statut : conséquence directe / clarification de la candidate.

Lorsqu'une recherche non exhaustive trouve un ordre représenté et vérifie
`is_precircular_order_cR(D, order)`, la réponse `exists=True` est certifiée par
le témoin. Cela ne rend pas la recherche complète pour les réponses négatives :
si aucun ordre échantillonné ne marche, `complete=False` reste obligatoire.

Ce que cela couvre :

- obligation 4 pour les positifs : avec `pc_tree`, l'ordre vient de
  `enumerate_frontiers`; avec `quasi_orders`, il vient de la famille fournie ;
  sans PC-tree, tout ordre sur `0..n-1` est admissible ;
- obligation 1/2 pour un résultat positif ponctuel : le témoin est vérifié par
  le prédicat fixed-order exact.

Limites :

- aucune preuve de non-existence ;
- aucune amélioration de complexité worst-case ;
- les résultats `False` du placeholder restent incomplets et doivent rester
  visibles dans les rapports.

### Famille explicite `quasi_orders` bornée

Statut : sous-cas exact intégré à la candidate pour une famille fournie
explicitement, finie et petite.

`candidate_exact_bounded_quasi_orders` s'applique seulement quand
`quasi_orders` expose une longueur fiable et que cette longueur est au plus
`EXACT_QUASI_ORDER_LIMIT`. Dans ce cas, la candidate valide chaque ordre fourni
comme permutation de `0..n-1`, teste toute la famille par
`is_precircular_order_cR`, puis retourne une décision complète relative à cette
famille explicite.

Ce que cela couvre :

- obligation 1 : chaque ordre inspecté est testé par le prédicat fixed-order
  exact ;
- obligation 2 : un témoin positif vérifié suffit pour prouver l'existence dans
  la famille explicite ;
- obligation 3 dans ce sous-cas : si la longueur est sous la limite, toute la
  famille `quasi_orders` fournie est inspectée ;
- obligation 4 : le témoin renvoyé appartient à la famille explicite fournie ;
- obligation 5 dans ce sous-cas : le temps est borné par
  `O(EXACT_QUASI_ORDER_LIMIT * n^4)` avec le prédicat direct actuel, hors coût
  de construction de la famille par l'appelant.

Limites :

- la complétude est relative à `quasi_orders`, pas au PC-tree et pas à tous les
  ordres quasi-circulaires ;
- si `quasi_orders` et `pc_tree` sont fournis ensemble, la sémantique actuelle
  garde la priorité à la famille explicite, pas à l'intersection des deux ;
- les itérateurs non dimensionnés ou les familles au-dessus de la limite restent
  soumis à l'échantillonnage incomplet ;
- ce sous-cas ne réduit pas directement les incomplets des benchmarks
  `pc_tree=star`, qui n'utilisent pas `quasi_orders`.

### PC-tree exact à frontiers bornées

Statut : sous-cas exact intégré à la candidate pour le scaffold P/C/leaf.

`candidate_exact_bounded_pc_tree_frontiers` calcule un upper bound indépendant
de l'énumération sur le nombre de frontiers représentées. Si ce bound est au
plus `EXACT_PC_TREE_FRONTIER_LIMIT`, toutes les frontiers sont énumérées sans
limite et testées par `is_precircular_order_cR`.

Depuis T040, la borne distingue la racine circulaire des nœuds internes : un
nœud `P` racine compte les permutations circulaires de ses branches modulo
renversement, et un nœud `C` racine ne compte pas deux orientations qui deviennent
identiques modulo renversement circulaire. Les nœuds internes gardent une borne
linéaire conservatrice. Cette correction reste un surcomptage sûr, mais évite de
saturer des cas où l'énumération canonique réelle est petite.

Ce que cela couvre :

- obligation 1 : la condition testée sur chaque ordre est le prédicat fixed-order
  exact ;
- obligation 2 : si une frontier représentée passe le prédicat, le témoin
  suffit ;
- obligation 3 dans ce sous-cas : toutes les frontiers représentées sont
  énumérées parce que la borne est indépendante et sous la limite ;
- obligation 4 : l'ordre vient de `enumerate_frontiers(pc_tree)`, donc il est
  représenté dans le scaffold ;
- obligation 5 dans ce sous-cas : le temps est borné par
  `O(frontier_limit * n^4)` pour le test direct actuel, plus le calcul de borne
  saturé ; hors sous-cas, aucune décision négative n'est prise.

Limites :

- la borne peut surcompter, ce qui est sûr mais incomplet ;
- les grands `P` restent hors sous-cas et ne doivent pas produire de rejet
  complet ;
- cette preuve concerne le scaffold PC-tree enraciné, pas la totalité d'une
  implémentation Hsu/McConnell ;
- la branche est ignorée quand `quasi_orders` explicite est fourni, pour ne pas
  décider sur un espace différent de celui demandé.

### Petite sous-matrice interdite

Statut : certificat négatif prouvé quand une obstruction est trouvée.

`candidate_small_forbidden_submatrix_obstruction` cherche des sous-ensembles de
tailles listées dans `SMALL_FORBIDDEN_SUBMATRIX_ORDERS`, actuellement
`(4, 5, 6)`, jusqu'à `SMALL_FORBIDDEN_SUBMATRIX_LIMIT = 4096` sous-ensembles
par taille. Pour chaque sous-ensemble inspecté, la sous-matrice induite est
renumérotée et testée exactement par la baseline brute-force de petite taille.
Si aucun ordre cR n'existe sur cette sous-matrice, la candidate retourne
`exists=False` et `complete=True` pour l'instance complète.

Preuve :

- restriction héréditaire : si un ordre circulaire complet est cR pour `D`,
  alors sa restriction à n'importe quel sous-ensemble est cR pour la
  sous-matrice induite, car les quadruplets du sous-ordre gardent le même ordre
  cyclique et les mêmes distances ;
- contraposée : si une sous-matrice induite n'a aucun ordre cR, aucun ordre
  complet ne peut être cR ;
- le PC-tree ne peut pas réparer cette obstruction, puisqu'il ne fait que
  restreindre la famille des ordres complets admissibles.

Ce que cela couvre :

- obligation 1 : le certificat négatif repose sur le prédicat fixed-order exact
  appliqué exhaustivement à la sous-matrice ;
- obligation 2 négative : l'obstruction induite est suffisante pour rejeter
  l'existence globale ;
- obligation 3 : aucun ordre représenté n'est manqué dans ce sous-cas, car
  aucun ordre complet sur `X` ne peut être cR ;
- obligation 5 dans ce sous-cas : le temps est borné par
  `O(SMALL_FORBIDDEN_SUBMATRIX_LIMIT * sum_k c_k)`, où `k` parcourt les tailles
  configurées et `c_k` est le coût constant de l'oracle brute-force sur `k`
  labels.

Limites :

- absence d'obstruction dans la fenêtre de recherche ne prouve rien ;
- le certificat est négatif seulement, il ne fournit aucun témoin positif ;
- ce n'est pas une caractérisation des randoms ni du problème général ;
- si le PC-tree fourni est invalide, ce certificat ne doit pas être interprété
  comme une validation de l'entrée PC-tree.

Contre-exemple T032 à la caractérisation 4-locale :

```text
[[0,1,1,2,2],
 [1,0,2,1,2],
 [1,2,0,1,2],
 [2,1,1,0,2],
 [2,2,2,2,0]]
```

Cette matrice n'admet aucun ordre cR global, mais chacune de ses sous-matrices
induites de taille 4 en admet un. Elle prouve que les obstructions 4-points ne
caractérisent pas la non-existence globale. L'ajout de la taille 5 est donc un
certificat héréditaire supplémentaire, pas une preuve de base finie
d'obstructions.

Contre-exemple T033 à la caractérisation 5-locale :

```text
[[0,1,1,1,1,1],
 [1,0,1,1,2,2],
 [1,1,0,2,1,2],
 [1,1,2,0,2,1],
 [1,2,1,2,0,1],
 [1,2,2,1,1,0]]
```

Cette matrice n'admet aucun ordre cR global, mais chacune de ses sous-matrices
induites de taille 5 en admet un. Elle réfute à son tour une caractérisation
par obstructions 5-points seulement. L'ajout de la taille 6 reste donc un
certificat négatif borné, pas une preuve de complétude.

### Membership PC-tree d'un ordre fixé

Statut : théorème prouvé pour le scaffold P/C/leaf enraciné, pas pour une
implémentation Hsu/McConnell complète.

`represents_order(T, order)` teste maintenant l'appartenance d'un ordre
circulaire fixé sans énumérer les frontiers quand `limit is None`. La partie
linéaire récursive vérifie que les feuilles de chaque enfant forment un bloc
contigu ; un nœud `P` accepte toute permutation de ces blocs, un nœud `C`
accepte seulement l'ordre local forward ou reverse. Les rotations et le
renversement global ne sont essayés qu'au root circulaire.

Ce que cela couvre :

- obligation 3/4 pour un témoin fixé dans le scaffold : un ordre accepté est
  représenté par construction inductive, et un ordre représenté par
  `_linear_frontiers` est accepté par la même induction ;
- obligation 5 dans le scaffold : l'implémentation actuelle est polynomiale,
  avec un facteur de rotations au root et des ensembles de labels recalculés ;
- obligation de cas dégénérés structurels : les `C` internes ne sont pas
  traités modulo rotation.

Limites :

- ce n'est pas une preuve pour les vrais PC-trees non enracinés
  Hsu/McConnell ;
- avec `limit`, `represents_order` garde l'ancien comportement de diagnostic
  par énumération bornée et ne doit pas être utilisé pour prouver un rejet ;
- ce test ne dit rien sur cR, seulement sur la représentation d'un ordre fixé.

Preuve expérimentale T019 : tests unitaires et probe locale ont comparé ce test
à `enumerate_frontiers` sur star, balanced `C/P/mixed` et arbres P/C imbriqués
jusqu'à `n <= 8`, `11837` checks sans désaccord. Un test verrouille le cas où
un `C` interne ne doit pas accepter une rotation locale.

### Témoin cycle par distances minimales

Statut : conséquence directe pour positifs vérifiés / sous-cas expérimental.

Si le graphe des arêtes de distance minimale positive est un cycle simple
couvrant tous les sommets, `candidate.py` reconstruit un ordre cyclique. Cet
ordre n'est accepté que si `is_precircular_order_cR` le valide et si la
représentation est certaine : pas de PC-tree fourni, ou `represents_order`
accepte l'ordre pour le PC-tree scaffold.

Ce que cela couvre :

- obligation 4 pour les positifs : le témoin est représenté par construction
  via le sous-cas sans PC-tree ou le membership PC-tree fixé ;
- obligation 1/2 pour le résultat positif ponctuel : le témoin est vérifié par
  le prédicat fixed-order exact.

Limites :

- le graphe minimum simple cycle n'implique pas cR ; un contre-exemple `n=6` est
  enregistré dans les régressions ;
- les graphes minimaux avec plusieurs cycles ou des cordes minimales restent
  ambigus ;
- un rejet du témoin cycle ne prouve pas la non-existence d'un autre ordre cR
  représenté.

Preuve expérimentale T018 : `make quick`, `make check` et
`make hunt-counterexamples` restent verts. Le benchmark ciblé
`permuted_cycle/star` utilise ce témoin pour tous les `n > 8` sans timeout ni
run incomplet, tandis que `paired_farthest` reste volontairement incomplet en
grande taille. Le benchmark fort mixed/star T018 garde `0` timeout jusqu'à
`n=100`, avec `42` runs incomplets visibles et non présentés comme des preuves
de non-existence.

Preuve expérimentale T019 : `cycle/mixed` utilise maintenant ce témoin pour
tous les `n > 8` dans `make bench-piste-f`, sans timeout ni run incomplet.
`paired_farthest` reste incomplet en grande taille, ce qui confirme que la
branche n'est qu'un certificat positif. Le benchmark fort mixed/star T019 garde
`0` timeout jusqu'à `n=100`, avec `42` runs incomplets visibles.

### Témoin paired-farthest par matching maximal

Statut : théorème prouvé pour le sous-cas three-level détecté + intégré à la
candidate comme certificat positif.

Hypothèses du sous-cas :

- les distances positives ont trois niveaux `low < mid < high` ;
- les arêtes de niveau `high` forment un matching sur tous les sommets sauf
  éventuellement un neutre ;
- le neutre, s'il existe, est à distance `low` de tous les autres sommets ;
- en retirant le neutre, les arêtes `low` forment exactement deux cliques de
  même taille ;
- chaque arête `high` relie les deux cliques, et toute autre arête entre les
  deux cliques vaut `mid`.

Pour une clique `A = (a_0, ..., a_{m-1})`, la candidate construit :

```text
a_0, ..., a_{m-1}, mate(a_0), ..., mate(a_{m-1}), neutral?
```

Preuve par la caractérisation bad-side d'un ordre fixé :

- une paire mate à distance `high` n'a aucun témoin mauvais ;
- pour deux points d'une même clique à distance `low`, tous les témoins mauvais
  sont dans l'autre clique, donc dans un seul bloc et sur un seul arc ;
- pour deux points non mates de cliques opposées à distance `mid`, les seuls
  témoins mauvais sont leurs deux mates. Comme les deux blocs utilisent le même
  ordre des paires, ces deux mates restent sur le même arc ;
- le neutre n'ajoute pas d'obstruction : pour `{neutral, A_i}`, les témoins
  mauvais sont dans le bloc `B`, et symétriquement.

Ce que cela couvre :

- obligation 1/2 dans le sous-cas : l'ordre construit satisfait cR par le lemme
  bad-side ;
- obligation 4 : avec PC-tree fourni, `represents_order` est vérifié avant tout
  retour positif ;
- obligation 5 : la détection structurelle et la construction sont `O(n^2)`,
  hors coût du test de représentation du scaffold ;
- obligation 6 : les niveaux sont comparés par égalité aux trois valeurs
  observées ; les cas d'égalités hors structure sont rejetés.

Limites :

- ce n'est pas une caractérisation générale de l'existence ;
- si le témoin construit n'est pas représenté par `T`, la candidate ne conclut
  pas, car un autre ordre représenté pourrait exister ;
- les petits cas dégénérés restent couverts par brute force `n <= 8`.

Preuve expérimentale T020 : témoins construits vérifiés par le prédicat cR sur
petites instances seeded `n=4..12`, probe large-n `paired_farthest/star`
jusqu'à `n=100`, et contre-exemple régressé où le témoin cR n'est pas
représenté par un PC-tree `C`. `make bench-piste-f` passe
`paired_farthest/star` à `0` incomplet, tandis que `paired_farthest/mixed`
reste incomplet lorsque le témoin canonique n'est pas représenté. Le benchmark
fort mixed/star T020 garde `0` timeout jusqu'à `n=100`, avec `42` runs
incomplets visibles.

Preuve expérimentale T021 / limite : pour `paired_farthest` non-star, le témoin
canonique n'est pas une caractérisation d'existence. Un cas minimal `n=6`
montre que l'ordre canonique est non représenté par le PC-tree mixed, alors
qu'un autre ordre représenté est cR et que l'oracle répond `True`. Inversement,
un autre cas `n=6` montre que la condition brute "les cordes farthest/high
croisent" n'est pas suffisante pour cR. Toute future branche non-star doit donc
prouver à la fois :

- que la famille d'ordres générée couvre tous les témoins représentés possibles,
  ou rester un certificat positif incomplet ;
- que les contraintes high/farthest sont complétées par les contraintes
  low/mid ou bad-side nécessaires ;
- que le coût de génération est borné sans retomber sur une énumération cachée
  des frontiers.

### Projection locale des farthest sets

Statut : outil expérimental / aucune obligation de suffisance satisfaite.

`project_farthest_sets_to_pc_nodes(D, T)` calcule pour chaque nœud interne les
ensembles de branches

```text
I_x(v) = { i : B_i intersecte F_x }
```

et mesure laminarité, intervalle dans l'ordre local déclaré et compatibilité
circular-ones brute force à petit degré.

Ce que cela couvre :

- obligation expérimentale : les signaux sont reproductibles et attachés à des
  nœuds précis du PC-tree ;
- obligation négative : la laminarité n'est pas nécessaire, car les cas
  égal-distance peuvent être cR pour tout ordre tout en violant massivement la
  laminarité ;
- obligation de séparation : le rapport n'est pas utilisé dans `candidate.py` et
  ne prouve ni existence ni non-existence.

Limites :

- les projections peuvent être triviales sur les arbres binaires ou les
  farthest sets singletons ;
- un échec circular-ones local peut guider une obstruction, mais aucune preuve
  ne relie encore ce signal à une décision d'existence globale ;
- les égalités et cas non stricts imposent de garder les clauses dégénérées
  séparées.

### Boules comme contraintes circular-ones

Statut : diagnostic borné Piste D / aucune décision cR.

`strict_ball_circular_ones_report` construit les boules métriques non triviales
`B_r(x) = {y : D[x][y] <= r}` avec `1 < |B_r(x)| < n`, puis énumère les petits
ordres ou frontiers représentées pour compter ceux où chaque boule est un arc.
Le rapport compare ce signal à `is_quasi_circular_order`,
`is_strict_quasi_circular_order`, `is_precircular_order_cR` et
`is_strict_circular_robinson_order`.

Ce que cela couvre :

- obligation expérimentale : sur les probes T025, la contrainte "toutes les
  boules non triviales sont arcs" coïncide avec le prédicat direct
  `is_quasi_circular_order` ;
- obligation négative : Fig. 2.2 montre que `ball_arc`/quasi peut avoir deux
  ordres tandis que strict circular n'en a qu'un ;
- obligation négative additionnelle : un random `n=6 seed=7` donne un ordre
  `ball_arc/quasi` mais aucun ordre cR sous star, donc le faux positif n'est
  pas limité à la figure source ;
- obligation de représentation : avec PC-tree fourni, le rapport énumère les
  frontiers de ce PC-tree, donc un ordre strict compté est représenté dans le
  scaffold borné ;
- obligation de cas non strict : equal-distance garde tous les ordres
  `ball_arc/quasi/precircular` mais aucun ordre strict, donc le rapport sépare
  explicitement non strict et strict.

Limites :

- le rapport est énumératif et marqué incomplet pour `n > max_n` ;
- il ne construit pas encore le PC-tree/circular-ones des boules ;
- il ne donne aucune contrainte suffisante pour cR : une fois l'ordre
  quasi-circulaire trouvé, les quartets cR ou prédicats stricts restent
  nécessaires ;
- les singletons sont exclus des boules de diagnostic pour ne pas masquer les
  signatures de modules, mais cela ne change pas le test d'arc ;
- les modules sont groupés par signature complète d'appartenance aux boules, pas
  par simple poids de signature.

### Mauvais témoins comme contraintes d'arcs

Statut : reformulation fixed-order exacte partielle ; deux réductions
circular-ones naïves réfutées.

Pour une paire `{a,b}`, `B(a,b)` désigne les témoins `w` tels que
`max(d(a,w), d(w,b)) > d(a,b)`.

Résultat exact pour ordre fixé :

- `bad_witness_one_side` est équivalent à `is_precircular_order_cR` : aucun
  `B(a,b)` ne doit être présent sur les deux arcs ouverts séparés par `a,b`.
- Cette équivalence est une conséquence directe de la condition cR sur
  quadruplets cycliques et du diagnostic `find_bad_side_cr_violation`.

Résultats négatifs T026 :

- exiger que chaque `B(a,b)` soit un arc est trop fort. Le test de régression
  `n=5`, ordre `(0,2,4,1,3)`, est cR mais a `B(0,3) = {1,2}` non arc ;
- exiger que chaque `B(a,b) union {a,b}` soit un arc n'est pas nécessaire :
  equal-distance `n=4` est cR, mais `{0,2}` n'est pas un arc dans
  `(0,1,2,3)` ;
- la même contrainte n'est pas suffisante : la matrice carrée opposée
  `[[0,2,1,2],[2,0,2,1],[1,2,0,2],[2,1,2,0]]` passe cette contrainte dans
  `(0,1,2,3)` mais viole cR.

Obligations ouvertes :

- prouver formellement si `B(a,b)` arc est toujours suffisant pour cR, ou
  produire un faux positif ;
- si ce filtre est conservé, l'utiliser seulement comme condition suffisante ou
  nogood local, jamais comme caractérisation d'existence ;
- construire un état DP/CSP qui mémorise les côtés déjà occupés par les mauvais
  témoins sans énumérer les frontiers complètes du PC-tree ;
- traiter les égalités avec l'inégalité stricte `>` dans la définition de
  mauvais témoin.

### Compilation bad-side par paire

Statut : diagnostic CSP exact après énumération / pas solveur compact.

`forbidden_bad_side_atoms(D)` transforme la caractérisation précédente en
atomes interdits : pour chaque paire `{a,b}` et chaque couple de mauvais
témoins `y,t`, les deux orientations cycliques `(a,y,b,t)` et `(a,t,b,y)` sont
interdites. `compile_bad_side_nogoods` projette ensuite ces atomes sur les
variables locales du PC-tree scaffold, comme les nogoods de quartets cR.

Ce que cela couvre :

- obligation fixed-order : l'exhaustif `n=4`, valeurs `{1,2,3}`, vérifie que la
  présence d'un atome bad-side dans un ordre équivaut à `not cR` ;
- obligation d'égalité : equal-distance ne produit aucun atome bad-side grâce
  au `>` strict ;
- obligation expérimentale CSP : sur PC-trees supportés, les frontiers acceptées
  par `solve_compiled_bad_side_nogood_csp` et
  `solve_pruned_bad_side_nogood_csp` coïncident avec le filtre cR direct.

Limites :

- la compilation énumère encore les affectations complètes pour découvrir les
  signatures de nogoods ;
- diviser les atomes/nogoods par deux sur les probes ne prouve aucune borne
  polynomiale ;
- les obligations 3, 4 et 5 de la candidate générale restent ouvertes tant
  qu'il n'existe pas de construction compacte des nogoods ou d'état DP
  suffisant ;
- les gros nœuds `P` non supportés restent `unsupported`, jamais des rejets.

### Prédicats stricts d'ordre fixé

Statut : définitions directes implémentées / base expérimentale Piste F.

Les prédicats stricts ajoutés vérifient uniquement un ordre fixé :

- `is_strict_robinson_linear` utilise
  `d(x,z) > max(d(x,y), d(y,z))` ;
- `is_strict_quasi_circular_order` utilise `sqcR` :
  `d(x,z) > min(d(y,z), d(t,z))` pour chaque quadruplet cyclique ;
- `is_strict_precircular_order_cR` utilise `scR` :
  `d(x,z) > min(max(d(x,y),d(y,z)), max(d(x,t),d(t,z)))` ;
- `is_strict_circular_robinson_order` vérifie la définition par arcs strictement
  Robinson.

Ce que cela couvre :

- obligation fixed-order : les égalités sont rejetées par `<=` dans les
  fonctions de violation ;
- obligation de séparation : `strict_order_report` est exact seulement par
  énumération pour `n <= max_n`, et marque explicitement les grandes tailles
  incomplètes ;
- obligation expérimentale : sur `n=4`, valeurs `{1,2,3}`, la définition par
  arcs strictement circular coïncide avec `scR` sur `2187` couples
  matrice-ordre.

Limites :

- aucune génération polynomiale des ordres stricts n'est encore implémentée ;
- aucune décision d'existence grande taille n'est ajoutée à `candidate.py` ;
- la Fig. 2.2 montre que strict quasi ne suffit pas à strict circular pour un
  ordre donné ;
- un témoin strict cR peut ne pas être représenté par le PC-tree, donc toute
  future intégration doit garder le garde `represents_order`.

### Générateur Algorithm 5.2 strict

Statut : artefact expérimental filtré / preuve de complétude non encore
formalisée.

`strict_algorithm52_report` implémente une génération de candidats inspirée de
l'Algorithm 5.2 du papier strict :

- choix de tous les couples `x, x' in F_x` ;
- construction de `N`, `F` et des ensembles stricts `J(x,y)` ;
- génération des orientations possibles dans le cas disjoint `N cap F = empty` ;
- filtrage par `represents_order` si un PC-tree est fourni ;
- vérification directe par `is_strict_quasi_circular_order`,
  `is_strict_precircular_order_cR` et `is_strict_circular_robinson_order`.

Ce que cela couvre expérimentalement :

- obligation 1 fixed-order : les ordres validés sont vérifiés par les
  prédicats stricts directs, donc aucune acceptation ne dépend seulement de la
  construction ;
- obligation 4 partielle : avec PC-tree fourni, le rapport ne compte un ordre
  strict que s'il est représenté ; les témoins stricts non représentés sont
  comptés à part ;
- obligation négative : Fig. 2.2 prouve dans les tests que `sqcR` seul ne doit
  pas être accepté comme strict circular ;
- obligation de séparation : le rapport n'est pas utilisé dans `candidate.py`.

Preuve expérimentale T024 : `cycle_metric(6)` est récupéré, Fig. 2.2 sépare les
deux ordres `sqcR` du seul ordre strict circular, un exemple random `n=5 seed=33`
montre un strict positif hors témoins minimum-cycle/paired-farthest, et
l'exhaustif `n=4`, valeurs `{1,2,3}`, récupère exactement les ordres strict
quasi et strict circular pour les `729` matrices. Probe additionnelle :
cycles `n=4..7`, equal-distance et random `n=5/6` seeds `0..199` sans
désaccord.

Limites :

- la preuve que la génération couvre tous les ordres stricts compatibles n'est
  pas encore écrite dans le dépôt ;
- `max_candidates` protège contre l'explosion sur entrées non strictes, et un
  hit de limite rend le rapport incomplet, jamais négatif ;
- aucune conclusion de non-existence générale ne peut être tirée si aucun ordre
  strict n'est trouvé ;
- les cas non stricts et les égalités restent hors périmètre de cet artefact.
