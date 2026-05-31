# External analysis digest - GPT 5.5 Pro

Statut : note de recherche externe, non preuve interne au dépôt.

Cette note préserve les éléments utiles d'une analyse GPT 5.5 Pro fournie par
l'utilisateur le 2026-05-23. Elle sert de guide pour l'agent chercheur. Elle ne
modifie pas l'oracle, ne remplace pas les contre-exemples, et ne doit pas être
citée comme preuve sans vérification dans `docs/proof_obligations.md`.

## Déjà traité dans le dépôt

- La distinction entre tester un ordre donné, décider l'existence dans un
  PC-tree et tester l'universalité est déjà présente dans
  `docs/problem_statement.md`, `docs/source_notes.md` et les pistes.
- La Proposition 4.4, sa clause dégénérée non stricte, et la différence avec le
  prédicat farthest-crossing brut sont documentées dans `docs/source_notes.md`
  et `docs/tracks/piste_e_farthest_quartets.md`.
- La Proposition 4.5 est implémentée comme diagnostic d'ordre fixé via
  `find_farthest_prop_4_5_obstruction` et
  `passes_farthest_prop_4_5_order_test`.
- La projection expérimentale des quartets sur le PC-tree existe déjà dans la
  Piste A, et les scaffolds CSP/nogoods dans la Piste C.
- Le risque de cyclic-ordering sur les gros nœuds `P` est déjà mentionné dans
  `docs/hypothesis_portfolio.md` et la Piste F.
- Les limites de Brucker/Osswald pour notre notion cR sont déjà notées dans
  `docs/source_notes.md` et la Piste D.

## À préserver explicitement

### Cas strict

L'analyse rappelle que le cas strict est beaucoup plus favorable : les résultats
de `strongly-circular-sidma-1.pdf` autour de l'Algorithme 5.2, Théorème 5.6,
Corollaire 5.7 et Proposition 5.9 suggèrent qu'un espace strict
quasi-circulaire n'a qu'un très petit nombre d'ordres compatibles, à renversement
près. Un sous-goal raisonnable est donc :

```text
si D est dans le sous-cas strict supporté, générer les candidats stricts,
tester represents_order(T, beta), puis is_precircular_order_cR(D, beta).
```

Ce serait un sous-cas polynomial, mais il n'est pas encore implémenté dans
`candidate.py`. Il faut d'abord formaliser dans le dépôt la détection du strict
et la génération des ordres stricts sans s'appuyer sur une intuition non
prouvée.

### Universalité

La variante suivante est distincte de l'existence :

```text
forall beta in Pi(T), beta est circular Robinson ?
```

L'analyse propose une procédure polynomiale candidate : énumérer les quartets
farthest non dégénérés de Proposition 4.4/4.5 et tester si le PC-tree peut
réaliser un motif non croisé sur les quatre feuilles. Si oui, l'universalité
échoue ; sinon tous les ordres représentés seraient cR.

Cette piste ne résout pas l'existence, mais elle peut produire :

- un outil de diagnostic utile ;
- des certificats négatifs pour "tous les ordres sont bons" ;
- une comparaison avec le sous-cas `candidate_universal_bad_witness_bound_all_orders`,
  qui est suffisant mais beaucoup plus restreint.

Point à vérifier avant implémentation : dans le cas non strict, utiliser la
clause dégénérée complète, pas le prédicat farthest-crossing brut déjà réfuté.

### Projection locale au nœud décisif

Pour chaque quartet interdit `(x,a;y,b)` avec `a in F_x`, `b in F_y`, l'analyse
propose de projeter la contrainte sur le sous-arbre de Steiner des quatre
feuilles. L'objectif est d'identifier :

- un nœud `C` où l'ordre local rend le croisement forcé ou impossible ;
- un nœud `P` où la contrainte devient une contrainte de cyclic ordering entre
  branches ;
- ou un cas récursif lorsqu'au moins deux feuilles restent dans la même branche.

Le lemme à tester expérimentalement est :

```text
toute contrainte de croisement farthest/cR se projette sur un unique lieu
décisif, sauf récursion dans les branches contenant plusieurs feuilles.
```

Le dépôt a déjà des supports de quartet et des nogoods compilés, mais il manque
encore un rapport lisible "quartet -> nœud décisif -> contrainte locale" avec
statistiques par nœud.

### Question clé sur les branches d'un P-nœud

