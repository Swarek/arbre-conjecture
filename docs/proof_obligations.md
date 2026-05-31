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

### Taille des domaines P et treewidth

Statut : limite expérimentale explicite depuis T064.

La DP treewidth T061 et le stress `p3_block_tree(k)` T062 montrent un paramètre
de largeur utile, mais T064 ajoute l'autre obstruction : un PC-tree star possède
un seul noeud `P`, donc le graphe primal d'un CSP local peut avoir treewidth
`0`, tandis que le domaine contient `(n-1)!/2` ordres circulaires.

Obligation de preuve ajoutée :

- toute revendication FPT doit expliciter à la fois la treewidth et la taille
  maximale des domaines locaux, ou donner une représentation compacte prouvée
  des permutations de `P` ;
- une preuve polynomial-time ne peut pas s'appuyer seulement sur la portée
  binaire des quartets ni sur une treewidth faible ;
- une intégration `candidate.py` de la DP treewidth ne doit pas conclure
  `False` sur un gros `P` non prouvé, et tout `True` doit rester vérifié par un
  ordre reconstruit.

Preuve expérimentale T064 : `make bench-single-p-stress` donne `30` lignes de
treewidth unary `0`, mais un domaine maximal `181440` à `n=10`, un domaine
complètement énuméré `20160` à `n=9`, et `cycle n=9` n'a qu'un ordre cR sur
`20160`. Ce n'est pas une preuve de dureté ; c'est un garde-fou contre une
fausse borne de complexité.

### Catalogue relationnel non booléen

Statut : diagnostic expérimental / red-team complexité, pas preuve de dureté.

T065 ajoute un catalogue des relations effectives non booléennes entre petits
nœuds `P3`. Le rapport expose `max_domain_size`, produits de domaines,
histogrammes de scopes, ratios de tuples rejetés, diversité des relations,
parasites unaires/constantes et mismatches de validation.

Obligations avant toute conclusion de dureté :

- montrer qu'une relation locale cataloguée est réalisable par une matrice
  globale `D` en taille polynomiale ;
- montrer qu'elle reste composable sans contraintes parasites destructrices ;
- montrer que le PC-tree utilisé respecte le promise attendu, ou déclarer qu'on
  prouve seulement une généralisation ;
- donner une réduction complète depuis un problème NP-hard avec équivalence
  satisfiable ssi il existe un ordre cR représenté ;
- distinguer les UNSAT du modèle relationnel des vrais certificats négatifs du
  problème général.

Preuve expérimentale T065 : `make bench-relation-catalog` produit `20` lignes
complètes, `0` mismatch, `38` instances de relations binaires non booléennes,
`27` hashes distincts, mais aussi `12` lignes avec parasite `constant_reject` et
`18` lignes avec parasite unaire non booléen. Ces chiffres suggèrent une piste
de gadgets, mais ne prouvent ni NP-hardness ni polynomialité.

T066 raffine ce catalogue par formes de profils (`sparse_partial_matching`,
`partial_bijection`, sélecteurs, `active_two_regular`, ponts `2 x 6`) et par
tags de composabilité. Le résultat observé contient `38` profils, `0` mismatch,
mais `0` candidat gadget positif sans parasite restrictif. Cela ne ferme aucune
obligation de dureté ni de complexité ; cela rend seulement explicites les
formes à isoler ou à compresser dans une prochaine étape.

T067 ajoute un diagnostic de composition de relations fonctionnelles en chaînes
et cycles. Il trouve des profils `permutation_like` sans parasite restrictif
dans un sweep `paired_farthest`, ainsi qu'une ligne `interaction_unsat` où les
parasites seuls et les relations binaires seules sont satisfaisables mais leur
combinaison ne l'est pas. Cela reste une preuve expérimentale dans le CSP
matérialisé : il faut encore prouver la suffisance du modèle relationnel, le
contrôle des parasites, la réalisation par une matrice globale `D`, le respect
du promise PC-tree et une borne de complexité.

T068 minimise cette ligne `interaction_unsat` dans le même CSP matérialisé. Le
noyau de cardinalité minimale observé contient une relation unaire non
booléenne et une relation binaire `sparse_partial_matching`. Le conflit exact
est une intersection vide entre les valeurs admises par l'unaire sur le bloc
`0` et la projection gauche brute de la binaire. Cette minimisation ne ferme pas
les obligations de preuve : elle ne prouve pas que le CSP matérialisé est une
réduction suffisante générale, ne respecte pas encore le promise
Hsu/McConnell, et ne donne aucune borne de complexité pour les domaines `P`.

T069 ajoute un contrôle plus proche du promise pour les profils
`permutation_like` : en `n=6`, le probe énumère tous les ordres circulaires,
filtre les ordres quasi-circulaires exacts de `D`, et compare cette famille aux
frontiers du scaffold `P3/P3`. Sur le sweep observé, toutes les lignes
`permutation_like` parasite-free coïncident avec
`scaffold_matches_exact_quasi_orders=True`, et toutes les affectations acceptées
restent quasi-circulaires. Cela ne ferme toujours pas les obligations de preuve
générales : le test est exhaustif seulement en petite taille, ne fournit pas
une construction Hsu/McConnell, et ne prouve pas qu'une relation locale
bijective se compose en gadget global.

T070 teste précisément cette dernière faiblesse par composition multi-blocs. Le
sweep `paired_farthest` sur `p3_block_tree(k)` pour `k=2,3,4` ne trouve aucun
réseau propre de plusieurs relations `permutation_like` : les bijections restent
isolées ou sont bloquées par parasites. Ce résultat ajoute une limite
expérimentale à la piste gadget. Il ne prouve pas qu'une autre construction
globale de `D` ne puisse pas composer ces relations, et ne satisfait donc pas
les obligations de réduction, de contrôle des parasites ni de promise
Hsu/McConnell.

T071 élargit ce test à toutes les relations binaires non booléennes du CSP
matérialisé. Une composante multi-arêtes parasite-free avec affectations
acceptées deviendrait seulement un candidat de gadget à analyser ; elle ne
fermerait aucune obligation de preuve sans construction globale de `D`,
contrôle des contraintes parasites, preuve du promise PC-tree, et réduction
complète. Inversement, l'absence d'un tel composant dans un sweep ne prouve pas
l'impossibilité d'une autre famille. Le sweep observé contient `127` lignes avec
composante multi-arêtes et `617` relations binaires non booléennes, mais `0`
ligne multi-arêtes parasite-free ; c'est une limite expérimentale du scaffold,
pas un théorème.

T072 isole la forme `sparse_partial_matching`. Le sweep observé contient `21`
relations sparse sur `14` lignes, `10` conflits projection/unaire à intersection
vide, et `3` lignes où les relations sparse seules forment une composante
insatisfiable. Ces `3` lignes ont encore des `constant_reject`, et le seul cas
sans constante reprend le noyau unaire+binaire T068. Le statut reste donc :
contre-exemple utile aux compressions qui sépareraient les relations binaires
des unaires, pas gadget autonome ni preuve de dureté.

T073 inspecte ces `3` composantes sparse zéro. Elles sont toutes expliquées par
des projections disjointes sur une variable partagée, et retirer une relation
sparse entière réouvre des affectations. En revanche, aucune ligne sparse zéro
sans `constant_reject` n'a été trouvée dans le sweep, et retirer un seul quartet
source ne suffit pas dans l'exemple canonique seed `20281931`. Statut :
diagnostic local plus précis, mais toujours aucune obligation de preuve fermée
pour une réduction de dureté ou pour un solver général.

