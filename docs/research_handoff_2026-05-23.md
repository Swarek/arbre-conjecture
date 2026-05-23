# Note de synthese pour le chercheur

Date : 2026-05-23.

Objectif de cette note : transmettre les idees mathematiques testees, les
contre-exemples trouves, les pistes qui semblent prometteuses, et les points ou
le travail du chercheur va plus loin que les experiences deja faites ici.

Cette note ne pretend pas resoudre le probleme. Elle separe autant que possible
les faits experimentaux, les lemmes stabilises, les conjectures et les impasses.

## 1. Clarification importante des notions

Dans nos experiences, il y a deux couches distinctes.

### Couche A : boules comme arcs

Un ordre circulaire est admissible si toutes les boules

```text
B_r(y) = {x : d(y,x) <= r}
```

sont des arcs circulaires. C'est ce que nous avons appele la couche
**quasi-circulaire**. Le PC-tree de Hsu-McConnell represente precisement une
famille compacte d'ordres de ce type.

### Couche B : condition circular Robinson forte

Parmi les ordres admissibles de la couche A, le probleme etudie ici demande s'il
existe un ordre qui satisfait aussi la condition de type circular Robinson :

```text
pour tout x < y < z < t,
d(x,z) >= min(max(d(x,y), d(y,z)), max(d(x,t), d(t,z))).
```

C'est cette couche B qui reste difficile.

Point a aligner avec les notes du chercheur : si le terme "Robinson circulaire"
y designe seulement "toutes les boules sont des arcs", alors il correspond a la
couche A. Le probleme du depot ajoute la couche B. Cela peut expliquer pourquoi
un algorithme base uniquement sur Hsu-McConnell pour les boules semble plus
simple : il resout l'admissibilite quasi-circulaire, mais pas encore la
selection d'un ordre circular Robinson dans le PC-tree obtenu.

## 2. Lemme le plus utile trouve : formulation bad-side

Pour deux points distincts `a,c`, definir :

```text
B_ac = {u notin {a,c} : max(d(a,u), d(u,c)) > d(a,c)}.
```

Ce sont les "mauvais temoins" pour la paire `{a,c}`.

Le critere experimentalement stabilise, et probablement le meilleur lemme de
base, est :

```text
Un ordre circulaire beta est circular Robinson
ssi pour toute paire {a,c}, tous les points de B_ac sont contenus
dans un seul des deux arcs ouverts entre a et c.
```

Autrement dit, si `b,d in B_ac`, alors `b` et `d` doivent etre du meme cote de
la corde `ac`. Il faut donc interdire l'alternance circulaire :

```text
a, b, c, d.
```

Cette formulation est plus forte et plus propre que les tests fondes seulement
sur les plus lointains voisins. Elle montre aussi que les diametres globaux ne
suffisent probablement pas : il faut controler toutes les paires `{a,c}`, pas
seulement celles de distance maximale.

Version equivalente par seuil :

```text
C_ac = N_{d(a,c)}[a] ∩ N_{d(a,c)}[c].
```

L'ordre est circular Robinson ssi, pour chaque paire `{a,c}`, au moins un des
deux arcs ouverts entre `a` et `c` est contenu dans `C_ac`.

Cette version par seuil semble etre la meilleure passerelle vers des idees de
graphes de seuil, ordres round, proper circular-arc, ou contraintes imbriquees.

## 3. Ce que les experiences ont refute

### 3.1 Les plus lointains voisins seuls ne suffisent pas

Les contraintes de croisement de plus lointains voisins sont utiles en regime
strict, mais elles ne donnent pas une caracterisation generale en non strict.

Deux types de contre-exemples apparaissent :

- des cas avec egalites ou la condition farthest brute rejette un ordre pourtant
  circular Robinson ;
- des cas ou le filtre farthest passe, mais une contrainte bad-side non
  maximale viole circular Robinson.

Conclusion : les farthest-neighbors sont un diagnostic, pas une solution.

### 3.2 Les petites obstructions ne suffisent pas

Nous avons cherche des sous-matrices induites minimales non circular Robinson.

Resultats utiles :

- il existe un noyau non-cR de taille `5` dont toutes les restrictions de taille
  `4` sont positives ;
- il existe un noyau non-cR de taille `6` dont toutes les restrictions de taille
  `5` sont positives ;
