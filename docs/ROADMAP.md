# Roadmap — Xool

Principe : chaque phase livre quelque chose d'utilisable et produit les données de la phase suivante.

## Phase 1 — Superviser (semaines 1 à 4)

- [ ] S1 : agent psutil → API FastAPI → TimescaleDB (sa propre machine)
- [ ] S1 : tampon SQLite hors connexion dans l'agent
- [ ] S2 : dashboard Next.js — liste des équipements + courbes 24 h
- [ ] S3 : ping (en ligne / hors ligne) + collecte SNMP (box, switch)
- [ ] S4 : agent packagé en `.exe` (PyInstaller) + service Windows
- [ ] S4 : déploiement Docker Compose sur un VPS

**Livrable** : 1 site réel supervisé 7 jours sans trou de données.

## Phase 2 — Alerter (semaines 5 à 8)

- [ ] Règles de seuils par équipement (CPU > 90 % pendant 10 min, température > 70 °C, hors ligne > 2 min)
- [ ] Alertes email (Resend), puis WhatsApp Cloud API, puis SMS
- [ ] Anti-spam : regroupement, délai entre deux alertes, résolution automatique
- [ ] **Journal des incidents** : chaque panne réelle est enregistrée et qualifiée (type, cause)
      → ce sont les futures étiquettes du ML
- [ ] Comptes utilisateurs + organisations (multi-clients)

**Livrable** : 3 clients pilotes, alertes utiles reçues.

## Phase 3 — Détecter les anomalies (semaines 9 à 12)

- [ ] Agrégats horaires (vues continues TimescaleDB)
- [ ] Isolation Forest par équipement, réentraîné chaque nuit
- [ ] Score de risque 0–100 affiché dans le dashboard
- [ ] Alerte « comportement inhabituel »
- [ ] Mesure : combien d'anomalies ont précédé une vraie panne ?

## Phase 4 — Prédire (mois 4 et +)

- [ ] Construction du dataset : fenêtres de 24 h avant chaque incident vs fenêtres normales
- [ ] Features : moyennes, tendances, pics, nb de redémarrages, erreurs logs
- [ ] Modèles : baseline Naive Bayes (mémoire) → Random Forest → LightGBM
- [ ] Évaluation honnête : validation temporelle, rappel sur la classe panne
- [ ] Prédiction « risque de panne dans les 48 h » + explication (importance des variables)

## Plus tard

- Console de bureau (Tauri) / installation 100 % locale
- Surveillance onduleurs (NUT), logs syslog
- Rapport mensuel PDF automatique pour le client
- Paiement Wave / Orange Money