T074 corrige une faiblesse de reconstruction dans `solve_quartet_2sat` :
les variables non booléennes inactives d'un rapport tautologique peuvent être
fixées arbitrairement avant validation du témoin. Le probe de couverture associé
montre `14` témoins treewidth validés sur `80` lignes, mais `0` témoin nouveau
par rapport à `candidate.py`. Statut : amélioration d'infrastructure et
contre-signal à une intégration positive-only immédiate ; aucune suffisance
globale ni aucun rejet général prouvé.

### Audit strict Algorithm 5.2

Statut : preuve expérimentale bornée pour un sous-cas strict, pas preuve de
complétude générale.

T076 ajoute un audit exact qui compare les ensembles produits par
`strict_algorithm52_report` aux ensembles stricts exacts obtenus par
énumération de tous les ordres/frontiers dans le périmètre borné. Le sweep
observé contient `360` lignes complètes, `0` mismatch, `0` ordre strict
quasi/pre-circular/circular manqué, `138` lignes avec ordre strict circular
exact positif, et aucune limite de candidats atteinte.

Obligations couvertes expérimentalement :

- obligation 1 fixed-order : tout ordre compté strict circular est vérifié par
  `is_strict_circular_robinson_order` ;
- obligation 4 avec PC-tree : les ordres stricts comptés par le rapport fourni
  avec `pc_tree` sont filtrés par `represents_order` ;
- obligation de non-confusion strict/quasi : Fig. 2.2 reste dans les tests et
  sépare strict quasi de strict circular ;
- obligation d'incomplétude visible : un cap `max_candidates` bas rend le
  rapport `complete=False` et ne doit pas produire de rejet.

Limites restantes :

- la preuve que l'Algorithm 5.2 généré couvre tous les ordres stricts
  compatibles n'est pas écrite ;
- les résultats sont bornés à l'énumération petite taille ;
- les cas non stricts et les égalités restent hors périmètre d'un sous-cas
  strict ;
- aucune intégration dans `candidate.py` n'est justifiée sans gain large-n
  mesuré, et elle ne devrait de toute façon être que positive-only avec témoin
  revérifié.

T077 mesure précisément ce dernier point. Le probe positive-only large-n trouve
`204` témoins strict circular validés, tous déjà couverts par `candidate.py`,
`0` nouveau positif, `0` limite candidate et `0` échec de validation de témoin.
Il observe aussi `152` lignes avec témoins stricts non représentés par le
PC-tree, qui doivent rester exclus. Conséquence : aucune obligation nouvelle
n'est fermée pour un solver général, et aucune intégration stricte dans
`candidate.py` n'est justifiée par la couverture empirique actuelle.

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

Conséquence T078 : la même caractérisation peut être écrite en clean-side par
seuil. Pour `{a,b}`, avec `r = D[a][b]`, définir
`C_ab = {w notin {a,b} : D[a][w] <= r and D[w][b] <= r}`. Comme `C_ab` est le
complément exact des mauvais témoins parmi les points distincts des endpoints,
un ordre fixé est cR ssi, pour chaque paire `{a,b}`, au moins un des deux arcs
ouverts entre `a` et `b` est contenu dans `C_ab`.

Preuve expérimentale T078 : `tests/test_predicates.py` compare
`passes_threshold_clean_side_condition`, `passes_bad_side_precircular_cR` et
`is_precircular_order_cR` sur l'exhaustif `n=4`, valeurs `{1,2,3}`, puis sur
des randoms `n=5..7`, sans désaccord. `make bench-threshold-roundness` vérifie
`6072` ordres sur `53` lignes (`cycle/random/equal/paired_farthest/
four_local_non_cr/five_local_non_cr`), `0` mismatch et `0` troncature.

Limite : T078 ferme seulement une reformulation d'ordre fixé. Les obligations
3, 4 et 5 restent ouvertes pour l'existence dans le PC-tree, et la contrainte
clean-side n'est pas encore une construction circular-ones/PC-tree.

### PC-représentabilité bornée de l'ensemble des ordres cR

Statut : résultat négatif expérimental dans le scaffold `PCNode`, pas théorème
Hsu/McConnell.

T079 ajoute un learner exact borné pour la grammaire enracinée `PCNode` du
dépôt. Pour une famille cible d'ordres circulaires canoniques, il énumère les
familles de frontiers linéaires générées par feuilles, nœuds `P` et nœuds `C`,
puis compare leur canonicalisation circulaire à la cible. Un cap par
sous-ensemble rend le résultat incomplet si dépassé.

Contre-exemple scaffold T079 :

```text
D = [
  [0, 1, 2, 3, 1],
  [1, 0, 3, 2, 1],
  [2, 3, 0, 1, 1],
  [3, 2, 1, 0, 1],
  [1, 1, 1, 1, 0],
]
S_cr(D) = {
  (0, 1, 3, 2, 4),
  (0, 1, 4, 3, 2),
}
```

Le learner est complet sur `n=5` avec le cap utilisé et ne trouve aucun
`PCNode` représentant exactement ces deux ordres. Le test régressé vérifie aussi
qu'aucun contre-exemple non vide/non total n'apparaît sur l'exhaustif `n=4`,
valeurs `{1,2,3}`.

Ce que cela couvre :

- obligation négative locale : la route naïve "calculer un `PCNode` des ordres
  cR" est fausse dans le scaffold actuel ;
- obligation de contre-exemple : la matrice et les deux ordres cR sont conservés
  dans `tests/test_pc_tree_learning.py` ;
- obligation de prudence : les rapports distinguent cible vide, recherche
  incomplète et contre-exemple informatif.

Limites :

- le scaffold `PCNode` est enraciné et plus pauvre qu'une implémentation
  Hsu/McConnell complète ;
- une non-représentabilité scaffold n'est pas une preuve de
  non-représentabilité par PC-tree général ;
- cette expérience ne donne pas encore de solveur d'existence dans le PC-tree
  quasi-circulaire fourni.

### Audit non enraciné du contre-exemple T079

Statut : renforcement expérimental borné, pas preuve générale.

T080 ajoute un modèle PC-tree non enraciné explicite pour `n <= 5`. Il énumère
les topologies d'arbres par séquences de Prüfer, filtre les feuilles de degré
`1` et les nœuds internes de degré au moins `3`, assigne les types `P/C`,
énumère les ordres cycliques des nœuds `C`, puis calcule les frontiers induites
par les embeddings autorisés.

Résultat observé : le contre-exemple T079 survit. Pour la matrice T079 à
`5` points, le modèle inspecte `893` candidats topologie/type/ordre C et
obtient `93` familles distinctes ; aucune ne représente exactement les deux
ordres cR

```text
(0, 1, 3, 2, 4)
(0, 1, 4, 3, 2)
```

Les contrôles positifs `cycle_n5` et `equal_n5` restent représentables.

Ce que cela couvre :

- la non-représentabilité T079 n'est pas seulement due au choix d'une racine
  dans `PCNode` ;
- le modèle non enraciné a un témoin positif sur familles simples, donc il ne
  rejette pas tout ;
- l'artefact reste un audit borné et indépendant de `candidate.py`.

Limites :

- l'énumération non enracinée n'est faite qu'à `5` feuilles ;
- l'implémentation reste un modèle expérimental minimal, pas une bibliothèque
  Hsu/McConnell validée ;
