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
7. `docs/tracks/README.md`

Vérifier ensuite :

```bash
git status --short --branch
make quick
```

Si `make quick` ne passe pas sur le dernier checkpoint green, corriger d’abord
le harnais ou l’environnement avant de proposer une nouvelle hypothèse.

## Mode Goal

Ce dépôt est prévu pour être repris dans un Goal long. Avant de démarrer ce
Goal, écrire explicitement :

- objectif borné ;
- critères de succès ;
- critères d’arrêt ou de bascule ;
- hypothèses qui seront testées ;
- artefacts attendus, même en cas d’échec.

Ne pas démarrer par "optimiser le solver" de façon générale. Le Goal doit viser
un résultat concret : contre-exemple minimal, sous-cas prouvé, invariant réfuté,
amélioration validée, ou preuve d’une obstruction.

## Exploration par subagents

Quand plusieurs pistes sont plausibles, l’agent principal peut lancer jusqu’à 5
subagents en parallèle. Le fanout recommandé est :

- 1 subagent sur contraintes locales P/C ;
- 1 subagent sur DP PC-tree ;
- 1 subagent sur encodage SAT/CSP ;
- 1 subagent sur génération et shrink de contre-exemples ;
- 1 subagent sur complexité ou sous-cas prouvable.

Chaque subagent doit recevoir une hypothèse distincte, un budget borné, les
fichiers à lire, les commandes autorisées et le livrable attendu. Les subagents
ne doivent pas tous essayer de faire passer la même candidate.

L’agent principal garde la responsabilité de :

- comparer les résultats ;
- détecter les contradictions ;
- intégrer seulement les changements utiles ;
- lancer les gates ;
- écrire `docs/experiment_log.md` ;
- créer le commit checkpoint.

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
3. Définir comment chercher des contre-exemples si l’hypothèse semble marcher.
4. Mettre à jour le fichier correspondant dans `docs/tracks/`.
5. Modifier le minimum de fichiers.
6. Lancer `make quick`.
7. Si vert et si le changement touche le solver, lancer
   `make hunt-counterexamples` ou une variante justifiée.
8. Si toujours vert, lancer `make bench-quick` quand le changement touche la
   complexité.
9. Ajouter une entrée à `docs/experiment_log.md`.
10. Ajouter tout contre-exemple dans les tests ou un fichier de régression.
11. Committer un checkpoint compréhensible.

La recherche de contre-exemples est un outil de compréhension, pas seulement un
test de validation. Chaque tentative sérieuse doit essayer de casser sa propre
hypothèse avec d’autres familles, d’autres seeds et des PC-trees différents.

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

## Sortie alternative du Goal courant

Le Goal actif demande une exploration beaucoup plus large avant abandon honnête :
si aucune voie valide ne reste, il faut documenter au moins 50 pistes actives ou
tentatives distinctes avant d’arrêter sur un rapport de blocage. Les règles de
bascule après deux itérations restent valables localement, mais elles ne suffisent
pas à conclure que le Goal global est bloqué.
