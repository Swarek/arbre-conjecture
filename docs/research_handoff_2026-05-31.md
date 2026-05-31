# Passation de recherche pour pause d'une semaine

Date : 2026-05-31.

Dernier checkpoint experimental important : `927c2d0 checkpoint: probe parity
gap cycles`.

Objectif de cette note : donner au chercheur une vue utile de ce qui a ete
teste dans le depot, de ce qui a casse, de ce qui semble encore prometteur, et
des points precis ou une intervention mathematique peut faire gagner du temps.

Cette note ne pretend pas resoudre le probleme general. Elle separe :

- theoremes ou lemmes a formaliser ;
- consequences directes ;
- preuves experimentales bornees ;
- conjectures ;
- intuitions et directions.

## 1. Point de vigilance sur les definitions

Le depot distingue deux couches.

### Couche quasi-circulaire

Un ordre est admissible si toutes les boules

```text
B_r(y) = {x : D(y,x) <= r}
```

sont des arcs circulaires. Le PC-tree de Hsu/McConnell represente une famille
compacte de tels ordres.

### Couche circular Robinson au sens du depot

Le probleme attaque ici est plus fin : parmi les ordres representes par le
PC-tree quasi-circulaire, existe-t-il un ordre qui satisfait la condition
pre-circular/circular Robinson par quartets :

```text
pour tout x < y < z < t,
D(x,z) >= min(max(D(x,y), D(y,z)), max(D(x,t), D(t,z))).
```

Donc un algorithme qui construit le PC-tree des boules resout la couche
quasi-circulaire, mais pas automatiquement la selection d'un ordre circular
Robinson dans ce PC-tree. Si le chercheur utilise "Robinson circulaire" pour
dire "toutes les boules sont des arcs", il faut aligner les notations avant de
comparer les preuves.

## 2. Socle mathematique le plus stable

### Bad-side fixed-order

Pour deux points distincts `a,c`, definir :

```text
B_ac = {u notin {a,c} : max(D(a,u), D(u,c)) > D(a,c)}.
```

Theoreme a rediger proprement :

```text
Un ordre circulaire beta satisfait la condition cR du depot
ssi pour toute paire {a,c}, tous les elements de B_ac sont contenus
dans un seul des deux arcs ouverts entre a et c.
```

Forme equivalente :

```text
pour tous b,d in B_ac, b et d doivent etre du meme cote de la corde ac.
```

Donc chaque paire `{a,c}` et chaque paire `b,d in B_ac` donnent une contrainte
de type :

```text
same_side(a,c;b,d)
```

ou, en negatif, interdire l'alternance circulaire `a,b,c,d`.

Statut : ce lemme est le meilleur socle. Il a ete teste intensivement contre le
predicat cR direct pour ordre fixe. Il doit maintenant etre mis sous forme de
preuve courte dans un texte mathematique propre.

### Version seuil clean-side

Pour `r = D(a,c)`, definir :

```text
C_ac = N_r[a] intersect N_r[c].
```

La condition bad-side equivaut a :

```text
pour chaque paire {a,c}, au moins un des deux arcs ouverts entre a et c
est entierement contenu dans C_ac.
```

Statut : equivalence experimentale verifiee par `make bench-threshold-roundness`
sur `6072` ordres, sans mismatch contre bad-side et cR directe. C'est une
porte theorique vers graphes de seuil, round orderings, proper circular-arc ou
simultaneous ordering.

## 3. Ce qui a ete refute ou fortement fragilise

### 3.1 Farthest-neighbor seul ne suffit pas

Les contraintes de plus lointains voisins sont utiles, surtout en strict, mais
ne caracterisent pas le cas non strict general.

Ce qui casse :

- egal-distance : la condition farthest brute peut rejeter des ordres pourtant
  cR ;
- instances strictes petites : la condition farthest brute peut passer alors
  que la condition cR par quartets echoue ;
- projections `I_x(v)` des farthest sets peuvent etre muettes sur des frontiers
  non-cR.

Conclusion : les farthest-neighbors restent un diagnostic, pas le langage
central. Le langage central est bad-side complet.

### 3.2 Les petites sous-matrices interdites ne suffisent pas

Experiences :

- obstruction minimale de taille `5` dont toutes les restrictions de taille
  `4` passent ;
- obstruction minimale de taille `6` dont toutes les restrictions de taille
  `5` passent ;
- familles high-cycle/low-hub globalement negatives mais invisibles sous cap
  local `<= 6`.

Conclusion : une caracterisation par obstruction de taille fixe `4/5/6` est
fausse. Des obstructions globales existent.

### 3.3 L'ensemble des ordres cR n'est probablement pas un PC-tree simple

Idee testee :

