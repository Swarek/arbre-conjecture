# GPT 5.5 Pro Global Strategy Addendum - 2026-05-23

Statut : cadrage utilisateur et revue externe, non preuve interne.

Cette note complète `gpt55_global_strategy_2026-05-23.md`. Le point important
ajouté par l'utilisateur est que la réponse GPT 5.5 Pro était trop ancrée sur
T056/T057. Elle doit donc servir de source d'hypothèses, pas de plan unique.

## Règle De Routage

T057 reste une piste de compression DP et de recherche de collisions de second
ordre. Elle ne doit pas absorber le Goal. À chaque itération longue, maintenir
au moins les pistes suivantes actives :

- Piste B/E : caractérisation bad-side et contre-exemples d'égalités ;
- Piste C : CSP exact par quartets et relations effectives ;
- Piste F : sous-cas 2-SAT, treewidth bornée et catalogue de relations ;
- Piste D : contraintes de type circular-ones/universalité séparées de
  l'existence ;
- Piste F dureté : gadgets `P` non booléens et contraintes parasites de `D`.

## Synthèse Des Lemmes A Tester

- Bad-side fixed-order : pour chaque paire `{a,c}`, tous les témoins
  `B_ac = {u : max(d(a,u), d(u,c)) > d(a,c)}` doivent rester d'un seul côté de
  `{a,c}`. Statut dépôt : testé et utilisé comme diagnostic, preuve écrite
  encore à renforcer.
- CSP de quartets : un ordre est cR ssi tous ses types de quartet sont dans
  les types autorisés par `D`. Statut dépôt : utilisé par
  `quartet_allowed_types`.
- Portée PC-tree des quartets : dans le scaffold actuel, l'acceptation observée
  a portée effective `<=2`, mais le support structurel peut être taille `3`.
  Statut dépôt : preuve expérimentale T058/T059, pas théorème général.
- Sous-cas booléen : arité `<=2` plus domaines booléens suggère 2-SAT exact.
  Statut dépôt : détecté par `row_class="two_sat_candidate"` et implémenté hors
  `candidate.py` par T060. Les SAT sont des témoins vérifiés ; les UNSAT restent
  confinés au modèle relationnel tant que sa suffisance globale n'est pas
  prouvée.
- Treewidth : si le graphe primal des relations fusionnées a largeur bornée,
  une DP exacte standard est possible. Statut dépôt : T061 implémente une DP
  exacte bornée hors `candidate.py`, et T062 ajoute `p3_block_tree(k)` comme
  stress de largeur croissante.

## Expériences A Garder Séparées

1. Prouver ou casser bad-side fixed-order par matrices non strictes.
2. Construire le CSP exact par quartets puis valider relation-CSP vs cR direct.
3. Implémenter le sous-cas C-only / domaines booléens par 2-SAT.
4. Cataloguer les relations non booléennes des petits nœuds `P`.
5. Chercher une collision de second ordre contre les signatures ouvertes T057.

Ces expériences doivent produire des artefacts séparés : test, générateur,
contre-exemple minimal, lemme négatif ou entrée de piste. Une réussite de T057
ne prouve pas 2-SAT/treewidth ; une réussite 2-SAT ne prouve pas la DP générale.

## Mise A Jour Apres T060-T062

Le recadrage utilisateur reste valide, mais le statut a avance :

- T060 a ferme l'experience "sous-cas booleen par 2-SAT" dans le scaffold
  supporté, sans integration candidate.
- T061 a ajoute une DP treewidth exacte bornee pour les relations effectives,
  couvrant aussi les domaines non booleens `P3`.
- T062 a fourni une famille de stress `p3_block_tree(k)` montrant que la largeur
  croit et que les caps doivent produire `treewidth_cap_exceeded` plutot qu'un
  faux rejet.

La prochaine decision ne doit donc pas etre "continuer T057 ou non", mais
choisir entre :

- une integration positive-only strictement gardee de T060/T061 dans
  `candidate.py`, uniquement si un probe montre de vrais temoins nouveaux ;
- un catalogue de relations non booleennes/gadgets pour evaluer la durete ;
- une collision de second ordre contre T057 ;
- une piste circular-ones/universalite gardee separee de l'existence.
