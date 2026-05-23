# GPT 5.5 Pro Global Strategy Review - 2026-05-23

Statut : revue externe fournie par l'utilisateur, a verifier dans le depot.

Note de cadrage : la demande envoyee a GPT 5.5 Pro etait trop ancree sur les
checkpoints T056/T057. La reponse doit donc etre lue comme une revue utile
post-T057, pas comme une decision de bloquer la suite sur un seul test de
collision. Les recommandations ci-dessous sont re-routees vers plusieurs pistes
independantes.

## Diagnostic Retenu

- Le coeur du probleme est l'existence d'un plongement local du PC-tree qui
  evite toutes les violations circular Robinson induites par `D`.
- Les quotients locaux fermes T056/T057 ressemblent a des projections CSP :
  ils peuvent perdre des correlations residuelles entre bords.
- Le bon objet pour une DP exacte est probablement une relation residuelle sur
  separateur, pas seulement un masque local.
- La signature ouverte one-hop de T057 est un bon diagnostic, mais elle n'est
  pas encore une congruence de composition.
- Une formulation exacte par contraintes de quartets reste le point d'appui le
  plus propre pour separer sous-cas polynomiaux, FPT et durete.

## Lemme Bad-Side A Formaliser

Pour une paire distincte `{a,c}`, definir :

```text
B_ac = { u notin {a,c} : max(d(a,u), d(u,c)) > d(a,c) }.
```

Revue externe : un ordre circulaire `beta` est cR si et seulement si, pour toute
paire `{a,c}`, tous les sommets de `B_ac` sont sur un seul des deux arcs ouverts
entre `a` et `c`. Equivalent : `a` et `c` sont adjacents dans l'ordre induit sur
`B_ac union {a,c}`.

Statut depot : proche de `passes_bad_side_precircular_cR`, mais l'obligation de
preuve doit etre ecrite explicitement et reliee aux contraintes CSP.

## CSP Exact Par Quartets

Revue externe : pour chaque quartet `Q`, calculer les types circulaires
autorises par `D`, puis traduire le type induit par le PC-tree en contrainte sur
les choix locaux. Le lemme propose que le type d'un quartet depend d'au plus
deux noeuds internes pertinents du PC-tree : un noeud central, ou deux noeuds de
branchement relies.

Consequences a tester :

- si tous les domaines effectifs sont booleens, reduction exacte a 2-SAT ;
- si le graphe primal du CSP de quartets a treewidth bornee, DP exacte en
  `O(n^4 q^(w+1))` ;
- sans borne de largeur, une DP par signatures enrichies peut simplement
  reencoder l'enumeration globale.

## T057 Dans Le Portefeuille

T057 doit continuer comme test de compositionalite, pas comme axe unique. La
prochaine experience pertinente est une collision de second ordre : comparer
une signature one-hop composee a la relation residuelle exacte d'un patch de
supports.

Une collision de second ordre a la forme :

```text
sig_T057(P, theta) = sig_T057(P, theta')
mais
R_P^theta != R_P^theta'
```

ou `R_P` est la relation residuelle exacte sur le bord du patch.

## Pistes Prioritaires A Partir De Cette Revue

1. Formaliser et tester la caracterisation bad-side exacte.
2. Construire un CSP exact par quartets et verifier experimentalement la portee
   `<= 2` des contraintes sur les variables PC-tree.
3. Implementer le sous-cas booleen / C-only par 2-SAT.
4. Cataloguer les relations binaires realisables entre deux petits noeuds `P`
   pour jauger la piste NP-hardness.
5. Chercher une collision de second ordre contre `local_boundary_response`.

Ces cinq pistes doivent rester actives en portefeuille. Si deux iterations
successives d'une piste n'apportent ni preuve partielle, ni benchmark meilleur,
ni contre-exemple, basculer vers une autre.

## Risques A Garder

- Le lemme de portee `<= 2` des quartets doit etre verifie sur le scaffold
  actuel avant toute preuve generale PC-tree Hsu/McConnell.
- Les distances sont globales : un gadget de durete local peut creer des
  contraintes parasites par les quartets non prevus.
- Le cas `single P-node` doit etre separe du probleme PC-tree general.
- Le sous-cas strict/farthest-neighbor ne controle pas toutes les paires
  `B_ac`, donc il ne suffit pas seul.
