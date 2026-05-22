# Piste C - SAT / CSP / contraintes d’ordre cyclique

## Question

Peut-on encoder exactement les choix locaux du PC-tree et les quartets cR
interdits en CSP, puis exploiter cet encodage pour un solver ?

## Intuition

Chaque nœud interne a un choix local :

- nœud `C` : orientation forward/reverse ;
- nœud `P` : permutation de ses enfants.

Une affectation complète détermine une frontier. Les quartets cR interdits
deviennent des nogoods sur les choix locaux qui rendent le quartet cycliquement
ordonné de façon interdite.

## Encodage proposé

Statut : conjecture algorithmique / non intégré.

Variables :

- une variable par nœud interne ;
- domaine `{forward, reverse}` pour `C` ;
- domaine des permutations d’enfants pour `P`, d’abord limité aux petits degrés.

Contraintes :

- exactement une valeur par variable ;
- pour chaque quadruplet interdit `(x,y,z,t)`, interdire les affectations où
  `x,y,z,t` apparaissent dans cet ordre cyclique.

Première cible :

- backtracking finite-domain sans dépendance SAT externe ;
- `n <= 7`;
- degrés internes `<= 3`;
- comparaison stricte avec l’oracle exact.

## Obstacles

Les grands nœuds `P` donnent des contraintes naturellement 4-aires sur l’ordre
cyclique de branches. Une réduction 2-SAT pure serait probablement fausse sans
structure supplémentaire.

## Tests à créer

- les frontiers générées par affectations doivent égaler `enumerate_frontiers`;
- les ordres acceptés par CSP doivent égaler les ordres cR exacts sur petits
  arbres balanced/mixed ;
- les régressions non strictes doivent passer ;
- un gros `P` doit être traité comme permutation-domain ou explicitement marqué
  non 2-SAT.

## Tentative T009 - Prop. 4.5 comme nogood de frontier

Statut : preuve expérimentale / scaffold, non intégré dans `candidate.py`.

Changement : `prop45_nogood_frontier_report` énumère des frontiers bornées ou
complètes, filtre optionnellement les ordres non quasi-circulaires, puis compare
le filtre Prop. 4.5 avec `is_precircular_order_cR`. Le rapport expose le premier
rejet, les faux positifs, les faux négatifs, un témoin accepté et si
l’énumération a été tronquée.

Invariant testé : sur les ordres quasi-circulaires, le filtre Prop. 4.5 doit
coïncider avec cR exact. Le test exhaustif `n=4` couvre les matrices à valeurs
`{1,2,3}` qui possèdent au moins un ordre quasi-circulaire.

Limite : ce n’est pas encore un CSP de choix locaux du PC-tree. C’est une
énumération contrôlée qui prépare les nogoods et les métriques de désaccord.

Risque : si le PC-tree fourni n’est pas garanti quasi-circulaire pour `D`,
`require_quasi=True` saute les ordres hors précondition ; `require_quasi=False`
doit être interprété comme diagnostic seulement.

Prochaine action : implémenter un vrai moteur de domaines locaux pour petits
nœuds `P/C`, en commençant par `source="cr"` pour valider le moteur sans
nouvelle hypothèse mathématique, puis comparer à `source="prop45"`.

## Tentative T010 - Domaines locaux P/C et source cR directe

Statut : conséquence directe expérimentale / scaffold, non intégré dans
`candidate.py`.

Changement : `build_local_domains` crée une variable par nœud interne, avec
domaine forward/reverse pour `C` et permutations bornées pour `P`.
`frontier_from_assignment` reconstruit la frontier d’une affectation complète.
`solve_nogood_csp(source="cr")` énumère ces affectations, déduplique les
frontiers circulaires canoniques, puis accepte exactement celles qui vérifient
`is_precircular_order_cR`.

Invariant testé : pour les PC-trees supportés, les frontiers reconstruites par
affectations locales coïncident avec `enumerate_frontiers`. Le filtre
`source="cr"` coïncide avec `enumerate_frontiers(T)` filtré par cR exact.

Limite : il n’y a pas encore de pruning compact ni de clauses projetées sur un
petit support. Le moteur énumère les affectations et sert à valider la couche de
variables avant compression. Un nœud `P` de degré supérieur à `max_p_degree`
renvoie `unsupported` et ne produit pas de décision négative.

Résultat expérimental : probe sur `1600` instances `n=4..7`, arbres
balanced/mixed, familles `random/cycle/block/ultrametric/equal/non_strict/
paired_farthest/permuted_cycle` : aucun désaccord entre CSP `source="cr"` et le
filtre exact de frontiers.

Prochaine action : compiler de vrais nogoods de quartets cR sur supports de
variables, puis chercher si ces nogoods prunent avant énumération complète ou si
des collisions forcent une signature plus riche.

## Tentative T011 - Nogoods compilés de quartets cR

Statut : preuve expérimentale / scaffold, non intégré dans `candidate.py`.

Changement : `forbidden_cr_atoms` génère les quartets ordonnés dont l’inégalité
cR échoue. `quartet_support_paths` calcule le sous-arbre de variables locales
pertinentes pour les quatre labels. `compile_cr_nogoods` projette les
affectations violant un atom sur ce support, puis
`solve_compiled_nogood_csp` compare les signatures compilées aux affectations.

Invariant testé : un nogood compilé ne doit rejeter qu’une affectation dont la
frontier viole `is_precircular_order_cR`, et toute frontier non-cR doit matcher
au moins un nogood. Les tests couvrent un split imbriqué, un test négatif où
retirer une variable du support change la projection du quartet, un cas de
wrapping autour de la coupure linéaire, et l’égalité avec le filtre cR direct.

Résultat expérimental : probe sur `960` instances `n=4..7`, arbres
balanced/mixed, familles `random/cycle/block/ultrametric/equal/non_strict/
paired_farthest/permuted_cycle` : aucun désaccord entre le solveur à nogoods
compilés et `solve_nogood_csp(source="cr")`. `153512` nogoods uniques ont été
produits dans cette probe, ce qui montre que la compilation est encore
énumérative et peut être volumineuse.

Limite : la compilation inspecte encore les affectations complètes pour découvrir
les signatures. Ce n’est pas une preuve de complexité ni un algorithme compact.

Prochaine action : mesurer la taille des supports et chercher des familles où le
nombre de nogoods explose, puis tenter un backtracking qui prune dès qu’une
signature partielle matche un nogood.

## Prochaine action

Mesurer les supports/nogoods et implémenter un backtracking avec pruning par
signatures partielles, sans appeler `candidate.py` tant que la suffisance et les
cas non stricts ne sont pas établis.
