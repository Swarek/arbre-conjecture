# Piste E - Obstructions farthest et quartets cR

## Question

Les obstructions farthest-neighbor suffisent-elles à caractériser les mauvais
ordres, ou faut-il utiliser les quartets cR exacts ?

## Résultat principal

Statut : preuve expérimentale avec contre-exemples minimaux.

La condition farthest-crossing brute n’est pas un critère de décision. Cette
condition brute n’est pas la Proposition 4.4 complète : elle ignore la clause
dégénérée non stricte mentionnée dans le papier `strongly-circular-sidma-1.pdf`.

Elle n’est pas nécessaire :

- matrice égal-distance à 4 points ;
- tout ordre est cR ;
- farthest brut échoue à cause de dégénérescences massives ;
- la condition Proposition 4.4 complète passe grâce à la clause dégénérée.

Elle n’est pas suffisante :

- exemple à 4 points avec farthest unique ;
- exemple à 4 points avec toutes les distances hors diagonale distinctes ;
- l’ordre passe farthest mais viole la condition pre-circular cR.

Artefacts :

- `tests/test_regression_counterexamples.py`;
- `docs/proof_obligations.md`;
- `docs/source_notes.md`;
- `find_precircular_cR_violation`;
- `find_farthest_crossing_violation`.
- `passes_farthest_prop_4_4_condition`.
- `find_farthest_prop_4_5_obstruction`.
- `passes_farthest_prop_4_5_order_test`.

## Données observées

Exploration exhaustive signalée par subagent :

- `n=4`, valeurs `{1,2,3}` : 405 cas `cR=True` mais `farthest=False`, 96 cas
  `cR=False` mais `farthest=True`.
- `n=5`, valeurs `{1,2,3}` : 31116 cas `cR=True` mais `farthest=False`, 24120
  cas `cR=False` mais `farthest=True`.

## Conséquence

Toute candidate basée sur farthest doit :

- traiter explicitement les égalités et dégénérescences ;
- ajouter des contraintes non-farthest ;
- ou annoncer un sous-cas strictement plus restreint.

La version Proposition 4.4 est une condition nécessaire pour un ordre cR
compatible. Elle n’est pas utilisée comme oracle global. Le prochain test utile
est de vérifier expérimentalement le couple Prop. 4.4/4.5 sur les ordres
quasi-circulaires.

## Prop. 4.5 sur ordre fixé

Statut : preuve expérimentale, ordre fixé seulement.

Le diagnostic `passes_farthest_prop_4_5_order_test` cherche l’absence de
certificat farthest du type :

- `x < x' < y < y'`, ou
- `x < y' < y < x'`,

avec `x' in F_x` et `y' in F_y`, et avec la clause non stricte qui exclut les
dégénérescences autorisées.

Résultat observé :

- aucun désaccord avec `is_precircular_order_cR` sur les ordres
  quasi-circulaires pour `n <= 5`, valeurs `{1,2,3}`;
- un test de régression exhaustif verrouille déjà le cas `n=4`;
- hors quasi-circularité, le diagnostic n’est pas suffisant et ne doit pas être
  utilisé comme oracle.

Prochaine action : utiliser ce diagnostic comme accélérateur ou générateur
d’obstructions pour le CSP/DP, sans le confondre avec l’existence dans PC-tree.

## Prochaine action

Utiliser les témoins `find_precircular_cR_violation` comme source principale
d’obstructions. Garder farthest comme diagnostic utile, pas comme oracle.