```text
calculer directement le PC-tree de tous les ordres cR de D, puis intersecter.
```

Resultat : contre-exemple complet des `n=5` dans le scaffold du depot :
l'ensemble des ordres cR peut etre une famille a deux ordres qui n'est pas
representable par les PC-trees enumeres, meme en modele non enracine borne.

Conclusion : une route "un PC-tree des ordres cR" est tres fragilisee. Il faut
probablement une structure plus riche : contraintes sur PC-tree, CSP, relation
residuelle, ou simultaneous ordering.

### 3.4 Treewidth seule ne suffit pas

Un seul gros noeud `P` donne un CSP local de treewidth `0`, mais son domaine
peut contenir `(n-1)!/2` ordres circulaires.

Conclusion : toute borne de complexite doit controler la taille effective des
domaines `P`, ou donner une compression prouvee des permutations de branches.

### 3.5 Les signatures locales simples perdent les correlations

Plusieurs signatures ont ete testees :

- masques de composants ;
- signatures one-hop ;
- ordre local des branches ;
- ordre des roles visibles ;
- signatures de separateur visibles.

Resultat global : elles ameliorent certains temoins, mais elles perdent des
correlations quand on compose les contraintes. Un meme ordre local de branches
peut satisfaire ou violer une obligation partielle selon l'ordre interne ou le
contexte.

Conclusion : une DP correcte doit transporter une relation de bord/residuelle,
pas seulement une signature locale.

## 4. Piste centrale actuelle : relations de gaps

Les obligations bad-side peuvent toucher un noeud `P` sans etre pleinement
visibles comme deux cordes entre quatre branches. Certaines roles sont visibles
dans le noeud, d'autres sont dans le contexte exterieur ou dans les sous-arbres.

Une abstraction testee est :

```text
etat visible -> relation des positions d'insertion cycliques des roles manquants
```

Ces positions sont appelees ici "gaps".

### Resultats T096-T103 : signal binaire tres fort, mais non prouve

Les premieres experiences ont montre :

- les marges unaires de gaps ne suffisent pas ;
- les relations jointes de gaps semblent souvent reconstruites par leurs
  projections binaires ;
- des jointures par petits overlaps sont fausses, mais les fausses jointures
  observees sont toutes reparees par des aretes binaires transverses.

Chiffres importants :

- T102 : `87533` cas non triviaux ou le produit unaire est trop large mais la
  closure binaire est exacte ; `0` higher-order ;
- T103 : `10271` fausses jointures par overlap, toutes reparees par aretes
  binaires transverses.

Interpretation avant T104 : l'interface binaire de gaps etait une hypothese de
travail credible, mais sans preuve de composition ni borne de taille.

### Resultat T104 : premier contre-signal cible

T104 a change de strategie : au lieu d'echantillonner plus, il cible les
familles high-cycle/low-hub et les obligations de cycle

```text
same_side(0,v; prev,next)
```

Le probe compare deux modes :

- `current_gap` : signature precedente, plus quotientee ;
- `gap_with_distance` : conserve en plus la distance cyclique du role manquant
  dans le gap.

Resultat T104 :

- `8` lignes completes ;
- `54` projections ciblees cycle ;
- `2880` cas visibles ;
- `product_capped_case_count = 0` ;
- `higher_order_case_count = 76` ;
- `pairwise_false_tuple_count = 92` ;
- `min_higher_order_projection_count = 4` ;
- `12` cas higher-order survivent sous `gap_with_distance`.

Lecture :

- le signal `current_gap` sur `cycle_pair_p` peut etre un artefact de quotient
  ou de PC-tree adversarial hors-promise ;
- le signal `gap_with_distance` sur `mixed/odd_high_cycle_low_hub` est plus
  important : il suggere qu'une relation de gaps peut ne pas etre determinee
  par ses projections binaires, meme avec une signature enrichie.

Ce que T104 ne prouve pas :

- pas de NP-difficulte ;
- pas d'impossibilite d'une interface encore plus riche ;
- pas de resultat sous le promise exact `T = T(D)` ;
- pas d'erreur dans `candidate.py`.

Mais T104 est maintenant le meilleur objet a shrinker et a montrer au chercheur.

## 5. Comparaison avec les avancees envoyees par le chercheur

### Phase 0/1 : boules et Hsu-McConnell

Le chercheur va plus loin sur la reconstruction propre du PC-tree des boules.
Dans le depot, cette couche est traitee comme le PC-tree quasi-circulaire
donne ou scaffold experimental. Elle n'est pas le verrou principal teste ici.

Point a clarifier ensemble : si son "Robinson circulaire" signifie seulement
"toutes les boules sont arcs", alors il resout la couche quasi-circulaire, pas
necessairement la condition cR par quartets du depot.

