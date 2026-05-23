# Piste F - Complexité et sous-cas

## Question

Quels sous-cas semblent tractables, et quelles familles stressent les filtres
locaux ou les heuristiques de recherche ?

## Famille planted-cycle

Statut : générateur ajouté.

`permuted_cycle` construit un cycle metric puis relabellise les points. C’est un
sous-cas polynomial-looking : le graphe des distances 1 devrait révéler le cycle
planté, puis le problème se rapproche d’un test de représentation de cet ordre
par le PC-tree.

Usage :

```bash
make bench-piste-f
```

Résultat observé star :

- `n=8` : `1/2520` ordre cR valide ;
- `24/2520` ordres passent farthest, donc farthest a déjà 23 faux positifs.

## Famille paired-farthest

Statut : générateur ajouté.

`paired_farthest` crée des paires farthest uniques. C’est une famille
hard-looking parce qu’elle met une pression d’alternance sur les gros nœuds `P`.

Résultat observé star :

- `n=6` : `3/60` ordres cR valides, `4/60` ordres farthest-pass ;
- `n=8` : `12/2520` ordres cR valides, `24/2520` ordres farthest-pass.

Résultat observé mixed :

- aucun ordre cR valide dans les diagnostics `n=4,6,8` du premier benchmark.

## Témoin paired-farthest par matching maximal

Statut : sous-cas structurel intégré à `candidate.py` pour positifs
représentés.

Le détecteur ne regarde pas le nom du générateur. Il reconnaît une structure à
trois niveaux `low < mid < high` :

- les arêtes `high` forment un matching parfait sur les sommets appariés ;
- il y a au plus un neutre sans arête `high`, à distance `low` de tous ;
- les arêtes `low` entre sommets appariés forment deux cliques disjointes de
  même taille ;
- les mates `high` sont dans des cliques opposées ;
- les autres arêtes entre cliques opposées valent `mid`.

Pour une clique `A = (a_0, ..., a_{m-1})`, l'ordre construit est :

```text
a_0, ..., a_{m-1}, mate(a_0), ..., mate(a_{m-1}), neutral?
```

Raison de correction : par la caractérisation bad-side d'un ordre fixé, les
seuls témoins mauvais d'une paire même côté sont tous dans l'autre bloc ; les
seuls témoins mauvais d'une paire croisée non mate `{A_i, B_j}` sont
`B_i` et `A_j`, qui sont du même côté de la corde grâce au même ordre des
paires dans les deux blocs. Une paire mate à distance `high` n'a pas de témoin
mauvais.

Résultat T020 :

- `paired_farthest/star` grandes tailles passe par
  `candidate_paired_farthest_matching_witness` pour tous les `n > 8` ;
- benchmark ciblé : `0` timeout et `0` incomplet pour `paired_farthest/star` ;
- `paired_farthest/mixed` reste incomplet en grande taille dans le scaffold
  lorsque le témoin reconstruit n'est pas représenté ;
- un contre-exemple `n=4` montre qu'un témoin paired-farthest cR non représenté
  ne doit pas être accepté pour un PC-tree non-star.

Résultat T021 :

- sur `balanced` et `mixed` fanout 2, les nœuds internes binaires rendent `P`
  et `C` localement équivalents dans le scaffold courant ;
- scan seeds `0..999` sur `paired_farthest` :
  - `n=6` : `202` témoins canoniques représentés, `96` cas où le canonique
    est non représenté mais l'oracle est `True`, `702` oracle `False` ;
  - `n=8` : `36` canoniques représentés, `20` positifs non canoniques,
    `944` oracle `False` ;
  - `n=10` : `6` canoniques représentés, `12` positifs non canoniques,
    `982` oracle `False` ;
- shrink par permutations : pas de phénomène "canonique non représenté mais
  oracle True" à `n=4`; il apparaît minimalement à `n=6` ;
- régression positive ajoutée : `n=6 seed=1`, le témoin canonique
  `(0,1,3,5,4,2)` est non représenté, mais l'ordre représenté
  `(0,1,2,5,4,3)` est cR et l'oracle PC-tree répond `True` ;