- ce résultat ne dit pas quelle structure alternative représenterait les
  ordres cR, seulement qu'un PC-tree unique paraît insuffisant sur ce cas.

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

### Témoin matching low-hub par projection de frontier

Statut : théorème dans le sous-cas matching / certificat positif borné côté
PC-tree.

Pour une matrice binaire `low/high` avec hubs bas et graphe haut matching, un
ordre fixé est cR si et seulement si, après suppression des hubs, toutes les
cordes du matching haut se croisent deux à deux. Preuve bad-side : une paire
haute n'a aucun mauvais témoin ; une paire contenant un hub en a au plus un ;
une paire basse entre deux non-hubs non mates a exactement les deux mates comme
mauvais témoins. Ces deux témoins sont sur le même arc exactement quand les deux
cordes hautes correspondantes se croisent. Les hubs ne sont jamais mauvais
témoins et n'affectent pas l'ordre circulaire relatif des non-hubs.

T044 utilise cette caractérisation seulement comme certificat positif : il teste
un frontier représenté, accepte seulement après `passes_bad_side_precircular_cR`
et `represents_order`, puis garde la construction segmentaire T043 comme
fallback.

Ce que cela couvre :

- obligation 1/2 dans le sous-cas : nécessité et suffisance pour un ordre fixé
  low-hub matching ;
- obligation 4 : le frontier accepté est représenté par construction puis
  recontrôlé par `represents_order` ;
- obligation 6 : `low=0`, égalités binaires et hubs multiples restent couverts
  par la définition stricte des mauvais témoins ;
- obligation de séparation : l'existence dans le PC-tree reste bornée par les
  frontiers inspectées, donc un échec reste incomplet.

Limites :

- ne vaut pas pour un graphe haut non matching ;
- ne donne pas encore une intersection PC-tree compacte non bornée ;
- la frontier tardive `n=8` reste manquée à `frontier_limit=64` ;
- la généralisation aux graphes bipartis à strong ordering reste ouverte.

Preuve expérimentale T044 : le split-hubs `n=6` devient positif au premier
frontier projeté, un split-hubs large `n=12` force la candidate à passer par ce
certificat, le cas non-crossing rigide `n=6` reste négatif exact, et les gates
`make quick`, `make hunt-counterexamples`, `make check`, `make bench-quick` et
`make bench` restent verts.

### Recherche exacte bornée des projections matching low-hub

Statut : décision exacte d'un sous-cas quand l'énumération finit sous limite ;
diagnostic incomplet sinon.

T045 exploite le théorème T044 : dans le sous-cas binaire low-hub matching, les
ordres cR sont exactement ceux dont la projection non-hub est, à
rotation/renversement près,

```text
seq, mate(seq)
```

avec les hubs insérés arbitrairement dans les interstices. Le rapport
`exact_low_hub_matching_projection_search_report` énumère ces formes, déduplique
les ordres circulaires, teste `represents_order`, puis revalide cR.

Ce que cela couvre :

- obligation 1/2 dans le sous-cas : la famille énumérée est nécessaire et
  suffisante par T044 ;
- obligation 3 sous limite : si tous les candidats uniques sont épuisés, aucun
  ordre représenté cR n'a été manqué dans ce sous-cas ;
- obligation 4 : tout témoin positif est vérifié par `represents_order` ;
- obligation 5 partielle : la borne brute est
  `2^m * m! * h! * C(h+2m-1,2m-1)` ; ce n'est pas polynomial ;
- obligation 6 : `low=0` et hubs multiples restent couverts par le même lemme
  bad-side strict.

Limites :

- hors matching low-hub, le rapport est non applicable ;
- au-dessus de `max_candidate_orders`, l'échec est incomplet, jamais négatif ;
- la borne brute est lâche et peut dépasser la limite alors qu'un témoin existe
  tôt ; l'implémentation énumère donc paresseusement les candidats uniques ;
- le résultat n'est pas une intersection PC-tree polynomial-time.

Preuve expérimentale T045 : frontier tardive `n=8` trouvée par énumération des
formes cR, rigide non-crossing `n=6` rejeté complètement, négatif non-crossing
`n=12` rejeté par la candidate après `21120` candidats uniques, et cas `n=13`
montrant qu'un témoin peut être trouvé sous la limite malgré une borne brute
supérieure à la limite. `make quick`, `make hunt-counterexamples`,
`make check`, `make bench-quick` et `make bench` restent verts.

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

Statut : diagnostic CSP exact après énumération, puis compilation support-local
expérimentale / pas solveur compact général.

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

- la compilation T027 énumère encore les affectations complètes pour découvrir
  les signatures de nogoods ;
- diviser les atomes/nogoods par deux sur les probes ne prouve aucune borne
  polynomiale ;
- les obligations 3, 4 et 5 de la candidate générale restent ouvertes tant
  qu'il n'existe pas de construction compacte des nogoods ou d'état DP
  suffisant ;
- les gros nœuds `P` non supportés restent `unsupported`, jamais des rejets.

T047 ajoute `compile_bad_side_nogoods_support_local`, qui parcourt seulement le
produit des domaines de `quartet_support_paths(T, atom)` pour chaque atom, puis
déduplique les nogoods par signature effective de pruning. Cela couvre une
obligation expérimentale plus forte : sur les probes `n=4..7`, les signatures
support-local coïncident avec les signatures de la compilation complète et le
solveur pruné accepte exactement les mêmes frontiers que le CSP cR direct.

Limites T047 :

- l'identité orientée de l'`atom` n'est pas stable sous canonicalisation
  circulaire globale ; seule la signature de pruning est utilisée comme objet
  sémantique ;
- le coût pertinent devient `sum_support_products`, qui peut rester supérieur à
  l'espace complet sur de très petits arbres ou quand le nombre d'atoms domine ;
- aucune branche T047 n'est intégrée à `candidate.py`, donc cela reste un
  artefact Piste C ;
- il faut encore une borne structurelle ou un regroupement d'atoms pour obtenir
  une preuve de complexité utile.

T048 ajoute `compile_bad_side_nogoods_grouped_support_local`, qui regroupe les
atoms par support identique et énumère chaque produit de domaines de support une
seule fois. Les obligations expérimentales renforcées sont :

- les signatures groupées coïncident avec T047 support-local sur les probes et
  tests ciblés ;
- le solveur pruné groupé accepte exactement les mêmes frontiers que le CSP cR
  direct sur les PC-trees supportés testés ;
- un dépassement de limite ou un gros nœud `P` unsupported reste incomplet et
  ne produit aucune décision négative.

Limites T048 :

- le regroupement réduit `sum_support_products` vers
  `sum_unique_support_products`, mais l'implémentation paie encore un
  `atom_checks` égal au coût T047 support-local sur la gate rapide ;
- aucune preuve ne borne encore la taille des groupes d'atoms partageant un
  support ;
- le champ `atom`/`pair` d'un nogood groupé reste diagnostique, pas sémantique ;
- rien n'est intégré à `candidate.py`, donc les obligations 2, 3 et 5 du
  problème général restent ouvertes.

T049 ajoute `compile_bad_side_nogoods_grouped_first_hit_support_local`, qui
s'arrête au premier atom violé pour une affectation de support. Cela couvre une
obligation expérimentale supplémentaire : le nogood effectif est la signature de
support, donc l'existence d'un atom violé suffit pour émettre cette signature.
Les tests et probes vérifient que les signatures first-hit coïncident avec T048
et T047, et que le solveur pruné reste aligné sur le CSP cR direct.

