# Piste D - Intersection PC-tree / circular-ones

## Question

La circularité Robinson peut-elle être reformulée comme une famille de
contraintes d’arcs ou de circular-ones à intersecter avec le PC-tree ?

## Intuition

Les ordres quasi-circulaires sont déjà décrits par des boules qui sont des arcs.
Il est tentant d’ajouter des contraintes dérivées de `D` pour éliminer les ordres
non cR sans quitter le monde PC/PQ/circular-ones.

## État courant

Statut : diagnostic borné ajouté, pas solver.

`strict_ball_circular_ones_report` teste expérimentalement la partie
quasi-circulaire attendue de la piste circular-ones : pour chaque ordre/frontier
énumérable, il vérifie que toutes les boules métriques non triviales sont des
arcs, puis compare ce signal à `is_quasi_circular_order`,
`is_strict_quasi_circular_order` et aux prédicats cR stricts.

Résultat T025 :

- sur les probes bornées, `ball_arc` coïncide avec `is_quasi_circular_order` ;
- Fig. 2.2 donne deux ordres `ball_arc/strict_quasi`, mais un seul ordre strict
  circular, donc les contraintes de boules ne décident pas cR ;
- un random `n=6 seed=7` a un unique ordre `ball_arc/quasi` sous star, mais
  aucun ordre cR, ce qui donne un faux positif non-source au-delà de Fig. 2.2 ;
- equal-distance donne tous les ordres `ball_arc/quasi/precircular` non stricts
  mais aucun ordre strict, ce qui protège les égalités ;
- le témoin strict cR non représenté par un PC-tree reste absent quand le
  rapport reçoit ce PC-tree ;
- une signature de modules par appartenance aux boules non triviales est
  exposée pour mesurer d'éventuelles contractions avant une intersection
  PC-tree/circular-ones.

Cet artefact ne construit pas encore un PC-tree de circular-ones et n'est pas
utilisé par `candidate.py`.

Les sources Hsu/McConnell et Hsu PC-vs-PQ sont listées dans
`docs/source_notes.md`. Elles justifient la pertinence des PC-trees pour les
arrangements circular-ones, mais l’implémentation actuelle reste un scaffold
minimal.

## Risques

- Les contraintes cR peuvent ne pas être exprimables comme contraintes d’arcs
  indépendantes.
- Des contraintes valables localement peuvent ne pas capturer les corrélations
  globales entre choix PC-tree.

## Prochaine action

Deux suites raisonnables :

- construire réellement le PC-tree/circular-ones des boules et l'intersecter
  avec le PC-tree donné, au lieu d'énumérer les frontiers ;
- chercher une famille de contraintes d'arcs dérivée des quartets cR et tester
  si elle sur-rejette Fig. 2.2, equal-distance ou les régressions paired-farthest.
