# Instructions pour agents

- Tu dois toujours commencer par lire `README.md`, `docs/experiment_protocol.md`, `docs/hypothesis_portfolio.md` et `docs/checkpoints.md`.
- Pour tout changement non trivial, crée ou mets à jour une entrée dans `docs/experiment_log.md`.
- Ne demande pas à l’utilisateur "quelle est la prochaine étape" si une prochaine expérience raisonnable est possible.
- Si une piste échoue deux fois de suite sans amélioration mesurable, bascule vers une autre piste du portefeuille.
- Si un contre-exemple apparaît, ajoute-le dans `tests/test_regression_counterexamples.py` ou dans un fichier JSON de régression.
- Ne supprime jamais un contre-exemple pour faire passer les tests.
- Ne modifie les tests qu’avec justification explicite dans `docs/experiment_log.md`.
- Ne confonds pas benchmark et preuve.
- Ne marque pas une solution comme "trouvée" sans `docs/proof_obligations.md` rempli.
- Chaque commit doit être un checkpoint compréhensible.
- Pour les grandes recherches, utiliser Browser Use pour interroger ChatGPT web avec GPT 5.5 Pro sur les questions très techniques, et Deep Research pour les recherches approfondies.
- State assumptions, never guess silently.
- Minimum code, nothing speculative.
- Surgical changes, do not refactor adjacent code.
- Define success, loop until verified.
- Toute commande à sortie inconnue ou potentiellement large doit être bornée, par exemple `COMMAND 2>&1 | head -c 4000` ou, pour des logs, `COMMAND 2>&1 | tail -c 4000`.