- il existe des familles low-hub / high-cycle globalement negatives, mais dont
  toutes les restrictions jusqu'a taille `6` restent positives.

Conclusion : une theorie par sous-matrices interdites de taille `4`, `5` ou
`6` ne peut pas etre complete. Les obstructions peuvent etre globales.

### 3.3 Un PC-tree unique des ordres circular Robinson est peu plausible

Une idee naturelle etait :

```text
Calculer directement la famille de tous les ordres circular Robinson de D,
puis l'intersecter avec le PC-tree quasi-circulaire.
```

Nous avons teste si, pour de petites matrices, l'ensemble de tous les ordres cR
est lui-meme representable par un PC-tree.

Un contre-exemple de taille `5` donne exactement deux ordres circular Robinson,
et cette famille n'est pas representable par les modeles PC-tree testes,
y compris un modele non enracine explicite a `5` feuilles.

Conclusion : la route "un PC-tree des ordres cR" est tres fragilisee. Il faut
probablement une structure plus riche qu'un seul PC-tree, ou une formulation
par contraintes supplementaires.

### 3.4 Les signatures locales de PC-tree sont insuffisantes

Plusieurs signatures locales ont ete testees : masques internes, signatures de
bord one-hop, projections locales des contraintes sur les branches d'un noeud.

Le comportement observe est le suivant :

- certaines signatures distinguent mieux les petits cas ;
- mais elles perdent des correlations de bord apres composition ;
- des frontiers non-cR peuvent avoir des projections locales silencieuses alors
  que le premier quartet interdit utilise plusieurs niveaux du PC-tree.

Conclusion : une vraie DP sur le PC-tree devra transporter une relation
residuelle sur separateur, pas seulement une signature locale par noeud.

### 3.5 Treewidth faible ne suffit pas si les P-noeuds sont gros

Une reduction vers CSP de quartets est naturelle. Mais meme si les contraintes
sont de portee binaire, les domaines locaux des P-noeuds peuvent etre
factoriels.

Cas critique :

```text
un seul gros P-noeud
```

Le graphe primal du CSP peut avoir treewidth `0`, mais le domaine local contient
deja tous les ordres circulaires des branches.

Conclusion : toute borne de complexite doit compter la taille effective des
domaines P, pas seulement la treewidth du graphe de contraintes.

## 4. Pistes qui restent prometteuses

### 4.1 Sous-cas C-only / domaines booleens

Si tous les choix locaux pertinents sont booleens, alors les contraintes de
quartets bad-side deviennent des contraintes binaires booleennes. Chaque tuple
interdit devient une clause 2-CNF.

Theoreme cible :

```text
Si tous les domaines locaux effectifs ont taille <= 2,
alors l'existence d'un ordre cR dans le PC-tree se reduit a 2-SAT.
```

C'est probablement le sous-cas polynomial le plus propre a formaliser rapidement.

### 4.2 CSP exact de quartets, mais comme classification FPT

La formulation suivante semble conceptuellement exacte :

```text
Pour chaque paire {a,c} et chaque b,d in B_ac,
interdire le type circulaire a,b,c,d.
```

Dans un PC-tree, le type d'un quartet depend d'un petit nombre de choix locaux.
Cela donne un CSP sur choix locaux du PC-tree.

Mais ce CSP n'est pas automatiquement polynomial, car les P-noeuds peuvent avoir
de grands domaines.

Direction raisonnable :

- polynomial pour domaines booleens ;
- FPT par taille effective des domaines P ;
- FPT par treewidth du CSP et domaine borne ;
- diagnostic utile pour chercher des contre-exemples et des sous-cas.

### 4.3 Graphes de seuil et clean-side

La version seuil

```text
C_ac = N_{d(a,c)}[a] ∩ N_{d(a,c)}[c]
```

dit qu'un des deux arcs entre `a` et `c` doit etre entierement contenu dans
`C_ac`.

Cela ressemble a des contraintes d'ordres round / umbrella-free sur une famille
imbriquee de graphes de seuil. Cette piste n'est pas encore prouvee, mais elle
est mathematiquement plus naturelle que les heuristiques farthest.

### 4.4 Familles low-hub / high-cycle

Les familles "cycle haut + hub bas" donnent des obstructions globales invisibles
localement jusqu'a un certain cap.

Elles sont utiles pour deux raisons :

