# Journal de développement — Xool

Une entrée par session, la plus récente en haut.

---

## 2026-11-12 — Initialisation du dépôt

**Tâche** : T1 (en cours, il reste la vérification de la base)
**Fait** :
- Installation de uv 0.13.8 et de Python 3.12.16 (géré par uv)
- `git init` sur la branche `main`
- `uv init` dans `api/` et `agent/`, Ruff configuré (ligne de 100, règles E, W, F, I, UP, B, SIM)
- Paquets vides `api/app/` et `agent/xool_agent/` (disposition à plat, sans dossier `src/`)
- `.env` créé à partir de `.env.example` avec des secrets aléatoires
- Roadmap corrigée : le tampon SQLite est en S1 (cohérent avec T6)
- `uv run ruff check .` et `ruff format --check .` passent dans `api/` et `agent/`

**Problèmes rencontrés** :
- Python, uv et Docker absents de la machine au départ
- Le projet est sur `Y:` et le cache uv sur `C:` : uv ne peut pas faire de liens physiques,
  d'où `link-mode = "copy"` dans les `pyproject.toml`
- Connexion lente : le téléchargement de Docker Desktop dure plus de 30 minutes

**Prochaine étape** :
- Finir l'installation de Docker Desktop, puis vérifier `docker compose up -d db` (critère restant de T1)
- Créer le dépôt GitHub privé et pousser
- T2 : squelette FastAPI + `GET /health`

---

## AAAA-MM-JJ — <titre de la session>

**Tâche** : T?
**Fait** :
- ...

**Problèmes rencontrés** :
- ...

**Prochaine étape** :
- ...

---

## À faire plus tard

- (idées et problèmes hors sujet notés pendant les sessions)
