# Décisions d'architecture — Xool

Format : une décision par entrée, jamais supprimée (on ajoute une nouvelle entrée qui la remplace).

---

## D001 — TimescaleDB pour les métriques

**Date** : 2026-11-12
**Contexte** : une mesure par minute et par équipement → des millions de lignes rapidement.
**Décision** : PostgreSQL + extension TimescaleDB (hypertables, agrégats continus, rétention).
**Alternatives écartées** : InfluxDB (une base de plus à maîtriser), PostgreSQL seul (requêtes lentes à terme).

## D002 — Agent avec tampon SQLite

**Date** : 2026-11-12
**Contexte** : connexions Internet instables chez les clients au Sénégal.
**Décision** : l'agent écrit chaque mesure dans une file SQLite locale et l'envoie par lots ;
suppression uniquement après réponse 2xx.
**Conséquence** : l'API doit accepter des lots et des horodatages passés.

## D003 — Pas de ML avant d'avoir des données réelles

**Date** : 2026-11-12
**Contexte** : le mémoire reposait sur un dataset Kaggle simulé.
**Décision** : phases 1–2 = supervision + journal des incidents (étiquettes). ML non supervisé en phase 3,
supervisé en phase 4 seulement.

## D004 — Python pour agent/API/ML, Next.js pour le dashboard

**Date** : 2026-11-12
**Décision** : un seul langage côté données (Python) ; le dashboard réutilise le stack web déjà maîtrisé.

## D005 — Clés d'agent hachées en SHA-256

**Date** : 2026-11-13
**Contexte** : la clé `X-Agent-Key` doit être stockée hachée, et vérifiée à chaque envoi de métriques.
**Décision** : clé aléatoire de 256 bits générée par Xool, stockée sous forme de SHA-256 (stdlib).
**Alternatives écartées** : argon2 ou bcrypt, conçus pour des mots de passe humains : lents par
conception et une dépendance de plus, sans gain pour une clé aléatoire longue.
**Conséquence** : ne jamais réutiliser `hash_agent_key` pour des mots de passe d'utilisateurs.

## D006 — Clé primaire `(device_id, time)` sur `metrics`

**Date** : 2026-11-13
**Contexte** : l'agent renvoie ses lots après une coupure (D002), donc l'API peut recevoir deux fois
la même mesure.
**Décision** : un équipement ne peut avoir qu'une mesure par instant ; la base refuse le doublon.
**Conséquence** : `POST /metrics` (T4) devra ignorer les doublons au lieu d'échouer
(`ON CONFLICT DO NOTHING`). Les identifiants des autres tables sont des entiers, plus compacts
qu'un UUID dans une table de millions de lignes.

## D007 — Configuration de l'agent dans `config.toml`

**Date** : 2026-11-13
**Contexte** : l'agent sera installé sur des postes clients, souvent sous Windows, par quelqu'un
qui n'est pas développeur.
**Décision** : un fichier `config.toml` à côté de l'agent (URL de l'API, clé, intervalle), lu avec
`tomllib` de la bibliothèque standard. Une variable d'environnement non vide remplace le fichier.
**Alternatives écartées** : un `.env` lu avec `python-dotenv`, soit une dépendance de plus à
embarquer chez le client pour un format moins naturel sur un poste Windows.
**Conséquence** : l'agent ne lit pas le `.env` racine, réservé à l'API et à Docker. `config.toml`
contient la clé : il est ignoré par Git et ne doit jamais être partagé.
