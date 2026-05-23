# GPT 5.5 Pro Red-Team: Domain Size Warning - 2026-05-23

Statut : analyse externe fournie par l'utilisateur, non preuve interne.

Cette revue red-team corrige un optimisme possible apres T058-T062 : une
reduction exacte vers CSP binaire peut etre vraie et rester peu utile si les
domaines locaux des noeuds `P` ne sont pas representes compactement.

## Point Principal

Le vrai ennemi n'est pas seulement l'arite des contraintes. C'est la taille du
domaine local des noeuds `P`.

Un PC-tree star a un seul noeud `P`. Dans une lecture CSP naive, le graphe
primal a treewidth `0`. Pourtant le domaine local contient deja :

```text
(n - 1)! / 2
```

ordres circulaires. Donc :

```text
portee <= 2       n'implique pas polynomial
treewidth petite  n'implique pas facile si les domaines P sont factoriels
```

Cette observation ne refute pas T059/T060/T061. Elle precise leur statut :
2-SAT et treewidth sont de vrais sous-cas/parametres, mais ils doivent etre
accompagnes d'une representation compacte ou d'un domaine effectivement borne.

## Priorites Recommandees Par La Revue

1. Verifier l'exactitude de l'extracteur quartet/CSP sans compression.
2. Tester le cas single `P`-node pour exposer l'explosion factorielle du domaine.
3. Prouver proprement le sous-cas C-only / domaines booleens par 2-SAT avec
   reconstruction de temoin.
4. Rendre les generateurs promise-aware : verifier ou reconstruire que `T`
   vient bien du scaffold admissible attendu pour `D`.
5. Cataloguer les relations non booleennes entre petits noeuds `P`, avec les
   contraintes parasites dues a la globalite de `D`.

## Consequences Pour Le Depot

- Toute metrique treewidth doit etre accompagnee de la taille maximale de
  domaine local.
- Une ligne de treewidth `0` peut etre dure si elle cache un grand noeud `P`.
- Les integrations `candidate.py` doivent rester positive-only ou limitees aux
  sous-cas prouves tant que la representation compacte des domaines `P` n'est
  pas comprise.
- La piste NP-hardness doit commencer par des catalogues de relations et des
  parasites, pas par une reduction complete prematuree.

## Experience T064 Derivee

Ajouter un benchmark single `P`-node qui enumere bornement les ordres du star
PC-tree, compte les ordres cR par le predicat bad-side fixed-order, et garde
visibles :

- domaine local `(n-1)!/2` ;
- treewidth unary `0` ;
- nombre de contraintes bad-side explicites ;
- lignes completes/incompletes sous limite d'enumeration.

Ce benchmark sert a empecher la fausse conclusion "treewidth faible donc facile".
