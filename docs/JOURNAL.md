# Journal de développement — Xool

Une entrée par session, la plus récente en haut.

---

## 2026-11-13 — Squelette de l'API et route /health

**Tâche** : T1 terminée (Docker et base vérifiés), T2 terminée
**Fait** :
- Docker Desktop 4.99.0 installé sur `Y:\Docker\Desktop`, données dans `Y:\Docker\wsl` ; WSL mis à jour en 3.0.5
- `docker compose up -d db` fonctionne : PostgreSQL 16.15 + TimescaleDB 2.32.0, état « healthy »
- `curl localhost:8000/health` répond `{"status":"ok","db":"ok"}` avec la vraie base
- `DATABASE_URL` pointe sur `127.0.0.1` au lieu de `localhost` (voir les problèmes)
- Dépendances de l'API : fastapi, uvicorn, pydantic-settings, sqlalchemy (async), asyncpg ;
  pytest et httpx pour les tests
- `app/config.py` : réglages lus depuis le `.env` racine
- `app/db.py` : moteur async créé au premier appel, dépendance `get_session`
- `app/main.py` : `GET /health` répond 200 si la base accepte un `SELECT 1`, 503 sinon
- 3 tests avec une fausse session (cas nominal, erreur SQLAlchemy, connexion refusée)
- Vérification réelle du 503 : API lancée sans base, `/health` répond `{"status":"degraded","db":"error"}`
- `api/README.md` créé

**Problèmes rencontrés** :
- Docker toujours absent en début de session, et C: n'a que 6,5 Go libres : décision d'installer
  Docker Desktop et ses données sur Y:
- WSL était à la version d'origine de Windows, alors que Docker Desktop exige WSL 2.1.5 ou plus ;
  la mise à jour demande les droits administrateur
- Premier essai d'installation de Docker en échec : « not enough disk space ». Le contrôle d'espace
  porte sur le disque du dossier temporaire (C:), pas sur le disque d'installation. Corrigé en
  pointant `TEMP` vers Y: pour l'installeur
- Malgré l'installation sur Y:, C: a perdu environ 1 Go (reste 3,4 Go)
- `/health` répondait 503 après 60 s alors que la base tournait : sous Windows, `localhost` est
  d'abord traduit en `::1` (IPv6), et sur cette adresse un relais de WSL accepte la connexion sans
  jamais répondre. En `127.0.0.1` (IPv4) la base répond en 0,15 s
- asyncpg laisse remonter un refus de connexion en `OSError` brut, pas en erreur SQLAlchemy :
  `/health` attrape les deux

**Prochaine étape** :
- Pousser sur GitHub une fois la visibilité du dépôt décidée
- T3 : Alembic et schéma initial

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
- Starlette signale que `httpx` est déprécié pour `TestClient` et recommande `httpx2`. Les tests
  passent. À vérifier (origine et fiabilité du paquet) avant de changer de dépendance.
- `AGENTS.md` est une copie de `CLAUDE.md` non suivie par Git : décider s'il faut la garder, et
  comment éviter que les deux fichiers divergent.
- C: n'a plus que 3,4 Go libres après l'installation de Docker (le dossier temporaire de
  l'utilisateur pèse environ 3 Go). Faire du ménage.
- `/health` met 60 s à répondre 503 quand la base accepte la connexion sans répondre (délai par
  défaut d'asyncpg). Ajouter un délai de connexion court (5 s) dans `app/db.py`.
- Au tout premier démarrage, le conteneur `db` passe « healthy » pendant l'initialisation, avant
  que la base accepte les connexions TCP. Sans effet ensuite, à garder en tête pour la CI.
