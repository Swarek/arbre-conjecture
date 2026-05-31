# Hypothesis portfolio

Le portefeuille doit conserver au moins 4 pistes actives. Une piste qui échoue
deux fois de suite sans meilleur benchmark, preuve partielle ou nouveau
contre-exemple doit être remplacée ou reformulée.

Les détails vivants par piste sont dans `docs/tracks/README.md`. Ce fichier
reste le portefeuille synthétique ; les fichiers `docs/tracks/piste_*.md`
contiennent les essais, résultats, artefacts et prochaines actions.

Complément externe : `docs/external_analysis_digest.md` résume une analyse GPT
5.5 Pro fournie par l'utilisateur. À intégrer dans les prochaines itérations
surtout pour trois axes : universalité comme variante polynomial-looking mais
distincte de l'existence, sous-cas strict, et projection des ensembles
`I_x(v) = {i : B_i intersecte F_x}` sur les branches d'un nœud `P`.

Complément externe 2026-05-23 : la revue
`docs/external_reviews/gpt55_bad_side_quartet_strategy_2026-05-23.md` doit être
lue comme un routage multi-pistes, pas comme une instruction de se concentrer
sur T057. Elle alimente bad-side fixed-order, quartet CSP, 2-SAT/treewidth,
circular-ones/universalité et catalogue de relations non booléennes.

Complément red-team 2026-05-23 :
`docs/external_reviews/gpt55_red_team_domain_warning_2026-05-23.md` rappelle
que la treewidth du CSP ne suffit pas sans borne ou compression prouvée des
domaines `P`. Le cas star/single `P` doit rester un stress prioritaire.

Complément stratégie globale 2026-05-23 :
`docs/external_reviews/gpt55_global_strategy_threshold_pc_2026-05-23.md` ajoute
un routage large après les saturations T075/T077. Priorités proposées :
reformulation par seuils, test de PC-représentabilité des ordres cR, phase
transition star, obstructions globales high-girth, compression de branches `P`
actives. Ces pistes doivent être traitées comme hypothèses falsifiables.

## Piste A : contraintes locales sur nœuds P/C

Intuition : les croisements de cordes farthest-neighbor imposent peut-être des
contraintes locales sur les permutations autorisées par chaque nœud.

Invariant testé : toute obstruction de quartet doit se projeter sur un petit
nombre de branches incidentes.

Signature algorithmique possible : filtrage local des ordres de branches,
propagé de bas en haut.

Test expérimental associé : générer de gros P-nodes et vérifier si les
contraintes locales prédisent exactement l’oracle sur `n <= 8`.

Raisons possibles d’échec : une obstruction peut dépendre de choix corrélés dans
plusieurs nœuds.

Prochain essai concret : journaliser les quartets farthest qui réfutent chaque
ordre et mesurer leur support minimal dans le PC-tree.

Question ajoutée depuis l'analyse externe : pour un nœud `P` de branches
`B_1,...,B_k`, mesurer si les projections `I_x(v)` des farthest sets sont
laminaires ou intervalles circulaires dans les ordres admissibles des branches.
Un résultat positif pointerait vers circular-ones local ; un résultat négatif
alimenterait la piste NP-difficulté.

Mise à jour T075 : le probe `make bench-frontier-obstructions` énumère des
frontiers représentées et profile le premier quartet cR interdit. Sur le sweep
borné `n=5..8`, `balanced/mixed`, les `494` frontiers non-cR profilées restent
silencieuses pour les projections locales `I_x(v)` et exigent toutes un
support multi-niveau. La prochaine tentative locale doit porter une relation de
bord, pas seulement des ensembles projetés par nœud.

Mise à jour T086 : le produit cartésien indépendant des complétions internes
est réfuté dans le scaffold par `single_bad_side_quartet_instance()` sur
`P(P(0,1),P(2,3))`. La prochaine formulation locale doit donc transporter une
relation résiduelle d'interface, au moins binaire dans ce témoin, plutôt qu'une
simple projection unaire par branche.

Mise à jour T087 : la même idée de produit indépendant reste fausse quand le
nœud focal est placé dans un contexte extérieur fixé
`context_before + focus + context_after`. Le seed `n=6` versionné a deux
complétions acceptées, mais le produit des projections en crée deux fausses.
La piste A doit donc mesurer et composer des relations résiduelles de bord, pas
des signatures unaires de branches.

