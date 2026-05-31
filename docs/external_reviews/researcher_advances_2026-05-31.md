# Researcher advances digest - 2026-05-31

Statut : triage de notes externes fournies par l'utilisateur. Ce document
conserve les idees utiles pour la suite, mais ne les transforme pas en theoremes
du depot. Les claims de polynomialite, de largeur 4 ou d'independance des
P-noeuds restent conditionnels tant qu'ils ne sont pas prouves ou reproduits par
des artefacts versionnes.

## Sources triees

| Source | Contenu | Statut |
| --- | --- | --- |
| Long preprint externe | Algorithme conditionnel via PC-tree de `(Q)`, diametres locaux, 2-SAT, P-noeuds et conjecture de largeur 4 | Utile comme plan theorique, non fiable comme preuve generale |
| Note interface P-noeud | Tests empiriques sans mismatch sur un lemme de produit cartesian des completions internes a interface fixee | Signal interessant, pas reproductible dans le depot pour l'instant |
| Note critique recollement | Rappelle que remplacer seulement l'ordre local d'un P-noeud en gardant les interieurs fixes peut echouer | Garde-fou important contre une preuve trop locale |
| Note largeur 4 / circle graph | Propose des relations `R_{ijlm}` sur quadruplets de branches et une route circle graph / split decomposition | Piste nouvelle a tester, non integree |
| Screenshot manuscrit | Gadget 4 blocs x 2 feuilles, distances de base 2, quelques paires hautes 3 | Seed ambigu pour un futur generateur, pas contre-exemple etabli |
| Prompt utilisateur | Priorite donnee a la projection des contraintes farthest sur les noeuds PC | Deja partiellement testee ; doit etre renforcee en bad-side complet |

Le screenshot est vendorise dans
`docs/source_materials/images/handwritten_block_gadget_2026-05-31.png`.

## Ce qui est solide et deja aligne avec le depot

### Bad-side reste l'objet central fixed-order

Pour un ordre fixe, la meilleure caracterisation reste :

```text
pour toute paire {a,c}, tous les mauvais temoins B_ac sont sur un seul cote
de la corde ac.
```

Equivalentement, pour tous `b,d in B_ac`, on impose
`same_side(a,c;b,d)`. Les notes externes vont dans le meme sens que T078/T082 :
le bon objet n'est pas seulement le farthest-neighbor brut, mais la famille
complete des contraintes bad-side.

Point a ne pas oublier : cette caracterisation decide un ordre donne. Elle ne
donne pas automatiquement un algorithme polynomial pour l'existence dans une
famille compacte de frontiers.

### Les contraintes de P-noeuds sont le vrai verrou

Les sources convergent sur un meme trou : quand un P-noeud a plusieurs branches
actives, une contrainte bad-side peut coupler l'ordre des branches et les ordres
internes des sous-arbres. Les resultats T075/T081/T082 du depot disent deja que
les signaux purement locaux et les petits certificats peuvent etre muets.

La bonne abstraction a poursuivre n'est donc pas :

```text
chaque noeud decide independamment avec des ensembles I_x(v)
```

mais plutot :

```text
chaque noeud transporte une relation de bord/residuelle assez fine pour
composer les contraintes bad-side ouvertes.
```

## Idees a garder comme hypotheses falsifiables

### H1 - Projection P-noeud des contraintes exactes

Question externe :

```text
Fixer un P-noeud v de branches B_1,...,B_k.
Pour chaque x, I_x(v) = { i : B_i intersecte F_x }.
Les familles I_x(v) sont-elles des intervalles circulaires ?
Les contraintes de croisement induites sont-elles convexes/laminaires ?
```

Triage :

- utile comme diagnostic ;
- insuffisant tel quel, car T046/T075 montrent que les `I_x(v)` farthest seuls
  peuvent etre silencieux sur des frontiers non-cR ;
- a relancer avec les contraintes `B_ac` / `same_side(a,c;b,d)` completes, pas
  seulement avec `F_x`.

Experience prioritaire :

```text
project_bad_side_obligations_to_pc_nodes(D,T)
```

Pour chaque noeud interne, lister les contraintes bad-side dont les quatre
feuilles traversent ses branches, puis mesurer :

- arite locale visible ;
- violations d'intervalle/circular-ones ;
- besoin de relation de bord multi-niveau ;
- comparaison avec les faux silences T046/T075.

### H2 - Lemme d'interface des P-noeuds

Conjecture externe reformulee :

```text
A ordre de branches sigma et contexte exterieur fixes, les completions internes
valides des blocs d'un P-noeud se factorisent en produit cartesian.
```

Ce qui est interessant :

- la note rapporte environ 57k contextes testes sans mismatch ;
- l'enonce attaque directement le trou de recollement des P-noeuds ;
- il pourrait expliquer pourquoi certaines contraintes locales se composent
  mieux que les signatures T056/T057.

Ce qui reste ouvert :

- les tests ne sont pas versionnes ;
- il faut definir exactement "contexte exterieur fixe", "interface", "ordre
  interne valide" et les contraintes bad-side traversantes ;
- les contre-signaux T075/T082 doivent etre inclus dans le banc d'essai ;
- `0 mismatch` ne suffit pas si la relation d'interface reste exponentielle.

Probe conseille :

```text
fixer (P, sigma, contexte)
enumerer toutes les completions internes
comparer l'ensemble accepte a produit_i R_i(interface_i)
chercher un mismatch et shrinker le premier cas
```

Si un mismatch apparait, l'ajouter comme regression. Si aucun mismatch n'apparait,
mesurer aussi la taille des relations, pas seulement leur exactitude.

### H3 - Conjecture de largeur 4 sur les P-noeuds

