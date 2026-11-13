# API Xool

API FastAPI qui reçoit les métriques des agents et les stocke dans PostgreSQL + TimescaleDB.

## Lancer

```bash
docker compose up -d db                      # depuis la racine du dépôt
cd api
uv sync
uv run uvicorn app.main:app --reload         # http://localhost:8000
```

La documentation interactive est sur http://localhost:8000/docs.

## Configuration

L'API lit le fichier `.env` **à la racine du dépôt** (voir `.env.example`). Une variable
d'environnement prime sur le fichier.

| Variable | Rôle |
|---|---|
| `DATABASE_URL` | Connexion à la base, au format `postgresql+asyncpg://user:motdepasse@hote:5432/base` |

## Routes

| Route | Réponse |
|---|---|
| `GET /health` | `200 {"status": "ok", "db": "ok"}` si la base répond |
| | `503 {"status": "degraded", "db": "error"}` si la base est injoignable |

## Organisation du code

| Fichier | Rôle |
|---|---|
| `app/config.py` | Réglages lus depuis `.env` (pydantic-settings) |
| `app/db.py` | Moteur SQLAlchemy async et dépendance `get_session` |
| `app/main.py` | Application FastAPI et routes |
| `tests/` | Tests pytest |

## Tests et qualité

```bash
uv run pytest
uv run ruff check . && uv run ruff format .
```

Les tests de `/health` remplacent la session de base par une fausse : ils passent sans Docker.