Mise à jour T088 : un premier probe d'arité résiduelle sur un focus
`P2 x P2 x P2` two-level a inspecté `24157` cas complets jusqu'à `4` paires
hautes. Il trouve `54` relations exigeant une projection binaire, mais aucune
relation exigeant une arité `3`. C'est un signal en faveur d'interfaces
binaires dans cette famille bornée, pas une preuve générale.

Mise à jour T089 : le stress sparse two-level plus riche sur
`P2 x P2 x P2 x P2` et `P3 x P3 x P3` trouve de nouveaux témoins binaires
contrôlés, mais toujours aucune arité `3` (`6500` essais random plus deux
contrôles). Après deux itérations sans arité `3`, la prochaine attaque doit
changer de famille : patches composés, contexte extérieur non fixe ou route
circle graph/split decomposition.

Mise à jour T090 : la projection de relations résiduelles après avoir caché des
branches internes ne trouve toujours aucune arité de bord `>2` sur `P2x4` et
`P2x5` sparse two-level (`40000` cas scannés au total) ni sur `500` essais
random multi-niveaux `P2x4`. Cela renforce expérimentalement l'intérêt d'une
interface binaire, sans preuve. La piste A doit maintenant changer de mécanisme
plutôt que continuer à augmenter les seeds two-level.

## Piste B : programmation dynamique sur le PC-tree

Intuition : un état de frontière pourrait résumer les contraintes externes d’un
sous-arbre.

Invariant testé : deux sous-ordres équivalents pour les interactions
farthest-neighbor futures doivent avoir la même signature.

Signature algorithmique possible : DP bottom-up avec états décrivant extrêmes,
classes de farthest et compatibilité cyclique.

Test expérimental associé : comparer le nombre d’états distincts sur arbres
balanced versus star.

Raisons possibles d’échec : explosion d’états ou signature non suffisante.

Prochain essai concret : définir une signature candidate et chercher un
contre-exemple minimal où deux états fusionnés divergent.

## Piste C : réduction à 2-SAT / CSP / contraintes d’ordre cyclique

Intuition : les choix d’orientation des nœuds `C` et de permutation des petits
nœuds pourraient être encodés en variables discrètes.

Invariant testé : les violations cR se traduisent en clauses interdites sur des
quartets de branches.

Signature algorithmique possible : CSP fini sur orientations/permutations, avec
2-SAT dans les sous-cas binaires.

Test expérimental associé : extraire toutes les clauses nécessaires sur petits
arbres et vérifier si elles sont suffisantes.

Raisons possibles d’échec : les grands nœuds `P` induisent des contraintes
d’ordre cyclique non binaires.

Prochain essai concret : après T062 et la revue R002, tester d'abord par un
probe borné si une intégration positive-only de `solve_quartet_2sat` ou
`solve_quartet_treewidth_csp` dans `candidate.py` apporte de vrais témoins
nouveaux sous garde de coût. Sans gain mesuré, basculer vers le catalogue de
relations non booléennes/gadgets ou vers la collision de second ordre T057.
Garder séparés les UNSAT relationnels tant que la suffisance globale du modèle
relationnel n'est pas prouvée.

Mise à jour T064 : avant toute intégration treewidth dans `candidate.py`,
toujours reporter aussi la taille maximale de domaine local. Une ligne de
treewidth `0` sur un gros `P` peut cacher `(n-1)!/2` états.

Mise à jour T073 : les composantes binaires `sparse_partial_matching`
insatisfiables observées dans le sweep T072 sont toutes accompagnées de
`constant_reject`. Elles sont utiles comme diagnostic de projections
disjointes sur une variable partagée, mais ne sont pas encore des gadgets
parasite-free.

Mise à jour T074 : un probe de couverture positive-only des solveurs
`solve_quartet_2sat` et `solve_quartet_treewidth_csp` sur `p3_block_tree(k)`
n'a trouvé aucun témoin positif nouveau par rapport à `candidate.py` dans le
sweep courant. L'intégration de ces solveurs dans la candidate n'est donc pas
justifiée sans nouvelle famille ou garde de coût plus ciblée.

## Piste D : intersection de contraintes type PC-tree / circular-ones