Fixer un nœud `P` avec branches `B_1, ..., B_k`. Pour chaque point `x`, projeter
son farthest set sur les branches :

```text
I_x(v) = { i : B_i intersecte F_x }
```

Question clé :

```text
Les familles I_x(v) sont-elles toujours des intervalles circulaires dans tout
ordre admissible des branches de v ?
Les contraintes de croisement induites sont-elles convexes/laminaires ?
```

Si oui, une réduction locale vers circular-ones/PC-tree est plausible. Si non,
les contre-exemples peuvent nourrir une piste NP-difficulté ou un générateur
hard-looking.

Cette question doit être testée sur :

- `paired_farthest` ;
- gros `P` star ;
- balanced/mixed ;
- cas non stricts avec égalités massives ;
- petits PC-trees où certains ordres marchent et d'autres non.

### Risque cyclic-ordering

Un gros nœud `P` autorise presque n'importe quel ordre circulaire de ses
branches. Si les contraintes projetées peuvent simuler des contraintes
arbitraires de cyclic ordering, le problème d'existence peut devenir NP-difficile.

Ce n'est pas une preuve de NP-difficulté pour le problème métrique : les
contraintes viennent de farthest sets d'une dissimilarité quasi-circulaire, et
peuvent donc être beaucoup plus structurées que des contraintes arbitraires.

Prochaine décision expérimentale utile :

- soit observer une structure laminaire/convexe robuste des `I_x(v)` ;
- soit construire un petit générateur où les contraintes projetées semblent
  arbitraires sur un grand `P`.

## Actions recommandées

1. Ajouter un rapport expérimental `project_farthest_sets_to_pc_nodes(D, T)` :
   pour chaque nœud interne, lister les ensembles `I_x(v)` non triviaux et
   mesurer s'ils sont intervalles dans les frontiers représentées.
2. Ajouter un diagnostic d'universalité séparé de `candidate.py`, probablement
   dans `local_constraints.py` ou `sat_like_experiments.py`, pour éviter de
   confondre "tous les ordres" avec "il existe un ordre".
3. Tester le sous-cas strict comme piste F distincte : détection stricte,
   génération de petits candidats, puis membership PC-tree et test cR.
4. Utiliser `paired_farthest` comme première famille pour chercher un échec de
   laminarité/convexité locale.

## Garde-fous

- Ne pas promouvoir le diagnostic d'universalité en solveur d'existence.
- Ne pas utiliser la condition farthest-crossing brute sans la clause dégénérée.
- Ne pas prétendre que le risque cyclic-ordering prouve la NP-difficulté.
- Ne pas supposer que le scaffold `PCNode` enraciné couvre toutes les subtilités
  des vrais PC-trees Hsu/McConnell non enracinés.

## Revue externe globale post-T057

Une seconde analyse GPT 5.5 Pro fournie par l'utilisateur le 2026-05-23 est
conservée dans
`docs/external_reviews/gpt55_global_strategy_2026-05-23.md`.

Important : cette analyse était partiellement ancrée par le prompt sur T056/T057.
Elle ne doit donc pas bloquer la recherche sur la seule collision de second
ordre. Les idées retenues sont re-routées vers un portefeuille large :

- caractérisation bad-side exacte par les ensembles `B_ac` ;
- CSP exact par quartets et test de portée `<= 2` ;
- sous-cas booléen / C-only par 2-SAT ;
- DP par treewidth du CSP de quartets ;
- catalogue de relations binaires entre petits nœuds `P` pour évaluer la piste
  NP-hardness ;
- collision de second ordre contre les signatures ouvertes T057.

L'addendum
`docs/external_reviews/gpt55_global_strategy_addendum_2026-05-23.md` formalise
ce recadrage : T057 est une piste de compression, tandis que T059/T060 doivent
également nourrir bad-side, CSP quartets, 2-SAT/treewidth, circular-ones et
catalogue non booléen.

## Revue externe 2026-05-31

Les notes externes et le screenshot fournis le 2026-05-31 sont triés dans
`docs/external_reviews/researcher_advances_2026-05-31.md`. Le statut retenu est
explicitement conditionnel : interface P-noeud, largeur 4 des P-noeuds,
projection bad-side complète et route circle graph sont des hypothèses à tester
contre T046/T075/T081/T082, pas des preuves ni des consignes à intégrer dans
`candidate.py`.
