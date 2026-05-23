# Handoff chercheur - PC-tree et circular Robinson

Date : 2026-05-23.
Branche : `research/agent-loop`.
Dernier checkpoint vert avant ce document : `1ce57f4` (`checkpoint: measure local obstruction depth`).

Ce document est une synthese de travail pour reprendre la recherche apres une
pause. Il ne pretend pas donner une solution generale. Il se concentre sur les
resultats utiles au chercheur : definitions effectivement utilisees dans le
repo, hypotheses testees, contre-exemples, pistes qui semblent mortes, et
prochaines questions mathematiques.

## 1. Point de vocabulaire critique

Le depot distingue deux couches.

1. **Quasi-circularite / boules arcs.**
   Un ordre circulaire est admissible si toutes les boules de `D` sont des arcs.
   C'est la couche que le PC-tree de Hsu-McConnell est cense representer
   compactement.

2. **Circular Robinson au sens du probleme du depot.**
   Parmi les ordres representes par ce PC-tree, on cherche un ordre qui satisfait
   la condition pre-circular/circular Robinson :

   ```text
   pour tout x < y < z < t,
   d(x,z) >= min(max(d(x,y), d(y,z)), max(d(x,t), d(t,z))).
   ```

Dans le texte du chercheur, "Robinson circulaire ssi toutes les boules sont des
arcs" correspond donc a la couche `quasi-circular` du depot. Le probleme restant
etudie ici est la couche supplementaire : existence d'un ordre `cR` dans le
PC-tree des ordres quasi-circulaires.

Cette distinction est probablement le point le plus important a aligner avant
de comparer les algorithmes.

## 2. Etat reproductible du depot

Commandes principales :

```bash
make quick
make check
make bench-quick
make bench
make bench-local-obstruction-depth
make bench-chirotope-high-girth
```

Interpretation :

- `JUSTE` signifie accord avec l'oracle exact sur les instances generees par le
  script ; ce n'est pas une preuve globale.
- `candidate.py` n'est pas vendu comme solution generale. Il combine brute force
  exacte pour `n <= 8`, des sous-cas certifies et des rapports incomplets
  explicites au-dela.
- Les probes `bench-*` sont des instruments de recherche. Ils ne doivent pas
  etre utilises pour affirmer un theoreme sans preuve separee.

Dernieres gates observees :

- `make quick` : `310 passed`, puis `JUSTE`.
- `make bench-quick` : `40/40` runs, `0` timeout, `0` incomplet.

## 3. Resultat central pour un ordre fixe : bad-side

Pour une paire distincte `{a,c}`, definir :

```text
B_ac = {u notin {a,c} : max(d(a,u), d(u,c)) > d(a,c)}.
```

Dans le depot, l'equivalence fixed-order suivante est le meilleur invariant
stabilise :

```text
un ordre beta est cR
ssi pour toute paire {a,c}, tous les points de B_ac
sont sur un seul des deux arcs ouverts entre a et c.
```

Equivalemment, pour tous `b,d in B_ac`, il faut interdire l'alternance
circulaire :

```text
a, b, c, d
```

ou, en langage "corde", `b` et `d` doivent etre du meme cote de la corde `ac`.

Artefacts :

- `passes_bad_side_precircular_cR` dans `src/pc_circular/predicates.py`.
- `threshold_common_neighborhood` et `passes_threshold_clean_side_condition`.
- `forbidden_bad_side_atoms` dans
  `src/pc_circular/solvers/sat_like_experiments.py`.
- Tests d'equivalence contre la definition directe dans `tests/test_predicates.py`.

Version seuil equivalente :

```text
C_ac = N_{d(a,c)}[a] intersect N_{d(a,c)}[c].

beta est cR
ssi pour chaque {a,c}, au moins un des deux arcs ouverts entre a et c
est contenu dans C_ac.
```

Cette reformulation semble etre la meilleure passerelle vers des idees
`round-order`, `proper circular-arc` ou contraintes de seuils imbriques.

## 4. Lien avec le plan du chercheur

### Phase 0 / Phase 1 : boules et PC-tree

Ces phases correspondent a la couche quasi-circulaire du depot. Elles sont
coherentes avec le setup : extraire les boules, construire un PC-tree des ordres
ou chaque boule est un arc, puis travailler dans cette famille compacte.

