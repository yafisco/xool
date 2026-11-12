# Tâches — Semaine 1

Objectif de la semaine : **ta propre machine envoie ses métriques toutes les 60 s et tu les vois en base.**

Fais-les dans l'ordre. Une tâche = une session avec l'agent = un ou plusieurs petits commits.

---

## T1 — Initialiser le dépôt

- Arborescence `agent/`, `api/`, `web/`, `ml/`, `docs/`
- `uv init` dans `agent/` et `api/` ; Ruff configuré dans les deux `pyproject.toml`
- `docker-compose.yml` avec le service `db` (TimescaleDB) qui démarre
- `.gitignore`, `.env.example`, README racine

**Critères** : `docker compose up -d db` fonctionne ; `uv run ruff check .` passe dans `api/` et `agent/`.

---

## T2 — API : squelette FastAPI + santé

- `api/app/main.py` avec `GET /health` → `{"status": "ok", "db": "ok"}` (vérifie la connexion à la base)
- Config via `pydantic-settings` lisant `.env`
- Connexion SQLAlchemy async (asyncpg)
- Test pytest de `/health`

**Critères** : `curl localhost:8000/health` répond ; `uv run pytest` passe.

---

## T3 — Base : schéma initial + migration

- Alembic initialisé
- Tables :
  - `organizations` (id, name, created_at)
  - `agents` (id, organization_id, name, key_hash, last_seen_at, created_at)
  - `devices` (id, organization_id, agent_id, name, kind, ip, created_at) — `kind` : server, pc, switch, router, ap, ups
  - `metrics` (time, device_id, cpu, ram, disk, temperature, uptime_h, online) → **hypertable** TimescaleDB
- Script `api/scripts/create_agent.py` qui crée une organisation + un agent et **affiche la clé une seule fois**
  (la base ne stocke que le hash)

**Critères** : `alembic upgrade head` crée tout ; `metrics` est une hypertable ; le script affiche une clé.

---

## T4 — API : `POST /metrics`

- Reçoit une **liste** de mesures (envoi par lots)
- Auth par header `X-Agent-Key` (comparaison du hash)
- Crée le `device` automatiquement s'il est inconnu pour cet agent (par nom d'hôte)
- Validation Pydantic (CPU/RAM/disque 0–100, horodatage requis)
- Met à jour `agents.last_seen_at`
- Tests : lot valide (201), clé invalide (401), valeur hors bornes (422)

**Critères** : les 3 tests passent ; des lignes apparaissent dans `metrics`.

---

## T5 — Agent : collecte + envoi

- `xool_agent/collect.py` : CPU, RAM, disque, température (si dispo), uptime
- `xool_agent/config.py` : URL de l'API, clé, intervalle (60 s par défaut) via `.env` ou `config.toml`
- `xool_agent/main.py` : boucle collecte → envoi ; logs propres ; arrêt propre sur Ctrl+C
- Fonctionne sous **Windows et Linux**
- Tests : `collect()` renvoie les bonnes clés et des valeurs dans les bornes

**Critères** : l'agent tourne 30 min et 30 lignes apparaissent en base.

---

## T6 — Agent : tampon hors connexion

- `xool_agent/buffer.py` : SQLite ; chaque mesure va d'abord dans la file, puis la file est vidée par lots
- Si l'API est injoignable : on garde, on réessaie au tour suivant
- Suppression seulement après réponse 2xx (pas de perte, pas de doublon)
- Limite de taille de la file (ex. 7 jours de mesures) pour ne pas remplir le disque
- Tests : API coupée → les mesures restent ; API revenue → la file se vide

**Critères** : tu coupes l'API 10 min, tu la relances, aucune minute ne manque en base.

---

## T7 — Bilan de semaine

- Requête SQL : moyennes horaires CPU/RAM de ta machine sur 24 h
- Mise à jour de `docs/JOURNAL.md` et de la section « Phase en cours » de `CLAUDE.md`
- Liste des points à améliorer pour la semaine 2