Limites T049 :

- `atom`, `pair`, `bad_witnesses`, `atom_hits`, `atoms_with_nogoods` et
  `pairs_with_nogoods` deviennent des diagnostics de premier témoin, pas une
  énumération exhaustive des obstructions supportées ;
- le gain est empirique sur les checks d'atoms, pas une borne de complexité ;
- les groupes sans hit rapide paient encore un scan séquentiel ;
- rien n'est intégré à `candidate.py`; les obligations générales de nécessité,
  suffisance et complexité restent ouvertes.

T050 ajoute des métriques de profil first-hit : affectations avec hit, sans
hit, histogramme de position du premier hit, checks dépensés sur no-hit et
checks sauvés sur hit. Ces métriques ne changent pas les nogoods ni les
frontiers acceptées ; elles servent seulement à orienter la prochaine
compression.

Limites T050 :

- les métriques `first_hit_*` dépendent de l'ordre courant de scan des atoms et
  ne sont pas des invariants mathématiques du PC-tree ;
- `position` signifie position ordinale dans la liste d'atoms du groupe, pas
  position dans l'ordre circulaire ;
- en mode first-hit, les champs `atom`/`pair` restent des représentants de
  premier témoin ;
- si `complete=False`, les compteurs de profilage sont partiels :
  `atom_checks_if_exhaustive_seen` concerne le préfixe inspecté, tandis que
  `atom_checks_if_exhaustive` reste la taille totale théorique.

T051 ajoute `bad_side_grouped_support_outcome_profile`. Pour chaque support
groupé, il mesure les affectations hit/no-hit et teste une reformulation par
graphe de mauvais témoins : pour chaque paire `{a,b}`, une composante de
témoins qui occupe les deux côtés de `{a,b}` équivaut à l'existence d'un atom
bad-side dans ce support. Sur la gate CSP rapide, cette reformulation a
`0` mismatch avec le scan atomique.

Limites T051 :

- le profil reste un diagnostic construit par énumération des affectations de
  support, pas une compilation compacte ;
- un no-hit local n'est pas un certificat positif de frontier cR ;
- les tranches unaires pures et le test pair-side/composantes ne sont pas des
  preuves de suffisance globale ;
- le test pair-side naïf est plus coûteux que first-hit sur la gate rapide
  (`profile_pair_side_split_work_ratio=1.7732`), donc il ne satisfait pas
  l'obligation de complexité ;
- les cas `limit` et `unsupported` restent des profils partiels, jamais des
  rejets.

T052 ajoute un cache expérimental des côtés de témoins. La clé
`(pair,witness,signature_triple)` est sound dans le scaffold si
`signature_triple` inclut tous les choix de
`quartet_support_paths(T, (a,b,w))`, sans canonicaliser le triple modulo
renversement. Les tests verrouillent un cas imbriqué où omettre le choix
interne `(1,)` confond deux côtés opposés.

Limites T052 :

- ce cache ne décide toujours aucun ordre et reste hors `candidate.py` ;
- le cache simple réduit les projections de côtés mais reste plus coûteux que
  first-hit sur la gate rapide (`1.1836x`) ;
- le modèle bitset-composantes est prometteur expérimentalement (`0.6650x`),
  mais ce n'est qu'un modèle de coût tant que les masques ne sont pas compilés
  en structure de données réelle ;
- aucune borne asymptotique sur le nombre de signatures triples ou de
  composantes n'est encore prouvée.

T053 ajoute un profil bitset/composantes réel. Pour chaque support groupé, il
calcule des masques de côtés par paire `{a,b}` et composante de mauvais témoins.
Sur la gate CSP rapide, ce profil a `0` mismatch avec le scan atomique et avec
le test pair-side T051.

Limites T053 :

- ce profil reste hors `candidate.py` et ne décide aucun ordre ;
- les masques sont exacts seulement pour un support groupé et une affectation
  locale donnés ; ils ne prouvent pas la représentabilité globale ;
- le coût réel (`1.0732x` first-hit) est supérieur au modèle de projection
  (`0.6645x`) car les visites de témoins dominent ;
- une signature qui anonymise les labels, les paires, les composantes ou les
  choix imbriqués est réfutée par les tests de régression ;
- aucune borne asymptotique sur le nombre d'états de masques distincts n'est
  encore établie.

T054 mesure cette dernière limite : les états distincts de masques par support
groupé sont comptés et comparés aux affectations locales. Sur la gate CSP
rapide, le profil a `0` état mixte et `0` mismatch, donc l'état est bien un
classifieur local exact.

Limites T054 :

- le nombre d'états est une somme par support groupé, pas un ensemble global
  composable ;
- le quotient observé est faible (`2920/6224`, ratio `0.4692`, bucket max `4`)
  et ne constitue pas une borne asymptotique ;
- construire l'état complet coûte encore plus que first-hit (`1.9412x`) et la
  projection coûte `0.9038x`, donc ce n'est pas un algorithme plus rapide ;
- aucune preuve ne montre que ces états peuvent être composés de bas en haut
  dans le PC-tree sans revisiter les témoins ;
- aucune intégration dans `candidate.py`, donc aucune obligation de décision
  générale n'est satisfaite par T054.

T055 mesure des quotients plus abstraits de ces états. Les quotients
`mask_multiset`, `hit_components`, `hit_pairs` et `decision_only` n'ont pas
d'état mixte sur la gate rapide, tandis que le contrôle `side_blind_schema`
produit des états mixtes. Le cas minimal régressé
`cycle_metric(4)`/`balanced_pc_tree(4, kind="C")` montre déjà que supprimer les
masques fusionne des affectations hit et no-hit dans un seul état.

Limites T055 :

- absence d'état mixte sur les probes n'est pas une preuve de soundness globale
  d'un quotient ;
- `decision_only`, `hit_components` et `hit_pairs` sont proches d'une table de
  décision locale et ne fournissent pas d'information évidente pour composer les
  sous-arbres ;
- `mask_multiset` perd les paires et composantes, donc il doit être testé
  contre des contextes parents avant toute utilisation DP ;
- le contrôle `side_blind_schema` prouve que la forme du support sans masques
  est insuffisante ;
- toujours aucune intégration dans `candidate.py` ni preuve de complexité.

T056 ajoute une obligation négative pour les états DP : un quotient local doit
rester stable sous contexte voisin. Le diagnostic
`component_mask_quotient_context_collision_profile` trouve des collisions de
contexte pour `mask_multiset`, `hit_components`, `hit_pairs` et
`decision_only`. Un contre-exemple global régressé sur `n=5` montre même deux
affectations locales avec `mask_multiset=(1,2)` et contexte externe identique,
dont les frontiers canoniques sont respectivement cR et non-cR.

Limites et obligations après T056 :

- `mask_multiset` est réfuté comme état DP autonome ;
- les collisions de `full` sur probes montrent que l'état de masques fermé par
  support n'est pas suffisant pour toutes les obligations ouvertes ;
- une future DP doit définir explicitement ce qui est transporté entre supports
  voisins, au-delà du hit/no-hit local ;
- le diagnostic est borné (`max_pairs=20` dans la gate CSP rapide) et sert de
  falsification, pas de preuve d'impossibilité générale ;
- aucune modification de `candidate.py`, donc aucune nouvelle obligation de
  décision générale n'est satisfaite.