Intuition : la condition circular Robinson pourrait être reformulée comme une
famille de contraintes d’arcs ou de circular-ones à intersecter avec le PC-tree.

Invariant testé : chaque contrainte dérivée de `D` doit préserver exactement les
ordres circular Robinson parmi les ordres quasi-circulaires.

Signature algorithmique possible : construire un second système PC/PQ/circular
ones et tester l’intersection.

Test expérimental associé : générer les contraintes de boules et de farthest,
puis comparer l’intersection à l’oracle.

Raisons possibles d’échec : les contraintes cR ne sont pas toutes exprimables en
arcs indépendants.

Prochain essai concret : cataloguer les violations minimales non représentables
par une simple contrainte d’arc.

Sous-piste à garder séparée : les contraintes de 2-balls/clusters de
Brucker-Osswald peuvent être traitables par hypercycles/circular-ones, mais la
condition cR actuelle est une contrainte de croisement de cordes, pas une simple
contrainte de consécutivité.

Mise à jour T075 : le probe frontier/support confirme que les variantes
circular-ones locales ne capturent pas les obstructions multi-niveaux. Même
quand `project_farthest_sets_to_pc_nodes` est silencieux sur tous les nœuds, les
frontiers non-cR exhibent un quartet bad-side exact. La piste D doit donc
chercher une intersection globale ou un modèle de projection-adjacence.

Mise à jour T078 : la reformulation clean-side par seuil est maintenant testée
comme équivalent fixed-order à bad-side. Elle ne restaure pas une contrainte
circular-ones simple, mais elle déplace l'objet vers les intersections
`N_{d(a,b)}[a] intersect N_{d(a,b)}[b]`, ce qui alimente les pistes round-order
commun, seuils imbriqués et projection-adjacence.

Mise à jour T079 : le test de PC-représentabilité bornée des ordres cR produit
des contre-exemples complets dans le scaffold `PCNode` dès `n=5` sur la famille
`paired_farthest`. L'ensemble cR y contient exactement deux ordres, sans arbre
`PCNode` généré par le learner exact borné. Cela réfute la route naïve
"calculer un PCNode des ordres cR" dans le scaffold, mais pas encore la
PC-représentabilité Hsu/McConnell complète.

Mise à jour T080 : le premier contre-exemple T079 survit à un modèle PC-tree
non enraciné explicite à `5` feuilles : `893` candidats topologie/type/ordre C,
`93` familles distinctes, `0` représentation exacte de la cible à deux ordres.
La route "les ordres cR forment toujours un PC-tree" devient nettement moins
plausible ; la prochaine étape doit chercher soit un argument général de
non-représentabilité, soit une structure plus riche qu'un seul PC-tree.

## Piste E : obstructions interdites par quartets farthest-neighbor

Intuition : les mauvais ordres pourraient être caractérisés par une famille
finie ou structurée d’obstructions de quartets.

Invariant testé : toute violation cR produit une obstruction farthest ou une
obstruction dérivée avec égalités contrôlées.

Signature algorithmique possible : séparation par obstructions, ajout
incrémental de contraintes, shrink de contre-exemples.

Test expérimental associé : enregistrer les quartets minimaux pour chaque
désaccord et mesurer leur fréquence par famille d’instances.

Raisons possibles d’échec : les cas non stricts peuvent casser une
caractérisation purement farthest.

Prochain essai concret : séparer strict, non strict et égal-distance dans les
générateurs.

État 2026-05-22 : la condition farthest-crossing brute est déjà réfutée comme
critère autonome. Deux contre-exemples minimaux à 4 points sont enregistrés :
un cas égal-distance circular Robinson où la condition brute échoue, et un cas à
farthest unique où la condition brute passe mais cR échoue. La piste reste utile
comme source d’obstructions, pas comme solver suffisant.

Mise à jour T081 : le probe local-to-global mesure la taille minimale des
sous-matrices induites non-cR. Les noyaux `four_local_non_cr` et
`five_local_non_cr` donnent des obstructions minimales de tailles `5` et `6`,
respectivement, avec toutes les restrictions plus petites positives dans le
scan exact. La piste doit donc chercher des familles high-girth/globales, pas
seulement accumuler des certificats 4/5.

