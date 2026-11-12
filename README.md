# Xool

> Supervision réseau intelligente pour les PME sénégalaises — surveiller, alerter, prédire.

## Démarrer aujourd'hui (30 minutes)

1. **Prérequis** : Git, Docker Desktop, Python 3.12, [uv](https://docs.astral.sh/uv/), Node 20+ et pnpm.
2. **Créer le dépôt** :
   ```bash
   cd xool
   git init && git add . && git commit -m "chore: kit de démarrage Xool"
   ```
   Puis crée un dépôt **privé** sur GitHub et pousse.
3. **Configurer** : `cp .env.example .env` puis change `DB_PASSWORD`.
4. **Lancer la base** : `docker compose up -d db`
5. **Ouvrir ta session IA** à la racine du dépôt et coller le prompt **n° 0** de `prompts/PROMPTS.md`.
6. Enchaîner les tâches de `docs/TACHES_SEMAINE_1.md`, une par session.

## Documents

| Fichier | Rôle |
|---|---|
| `CLAUDE.md` | Règles et contexte lus par l'agent à chaque session |
| `docs/BRIEF.md` | Problème, cible, proposition de valeur |
| `docs/ROADMAP.md` | Les 4 phases |
| `docs/TACHES_SEMAINE_1.md` | Tâches concrètes de la semaine |
| `docs/JOURNAL.md` | Journal de bord (mis à jour à chaque session) |
| `docs/DECISIONS.md` | Décisions d'architecture |
| `prompts/PROMPTS.md` | Prompts prêts à l'emploi |

## Origine

Mémoire de Licence SRT — Université Alioune Diop de Bambey :
« Analyse prédictive des pannes de matériels réseaux avec l'intelligence artificielle ».