Attention : l'implementation actuelle du depot contient un scaffold PC-tree
simple pour experiments, pas une implementation complete Hsu-McConnell de
production. Les PDF et notes sont conserves dans `docs/source_materials/` et
`docs/source_notes.md`.

### Phase 2 / Phase 3 : effets des C-noeuds et invariant `Y_x`

Cette piste n'a pas encore ete testee directement sous la forme `Y_x`.
Elle est compatible avec plusieurs resultats du depot :

- le sous-cas ou les vrais choix sont booleens est naturellement proche de
  2-SAT/XOR ;
- les rapports de quartets montrent que beaucoup de contraintes se projettent
  sur un petit nombre de choix locaux ;
- les C-noeuds seuls restent la zone la plus prometteuse pour un sous-cas
  polynomial propre.

Mais il faut etre prudent : les obstructions observees ne sont pas toujours
locales a un seul noeud. T075 montre des frontiers non-cR dont le premier
quartet interdit a un support multi-niveau dans le PC-tree.

### Phase 4 : diametres, XOR, contraintes non maximales

Le depot donne un avertissement fort : les diametres globaux ne suffisent
probablement pas. La condition exacte fixed-order ne parle pas seulement des
plus lointains voisins ; elle parle de toutes les paires `{a,c}` et de tous les
temoins dans `B_ac`.

Donc si une formulation XOR est poursuivie, elle doit expliquer comment elle
encode ou elimine toutes les contraintes :

```text
same_side(a,c; b,d) pour b,d in B_ac
```

et pas seulement les contraintes de diametre global.

La formulation `same_side` de T082 peut servir de pont : elle donne le systeme
de contraintes exact pour `T=star`, resolu par enumeration d'ordres reels.

### Phase 5 : ordre interne des P-noeuds

C'est effectivement le vrai danger.

Le depot a plusieurs signaux convergents :

- Un seul gros P-noeud peut avoir treewidth CSP `0`, mais un domaine factoriel
  `(k-1)!/2`. La largeur seule n'est donc pas un bon parametre.
- Les relations non booleennes entre petits P-noeuds apparaissent dans les
  catalogues experimentaux, souvent avec parasites.
- Aucune preuve n'a ete trouvee que les P-noeuds residuels soient toujours des
  modules parfaits au sens distances.
- La conjecture "P-noeud residuel = mmodule parfait" doit etre testee ou prouvee
  avant de l'utiliser.

Proposition de test direct pour le chercheur :

1. Construire ou extraire le PC-tree quasi-circulaire `T(D)`.
2. Pour chaque P-noeud residuel et deux branches `A,B`, comparer les profils de
   distances externes :

   ```text
   d(x,a) pour x hors du P-noeud, a in A
   d(x,b) pour x hors du P-noeud, b in B
   ```

3. Chercher un P-noeud ou les boules ne distinguent pas les branches mais les
   contraintes `B_ac` les distinguent.

Si un tel exemple existe, Phase 5 doit devenir un sous-probleme recursif ou CSP.

### Phase 6 : verification finale

Cette philosophie est deja appliquee dans le depot : tout temoin positif
retourne par la candidate ou par les probes est revu par un predicat cR direct
et, si un PC-tree est fourni, par `represents_order`. C'est indispensable.

## 5. Ce qui a ete teste et ce qu'on sait

### Farthest-neighbor seul : refute comme critere autonome

Les conditions de croisement des plus lointains voisins sont utiles comme
diagnostic, surtout en strict. Mais en non strict elles ne suffisent pas et ne
sont pas necessaires sous leur forme brute.

Contre-exemples de petite taille sont dans `tests/test_predicates.py` et
`tests/test_regression_counterexamples.py`.

Conclusion : garder farthest comme source de filtres et d'intuition, pas comme
solveur.

### Bad-side et seuil clean-side : stabilises pour ordre fixe

T078 a compare la definition directe, bad-side et clean-side par seuil :

- `6072` ordres verifies ;
- `0` mismatch.

Conclusion : c'est la bonne brique locale pour toute preuve.

### CSP de quartets : exact conceptuellement, pas solution generale

Chaque contrainte bad-side donne des quartets interdits. Des solveurs
experimentaux existent :

- 2-SAT pour domaines booleens ;
- DP treewidth pour relations effectives ;
- catalogues de relations non booleennes.

Mais :

- un CSP binaire sur domaines factoriels peut rester dur ;
- T074 n'a trouve aucun temoin positif nouveau par rapport a `candidate.py` ;
- les `False` relationnels restent diagnostiques tant que les hypotheses de
  reduction ne sont pas prouvees.