### Phases 2/3 : invariants XOR des C-noeuds

Le depot n'a pas reproduit en detail cette piste algebrique `Y_x` pour les
C-noeuds impairs. Elle peut etre utile pour un sous-cas C-only ou booleen.

Connexion possible avec le depot :

- les contraintes bad-side `same_side(a,c;b,d)` peuvent etre traduites en
  contraintes sur orientations `C` dans le cas booleen ;
- si tous les domaines effectifs ont taille `<= 2`, le probleme devient un
  CSP booleen binaire, donc une route 2-SAT est plausible.

Mais cette piste ne traite pas encore le verrou des grands `P`.

### Phase 4 : diametres / contraintes XOR

Le depot suggere que les diametres globaux ne suffisent probablement pas. Le
lemme bad-side montre que toutes les paires `{a,c}` peuvent produire des
contraintes, pas seulement les paires a distance maximale.

Conseil : reformuler la phase 4 non pas en "diametres seulement", mais en
contraintes `same_side(a,c;b,d)` pour tous `b,d in B_ac`.

### Phase 5 : P-noeuds residuels et modules

Le chercheur pose la bonne question : un P-noeud residuel est-il assez modulaire
pour rendre son ordre interne libre ou simple ?

Ce que le depot a teste :

- la factorisation produit naive des completions internes est fausse dans le
  scaffold ;
- meme avec contexte exterieur fixe, il existe des seeds ou le produit des
  projections cree des completions fausses ;
- les relations de bord semblent necessaires, parfois binaires, et T104 montre
  qu'une arite superieure peut apparaitre dans certains scaffolds.

Cela ne refute pas une version plus forte sous le vrai promise Hsu/McConnell
`T=T(D)`, mais cela avertit qu'une preuve "P residuel = module parfait" doit
etre tres precise.

## 6. Sous-cas et resultats encore prometteurs

### Sous-cas booleen / C-only

Conjecture a formaliser :

```text
Si tous les choix locaux effectifs ont taille <= 2,
alors les contraintes bad-side donnent une instance 2-SAT.
```

Pourquoi c'est plausible :

- chaque contrainte de quartet touche au plus un petit nombre de choix locaux ;
- en domaine booleen, chaque tuple interdit devient une clause 2-CNF ;
- les temoins peuvent etre reconstruits puis verifies par bad-side direct.

Point a prouver : localite exacte du quartet et reconstruction de l'ordre.

### FPT par domaines P actifs

Une solution generale polynomial-time n'est pas etablie. En revanche, un resultat
FPT propre semble atteignable avec parametres :

- taille effective des domaines `P` ;
- nombre de branches actives par P-noeud ;
- treewidth du graphe relationnel ;
- taille maximale de relation residuelle de bord.

Important : treewidth sans domaine borne est insuffisant.

### Route graphes de seuil / round orderings

La reformulation clean-side par seuil est probablement la meilleure porte
theorique externe. Il faudrait comprendre si les contraintes

```text
un arc entre a,c est contenu dans N_r[a] intersect N_r[c]
```

forment une classe de simultaneous circular ordering tractable grace a
l'imbrication des seuils.

### Route circle graph / interlacement

Les contraintes pleinement visibles sur un P-noeud ressemblent a des
contraintes de non-croisement entre cordes de branches.

Ce qui a ete observe :

- aucun ordre de branches cR projete ne manque dans le lab circle local ;
- les supersets locaux vacus sont expliques par obligations partielles ou
  multi-niveaux.

Piste : relier cette observation a circle graphs, split decomposition ou
contraintes de chord non-crossing, mais en integrant les obligations ouvertes.

## 7. Objets experimentaux a montrer en priorite

### 7.1 `mixed/odd_high_cycle_low_hub` sous `gap_with_distance`

C'est la cible principale apres T104.

Pourquoi :

- pas seulement un arbre custom `cycle_pair_*` ;
- le signal survit a une signature enrichie par distance ;
- il donne des cas `higher_order` de taille minimale `4`.

Tache conseillee :

```text
shrink du tuple de 4 projections,
extraction lisible des same_side impliques,
comparaison avec full_context et frontiers non canoniques.
```

### 7.2 High-cycle/low-hub comme familles globales

Ces familles ont deja casse les strategies locales de petite taille. Elles sont
bonnes pour chercher une preuve parametree d'obstruction globale.

Question :

```text
Quelle est la taille minimale d'une sous-instance non-cR dans C_m + hub bas ?
```

### 7.3 P-noeud interface product false

Les temoins T086/T087 montrent que la factorisation par projections unaires est
fausse. Ils peuvent aider a calibrer une preuve du chercheur sur les P-noeuds :
toute formulation correcte doit exclure ou expliquer ces cas.