Mise à jour T082 : le probe chirotope same-side réexprime bad-side comme un
système de contraintes de côté et trouve des candidats high-girth calibrés :
`odd_high_cycle_low_hub` en `n=8` et `even_high_cycle_low_hub` en `n=9` sont
globalement négatifs alors que tous les sous-ensembles de taille au plus `6`
sont positifs. Cela réfute plus nettement toute stratégie fondée sur un cap
local `<=6` seul.

## Piste F : complexité / NP-difficulté / contre-exemples à la tractabilité

Intuition : l’existence dans un PC-tree compact peut être plus dure que le test
d’un ordre donné.

Invariant testé : grands P-nodes et contraintes d’alternance peuvent simuler un
problème de permutation difficile.

Signature algorithmique possible : réduction depuis betweenness, cyclic ordering
ou un CSP d’ordre.

Test expérimental associé : chercher des familles où le nombre d’ordres valides
est rare et où les filtres locaux échouent.

Raisons possibles d’échec : la structure quasi-circulaire imposée par
Hsu/McConnell peut rendre le problème plus rigide que les PC-trees arbitraires.

Prochain essai concret : utiliser le graphe primal et le catalogue de relations
fusionnées T059 pour comparer PC-trees arbitraires, arbres binaires C-only,
arbres balanced/mixed et gros nœuds `P`, puis chercher une relation non
booléenne de type gadget sans masquer les contraintes parasites de `D`.

Mise à jour T064 : le benchmark single `P` confirme que le paramètre "treewidth
du graphe primal" est insuffisant seul. Le prochain axe F doit donc combiner
largeur, taille de domaine et représentation compacte des permutations de gros
`P`.

Mise à jour T065 : le catalogue `P3/P3` produit de nombreuses relations
binaires non booléennes distinctes, mais aussi beaucoup de parasites
unaires/constantes. La prochaine expérience doit chercher une relation
structurée isolable, pas conclure à la dureté depuis le catalogue brut.

Mise à jour T066 : le minage des formes trouve des relations
`sparse_partial_matching`, `partial_bijection`, sélecteurs,
`active_two_regular` et ponts `2 x 6`, mais aucun candidat positif sans parasite
restrictif. La prochaine expérience prioritaire est donc soit une recherche
d'élimination de parasites pour une forme choisie, soit une composition de
chaînes fonctionnelles qui révèle une corrélation globale.

Mise à jour T067 : un sweep `paired_farthest` ciblé révèle des profils
`permutation_like` sans parasite restrictif dans le scaffold `P3/P3`, et une
ligne `interaction_unsat` sans `constant_reject` apparaît sur une obstruction
paddée. Ces signaux restent expérimentaux, mais ils donnent deux prochaines
cibles : isoler les permutations-like sous le promise `T(D)` et minimiser
l'interaction UNSAT entre parasites unaires et relation fonctionnelle.

Mise à jour T068 : l'interaction UNSAT T067 se minimise en un noyau relationnel
de taille `2` dans le CSP matérialisé : une unaire non booléenne sur le bloc
`0` et une relation binaire `sparse_partial_matching` entre `0` et `1`. La
projection gauche brute de la binaire est disjointe des valeurs acceptées par
l'unaire. C'est un diagnostic de conflit uniaire+binaire, pas une preuve de
dureté globale.

Mise à jour T069 : le probe `permutation_like` vérifie sur `n=6` que les profils
bijectifs parasite-free de `paired_farthest/P3x2` apparaissent exactement dans
les lignes où le scaffold `P3/P3` égale l'ensemble exhaustif des ordres
quasi-circulaires de `D`. Cela renforce le signal promise-aware en petite
taille, mais ne reconstruit pas Hsu/McConnell en général et ne prouve pas la
composabilité des gadgets.

Mise à jour T070 : le probe de composition multi-blocs ne trouve aucun candidat
propre sur `paired_farthest/P3x{k}` pour `k=2,3,4` et `64` seeds. Les
`permutation_like` restent isolées : `5` lignes propres en `k=2`, aucune en
`k=3`, et une seule ligne en `k=4` bloquée par parasites. C'est un signal
négatif contre la composition naïve de ce gadget local, pas une preuve
d'impossibilité.

