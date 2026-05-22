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
- `represents_order` non énumératif quand `limit is None`;
- `--diagnostics-up-to` dans `tools/pc_circular_complexity_benchmark.py`;
- `make bench-piste-f`.

## Prochaine action

Utiliser `paired_farthest` pour casser tout filtre local ou farthest-like.
Utiliser `permuted_cycle` comme sous-cas où un futur solver devrait reconnaître
un témoin caché sans brute force star.
Chercher ensuite un sous-cas plus structuré que le critère universel, par
exemple planted-cycle représenté par un vrai PC-tree Hsu/McConnell, ou degré
interne borné.