### Signatures locales et DP naive : insuffisantes

Plusieurs tentatives de signatures locales ont ete attaquees :

- masques fermes ;
- `mask_multiset`;
- signatures one-hop ;
- projections locales `I_x(v)`.

T075 est important : `494` frontiers non-cR avaient des projections locales
silencieuses, mais un premier quartet interdit a support multi-niveau.

Conclusion : une DP correcte devra transporter une relation residuelle sur
separateur, pas seulement des signatures locales par noeud.

### L'ensemble des ordres cR n'est pas simplement un PC-tree

T079 a teste si l'ensemble de tous les ordres cR d'une matrice pouvait etre
represente par le scaffold PC-tree du depot. Contre-exemple complet des `n=5`.

T080 a ensuite audite ce contre-exemple avec un modele PC-tree non enracine a
5 feuilles :

- `893` candidats PC-tree inspectes ;
- `93` familles distinctes ;
- la famille cible a deux ordres n'est pas representable.

Conclusion : la route "calculer un PC-tree des ordres cR puis intersecter avec
T" est tres fragilisee.

### Petites obstructions : cap local insuffisant

T081 :

- noyau `four_local_non_cr` : obstruction minimale de taille `5` ;
- noyau `five_local_non_cr` : obstruction minimale de taille `6`;
- toutes les restrictions plus petites sont positives dans l'oracle exact.

T082 :

- `odd_high_cycle_low_hub`, `n=8`, globalement non-cR, toutes les restrictions
  jusqu'a `6` positives ;
- `even_high_cycle_low_hub`, `n=9`, globalement non-cR, toutes les restrictions
  jusqu'a `6` positives ;
- `0` mismatch oracle dans le probe.

Conclusion : une theorie par sous-matrices interdites de taille `<=6` est
impossible. Il faut soit une famille d'obstructions parametree, soit un
algorithme global.

### Sous-cas low-hub

Plusieurs certificats negatifs/positifs low-hub ont ete implementes ou probes :

- graphes hauts non bipartis avec hub bas ;
- cycles hauts pairs/impairs ;
- strong-ordering low-hub ;
- matching low-hub avec releve PC-tree.

Ces sous-cas sont utiles et souvent rapides, mais ils ne couvrent pas le probleme
general. Ils fournissent surtout une bonne famille de contre-exemples globaux.

### Cas strict

Un audit experimental de l'Algorithm 5.2 strict a ete ajoute :

- `360` lignes completes ;
- `0` mismatch contre enumeration exacte ;
- puis un probe large-n a trouve `204` temoins stricts valides, mais `0` nouveau
  positif par rapport a `candidate.py`.

Conclusion : sous-cas interessant a formaliser, mais pas prioritaire pour
ameliorer la candidate actuelle.

## 6. Pistes qui semblent faibles ou dangereuses

Ne pas investir lourdement sans nouvel angle dans :

- farthest-neighbor brut ;
- petits certificats jusqu'a taille `6` ;
- PC-tree unique des ordres cR ;
- treewidth CSP sans tenir compte de la taille des domaines P ;
- signatures locales qui ne transportent pas de correlations de bord ;
- integration de solveurs 2-SAT/treewidth dans `candidate.py` sans nouveaux
  temoins ou preuve de sous-cas.

## 7. Pistes les plus utiles pour le chercheur

### A. Clarifier le theoreme voulu

Il faut d'abord aligner les definitions :

- si le but est seulement "boules arcs", Hsu-McConnell resout deja la couche ;
- si le but est le probleme du depot, il faut ajouter la couche bad-side/cR.

### B. Prover ou refuter Phase 5 : P-noeuds residuels et modules

C'est probablement la meilleure jonction avec le travail du chercheur.

Question precise :

```text
Dans le PC-tree des boules, tout P-noeud residuel est-il un module de distances
suffisant pour que son ordre interne soit libre vis-a-vis des contraintes cR ?
```

Le depot suggere qu'il faut etre sceptique. Un contre-exemple serait tres utile.

### C. Remplacer "diametres globaux" par bad-side complet

Si une formulation XOR/2-SAT sur C-noeuds est poursuivie, elle doit partir de :

```text
same_side(a,c;b,d), pour toutes paires b,d dans B_ac.
```

