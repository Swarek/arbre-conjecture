# GPT 5.5 Pro global strategy review - 2026-05-23

Statut : revue externe fournie par l'utilisateur. Ce document guide les
prochaines expériences, mais ne prouve rien et ne modifie pas les gates.

## Diagnostic central

Le problème dur n'est plus le test d'un ordre fixé, mais la structure de
l'ensemble des ordres qui évitent simultanément toutes les séparations
`B_ac`. Les heuristiques actuelles capturent surtout des cas presque locaux,
presque stricts ou presque booléens. Les risques centraux restent :

- gros nœuds `P` actifs et domaines factoriels ;
- égalités non strictes ;
- corrélations de côté sur plusieurs niveaux ;
- obstructions globales sans petit témoin local.

## Hypothèses à attaquer

- Les obstructions utiles ne sont pas forcément petites.
- Un PC-tree donne une représentation compacte, pas nécessairement un domaine
  algorithmique petit.
- Les projections locales `I_x(v)` ne suffisent pas après T075.
- Farthest-neighbor seul ne capture pas les contraintes `B_ac`.
- Les témoins positifs stricts semblent saturés après T077.
- La portée CSP `<= 2` ne suffit pas si les domaines `P` sont factoriels.

## Pistes nouvelles ou réactivées

1. Reformulation par graphes de seuil et ordres round/umbrella-free.
2. Test de représentabilité PC-tree de l'ensemble des ordres cR.
3. Phase transition du cas star/single `P`.
4. Encodage SAT par chirotope cyclique.
5. Minage d'obstructions ordinales minimales.
6. Instances localement satisfiables mais globalement impossibles.
7. Route proper circular-arc par seuil.
8. Intersection de `T` avec des structures de seuil.
9. Compression des branches `P` par types actifs.
10. DP avec relation résiduelle sur séparateur.
11. Paramètre active P-degree.
12. Paramètre nombre de niveaux de distance.
13. Couverture par perturbations strictes.
14. Décomposition modulaire de la dissimilarité.
15. Comparaison Kalmanson / circular Robinson.
16. Sous-cas métrique, ultramétrique et tree metric.
17. Hardness par cyclic ordering avec ancres.
18. Hardness par betweenness linéaire avec sentinelles.
19. Hardness par simultaneous PQ-ordering.
20. Construction promise-aware où `T` vient de `D`.
21. Générateur correlation ladder multi-niveaux.
22. Paysage de flips des frontiers.
23. Branch-and-cut exact avec certificats.
24. Sous-cas `max |B_ac| <= 2`.

## Top 5 recommandé

1. `threshold_roundness.py` / clean-side : prouver ou réfuter l'équivalence
   fixed-order entre cR, bad-side et seuils.
2. `learn_cr_pc_tree.py` : tester si les ordres cR d'une matrice forment une
   famille PC-tree.
3. `star_phase_transition.py` : isoler la difficulté du cas star.
4. `high_girth_obstructions.py` : chercher des obstructions globales sans petit
   témoin.
5. `branch_type_compression.py` : compresser les nœuds `P` par activité réelle.

## Décision de routage

T078 démarre par la reformulation seuil/clean-side, car elle est la plus courte
à falsifier et peut devenir une brique de preuve pour les pistes D/E. Les autres
pistes restent actives et doivent être lancées si T078 ne donne qu'une
réécriture fixed-order sans levier PC-tree.