- régression négative ajoutée : `n=6 seed=21`, l'ordre
  `(0,1,2,5,3,4)` passe la condition brute de croisement farthest, mais viole
  cR sur le quadruplet `(0,1,2,5)`.

Une probe locale a testé une génération d'ordres side-by-side dérivés des
rotations des frontiers représentées. Elle retrouve tous les positifs oracle
observés sur `paired_farthest` `n=6/8`, mais la version naïve devient trop
coûteuse en grande taille ; une version bornée trouve peu de hits au-delà de
`n=10`. Cette idée reste donc hors `candidate.py` tant qu'elle n'a pas de preuve
de complétude ou de borne utile.

## Sous-cas universel par témoins mauvais

Statut : sous-cas prouvé intégré à `candidate.py`.

Pour une paire `{a,b}`, définir :

```text
B(a,b) = {w != a,b : max(D[a][w], D[w][b]) > D[a][b]}
```

Si `|B(a,b)| <= 1` pour toute paire, alors tout ordre circulaire est circular
Robinson. Par le lemme bad-side T014, une violation cR demanderait deux témoins
mauvais pour une même paire, situés sur les deux arcs opposés. Le cas constant
hors diagonale est inclus, car tous les ensembles `B(a,b)` sont vides.

Artefacts :

- `has_at_most_one_bad_witness_per_pair` dans `predicates.py` ;
- `sample_frontier` dans `pc_tree.py` pour produire un témoin représenté sans
  énumération ;
- `candidate_universal_bad_witness_bound_all_orders` dans `candidate.py`.

Contre-exemples aux faux amis :

- une matrice presque constante avec toutes les distances `2` sauf une arête
  basse `D[0][2]=1` sort du sous-cas et peut violer cR ;
- deux arêtes hautes disjointes ne suffisent pas non plus comme règle générale.

Résultat T016 : probe large-n `n=9..30` sur star/balanced/mixed, `33` checks,
témoin cR et représenté/échantillonné ; le faux ami à arête basse reste
placeholder incomplet.

## Sous-cas strict

Statut : prometteur, mais pas encore implémentable sans transcription validée
des sources.

Résultat exploratoire T022 :

- dans le strict, les inégalités deviennent strictes (`scR`, `sqcR`) ;
- pour un ordre fixé, le papier donne un test `O(n^2)` via unimodalité stricte
  et obstructions farthest de type Prop. 4.5 ;
- Algorithm 5.2 produit un ordre compatible en `O(n log n)` si l'espace est
  strict quasi-circular/strict circular, avec reconnaissance complète après
  vérification `O(n^2)` ;
- Prop. 5.9 indique qu'un strict quasi-circular possède seulement un ou deux
  ordres compatibles modulo opposés, et qu'un strict circular en possède un.

Limite importante : une transcription naïve en probe rate `cycle_metric(6)` et
produit des mismatches sur des matrices `n=4`, valeurs `{1,2,3}`. Ce n'est pas
une réfutation du papier ; cela montre que les choix de `J`-sets, ties et
orientations doivent être codés avec une preuve/test avant toute intégration.

API expérimentale envisagée :

- `is_strict_quasi_circular_order(D, order)` ;
- `is_strict_precircular_order_cR(D, order)` ;
- `strict_algorithm52_candidates(D) -> report` ;
- `strict_subcase_solve(D, pc_tree=None, quasi_orders=None)` seulement quand
  tous les candidats stricts sont générés et vérifiés représentés/cR.

Tests requis avant `candidate.py` :

- exemple Fig. 2.2 du PDF : ordre strict quasi non cR et autre ordre cR ;
- `cycle_metric(n)` pour `n=5,6,7` ;
- exhaustif `n=4`, valeurs `{1,2,3}`, contre définition directe ;
- comparaison oracle PC-tree sur star/balanced/mixed petits `n` ;
- cas non applicables : equal-distance, non strict, random hors strict ;
- régression témoin strict cR mais non représenté par `T`.

Résultat T023 :

- prédicats d'ordre fixé ajoutés :
  `is_strict_robinson_linear`, `is_strict_quasi_circular_order`,
  `is_strict_precircular_order_cR`, `is_strict_circular_robinson_order` ;