Ensuite seulement on peut chercher quelles contraintes se reduisent a XOR dans
les C-noeuds, et lesquelles restent des contraintes d'ordre/P-noeud.

### D. Formaliser le sous-cas C-only / domaines booleens

Le depot a deja les briques experimentales. Theoreme cible :

```text
si tous les choix locaux pertinents sont booleens,
les contraintes de quartets deviennent une instance 2-SAT.
```

Il faut une preuve de reconstruction du temoin et de couverture des quartets.

### E. Comprendre les obstructions low-hub high-cycle

T082 donne des exemples globaux invisibles localement jusqu'a `6`. Il serait
utile de prouver une famille :

```text
cycle haut + hub bas
```

avec profondeur locale croissante, ou au moins de relier cette famille a une
obstruction connue d'ordre circulaire.

### F. Construire une vraie DP residuelle

Si l'objectif est algorithmique general, la DP devra probablement porter :

```text
relation residuelle sur separateur,
pas signature locale one-hop.
```

Les collisions T056/T057 et le support multi-niveau T075 vont dans ce sens.

## 8. Fichiers utiles

Predicats et oracles :

- `src/pc_circular/predicates.py`
- `src/pc_circular/oracle.py`
- `src/pc_circular/local_obstructions.py`
- `src/pc_circular/cyclic_order_sat.py`

PC-tree et experiments :

- `src/pc_circular/pc_tree.py`
- `src/pc_circular/unrooted_pc_tree.py`
- `src/pc_circular/solvers/sat_like_experiments.py`
- `src/pc_circular/solvers/dp_experiments.py`

Probes importants :

- `tools/pc_threshold_roundness_probe.py`
- `tools/pc_cr_pc_representability_probe.py`
- `tools/pc_unrooted_representability_probe.py`
- `tools/pc_local_obstruction_depth_probe.py`
- `tools/pc_chirotope_high_girth_probe.py`
- `tools/pc_frontier_obstruction_support_probe.py`

Docs vivantes :

- `docs/experiment_log.md`
- `docs/checkpoints.md`
- `docs/proof_obligations.md`
- `docs/tracks/README.md`
- `docs/tracks/piste_c_sat_csp.md`
- `docs/tracks/piste_e_farthest_quartets.md`

## 9. Commandes de reprise recommandees

Pour reprendre proprement :

```bash
git status --short --branch
make quick
make bench-chirotope-high-girth
make bench-local-obstruction-depth
```

Puis, selon la piste :

```bash
make bench-frontier-obstructions
make bench-single-p-stress
make bench-quartet-coverage
```

Si une candidate algorithmique nouvelle est modifiee :

```bash
make quick
make hunt-counterexamples
make bench-quick
```

## 10. Recommandation concrete pour la semaine

Pour le chercheur, je recommanderais de creuser dans cet ordre :

1. **Aligner les definitions.**
   Decider explicitement si "Robinson circulaire" des notes designe la couche
   boules-arcs ou la couche cR forte du depot.

2. **Tester/prover la conjecture P-noeud residuel = module.**
   C'est le trou le plus proche de la Phase 5 du chercheur et le plus dangereux
   pour une preuve polynomial-time.

3. **Reformuler Phase 4 avec bad-side complet.**
   Remplacer les seuls diametres par les contraintes
   `same_side(a,c;b,d)` pour `b,d in B_ac`, puis verifier quelles contraintes
   deviennent XOR sur les C-noeuds.

4. **Prouver le sous-cas C-only/booleen.**
   C'est probablement le resultat polynomial partiel le plus propre et le plus
   proche d'une preuve courte.

5. **Comprendre la famille low-hub high-cycle.**
   Elle montre deja que les obstructions locales jusqu'a `6` ne suffisent pas.
   Une generalisation parametree serait tres informative.

## 11. Ce qu'il ne faut pas conclure

- Le probleme general n'est pas resolu.
- Les benchmarks ne remplacent pas une preuve.
- Les rejets de petits probes ne justifient pas un `False` dans `candidate.py`.
- Les PC-trees du scaffold ne prouvent pas a eux seuls une propriete complete
  des PC-trees Hsu-McConnell.
- Les resultats star/all-orders ne decident pas automatiquement l'existence dans
  un PC-tree restreint.

Le depot est surtout devenu un laboratoire reproductible : chaque conjecture
peut maintenant etre transformee en test, en contre-exemple minimal, ou en
sous-cas prouve.