1. Elles cassent les theories par petites obstructions.
2. Elles donnent une famille structuree ou une preuve parametree semble
   possible.

Question utile :

```text
Peut-on prouver une famille de profondeur locale croissante ?
```

Par exemple : pour un cycle haut de longueur croissante avec un hub bas, quelle
est la taille minimale d'une sous-instance non-cR ?

### 4.5 P-noeuds residuels et modules

La conjecture proposee par le chercheur est centrale :

```text
Un P-noeud residuel du PC-tree des boules est-il toujours un module parfait
pour les distances pertinentes ?
```

Si oui, l'ordre interne des P-noeuds pourrait etre choisi librement ou gere
recursivement de facon simple.

Si non, le probleme general doit garder une vraie procedure d'ordonnancement
interne des P-noeuds.

Nous n'avons pas prouve ni refute cette conjecture. Les experiences rendent
seulement prudent : les gros P-noeuds sont le principal danger combinatoire.

## 5. Comparaison avec les phases proposees par le chercheur

### Phase 0 - Extraction des boules

Cette phase est solide pour construire la famille quasi-circulaire.

Attention toutefois : dans nos notations, cela ne resout pas encore la condition
cR forte. Cela construit l'espace des ordres admissibles dans lequel on cherche.

### Phase 1 - PC-tree de Hsu-McConnell

Solide comme couche de representation des ordres ou les boules sont arcs.

Nous n'avons pas implemente Hsu-McConnell complet dans les experiences ; nous
avons surtout utilise un scaffold PC-tree pour tester les conjectures. Donc le
chercheur est probablement plus avance sur l'aspect "vrai PC-tree des boules".

### Phases 2 et 3 - Effets des C-noeuds et invariant `Y_x`

Le chercheur va plus loin que nous sur ce point.

Nous n'avons pas teste directement l'invariant :

```text
Y_x = XOR des effets des C-noeuds sur le chemin vers x.
```

Ce que nos experiences apportent :

- le sous-cas booleen/C-only semble effectivement la zone ou XOR/2-SAT peut
  marcher ;
- mais il faut verifier que les contraintes bad-side completes se reduisent
  bien aux variables `Y_x` dans le sous-cas considere ;
- les obstructions multi-niveaux indiquent qu'un raisonnement purement local au
  premier C-noeud risque d'etre insuffisant.

Conclusion : l'idee `Y_x` est une piste interessante non encore epuisee par nos
tests.

### Phase 4 - Systemes XOR, diametres et contraintes non maximales

Ici nos experiences donnent un avertissement important.

Une formulation uniquement fondee sur les diametres globaux semble trop faible.
La condition exacte implique toutes les paires `{a,c}` et tous les couples de
mauvais temoins dans `B_ac`.

Donc une version corrigee de la Phase 4 devrait partir de :

```text
same_side(a,c;b,d) pour tous b,d in B_ac.
```

Ensuite, on peut chercher quelles de ces contraintes deviennent des equations
XOR sur les variables de C-noeuds, et lesquelles restent des contraintes d'ordre
ou de P-noeud.

En ce sens, notre travail peut aider directement : il donne la forme exacte des
contraintes a ne pas oublier.

### Phase 5 - Ordre interne des P-noeuds

Le chercheur identifie le bon point dur.

Nous n'avons pas resolu cette phase. Nous avons surtout montre pourquoi elle est
dangereuse :

- gros domaines factoriels ;
- relations non booleennes entre P-noeuds ;
- compressions locales qui perdent des correlations ;
- absence de preuve que les P-noeuds residuels soient des modules parfaits.

Donc le chercheur n'est pas "derriere" ici : il pointe exactement le trou
principal. La prochaine etape utile serait de chercher un contre-exemple a la
conjecture module, ou une preuve sous hypotheses precises.

### Phase 6 - Verification finale

Cette phase est entierement en accord avec notre methode.

Tous les temoins positifs doivent etre verifies par la condition cR directe et,
si un PC-tree est fixe, par appartenance au PC-tree. C'est indispensable parce
que beaucoup de sous-procedures experimentales sont incompletes.

## 6. Ce que le chercheur apporte de nouveau

Les notes du chercheur vont plus loin que nos tests sur trois points.

### 6.1 Le traitement fin des C-noeuds impairs

