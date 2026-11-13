# CLAUDE.md — Xool

> Ce fichier est lu au début de chaque session. Il décrit le projet, les règles et la phase en cours.
> Le tenir à jour est une tâche à part entière : si une règle ou une décision change, mets-le à jour.

## 1. Le projet en une phrase

**Xool** (« regarder » en wolof) est un logiciel de supervision réseau intelligent pour les PME sénégalaises :
il surveille automatiquement les équipements (serveurs, PC, switchs, routeurs, onduleurs), prévient par
WhatsApp/SMS/email avant qu'une panne arrive, et apprend avec le temps à prédire les défaillances.

Origine : mémoire de licence SRT (UADB) « Analyse prédictive des pannes de matériels réseaux avec l'IA ».
Le mémoire utilisait un dataset Kaggle simulé (1000 lignes, Naive Bayes, ~81 %). Xool doit produire
ses **propres données réelles** — c'est le cœur du projet.

Porteur : Yafa (YAFABiz Digital), Thiès, Sénégal. Développement solo assisté par agents IA.

## 2. Phase en cours

**PHASE 1 — SUPERVISER** (voir `docs/ROADMAP.md`)
Objectif : un agent collecte les métriques d'une machine, les envoie à l'API, qui les stocke ;
le dashboard les affiche. Pas de ML dans cette phase.

Tâches actives : `docs/TACHES_SEMAINE_1.md`

⚠️ Ne pas anticiper les phases suivantes (ML, Celery, multi-tenant avancé…) sauf demande explicite.

## 3. Architecture

```
[Équipements] --SNMP/ping/agent--> [agent/ Python] --HTTPS + X-Agent-Key--> [api/ FastAPI]
                                    (tampon SQLite                              |
                                     hors connexion)                            v
                                                              [PostgreSQL + TimescaleDB]
                                                                   |            |
                                                          [web/ Next.js]   [ml/ scikit-learn]  (phase 3+)
```

## 4. Stack

| Dossier | Techno |
|---|---|
| `agent/` | Python 3.12, psutil, pysnmp, icmplib, requests, SQLite (stdlib) |
| `api/` | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async) + asyncpg, Alembic |
| base | PostgreSQL 16 + TimescaleDB (Docker) |
| `web/` | Next.js (App Router), TypeScript, Tailwind, shadcn/ui, Recharts |
| `ml/` | pandas, scikit-learn, joblib (phase 3+) |
| outils | Docker Compose, uv (Python), pnpm (JS), Ruff, pytest, Vitest, GitHub Actions |

Ne pas ajouter de nouvelle dépendance sans le dire explicitement et justifier en une ligne.

## 5. Commandes

```bash
# Infrastructure
docker compose up -d db                 # base seule
docker compose up -d                    # tout

# API
cd api && uv sync && uv run uvicorn app.main:app --reload
cd api && uv run pytest
cd api && uv run alembic upgrade head
cd api && uv run ruff check . && uv run ruff format .

# Agent
cd agent && uv sync && uv run python -m xool_agent.main
cd agent && uv run pytest

# Web
cd web && pnpm install && pnpm dev
cd web && pnpm test && pnpm lint
```

## 6. Conventions

- **Langue** : code (variables, fonctions) en **anglais** ; commentaires, docs, messages utilisateur et
  messages de commit en **français**.
- **Python** : type hints partout, fonctions courtes, Ruff (format + lint), pas de `print` dans l'API
  (utiliser `logging`).
- **TypeScript** : `strict`, pas de `any`, composants serveur par défaut.
- **API** : routes REST en kebab-case, réponses JSON, erreurs via `HTTPException` avec message clair.
- **Base** : toute modification de schéma passe par une migration Alembic. Jamais de SQL ad hoc en prod.
- **Temps** : tout en UTC (`TIMESTAMPTZ`) ; conversion Africa/Dakar uniquement à l'affichage.
- **Commits** : petits, un sujet par commit, format `type(zone): message` — ex. `feat(api): route POST /metrics`.

## 7. Définition de « terminé »

Une tâche est terminée seulement si :
1. le code fonctionne et a été lancé localement ;
2. des tests couvrent le cas nominal + au moins un cas d'erreur ;
3. `ruff check` / `pnpm lint` passent ;
4. la doc concernée est à jour (README du dossier, ce fichier si une règle change) ;
5. une entrée est ajoutée dans `docs/JOURNAL.md`.

## 8. Sécurité — règles non négociables

- Jamais de secret dans le code ni dans Git : tout passe par `.env` (voir `.env.example`) et, pour
  l'agent, par `agent/config.toml` (voir `agent/config.example.toml`, décision D007). Ces deux
  fichiers sont ignorés par Git.
- Les agents s'authentifient avec une clé (`X-Agent-Key`) stockée **hachée** en base.
- Communautés SNMP, mots de passe d'équipements clients : chiffrés en base, jamais loggés.
- Valider toutes les entrées avec Pydantic ; borner les valeurs (CPU 0–100, etc.).
- L'agent ne doit jamais exécuter de commande reçue du serveur.

## 9. Contraintes terrain (Sénégal)

- Connexion Internet du client instable → l'agent **doit** tamponner en SQLite et renvoyer plus tard.
- Coupures de courant fréquentes → l'agent redémarre proprement, sans perte ni doublon.
- Machines clientes souvent sous **Windows** → l'agent doit fonctionner sous Windows et Linux.
- Alertes : WhatsApp en priorité (phase 2).

## 10. Comment travailler avec moi (Yafa)

- Avant de coder une tâche non triviale : propose un **plan court** (fichiers touchés, étapes) et attends
  mon accord.
- Une tâche à la fois. Si tu découvres un problème hors sujet, note-le dans `docs/JOURNAL.md` (section
  « À faire plus tard ») au lieu de le corriger.
- Explique brièvement tes choix techniques : j'apprends en construisant. Exemples de code > théorie.
- Si une consigne est ambiguë, pose une question au lieu de deviner.
- Les décisions d'architecture importantes vont dans `docs/DECISIONS.md`.