Mise à jour T071 : le prochain stress élargit T070 à toutes les relations
binaires non booléennes. L'hypothèse à tester est que les composantes
multi-arêtes existent pour d'autres formes (`active_two_regular`,
`partial_bijection`, sélecteurs, ponts), mais qu'elles restent bloquées par
parasites dans le scaffold `paired_farthest/P3x{k}`. Un composant multi-arêtes
parasite-free serait un nouveau candidat gadget ; son absence est seulement un
signal négatif expérimental.

Mise à jour T072 : la piste `sparse_partial_matching` est traitée comme
diagnostic de conflits locaux. Le test prioritaire mesure les intersections
vides entre projections sparse et unaires, ainsi que les composantes formées
seulement de relations sparse. Un noyau binaire sparse sans parasite serait un
signal nouveau ; un conflit unaire+binaire confirme surtout une limite des
compressions qui séparent binaires et parasites.

Sous-cas ajouté : explorer le cas strict comme algorithme spécialisé
potentiellement polynomial. Ne pas l'intégrer à `candidate.py` avant d'avoir une
détection stricte et une génération de candidats stricts vérifiées contre les
PDF/source notes.

Mise à jour T076 : l'audit borné `make bench-strict-algorithm52` ne trouve aucun
mismatch entre `strict_algorithm52_report` et l'énumération exacte des ordres
stricts sur `360` lignes `n=4..7`, avec PC-trees `none/star/balanced/mixed`.
La piste stricte devient un bon candidat de sous-cas à formaliser, mais pas
encore une intégration candidate : pas de preuve de complétude générale, pas de
gain large-n mesuré, et aucun rejet `False` ne serait justifié.

Mise à jour T077 : le probe large-n positive-only strict trouve `204` témoins
stricts validés mais `0` nouveau positif par rapport à `candidate.py` sur
`708` lignes. La piste stricte ne doit donc pas être intégrée maintenant ; elle
doit soit recevoir une preuve de sous-cas, soit être relancée avec une famille
où la candidate est réellement incomplète.

Mise à jour R004 (2026-05-31) : les notes externes récentes sont triées dans
`docs/external_reviews/researcher_advances_2026-05-31.md`. Les idées à garder
ne sont pas des résultats : (1) projection des contraintes bad-side complètes
sur les nœuds PC plutôt que projection farthest seule, (2) lemme d'interface
pour les P-nœuds à contexte fixé, (3) conjecture de largeur 4 sur les ordres de
branches d'un P-nœud, (4) route circle graph / split decomposition. La suite ne
doit pas intégrer ces claims à `candidate.py`; elle doit d'abord les transformer
en probes falsifiables contre T046/T075/T081/T082.

Mise à jour T083 : le probe `make bench-r004-bad-side-projections` matérialise
la projection bad-side complète. Le signal clé du sweep est que `82` lignes ont
une projection farthest silencieuse mais des obligations bad-side actives, et
`77` lignes ont des obligations multi-niveaux. La prochaine hypothèse
falsifiable n'est donc plus "`I_x(v)` suffit", mais "les obligations
multi-niveaux admettent une petite relation d'interface exploitable".

Mise à jour T084 : le probe `make bench-pnode-width4` teste directement, dans
le scaffold enraciné, si les ordres de branches cR projetés sur un nœud `P`
sont déterminés par leurs restrictions à quatre branches. Le sweep initial ne
trouve aucune réfutation complète (`0` nœud réfuté sur `35` lignes testées),
mais cela reste une preuve expérimentale bornée : la branche parent/outside et
la vraie relation d'interface ne sont pas encore modélisées.

État 2026-05-22 : deux familles explicites ont été ajoutées sans modifier
`mixed` :

- `permuted_cycle` : sous-cas planted-cycle où le témoin est caché par
  relabellisation ;
- `paired_farthest` : famille à appariements farthest uniques, rareté d’ordres
  cR et faux positifs farthest.

Le benchmark peut maintenant ajouter des diagnostics exacts jusqu’à une taille
bornée via `--diagnostics-up-to`.

## Sous-cas

Sous-cas à maintenir séparément : strict, degré borné, PC-arbre sans gros
P-nœuds, familles laminaires, balanced PC-tree, cas où certains ordres marchent
et d’autres non.

Chaque conjecture cassée doit produire un artefact durable : test, générateur,
contre-exemple minimal, lemme négatif ou entrée dans `experiment_log`.