T057 ajoute une obligation positive/négative pour les états ouverts :
un état enrichi par réponses de bord one-hop doit être montré composable, pas
seulement exact localement. Le diagnostic
`component_mask_open_boundary_profile` mesure, pour chaque support `S`, la table
des réponses hit/no-hit des supports voisins `C` sous les choix de contexte
externe `(S union C) \\ S`.

Ce que T057 couvre expérimentalement :

- les collisions de réponse de bord mesurées pour `mask_multiset` et `full` sont
  supprimées par `mask_multiset_plus_boundary`, `full_plus_boundary` et
  `local_boundary_response` sur la gate CSP rapide ;
- les clés incluent le support de base, ce qui évite une fausse compression par
  pooling de supports différents ;
- `boundary_response` seul ne couvre pas l'obligation de décision locale, car
  il peut mélanger plusieurs hits locaux dans un même bucket ;
- le profil reste hors `candidate.py` et n'implique aucune décision
  d'existence générale.

Obligations restantes après T057 :

- prouver que la réponse one-hop est nécessaire, ou exhiber un état plus faible
  qui répare les mêmes collisions ;
- prouver la suffisance récursive : deux affectations avec même
  `local_boundary_response` doivent rester indiscernables après composition de
  deux supports voisins et dans la décision globale ;
- borner la taille totale des tables de réponses en fonction de `n` et `|T|`,
  y compris quand plusieurs supports se chevauchent simultanément ;
- traiter le cas où le diagnostic est tronqué par `max_pairs` ou `limit` :
  cette troncature ne doit jamais devenir une réponse négative ;
- formaliser les cas d'égalité/non stricts dans les réponses de bord, pas
  seulement les hits booléens d'atomes bad-side.

### Obligations issues de la revue externe post-T057

Statut : obligations ouvertes, non satisfaites par T057.

La revue externe GPT 5.5 Pro du 2026-05-23 est conservée dans
`docs/external_reviews/gpt55_global_strategy_2026-05-23.md`. Elle était
partiellement ancrée sur T057 ; les obligations suivantes servent à élargir le
portefeuille plutôt qu'à imposer une seule prochaine expérience :

1. écrire une preuve interne complète de la caractérisation bad-side par les
   ensembles `B_ac`, et maintenir des tests d'équivalence contre la définition
   directe cR ;
2. vérifier dans le scaffold PC-tree que le type induit d'un quartet dépend
   effectivement d'au plus deux variables locales pertinentes ;
3. si les domaines effectifs sont booléens, prouver et tester la réduction
   2-SAT plutôt que continuer un backtracking CSP général ;
4. si le graphe primal du CSP de quartets a treewidth bornée, définir la DP
   exacte sur bags et sa complexité ;
5. pour la piste dureté, produire un catalogue de relations binaires
   réalisables et documenter les contraintes parasites dues à la globalité de
   `D`.

T058 satisfait partiellement l'obligation 2 dans le scaffold actuel, mais ne la
ferme pas comme théorème général :

- `quartet_pc_scope_report` vérifie expérimentalement que la projection
  support-local d'un quartet coïncide avec la projection des frontiers complets
  sur la gate CSP rapide et sur probes stress ;
- la portée structurelle `quartet_support_paths` peut être de taille `3`, donc
  le lemme naïf "le support vaut toujours au plus deux nœuds" est faux dans le
  scaffold ;
- la portée effective observée du type et de l'acceptation est `<=2` sur les
  probes T058, ce qui est une conjecture de travail, pas une preuve ;
- les domaines non booléens observés avec des nœuds `P` fanout `3` empêchent de
  conclure directement à 2-SAT hors du sous-cas booléen.

Obligations restantes après T058 :

- prouver pourquoi la variable redondante des supports taille `3` peut être
  éliminée pour le type/acceptation du quartet ;
- construire les relations par scope effectif et prouver qu'elles sont
  suffisantes pour le CSP global ;
- dans le sous-cas booléen, transformer les relations en clauses 2-SAT et
  prouver l'équivalence avec l'existence d'un frontier cR représenté ;
- hors booléen, mesurer/prouver la treewidth ou cataloguer les relations dures.

T059 satisfait expérimentalement la construction relationnelle dans le scaffold
supporté, mais ne ferme pas encore les preuves générales :

- `quartet_effective_relation_report` matérialise la relation acceptée de
  chaque quartet sur sa portée effective d'acceptation ;
- les relations ayant même scope sont fusionnées par intersection, ce qui donne
  le CSP effectif par scopes ;
- la conjonction de ces relations est validée contre
  `is_precircular_order_cR(frontier_from_assignment(...))` sur toutes les
  affectations locales complètes supportées ;
- le rapport distingue explicitement les lignes `two_sat_candidate`, les
  lignes de catalogue non booléen, les hautes arités, les incomplets et les
  mismatches de validation.

Obligations partiellement couvertes par T059 :

- obligation 1, dans le scaffold : chaque relation provient des types de
  quartet cR autorisés par `D`, donc elle est nécessaire pour l'affectation
  locale profilée ;
- obligation 2, expérimentale : sur les probes ciblées, la conjonction des
  relations fusionnées est suffisante pour retrouver exactement le filtre cR
  des frontiers représentées ;
- obligation 5, diagnostic : le graphe primal et une borne greedy de treewidth
  sont maintenant mesurés, mais pas encore utilisés comme algorithme prouvé.

T060 implémente le sous-cas 2-SAT du rapport relationnel, mais uniquement dans
le scaffold expérimental et hors `candidate.py` :

- `solve_quartet_2sat` exige un rapport complet avec
  `row_class="two_sat_candidate"` ;
- chaque tuple rejeté d'une relation fusionnée est réécrit en clause 2-CNF :
  scope vide rejeté comme contradiction, rejet unaire comme clause unitaire,
  rejet binaire comme clause `(x != a) or (y != b)` ;
- les domaines de taille `1` sont simplifiés comme choix fixés et les domaines
  de taille `2` deviennent les seules variables booléennes ;
- un témoin SAT est reconstruit en affectation locale, converti en frontier, et
  vérifié directement par `is_precircular_order_cR`.

Obligations couvertes par T060 dans ce périmètre :

- obligation 1 : les clauses sont nécessaires, car elles ne font que réécrire
  les signatures explicitement rejetées par les relations T059 ;
- obligation 2 : la suffisance est héritée expérimentalement de la validation
  T059 relation-CSP vs cR direct sur les affectations complètes supportées ;
- obligation 4 : tout témoin SAT retourné est contrôlé par le prédicat cR fixé ;
- obligation 5 partielle : la résolution 2-SAT elle-même est linéaire dans le
  nombre de clauses produites, mais la construction actuelle des relations reste
  énumérative et bornée par le scaffold.

Limites après T060 :

- l'équivalence globale dépend encore du lemme T059 non prouvé hors scaffold :
  les relations de quartets fusionnées doivent capturer exactement toutes les
  contraintes cR sur les frontiers représentées ;
- les résultats UNSAT 2-SAT ne doivent pas être intégrés comme rejets généraux
  dans `candidate.py` avant une preuve de suffisance du modèle relationnel ;
- les nœuds `P3` et autres domaines non booléens restent explicitement refusés
  comme `not_two_sat_candidate` ;
- les vrais PC-trees Hsu/McConnell non enracinés peuvent avoir des subtilités
  non capturées par le scaffold `PCNode`.

