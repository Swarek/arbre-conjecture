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

Statut : conséquence directe pour ordre fixé + preuve expérimentale.

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