L'idee que certains enfants "milieu" d'un C-noeud impair soient invariants sous
renversement n'a pas ete exploree dans nos probes. Cela peut etre important pour
eviter de fausses equations XOR.

### 6.2 L'invariant `Y_x`

Nous n'avons pas developpe cette algebre des orientations le long des chemins.
C'est une vraie piste a tester, surtout dans les PC-trees sans gros P-noeuds.

### 6.3 La separation explicite des phases incertaines

Le chercheur identifie bien deux trous :

- suffisance des contraintes de Phase 4 ;
- structure interne des P-noeuds de Phase 5.

Cette separation est utile. Nos experiences suggerent que Phase 4 doit etre
renforcee avec bad-side complet, et que Phase 5 est probablement le principal
obstacle general.

## 7. Ce que nos experiences peuvent apporter au chercheur

### 7.1 Ne pas se limiter aux diametres

Les contraintes exactes sont :

```text
pour toute paire {a,c},
pour tous b,d in B_ac,
b et d doivent etre du meme cote de ac.
```

C'est la forme a integrer dans toute preuve XOR, 2-SAT, CSP ou DP.

### 7.2 Utiliser les familles high-cycle comme tests de robustesse

Les familles low-hub / high-cycle sont de bons tests pour toute conjecture
locale. Une preuve qui ne les explique pas est probablement incomplete.

### 7.3 Tester la conjecture P-noeud/module avec les profils bad-side

Meme si les boules ne distinguent pas deux branches d'un P-noeud, les ensembles
`B_ac` peuvent potentiellement les distinguer.

Test conceptuel :

```text
Deux branches d'un P-noeud sont-elles equivalentes pour toutes les contraintes
bad-side externes ?
```

Si non, l'ordre interne du P-noeud n'est pas libre pour la couche cR.

### 7.4 Ne pas confondre CSP binaire et facilite algorithmique

Meme si chaque quartet se traduit en contrainte de portee faible, les domaines
de P-noeuds peuvent etre enormes. Il faut mesurer ou borner l'entropie effective
des P-noeuds.

## 8. Questions prioritaires a creuser

1. **Alignement des definitions.**
   La couche "boules arcs" est-elle le but final du chercheur, ou seulement le
   PC-tree de depart pour imposer la condition cR forte ?

2. **Bad-side complet vs diametres.**
   Peut-on montrer que certaines contraintes bad-side non maximales sont
   impliquees par les contraintes de diametres dans le PC-tree des boules ?
   Si non, il faut les ajouter explicitement.

3. **C-only / booleen.**
   Peut-on prouver un sous-cas polynomial via XOR/2-SAT quand il n'y a pas de
   gros P-noeud actif ?

4. **P-noeud residuel = module ?**
   Vrai, faux, ou vrai seulement pour les boules mais faux pour bad-side ?

5. **Famille high-cycle parametree.**
   Peut-on prouver que les cycles hauts avec hub bas donnent des obstructions
   globales de profondeur locale croissante ?

6. **DP residuelle.**
   Quelle est la bonne relation de bord a transporter pour composer les
   sous-arbres sans perdre les correlations ?

## 9. Synthese courte

Ce qui semble solide :

- La couche boules-arcs donne bien le PC-tree admissible de depart.
- Pour un ordre fixe, la formulation bad-side est la meilleure caracterisation
  de la condition cR forte.
- Les plus lointains voisins et les petits certificats ne suffisent pas.
- Les P-noeuds sont le principal danger combinatoire.

Ce qui est prometteur :

- sous-cas C-only / booleen par XOR ou 2-SAT ;
- CSP de quartets comme classification FPT ;
- graphes de seuil via `C_ac`;
- analyse fine des P-noeuds residuels ;
- familles low-hub high-cycle comme obstructions globales.

Ce qui reste ouvert :

- preuve generale de polynomialite ou NP-difficulte ;
- suffisance d'un systeme XOR sur C-noeuds ;
- statut exact des P-noeuds residuels ;
- structure exacte de l'ensemble des ordres cR dans un PC-tree quasi-circulaire.

La recommandation principale est de ne pas repartir de farthest-neighbor ni de
petites obstructions, mais de prendre `B_ac` / `same_side(a,c;b,d)` comme objet
central, puis d'analyser comment ces contraintes se projettent sur les C-noeuds
et P-noeuds du PC-tree des boules.
