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
