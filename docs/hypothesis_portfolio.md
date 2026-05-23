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

Sous-cas ajouté : explorer le cas strict comme algorithme spécialisé
potentiellement polynomial. Ne pas l'intégrer à `candidate.py` avant d'avoir une
détection stricte et une génération de candidats stricts vérifiées contre les
PDF/source notes.

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
