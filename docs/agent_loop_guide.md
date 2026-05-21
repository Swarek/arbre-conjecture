# Agent loop guide

Ce guide est le mode d’emploi court pour reprendre le dépôt après le setup
initial. Il ne remplace pas `docs/experiment_protocol.md`,
`docs/hypothesis_portfolio.md` ni `docs/proof_obligations.md`.

## Démarrage obligatoire

Lire dans cet ordre :

1. `README.md`
2. `docs/experiment_protocol.md`
3. `docs/hypothesis_portfolio.md`
4. `docs/checkpoints.md`
5. `docs/proof_obligations.md`
6. `docs/experiment_log.md`

Vérifier ensuite :

```bash
git status --short --branch
make quick
```

Si `make quick` ne passe pas sur le dernier checkpoint green, corriger d’abord
le harnais ou l’environnement avant de proposer une nouvelle hypothèse.

## Rôle des tailles de benchmark

`make bench-quick` utilise 8 tailles :

```text
4,5,6,8,10,12,16,20
```

Ces tailles suffisent pour une boucle rapide : elles couvrent les petits cas
exacts, le passage au placeholder grande taille, et une première tendance.

`make bench` utilise davantage de tailles :

```text
4,5,6,8,10,12,16,20,30,40,60,80,100
```

Cette version sert aux checkpoints plus sérieux et à observer l’évolution. Si un
futur algorithme prétend être général, il doit passer `make check` et produire un
benchmark fort lisible, avec timeouts et runs incomplets visibles.

## Boucle d’expérience

Pour chaque tentative non triviale :

1. Choisir une piste active dans `docs/hypothesis_portfolio.md`.
2. Écrire l’hypothèse testée avant de coder.
3. Modifier le minimum de fichiers.
4. Lancer `make quick`.
5. Si vert, lancer `make bench-quick` quand le changement touche le solver.
6. Ajouter une entrée à `docs/experiment_log.md`.
7. Ajouter tout contre-exemple dans les tests ou un fichier de régression.
8. Committer un checkpoint compréhensible.

## Décisions

Continuer une piste si elle produit au moins un des résultats suivants :

- meilleur benchmark sans perte de correction ;
- preuve partielle ;
- invariant plus net ;
- nouveau contre-exemple ;
- sous-cas polynomial mieux défini.

Changer de piste après deux itérations sans amélioration mesurable.

Rollback seulement depuis un checkpoint green, après avoir noté la régression
dans `docs/experiment_log.md`.

## Séparation des statuts

Toujours écrire explicitement si un résultat est :

- théorème prouvé ;
- conséquence directe ;
- conjecture ;
- preuve expérimentale ;
- intuition.

Un solver qui passe tous les tests n’est pas une solution tant que
`docs/proof_obligations.md` n’est pas rempli.
