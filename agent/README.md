# Agent Xool

Petit programme installé sur une machine à surveiller. Toutes les 60 secondes, il mesure l'état
de la machine (CPU, RAM, disque, température, durée depuis le démarrage) et l'envoie à l'API Xool.

Il fonctionne sous Windows et Linux.

## Lancer

```bash
cd agent
uv sync
cp config.example.toml config.toml      # puis remplir agent_key
uv run python -m xool_agent.main        # Ctrl+C pour arrêter
```

L'API doit tourner (voir `api/README.md`) et l'agent doit avoir été créé :

```bash
cd api
uv run python -m scripts.create_agent --org "Clinique Exemple" --name "serveur-accueil"
```

La clé affichée va dans `agent_key`. Elle n'est montrée qu'une fois.

## Configuration

Fichier `config.toml`, à côté du dossier `xool_agent/`. Il contient une clé secrète : il est
ignoré par Git.

| Réglage | Variable d'environnement | Rôle |
|---|---|---|
| `api_url` | `XOOL_API_URL` | Adresse de l'API, en `http://` ou `https://`. Obligatoire |
| `agent_key` | `XOOL_AGENT_KEY` | Clé de l'agent. Obligatoire |
| `interval_seconds` | `XOOL_INTERVAL_SECONDS` | Secondes entre deux mesures, de 5 à 3600 (60 par défaut) |

Une variable d'environnement non vide remplace la valeur du fichier. L'agent refuse de démarrer
si un réglage manque, est invalide, ou porte un nom inconnu (faute de frappe).

Hors essais locaux, `api_url` doit être en `https://` : en `http://`, la clé circule en clair
sur le réseau. L'agent l'écrit dans ses logs au démarrage.

## Ce qui est mesuré

| Champ | Source | Remarque |
|---|---|---|
| `hostname` | nom de la machine | L'API crée l'équipement au premier envoi |
| `time` | horloge de la machine | En UTC, à la seconde |
| `cpu` | `psutil.cpu_percent` | Moyenne depuis la mesure précédente, pas un instantané |
| `ram` | `psutil.virtual_memory` | Pourcentage utilisé |
| `disk` | `psutil.disk_usage` | Disque système seulement (`C:\` ou `/`) |
| `temperature` | `psutil.sensors_temperatures` | Linux seulement. Vide sous Windows |
| `uptime_h` | `psutil.boot_time` | Heures depuis le démarrage |
| `online` | toujours `true` | Une machine qui répond est en ligne |

## Comportement en cas de problème

| Situation | Ce que fait l'agent |
|---|---|
| API injoignable ou muette | Il l'écrit dans les logs et réessaie au tour suivant |
| Clé refusée (401) | Erreur dans les logs, il continue de tourner |
| Lot refusé (422, 500) | Avertissement avec le début de la réponse |
| Erreur pendant la collecte | L'erreur est loggée, l'agent continue |
| Ctrl+C ou arrêt du système | Arrêt propre, code de sortie 0 |
| Configuration invalide | Message clair, code de sortie 2 |

**Limite actuelle** : une mesure qui n'a pas pu être envoyée est perdue. Le tampon SQLite
(tâche T6) la gardera pour la renvoyer plus tard.

## Sécurité

- La clé n'est jamais écrite dans les logs.
- L'agent ne suit pas les redirections : la clé ne part que vers `api_url`.
- L'agent n'exécute rien de ce que l'API lui répond. Il lit le code HTTP, c'est tout.

## Organisation du code

| Fichier | Rôle |
|---|---|
| `xool_agent/config.py` | Lecture et validation de la configuration |
| `xool_agent/collect.py` | Mesure de la machine avec psutil |
| `xool_agent/client.py` | Envoi d'un lot à `POST /metrics` |
| `xool_agent/main.py` | Boucle collecte, envoi, attente |
| `tests/` | Tests pytest, sans réseau |

## Tests et qualité

```bash
uv run pytest
uv run ruff check . && uv run ruff format .
```

Les tests n'ont besoin ni de l'API ni de Docker : l'envoi est remplacé par une fausse session
HTTP, et le temps par une fausse horloge.
