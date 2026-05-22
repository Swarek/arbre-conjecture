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
