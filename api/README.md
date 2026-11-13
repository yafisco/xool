# API Xool

API FastAPI qui reçoit les métriques des agents et les stocke dans PostgreSQL + TimescaleDB.

## Lancer

```bash
docker compose up -d db                      # depuis la racine du dépôt
cd api
uv sync
uv run alembic upgrade head                  # crée ou met à jour les tables
uv run uvicorn app.main:app --reload         # http://localhost:8000
```

La documentation interactive est sur http://localhost:8000/docs.

## Base de données

Le schéma est décrit dans `app/models.py`. On ne modifie jamais la base à la main : on change
les modèles, puis on crée une migration.

```bash
uv run alembic revision --autogenerate -m "description courte"   # crée la migration
uv run alembic upgrade head                                      # l'applique
uv run alembic downgrade -1                                      # annule la dernière
uv run alembic check                                             # modèles et base identiques ?
```

Toujours relire le fichier généré dans `migrations/versions/` avant de l'appliquer : Alembic ne
connaît pas TimescaleDB (hypertables) et ne voit pas tous les changements.

| Table | Contenu |
|---|---|
| `organizations` | Les clients |
| `agents` | Les programmes de collecte, avec le hash de leur clé |
| `devices` | Les équipements supervisés |
| `metrics` | Les mesures, en hypertable TimescaleDB, clé primaire `(device_id, time)` |

## Créer un agent

```bash
uv run python -m scripts.create_agent --org "Clinique Exemple" --name "serveur-accueil"
```

La clé est affichée **une seule fois**. La base ne garde que son hash SHA-256 : si la clé est
perdue, il faut créer un nouvel agent.

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
| `app/models.py` | Tables de la base (modèles SQLAlchemy) |
| `app/security.py` | Génération et hachage des clés d'agent |
| `app/main.py` | Application FastAPI et routes |
| `migrations/` | Migrations Alembic |
| `scripts/` | Outils en ligne de commande |
| `tests/` | Tests pytest |

## Tests et qualité

```bash
uv run pytest
uv run ruff check . && uv run ruff format .
```

Deux sortes de tests :

- **sans base** (`test_health.py`, `test_security.py`) : ils passent même si Docker est arrêté ;
- **avec base** (`test_schema.py`) : ils créent une base jetable `xool_test`, y appliquent les
  migrations, puis la suppriment. La base de développement n'est jamais touchée. Si Docker est
  arrêté, ces tests sont ignorés (« skipped »), pas en échec.