- `strict_order_report(D, pc_tree=None, max_n=8)` énumère les ordres stricts
  seulement pour petites tailles et marque `complete=False` au-delà ;
- Fig. 2.2 est régressée : ordre `(0,1,2,3)` strict quasi mais non strict
  pre-circular, ordre `(0,1,3,2)` strict circular ;
- `equal_distance_instance(4)` verrouille le rejet strict des égalités ;
- `cycle_metric(6)` verrouille l'ordre strict positif unique modulo
  rotation/renversement ;
- un témoin strict cR non représenté par un PC-tree `C` de 4 feuilles est
  régressé pour empêcher toute future intégration qui accepterait un ordre hors
  arbre ;
- probe exhaustive `n=4`, valeurs `{1,2,3}` : `2187` couples matrice-ordre
  sans désaccord entre strict pre-circular et définition stricte par arcs.

Décision : garder ces fonctions comme base expérimentale. La prochaine étape
strict doit être la génération exhaustive des un ou deux ordres compatibles
stricts annoncés par Prop. 5.9 ou une reproduction validée d'Algorithm 5.2.

## Témoin cycle par distances minimales

Statut : certificat positif intégré pour tout PC-tree du scaffold où le témoin
est représenté, pas critère complet.

Si les arêtes de distance minimale positive forment un cycle simple couvrant
tous les sommets, `candidate.py` reconstruit cet ordre. Il l'accepte seulement
si l'ordre passe `is_precircular_order_cR` et si la représentation est sûre :
pas de PC-tree, ou `represents_order(T, order)` vrai pour le scaffold P/C/leaf.

Résultat T018 :

- `permuted_cycle/star` grandes tailles passe par
  `candidate_minimum_distance_cycle_witness` ;
- benchmark ciblé : `0` timeout et `0` incomplet pour `permuted_cycle/star`,
  avec la branche minimum-cycle utilisée pour tous les `n > 8` ;
- `paired_farthest` ne déclenche pas ce témoin et reste un stress négatif ;
- benchmark ciblé : `paired_farthest/star` garde `60` runs incomplets sur les
  tailles `n > 8`, et `paired_farthest/mixed` en garde `40` ;
- un contre-exemple `n=6` montre que "graphe minimum = cycle" ne suffit pas pour
  cR ; le garde fixed-order est donc indispensable ;
- à T018, les PC-trees non-star étaient volontairement exclus de cette branche
  faute de test de représentation non énumératif.

Résultat T019 :

- `represents_order` teste maintenant l'appartenance d'un ordre fixé au
  PC-tree scaffold sans énumérer les frontiers quand `limit is None` ;
- le test parse récursivement des blocs contigus d'enfants, avec rotations et
  renversement autorisés seulement au root circulaire ;
- comparaison exhaustive contre `enumerate_frontiers` sur petits arbres :
  `11837` checks locaux sans désaccord ;
- `cycle/mixed` grandes tailles passe par
  `candidate_minimum_distance_cycle_witness` pour tous les `n > 8` ;
- `permuted_cycle` avec labels aléatoires reste rarement représenté par
  balanced/mixed dans le scaffold, donc la branche n'est pas forcée hors cas
  réellement représentés.

## Artefacts

- `permuted_cycle_metric`;
- `paired_farthest_matching`;
- `instance_by_kind(..., kind="permuted_cycle")`;
- `instance_by_kind(..., kind="paired_farthest")`;
- `has_at_most_one_bad_witness_per_pair`;
- `sample_frontier`;
- `candidate_minimum_distance_cycle_witness`;
- `candidate_paired_farthest_matching_witness`;
- `represents_order` non énumératif quand `limit is None`;
- `--diagnostics-up-to` dans `tools/pc_circular_complexity_benchmark.py`;
- `make bench-piste-f`.

## Prochaine action

Utiliser `paired_farthest` pour casser tout filtre local ou farthest-like.
Utiliser `permuted_cycle` comme sous-cas où un futur solver devrait reconnaître
un témoin caché sans brute force star.
Chercher ensuite un sous-cas plus structuré que le critère universel, par
exemple paired-farthest représenté par PC-tree non-star avec choix de témoin
prouvé, planted-cycle représenté par un vrai PC-tree Hsu/McConnell, ou degré
interne borné.
