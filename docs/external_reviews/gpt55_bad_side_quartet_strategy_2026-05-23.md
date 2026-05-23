# GPT 5.5 Pro Bad-Side / Quartet Strategy - 2026-05-23

Statut : analyse externe fournie par l'utilisateur, non preuve interne.

Note de cadrage : cette revue est utile, mais elle a ete partiellement orientee
par le contexte T056/T057. Elle doit donc alimenter plusieurs pistes du
portefeuille, pas devenir un plan unique centre sur les collisions de signatures.

## Diagnostic Retenu

- Le coeur du probleme est l'existence d'un plongement local du PC-tree dont la
  frontier evite toutes les violations circular Robinson induites par `D`.
- Les quotients locaux T056/T057 ont le comportement attendu d'une projection
  CSP : ils peuvent perdre des correlations residuelles entre bords.
- Le bon objet DP exact est probablement une relation residuelle sur separateur.
  Une signature compacte n'est valide que si elle determine cette relation.
- La signature ouverte one-hop reste un bon diagnostic de compression, mais elle
  n'est pas une congruence de composition tant qu'une propriete de
  2-decomposabilite n'est pas prouvee.
- La reformulation par mauvais temoins et par quartets donne une base plus
  propre pour les sous-cas 2-SAT, treewidth, circular-ones et les pistes de
  durete.

## Lemmes A Formaliser Ou Garder Comme Obligations

### Bad-Side Fixed-Order

Pour deux sommets distincts `{a,c}` :

```text
B_ac = { u notin {a,c} : max(d(a,u), d(u,c)) > d(a,c) }.
```

Un ordre circulaire fixe est circular Robinson si et seulement si, pour toute
paire `{a,c}`, tous les elements de `B_ac` restent sur un seul des deux arcs
ouverts entre `a` et `c`. Equivalent : `a` et `c` sont adjacents dans l'ordre
induit sur `B_ac union {a,c}`.

Statut depot : implemente et teste comme `passes_bad_side_precircular_cR`, mais
les obligations de preuve doivent rester explicites dans `docs/proof_obligations.md`.

### Version Seuil

Pour chaque seuil `lambda`, definir `G_lambda` par `uv in E_lambda` si
`d(u,v) <= lambda`. La condition cR d'un ordre fixe peut se reformuler comme une
condition de type "circular umbrella" commune a tous les graphes de seuil. Cette
piste doit rester separee de l'existence dans le PC-tree.

### CSP De Quartets

Pour chaque quartet `Q`, calculer les types circulaires autorises par `D`.
L'ordre est cR si et seulement si tous les quartets induisent un type autorise.
Dans le scaffold PC-tree courant, les relations effectives observees ont portee
au plus `2`, ce qui justifie les experiences T058/T059/T060/T061.

Limite : le support structurel peut etre plus large que la portee effective
observee. Le lemme general pour vrais PC-trees Hsu/McConnell reste a prouver.

### Sous-Cas 2-SAT

Si tous les domaines effectifs sont booleens et si les relations fusionnees ont
arite au plus `2`, chaque affectation interdite se traduit par une clause 2-CNF.

Statut depot : T060 implemente `solve_quartet_2sat` hors `candidate.py`. Les SAT
donnent des temoins reconstruits et verifies ; les UNSAT ne doivent pas encore
etre promus en rejets generaux de `candidate.py` sans preuve de suffisance du
modele relationnel.

### Treewidth Bornee

Si le graphe primal du CSP de quartets a treewidth `w` et domaines max `q`, une
DP exacte standard coute `O(n^4 q^(w+1))` apres construction des relations.

Statut depot : T061 implemente `solve_quartet_treewidth_csp` hors `candidate.py`
pour les relations effectives, y compris les domaines non booleens `P3`, sous
caps explicites. T062 ajoute `p3_block_tree(k)` pour rendre la largeur visible
comme parametre limitant.

### Condition Necessaire Pour T057

Pour un patch `P`, la vraie information DP est :

```text
R_P = { affectations du bord qui admettent une extension interne compatible }.
```

Une signature `sigma(P)` est valide seulement si
`sigma(P) = sigma(P')` implique `R_P = R_P'`. La signature one-hop T057 doit
donc etre testee contre des collisions de second ordre, pas seulement contre des
collisions primitives.

## Experiences Prioritaires

1. Maintenir le lemme bad-side comme preuve fixed-order et base des nogoods.
2. Continuer le CSP exact par quartets, en separant portee effective observee et
   lemme PC-tree general.
3. Utiliser 2-SAT uniquement pour le sous-cas booleen complet ou comme
   extracteur de temoins positifs verifies.
4. Utiliser la DP treewidth comme solveur exact FPT sous largeur bornee, avec
   stress `p3_block_tree(k)` pour eviter toute revendication de polynomialite
   generale.
5. Cataloguer les relations non booleennes entre petits noeuds `P` pour jauger
   la piste NP-difficulte.
6. Chercher une collision de second ordre contre T057, mais sans bloquer les
   autres pistes sur cette seule question.
7. Garder separees les pistes circular-ones/universalite : elles peuvent donner
   des diagnostics ou sous-cas, pas une solution directe a l'existence.

## Contre-Exemples Et Stress Tests A Privilegier

- matrices non strictes avec beaucoup d'egalites ;
- cas ou certains ordres du PC-tree marchent et d'autres non ;
- gros noeuds `P` et domaines `P3` non booleens ;
- `p3_block_tree(k)` pour largeur croissante ;
- gadgets de relations binaires : egalite, inegalite, implication, relations
  non bijonctives ;
- cycles de parite abstraits comme modele de correlation perdue par une
  signature one-hop ;
- familles ou les distances parasites de `D` cassent un gadget local trop
  naif.

## Decision De Routage

Cette revue confirme la strategie multi-pistes :

- Piste B/E : bad-side exact et signatures DP a falsifier ;
- Piste C : quartet CSP, 2-SAT booleen, DP treewidth ;
- Piste D : circular-ones, seuils, universalite, sans confusion avec existence ;
- Piste F : sous-cas stricts, largeur bornee, relations non booleennes et
  durete plausible.

La suite ne doit pas etre formulee comme "faire T057". T057 devient un test de
compression parmi d'autres, tandis que T060-T062 fournissent deja des solveurs de
sous-cas experimentaux et des benchmarks de largeur.