Conjecture externe :

```text
Pour un P-noeud v, l'ensemble A_v des ordres admissibles des branches serait
determine par toutes ses restrictions a 4 branches via des relations R_ijlm.
```

Impact si vrai :

- cela donnerait une compression forte des gros P-noeuds ;
- cela expliquerait pourquoi une coherence d'ordre 4 pourrait suffire sous la
  promesse quasi-circulaire ;
- cela fournirait une route vers un algorithme polynomial conditionnel.

Triage :

- nouveau et important ;
- non prouve ;
- en tension avec le danger "single P-node : domaine factoriel" ;
- pas directement refute par T081/T082, car ces diagnostics sont star/all-orders
  et pas necessairement sous l'hypothese exacte `(Q)` revendiquee ;
- doit etre teste contre les familles hard du depot avant toute integration.

Experience de reconciliation :

```text
reproduire A_v et R_ijlm dans le scaffold actuel
tester largeur 4 sur paired_farthest, p3_block_tree, T075, T079/T080, T082
separer lignes sous promesse (Q) des lignes hors promesse
```

### H4 - Route circle graph / split decomposition

Les notes proposent de voir les contraintes locales d'un P-noeud comme un
systeme de cordes ou de graphes d'entrelacement, puis d'utiliser des idees de
Bouchet/Cunningham.

Statut :

- absente des pistes actuelles comme experience explicite ;
- mathematiquement plausible pour les contraintes de cotes de cordes ;
- a garder comme piste theorique, pas comme dependance de code immediate.

Premier probe possible :

```text
Pour un P-noeud, transformer les contraintes same_side localisees en graphe
d'entrelacement de branches, puis chercher si les obstructions produites par
les generateurs du depot ressemblent a des obstructions circle-graph connues.
```

### H5 - Gadget manuscrit 4 blocs x 2 feuilles

Lecture prudente du screenshot :

- quatre blocs/branches `A,B,C,D`, chacun avec deux feuilles ;
- distance de base probablement `2` partout ;
- quelques paires inter-blocs a distance `3` ;
- objectif probable : montrer un cas ou la projection locale est muette alors
  qu'un ordre de blocs fixe viole bad-side.

Statut :

- pas assez specifie pour etre un contre-exemple ;
- avec un root `P` libre, une lecture naturelle semble probablement positive ;
- avec un root `C` fixe `A-B-C-D`, la meme lecture peut devenir negative avec
  projection `I_x(v)` silencieuse ;
- a formaliser comme generateur, puis valider par oracle et shrink.

## Claims a ne pas importer comme faits

- "Le probleme non strict general est resolu en temps polynomial."
- "La largeur 4 suffit sans preuve de la conjecture correspondante."
- "Les diametres locaux ou farthest-neighbors seuls suffisent en general."
- "Un ordre de branches valide permet de garder les interieurs des blocs fixes."
- "Les validations numeriques non versionnees remplacent les gates du depot."
- "Un cap local 4/5/6 suffit a detecter toute obstruction globale."
- "Treewidth faible suffit si les domaines P restent factoriels."

## Relation avec les resultats actuels

- T046/T075 : les projections locales `I_x(v)` peuvent etre silencieuses. Toute
  nouvelle piste locale doit transporter du bad-side complet ou une relation de
  bord.
- T056/T057 : les signatures locales perdent des correlations de contexte. Le
  lemme d'interface doit etre teste precisement contre ces pertes.
- T064 : un seul gros `P` peut avoir treewidth `0` et domaine factoriel. La
  largeur du graphe de contraintes ne suffit pas sans compression de domaine.
- T081/T082 : des obstructions globales peuvent etre invisibles sous petits
  caps locaux. La largeur 4 doit donc etre comprise comme hypothese structurelle
  sous `(Q)`, pas comme simple certificat de sous-matrice.
- T078/T082 : les contraintes `same_side` sont le meilleur socle experimental
  pour verifier les claims fixes-order.

## Prochaines experiences recommandees

1. **Probe d'interface P-noeud.**
   Rejouer l'enonce "produit cartesian des completions internes" dans le depot,
   avec seeds sauvegardees, et l'attaquer par T075/T082.

2. **Projection bad-side vers noeuds PC.**
   Remplacer le diagnostic `I_x(v)` farthest par une projection des obligations
   `same_side(a,c;b,d)` completes.

3. **Test largeur 4 P-noeud.**
   Construire `A_v` et `R_{ijlm}` pour les P-noeuds du scaffold, puis verifier
   si les restrictions a 4 branches caracterisent vraiment les ordres locaux
   admissibles sur les familles connues.

4. **Circle graph lab.**
   Traduire les contraintes localisees en graphe d'entrelacement et mesurer si
   les obstructions observees ont une structure circle-graph ou au contraire
   simulent cyclic ordering arbitraire.

5. **Formalisation du gadget manuscrit.**
   Transformer le dessin en matrice explicite versionnee, tester `P` libre vs
   `C` fixe, puis documenter le resultat comme regression ou comme faux lead.

## Synthese pour la suite

Le meilleur usage de ces notes n'est pas de changer `candidate.py`. Elles
doivent orienter la prochaine boucle de recherche vers un point precis :

```text
Comprendre si les contraintes bad-side projetees sur un gros P-noeud ont une
structure compressible, ou si elles peuvent simuler un probleme d'ordre
circulaire dur.
```

Les hypotheses les plus utiles sont donc : interface P-noeud, largeur 4
conditionnelle, projection bad-side complete, et route circle graph. Les claims
de resolution generale restent hors statut tant que `docs/proof_obligations.md`
n'est pas rempli avec preuves et contre-tests reproductibles.
