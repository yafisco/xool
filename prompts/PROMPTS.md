# Prompts — Xool avec Claude Fable 5.2

Copie-colle ces prompts dans ta session (Claude Code ou équivalent), depuis la racine du dépôt.
Remplace ce qui est entre `<...>`.

---

## 0. Première session (à faire une seule fois)

```
Lis CLAUDE.md, docs/BRIEF.md, docs/ROADMAP.md et docs/TACHES_SEMAINE_1.md.

Ensuite :
1. Résume en 5 lignes ce que tu as compris du projet et de la phase en cours.
2. Liste les questions ou ambiguïtés que tu vois avant de commencer.
3. Propose un plan pour la tâche T1 (fichiers à créer, commandes à lancer).

Ne code rien tant que je n'ai pas validé le plan.
```

---

## 1. Démarrer une tâche

```
Tâche : <T4 — API : POST /metrics> (voir docs/TACHES_SEMAINE_1.md).

1. Relis les critères de la tâche et le code existant concerné.
2. Propose un plan court : fichiers touchés, étapes, tests prévus.
3. Attends mon OK, puis implémente étape par étape.
4. Lance les tests et le lint, montre-moi le résultat.
5. Termine par : ce qui a été fait, comment le tester moi-même, et l'entrée à ajouter dans docs/JOURNAL.md.

Respecte CLAUDE.md (conventions, définition de « terminé », sécurité).
```

---

## 2. Comprendre le code (pour apprendre)

```
Explique-moi <api/app/routes/metrics.py> comme à un développeur junior :
- le rôle de chaque fonction,
- pourquoi ces choix (async, Pydantic, hash de la clé…),
- 2 erreurs fréquentes qu'on pourrait faire ici.
Donne des exemples de code plutôt que de la théorie.
```

---

## 3. Déboguer

```
J'ai cette erreur :

<colle l'erreur complète + la commande lancée>

1. Explique la cause probable.
2. Vérifie dans le code avant de proposer une correction.
3. Propose la correction minimale, sans toucher au reste.
4. Ajoute un test qui aurait détecté ce bug.
```

---

## 4. Revue de code avant commit

```
Fais une revue du diff actuel (git diff) comme un développeur senior exigeant :
- bugs ou cas limites oubliés,
- problèmes de sécurité (secrets, validation, injection),
- écarts avec CLAUDE.md,
- tests manquants.
Classe par gravité. Ne corrige rien, liste seulement.
```

---

## 5. Écrire les tests d'abord

```
Pour la tâche <T6 — tampon hors connexion>, écris d'abord les tests pytest qui décrivent
le comportement attendu (ils doivent échouer). Montre-les-moi. Ensuite seulement, implémente
le code pour les faire passer.
```

---

## 6. Décision d'architecture

```
Je dois choisir entre <option A> et <option B> pour <sujet>.
Compare-les pour Xool (contexte : solo, Sénégal, connexion instable, petit budget VPS) :
avantages, inconvénients, coût, complexité. Donne ta recommandation.
Si je valide, rédige l'entrée correspondante dans docs/DECISIONS.md.
```

---

## 7. Fin de session

```
On s'arrête là pour aujourd'hui.
1. Vérifie que les tests et le lint passent.
2. Ajoute une entrée dans docs/JOURNAL.md (fait / problèmes / prochaine étape).
3. Si une règle ou décision a changé, mets à jour CLAUDE.md.
4. Propose le message de commit.
```

---

## 8. Reprise après une pause

```
Je reprends le projet. Lis CLAUDE.md, les 3 dernières entrées de docs/JOURNAL.md
et git log --oneline -15. Dis-moi où on en est et quelle est la prochaine tâche.
```

---

## 9. Passer à la semaine suivante

```
La semaine 1 est terminée. À partir de docs/ROADMAP.md (Phase 1, S2) et de ce qui existe,
rédige docs/TACHES_SEMAINE_2.md au même format que TACHES_SEMAINE_1.md :
tâches numérotées, petites, avec critères vérifiables. Ne code rien.
```

---

## Règles d'or

1. **Une tâche par session.** Les sessions courtes et ciblées donnent un meilleur code.
2. **Toujours un plan avant le code** pour tout ce qui touche plus de 2 fichiers.
3. **Tu relis chaque diff.** Si tu ne comprends pas une ligne, utilise le prompt n° 2.
4. **Commit souvent.** Si l'agent part dans une mauvaise direction : `git restore .` et on recommence.
5. **Le journal est ta mémoire.** Sans `JOURNAL.md` à jour, chaque session repart de zéro.