T061 étend le traitement relationnel aux domaines non booléens sous largeur
bornée, toujours dans le scaffold expérimental :

- `solve_quartet_treewidth_csp` exige un rapport complet avec relations
  matérialisées ;
- un ordre d'élimination exact est cherché sous `max_treewidth` et
  `max_exact_width_variables` ;
- les facteurs sont éliminés en projetant les affectations compatibles ;
- si SAT, une affectation locale témoin est reconstruite et l'ordre obtenu est
  vérifié directement cR.

Obligations couvertes par T061 dans ce périmètre :

- obligation 2 expérimentale : les relations non booléennes `P3` ne sont plus
  rejetées hors du solveur ; elles sont résolues par le CSP relationnel ;
- obligation 4 : tout témoin SAT reconstruit est validé par le prédicat cR fixé ;
- obligation 5 partielle : après construction du rapport, le solveur est FPT en
  `O(m q^(w+1))` pour domaine maximal `q`, nombre de relations `m` et treewidth
  bornée `w`.

Limites après T061 :

- les lignes au-dessus du cap de largeur restent incomplètes, jamais négatives ;
- les UNSAT du CSP relationnel ne doivent pas encore être interprétés comme une
  preuve générale hors scaffold ;
- la construction des relations par quartets reste énumérative et domine le
  coût actuel ;
- une famille de blocs `P3` peut faire croître la largeur, donc la piste n'est
  pas une preuve de polynomialité générale.

T062 matérialise cette dernière limite :

- `p3_block_tree(k)` est une famille de stress où les domaines locaux ont taille
  `6` sur chaque bloc `P3` ;
- sur `cycle_metric(3k)`, le graphe primal observé a une largeur qui croît avec
  `k` dans le rapport borné ;
- avec le cap de benchmark `max_treewidth=4`, la ligne `cycle,k=5` est
  correctement marquée incomplète, pas négative ;
- les contrôles equal-distance restent tautologiques et les témoins SAT sont
  vérifiés directement quand ils existent.

Conséquence : toute preuve future fondée sur T061 devra être paramétrée par la
treewidth ou fournir un argument structurel qui borne cette largeur pour les
PC-trees issus de Hsu/McConnell. Les expériences T061/T062 ne donnent pas un
algorithme polynomial général.

Limites restantes après T059/T060/T061 :

- la validation reste par énumération complète des affectations locales ; elle
  ne prouve pas une complexité polynomiale ;
- une borne greedy de treewidth n'est pas une décomposition certifiée ni une
  preuve de complexité ;
- les vrais PC-trees Hsu/McConnell non enracinés peuvent avoir des subtilités
  non capturées par le scaffold `PCNode`.

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

### Relèvement de projections matching low-hub dans le PC-tree

Statut : conséquence directe bornée pour un sous-cas ; pas polynomial général.

`exact_low_hub_matching_projected_pc_tree_search_report` traite le sous-cas
binaire avec au moins un hub bas et un graphe haut matching. Il énumère les
projections high-vertices de la forme `seq + mate(seq)`, puis tente de relever
chaque projection à un frontier complet du PC-tree original en insérant les hubs
uniquement là où la structure `P/C` le permet. Le témoin retourné est toujours
revérifié par `passes_bad_side_precircular_cR` et `represents_order`.

Obligations couvertes dans ce périmètre :

- nécessité et suffisance fixed-order : héritées du lemme T044/T045 pour le
  sous-cas matching low-hub, où un ordre est cR ssi la projection des endpoints
  est `seq + mate(seq)` à rotation/renversement près ;
- représentation du témoin : le releveur construit un frontier complet et le
  contrôle par `represents_order` avant acceptation ;
- négatif complet borné : si toutes les projections uniques sont épuisées sous
  `max_projection_orders` et aucune n'est relevable, aucun ordre représenté du
  sous-cas matching low-hub n'est cR.

Limites :

- l'énumération reste factorielle en nombre de paires du matching
  (`2^m * m!` avant déduplication circulaire) ;
- `projection_limit_exceeded` est incomplet et ne doit jamais être converti en
  rejet ;
- le résultat ne s'applique pas aux graphes hauts non matching ni au cas sans
  hub bas ;
- ce n'est pas encore la DP/CSP d'intersection PC-tree demandée : l'ordre commun
  des paires reste explicitement énuméré ;
- les contre-exemples T046 montrent qu'une signature locale par ensembles
  projetés ou par simples variables "côté A/B" est insuffisante.

### Diagnostic T075 : support multi-niveau des premiers quartets non-cR

Statut : obligation négative expérimentale pour les règles locales `I_x(v)`,
pas preuve d'un algorithme.

Le probe `pc_frontier_obstruction_support_probe.py` énumère des frontiers
représentées, vérifie cR par le prédicat fixed-order bad-side, puis profile le
premier quartet cR interdit de chaque mauvais ordre.

Ce que T075 couvre :

- obligation 1 fixed-order : les frontiers sont classées par
  `passes_bad_side_precircular_cR`, pas par un filtre farthest approximatif ;
- obligation de non-suffisance locale : dans le sweep borné, `494` frontiers
  non-cR apparaissent dans des lignes où les projections locales `I_x(v)` sont
  silencieuses ;
- obligation de structure : les premiers quartets interdits profilés utilisent
  toujours `3` supports PC-tree, donc une décision locale indépendante par nœud
  ne peut pas expliquer ces rejets.

Limites :

- le probe énumère seulement sous `frontier_limit` et ne prouve rien sur les
  lignes tronquées ;
- le premier quartet d'un ordre n'est pas nécessairement une obstruction
  minimale globale ;
- les supports sont ceux du scaffold `PCNode`, pas encore une preuve
  Hsu/McConnell générale ;
- les mismatchs des variantes `B(a,b)` arc et `B(a,b) union {a,b}` rappellent
  qu'elles ne doivent pas être promues en prédicats de décision.

### Diagnostic T081 : profondeur locale des obstructions induites

Statut : preuve expérimentale bornée d'insuffisance des petits certificats,
pas obligation positive de solveur.

`local_obstruction_profile` utilise l'hérédité suivante : si une sous-matrice
induite `D[S]` n'a aucun ordre cR, alors `D` n'a aucun ordre cR global dont la
restriction à `S` serait cR. Dans le cas `T=star`, cette obstruction induite
donne donc un certificat négatif pour l'existence globale.

Ce que T081 couvre :

- les familles `four_local_non_cr` et `five_local_non_cr` vérifient
  expérimentalement des obstructions minimales de taille `5` et `6` ;
- toutes les restrictions plus petites de ces noyaux sont positives selon
  l'oracle exact ;
- le rapport distingue une obstruction visible sous cap d'une ligne seulement
  décidée par oracle global exact.

Limites :

- pour un PC-tree restreint, une sous-matrice positive en star ne dit pas que le
  PC-tree global peut relever un ordre positif ;
- le scan n'est complet que jusqu'au cap demandé, sauf appel explicite à
  l'oracle global exact ;
- aucune borne universelle sur la taille des obstructions n'est prouvée ;
- ce diagnostic ne justifie aucun nouveau `False` dans `candidate.py`.

### Diagnostic T082 : système same-side et obstructions high-girth

Statut : reformulation expérimentale exacte pour `T=star` sous énumération
complète ; pas solveur général.

