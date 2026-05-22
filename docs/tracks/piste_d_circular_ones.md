# Piste D - Intersection PC-tree / circular-ones

## Question

La circularité Robinson peut-elle être reformulée comme une famille de
contraintes d’arcs ou de circular-ones à intersecter avec le PC-tree ?

## Intuition

Les ordres quasi-circulaires sont déjà décrits par des boules qui sont des arcs.
Il est tentant d’ajouter des contraintes dérivées de `D` pour éliminer les ordres
non cR sans quitter le monde PC/PQ/circular-ones.

## État courant

Statut : non testée expérimentalement.

Aucun générateur de contraintes circular-ones additionnel n’a encore été écrit.
Les contre-exemples de la Piste E indiquent que les contraintes farthest seules
ne suffisent pas ; cette piste doit donc partir des quartets cR exacts ou d’une
reformulation prouvée plus forte.

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

Prendre les contre-exemples 4 points et tester si la violation cR minimale peut
être exprimée comme une contrainte d’arc simple. Si non, documenter le lemme
négatif et basculer vers CSP/DP.