## 8. Ce qu'il ne faut pas conclure

- Ne pas conclure que le probleme general est NP-difficile : aucune reduction
  complete n'est etablie.
- Ne pas conclure que le probleme general est polynomial : aucune interface
  compacte prouvee n'est connue.
- Ne pas conclure que les farthest-neighbors suffisent.
- Ne pas conclure que le PC-tree des boules resout la couche cR par quartets.
- Ne pas conclure que les relations de gaps binaires suffisent : T104 donne un
  contre-signal experimental.
- Ne pas utiliser les UNSAT experimentaux comme `False` dans `candidate.py`.
- Ne pas oublier le promise `T=T(D)` : beaucoup de stress tests utilisent des
  PC-trees scaffolds utiles, mais pas necessairement reconstruits depuis `D`.

## 9. Questions concretes pour le chercheur

1. La definition "boules arcs" qu'il utilise est-elle exactement le meme objet
   que la condition quartet cR du depot, ou seulement la quasi-circularite ?

2. Peut-il prouver le lemme bad-side fixed-order proprement et verifier les cas
   degeneres non stricts ?

3. Pour un PC-tree de Hsu/McConnell issu des boules, les contraintes
   `same_side(a,c;b,d)` ont-elles une structure speciale absente des scaffolds
   adversariaux ?

4. Le cas `mixed/odd_high_cycle_low_hub` de T104 est-il hors-promise, ou peut-il
   apparaitre comme PC-tree admissible d'une matrice `D` proche ?

5. Existe-t-il une signature de bord exacte plus riche que `gap_with_distance`
   qui rend la relation T104 2-decomposable ?

6. Les P-noeuds residuels sont-ils des modules de distances dans un sens assez
   fort pour neutraliser les contre-exemples produit T086/T087 ?

7. Dans le cas C-only / domaines booleens, peut-on ecrire une preuve courte de
   reduction 2-SAT a partir des contraintes bad-side ?

8. La route clean-side par seuil correspond-elle a une classe connue
   d'ordres round / proper circular-arc / simultaneous PC-ordering ?

9. Peut-on obtenir une famille parametree de high-cycle/low-hub dont la
   profondeur locale d'obstruction croit avec la taille ?

10. Si la closure binaire de gaps echoue vraiment, quelle arite minimale de
    relation residuelle faut-il transporter ?

## 10. Reprise recommandee apres la pause

Ordre de reprise conseille :

1. **Shrinker T104.**
   Produire un contre-exemple minimal lisible pour
   `mixed/odd_high_cycle_low_hub` sous `gap_with_distance`.

2. **Audit exact du signal T104.**
   Comparer `current_gap`, `gap_with_distance`, `full_context`, et frontiers
   canoniques/non canoniques. Classer le signal : artefact de quotient ou vraie
   relation higher-order.

3. **Preuve bad-side.**
   Rediger le lemme fixed-order et la version seuil clean-side comme socle
   propre.

4. **Sous-cas booleen.**
   Formaliser le C-only / domaines effectifs `<=2` en 2-SAT avec reconstruction
   et verification finale.

5. **Promise-aware.**
   Pour chaque contre-exemple important, separer :
   `PC-tree scaffold arbitraire` vs `PC-tree reconstruit/valide comme T(D)`.

6. **P-noeuds.**
   Reformuler la conjecture "P residuel = module" en termes bad-side et
   relation de bord, puis la tester contre T086/T087/T104.

## 11. Documents du depot a lire

Pour le contexte detaille :

- `docs/problem_statement.md`
- `docs/math_notes.md`
- `docs/proof_obligations.md`
- `docs/hypothesis_portfolio.md`
- `docs/tracks/README.md`
- `docs/external_reviews/researcher_advances_2026-05-31.md`

Pour l'evolution chronologique :

- `docs/experiment_log.md`
- `docs/checkpoints.md`

Pour les pistes les plus utiles :

- `docs/tracks/piste_a_local_pc_constraints.md`
- `docs/tracks/piste_b_dp_pc_tree.md`
- `docs/tracks/piste_c_sat_csp.md`
- `docs/tracks/piste_d_circular_ones.md`
- `docs/tracks/piste_e_farthest_quartets.md`
- `docs/tracks/piste_f_complexity_subcases.md`

## 12. Resume en une phrase

Le travail recent a transforme le probleme d'une recherche de contraintes
locales sur P/C en une question plus precise : quelles relations residuelles de
bord faut-il transporter pour composer les obligations bad-side ouvertes ? Les
relations binaires de gaps semblaient tres prometteuses jusqu'a T103, mais T104
fournit maintenant un contre-signal cible qui doit etre shrinke et compris
avant de continuer vers une DP ou une preuve de complexite.