Pour un ordre fixé, la contrainte bad-side pour `{a,c}` équivaut à exiger que
toutes les paires de témoins `b,d in B_ac` satisfassent
`same_side(a,c;b,d)`. `solve_bad_side_chirotope` résout exactement ce système
en énumérant des ordres circulaires réels, ce qui évite d'avoir à prouver des
axiomes de chirotope abstrait.

Ce que T082 couvre :

- équivalence expérimentale avec `exact_oracle_all_orders` sur les petites
  tailles testées ;
- extraction de candidats high-girth où tous les sous-ensembles jusqu'à `6`
  sont positifs mais l'instance globale est négative ;
- séparation explicite entre résultat complet et limite d'énumération.

Limites :

- l'énumération est factorielle et seulement utilisée jusqu'à de petites
  tailles ;
- les lignes high-girth sont pour `T=star`; un PC-tree restreint demande un
  contrôle de frontiers représentées ;
- ce module ne prouve pas que la profondeur d'obstruction est non bornée ;
- aucun rejet supplémentaire dans `candidate.py` n'est justifié sans lemme de
  sous-cas.

### R004 : obligations issues des notes externes du 2026-05-31

Statut : nouvelles obligations de preuve, pas résultats.

Le digest `docs/external_reviews/researcher_advances_2026-05-31.md` conserve
quatre hypothèses externes utiles. Pour qu'elles deviennent des résultats du
dépôt, il faut au minimum :

1. **Projection bad-side complète sur PC-tree.** Définir formellement, pour un
   nœud PC `v`, la projection d'un atome `same_side(a,c;b,d)` sur les branches
   de `v`. Montrer si cette projection est nécessaire, suffisante, locale ou
   seulement diagnostique. Les projections farthest `I_x(v)` seules sont déjà
   insuffisantes par T046/T075.

2. **Lemme d'interface P-noeud.** Définir l'interface d'un bloc, le contexte
   extérieur fixé, les ordres internes valides et la relation résiduelle. Prouver
   ou réfuter que les complétions internes se factorisent en produit cartésien
   à ordre de branches fixé.

3. **Largeur 4 P-noeud.** Définir `A_v` et les relations `R_ijlm` sur
   quadruplets de branches. Prouver que les restrictions à quatre branches
   caractérisent `A_v`, ou produire un contre-exemple minimal sous le scaffold
   actuel.

4. **Route circle graph.** Formaliser le graphe d'entrelacement induit par les
   contraintes bad-side localisées et prouver qu'il appartient à une classe
   tractable, ou montrer qu'il peut simuler cyclic ordering sous les contraintes
   réalisables par une matrice `D`.

5. **Gadget manuscrit.** Transformer le screenshot 4 blocs x 2 feuilles en
   matrice, PC-tree et objectif explicites. Sans validation oracle et shrink, il
   reste un seed de générateur, pas un contre-exemple.

Ces obligations doivent être testées contre les garde-fous T046, T075, T081 et
T082 avant toute intégration dans `candidate.py`.

### T083 : projection bad-side complète sur nœuds PC

Statut : diagnostic expérimental R004, pas algorithme de décision.

`project_bad_side_obligations_to_pc_nodes(D,T)` matérialise les obligations
exactes d'ordre fixé :

```text
same_side(a,c;b,d) pour b,d in B_ac.
```

Pour chaque obligation, le diagnostic calcule les nœuds support du quartet,
puis enregistre, pour chaque nœud interne du PC-tree, les branches portant les
deux endpoints et les deux mauvais témoins. Le rapport distingue notamment les
obligations vues dans un seul nœud, les obligations multi-niveaux, les
projections à quatre branches distinctes, les rôles effondrés dans une même
branche et les charges d'interface de branches.

Ce que T083 couvre :

- il remplace le signal farthest `I_x(v)` seul par les obligations bad-side
  complètes ;
- il donne un objet mesurable pour tester les conjectures P-nœud/interface des
  notes R004 ;
- il verrouille T046 comme garde-fou : la projection farthest peut être muette
  alors que les obligations bad-side multi-niveaux sont actives.

Limites :

- le rapport ne prouve ni nécessité/suffisance d'une règle locale projetée, ni
  polynomialité ;
- une obligation multi-niveaux n'est pas automatiquement une obstruction, elle
  indique seulement où une relation résiduelle peut être nécessaire ;
- les counts de quatre branches et de violations dans l'ordre déclaré sont des
  métriques de stress, pas des certificats de `False` ;
- aucun résultat T083 ne doit être utilisé dans `candidate.py` sans lemme de
  sous-cas et témoin/rejet vérifiable.

### T084 : test empirique largeur 4 des P-nœuds

Statut : diagnostic expérimental borné, pas preuve de largeur 4.

Pour un nœud `P` du scaffold `PCNode`, `pnode_width4_frontier_projection_report`
définit :

```text
A_v = ordres circulaires des branches de v induits par les frontiers globales
      représentées et vérifiées cR.
```

Le diagnostic construit ensuite, pour chaque quadruplet de branches `Q`, la
relation `R_Q` obtenue en restreignant les ordres de `A_v` à `Q`. La fermeture
width4 est l'ensemble des ordres de branches dont toutes les restrictions à
quatre branches appartiennent aux `R_Q`. Une ligne complète est `refuted` si
cette fermeture contient un ordre absent de `A_v`.

Ce que T084 couvre :

- test direct de la conjecture R004 "les restrictions à quatre branches
  caractérisent les ordres de branches admissibles" dans le scaffold actuel ;
- séparation explicite entre énumération complète et troncature de frontiers ;
- garde de canonicalisation : les restrictions sont prises modulo rotation et
  renversement, et l'extraction d'ordre de branches tolère un bloc qui traverse
  la coupure linéaire de la frontier globale.

Limites :

- le test porte sur les enfants immédiats d'un nœud enraciné `PCNode`; il
  n'inclut pas encore la branche parent/outside d'un vrai PC-tree non enraciné ;
- `A_v` est défini par frontiers globales cR sous cap, pas par une relation
  d'interface locale indépendante ;
- une absence de réfutation sur un sweep ne prouve pas la largeur 4 ;
- un statut `holds` ne justifie aucune intégration candidate sans preuve que le
  modèle local ainsi testé est nécessaire, suffisant et composable.

### T085 : formalisation du gadget manuscrit 4 blocs

Statut : preuve expérimentale bornée / artefact de provenance, pas théorème.

Le probe T085 donne une matrice et des PC-trees explicites pour une famille de
lectures du screenshot 4 blocs x 2 feuilles. La comparaison `P` libre vs `C`
fixé est faite par énumération exacte des frontiers `n=8` et validation
bad-side/cR de chaque ordre accepté.

Ce que T085 permet d'affirmer :

- dans le budget testé, le seed manuscrit a bien un ordre de branches cR
  représenté par le `P` libre ;
- pour le même seed, le root `C=ABCD` est négatif alors que `ABDC` est positif ;
- dans la lecture plate `2/2/3`, le signal farthest projeté peut être silencieux
  alors que les obligations bad-side au root sont actives.

Ce que T085 ne prouve pas :

- aucune dureté générale ;
- aucune réfutation du cas `P` libre ;
- aucune preuve du lemme d'interface P-nœud ;
- aucune preuve de largeur 4 ;
- aucun `False` utilisable par `candidate.py`.

Obligation suivante : définir et tester une relation d'interface à ordre de
branches fixé, car T085 montre un phénomène de contrainte sur l'ordre de
branches mais ne teste pas encore la factorisation des complétions internes.

### T086 : produit d'interface à ordre de branches fixé

