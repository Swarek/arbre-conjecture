# Source notes

Ces notes collectent les idées issues des PDF locaux fournis par l’utilisateur.
Elles ne remplacent pas les oracles, tests, contre-exemples ni obligations de
preuve du dépôt.

## Sources locales consultées

| Fichier versionné | Source originale | Pages | Usage actuel |
| --- | --- | ---: | --- |
| `docs/source_materials/pdfs/strongly-circular-sidma-1.pdf` | `/Users/mathisblanc/Downloads/strongly-circular-sidma-1.pdf` | 19 | Conditions cR/pre-cR, farthest-neighbor, test d’un ordre fixé |
| `docs/source_materials/pdfs/Robinson_modules-1.pdf` | `/Users/mathisblanc/Downloads/Robinson_modules-1.pdf` | 27 | Modules en espaces Robinson linéaires, analogies structurelles |
| `docs/source_materials/pdfs/PC-Trees_vs._PQ-Trees__Hsu-2.pdf` | `/Users/mathisblanc/Downloads/PC-Trees_vs._PQ-Trees__Hsu-2.pdf` | 15 | PC-trees vs PQ-trees, circular-ones |
| `docs/source_materials/pdfs/Modules_PQ-tree-1.pdf` | `/Users/mathisblanc/Downloads/Modules_PQ-tree-1.pdf` | 43 | Modules et PQ-trees pour ordres Robinson linéaires |
| `docs/source_materials/pdfs/Hsu-McConnel_PC-trees-1.pdf` | `/Users/mathisblanc/Downloads/Hsu-McConnel_PC-trees-1.pdf` | 18 | PC-trees pour circular-ones arrangements |
| `docs/source_materials/pdfs/Brucker_Osswald-1.pdf` | `/Users/mathisblanc/Downloads/Brucker_Osswald-1.pdf` | 17 | Hypercycles, dissimilarités et liens circular/Robinson |
| Screenshot utilisateur 2026-05-22 | temporary UI path, not recoverable at import time | 1 | Proposition 4.4 farthest-neighbor |

Les fichiers PDF sont conservés dans `docs/source_materials/pdfs/`, avec hashes
dans `docs/source_materials/README.md`. Le screenshot temporaire n’a pas pu être
récupéré comme fichier, mais son contenu mathématique est documenté ici.

Commandes utilisées :

```bash
pdfinfo <file>
pdftotext -f 1 -l 1 -layout <file> -
pdftotext -layout strongly-circular-sidma-1.pdf - | grep -n "Proposition 4.4"
```

## Strong circular seriation

Le PDF `strongly-circular-sidma-1.pdf` annonce :

- un algorithme simple pour la sération circulaire stricte ;
- l’équivalence entre dissimilarités circular Robinson et pre-circular Robinson ;
- une vérification d’ordre fixé en `O(n^2)` après conditions de compatibilité.

### Proposition 4.4, interprétation pour le dépôt

Statut : source mathématique externe + prédicat expérimental ajouté.

Pour un ordre compatible circular Robinson, les paires de cordes vers des
farthest-neighbors doivent alterner, sauf une clause dégénérée en non strict :
certains endpoints peuvent eux-mêmes appartenir aux ensembles farthest opposés.
Dans le cas strict, seule l’alternance reste.

Impact sur le dépôt :

- notre ancien `passes_farthest_crossing_condition` est volontairement plus
  brut : il teste seulement l’alternance de cordes et ignore la clause
  dégénérée ;
- `passes_farthest_prop_4_4_condition` encode maintenant la version
  Proposition 4.4 comme diagnostic séparé ;
- les contre-exemples égal-distance ne réfutent pas Proposition 4.4 : ils
  réfutent seulement la version brute qui ignorait la clause dégénérée.

### Proposition 4.5 / 4.6, piste à tester

Le texte indique que, sous hypothèse quasi-circular Robinson pour l’ordre fixé,
une violation circular Robinson produit un certificat farthest du type
Proposition 4.5. Combiné avec Proposition 4.4, cela donne une vérification
quadratique d’un ordre fixé.

Impact pour le Goal :

- cela concerne le test d’un ordre donné, pas encore l’existence dans un
  PC-tree ;
- `find_farthest_prop_4_5_obstruction` et
  `passes_farthest_prop_4_5_order_test` encodent maintenant ce diagnostic ;
- première vérification expérimentale : aucun désaccord avec
  `is_precircular_order_cR` sur tous les ordres quasi-circulaires pour
  `n <= 5`, valeurs `{1,2,3}` ;
- il faut garder séparés : ordre fixé, existence dans PC-tree, universalité.

## Modules et PQ-trees

Les deux PDF sur modules Robinson/PQ-trees suggèrent une direction structurelle :
les modules et copoints peuvent compacter les ordres compatibles en linéaire.

Impact pour ce dépôt :

- analogie potentielle pour Piste B/D ;
- pas encore de transfert prouvé vers le cas circulaire PC-tree ;
- à tester seulement après avoir identifié quels ensembles jouent le rôle de
  modules/copolymères dans les ordres quasi-circulaires.

## PC-trees et circular-ones

Les PDF Hsu/McConnell et Hsu PC-vs-PQ confirment le rôle naturel des PC-trees
pour représenter les arrangements circular-ones. Ils sont pertinents pour la
Piste D : intersection entre contraintes PC-tree et contraintes d’arcs.

Impact pour ce dépôt :

- l’implémentation actuelle reste un petit scaffold, pas une implémentation
  Hsu/McConnell complète ;
- toute preuve sur le scaffold doit ensuite être reformulée pour les vrais
  PC-trees non enracinés.

## Hypercycles et dissimilarités

Le PDF Brucker/Osswald sert de contexte sur les hypercycles, les boules et les
dissimilarités. Il est surtout pertinent pour relier quasi-circularité, arcs de
boules et familles hypergraphiques.

Impact pour ce dépôt :

- utile pour Piste D et pour générateurs de boules/arcs ;
- pas encore utilisé dans un algorithme candidat.

## Prochaine action issue des sources

Priorité raisonnable :

1. Tester un prédicat d’ordre fixé inspiré Prop. 4.4/4.5 contre
   `is_precircular_order_cR` sur les ordres quasi-circulaires de petits `n`.
2. Si équivalent expérimentalement, l’utiliser seulement comme accélérateur de
   test d’ordre, pas comme solver d’existence.
3. Chercher comment cette condition se projette sur un PC-tree : CSP de quartets
   interdits ou DP par signatures de sous-frontiers.
