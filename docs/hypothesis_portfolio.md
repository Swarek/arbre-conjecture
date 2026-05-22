# Hypothesis portfolio

Le portefeuille doit conserver au moins 4 pistes actives. Une piste qui échoue
deux fois de suite sans meilleur benchmark, preuve partielle ou nouveau
contre-exemple doit être remplacée ou reformulée.

Les détails vivants par piste sont dans `docs/tracks/README.md`. Ce fichier
reste le portefeuille synthétique ; les fichiers `docs/tracks/piste_*.md`
contiennent les essais, résultats, artefacts et prochaines actions.

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

Prochain essai concret : isoler les sous-cas où tous les nœuds internes ont
degré au plus 3.

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

Prochain essai concret : comparer PC-trees arbitraires et PC-trees obtenus à
partir de dissimilarités quasi-circulaires.

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