Statut : lemme négatif expérimental dans le scaffold général.

`root_fixed_order_interface_product_report` fixe un ordre de branches `sigma`,
énumère les complétions internes de chaque branche, puis calcule la relation
exacte `A_exact` des tuples qui donnent un ordre cR. Le diagnostic compare
`A_exact` au produit des projections unaires.

Ce que T086 prouve expérimentalement dans le scaffold testé :

- sur `single_bad_side_quartet_instance()` avec
  `T = P(P(0,1),P(2,3))` et `sigma=(0,1)`, la factorisation produit échoue ;
- l'échec est binaire : `minimal_coupling_support_size=2` ;
- les tuples faux du produit sont rejetés par une violation bad-side explicite
  `same_side(0,2;1,3)`.

Ce que T086 ne prouve pas :

- il ne réfute pas une version du lemme d'interface sous la promesse stricte
  "T vient de D" ou avec une définition enrichie d'interface ;
- il ne donne pas une preuve de dureté ;
- il ne justifie aucun `False` dans `candidate.py`.

Obligation suivante : remplacer la conjecture produit par une relation
résiduelle d'interface, au minimum binaire dans ce scaffold, puis tester si la
taille/largeur de cette relation reste contrôlable dans les familles T046,
T075, T082 et T085.

### T087 : interface avec contexte extérieur explicite

Statut : lemme négatif expérimental dans le scaffold général.

`fixed_context_interface_product_report` fixe un contexte linéaire extérieur et
compose les ordres sous la forme :

```text
context_before + frontier(focus) + context_after
```

Il énumère ensuite la relation exacte `A_exact` des complétions internes qui
donnent un ordre cR et compare cette relation au produit de ses projections
unaires par branche.

Ce que T087 prouve expérimentalement dans le scaffold testé :

- sur `context_coupling_seed_matrix()` avec focus
  `P(P(0,1),P(2,3))`, contexte `(4) ... (5)` et ordre de branches `(0,1)`,
  la factorisation produit échoue ;
- l'échec est non vide : `A_exact` contient `2` tuples et le produit des
  projections en contient `4` ;
- l'échec reste binaire : `minimal_coupling_support_size=2` ;
- les faux tuples sont rejetés par des violations bad-side explicites.

Ce que T087 ne prouve pas :

- le contexte utilisé est une linéarisation fixe de l'extérieur, pas une branche
  parent/outside complète avec ses propres degrés de liberté ;
- le seed n'est pas une preuve que la promesse "T vient de D" permet de telles
  relations ;
- les lignes T046/T085 avec relation vide ne sont pas des réfutations de
  factorisation non vide, seulement des collapses de contexte ;
- aucun `False` ne doit être ajouté à `candidate.py`.

Obligation suivante : définir la relation résiduelle exacte d'un patch/focus et
mesurer sa taille, ses projections minimales et sa composabilité sur T046,
T075, T082, T085 et des seeds générés.

### T088 : arité des relations résiduelles d'interface

Statut : preuve expérimentale bornée, pas théorème.

`tools/pc_residual_interface_probe.py` matérialise `A_exact`, la relation des
complétions internes acceptées pour une interface fixe, puis calcule pour chaque
arité `k` la fermeture déterminée par toutes les projections `k`-aires.

Ce que T088 couvre :

- le seed T087 est bien une relation non unaire, mais binaire ;
- dans le sweep two-level `P2 x P2 x P2` avec contexte `(6) ... (7)`,
  `24157` matrices sont inspectées complètement jusqu'à `4` paires hautes ;
- `2514` relations sont non triviales ;
- `54` cas exigent une arité minimale `2` ;
- aucun cas exigeant une arité strictement supérieure à `2` n'est trouvé dans
  ce budget.

Ce que T088 ne prouve pas :

- il ne prouve pas que toutes les interfaces résiduelles sont binaires ;
- le focus testé a seulement trois branches `P2` et des distances two-level ;
- le contexte extérieur est fixé linéairement ;
- la promesse "PC-tree issu de D" n'est pas vérifiée ;
- aucun résultat ne justifie une intégration dans `candidate.py`.

Obligation suivante : chercher activement une relation résiduelle d'arité `3`
dans des familles plus riches : branches `P3`, plus de niveaux de distance,
contexts non vides plus longs, et patches composés de plusieurs supports.

### T089 : stress d'interfaces résiduelles plus riches

Statut : preuve expérimentale bornée, pas théorème.

`tools/pc_residual_interface_stress_probe.py` étend T088 avec deux familles :

- `P2 x P2 x P2 x P2` sparse two-level ;
- `P3 x P3 x P3` sparse two-level.

Ce que T089 couvre :

- deux contrôles déterministes binaires sont versionnés :
  `p2x4_binary_seed` et `p3x3_binary_seed` ;
- le stress `P2x4` lance `5000` essais random : `384` relations non
  triviales, `19` relations d'arité minimale `2`, aucun cas `>2` ;
- le stress `P3x3` lance `1500` essais random : `198` relations non triviales,
  `22` relations d'arité minimale `2`, aucun cas `>2` ;
- la meilleure ligne `P3x3` observée a `4` tuples acceptés et reste
  déterminée par ses projections binaires.

Ce que T089 ne prouve pas :

- deux stress sparse two-level ne prouvent pas une largeur binaire générale ;
- les contextes restent fixés linéairement ;
- les patches composés et les interactions multi-supports ne sont pas testés ;
- la promesse "T vient de D" n'est pas vérifiée.

Obligation suivante : après T088/T089, ne pas continuer uniquement à augmenter
les essais sparse two-level. Basculer vers une nouvelle source de complexité :
patchs composés, contexte extérieur avec degrés de liberté, ou modélisation
circle graph/split decomposition des contraintes same-side.

### T090 : projection de relation résiduelle de bord

Statut : preuve expérimentale bornée, pas théorème.

`tools/pc_boundary_residual_projection_probe.py` teste une faiblesse plus proche
d'une DP de patch composé : partir de la relation exacte sur toutes les branches
d'un focus `P`, cacher au moins une branche interne, et mesurer l'arité minimale
nécessaire pour reconstruire la relation projetée sur le bord.

Ce que T090 couvre :

- contrôle `P2x4` reproduisant une relation de bord binaire ;
- sweep `P2x4` sparse two-level : `20000` cas scannés, `2645` relations
  complètes non triviales, histogramme de projections de bord `{1: 9315, 2: 168}`,
  aucun cas d'arité `>2` ;
- sweep `P2x5` sparse two-level : `20000` cas scannés, `3166` relations
  complètes non triviales, histogramme de projections de bord
  `{1: 37708, 2: 792}`, aucun cas d'arité `>2` ;
- random multi-niveaux `P2x4` : `500` essais, aucune projection de bord
  non triviale.

Ce que T090 ne prouve pas :

- une absence d'arité `3` dans ces sweeps ne prouve pas une interface binaire
  générale ;
- les scans sparse sont tronqués par nombre de cas et restent two-level ;
- le random multi-niveaux est surtout vide/plein, donc peu stressant ;
- le contexte extérieur reste fixe et les patches multiples avec contexte
  variable ne sont pas encore modélisés ;
- aucun résultat ne justifie une intégration dans `candidate.py`.

Obligation suivante : chercher une source de complexité différente, soit par
contexte extérieur avec degrés de liberté, soit par une traduction circle
graph/split decomposition des contraintes `same_side`.
