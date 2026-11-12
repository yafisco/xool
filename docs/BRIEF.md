# Brief projet — Xool

## Le problème

Au Sénégal, les PME, écoles privées, cliniques, hôtels, cybercafés et petits fournisseurs d'accès
dépendent de leur réseau (serveurs, switchs, routeurs, points d'accès, onduleurs), mais :

- ils n'ont pas d'administrateur réseau à plein temps ;
- ils découvrent les pannes quand tout est déjà arrêté (maintenance corrective) ;
- la chaleur et les coupures de courant usent le matériel plus vite ;
- les outils existants sont soit chers (PRTG, Datadog), soit trop complexes (Zabbix, Nagios).

## La solution

Xool, un logiciel qui :

1. **surveille** automatiquement les équipements (CPU, RAM, disque, température, trafic, disponibilité) ;
2. **alerte** par WhatsApp/SMS/email quand quelque chose dérive ou tombe ;
3. **détecte** les comportements anormaux sans configuration (IA non supervisée) ;
4. **prédit** les pannes à partir de l'historique réel accumulé (IA supervisée).

## Utilisateurs cibles

| Cible | Besoin principal |
|---|---|
| PME (5–100 postes) | Savoir avant que le serveur tombe |
| Écoles privées | Réseau du labo et de l'administration disponible |
| Cliniques / pharmacies | Continuité du logiciel de gestion |
| Hôtels | Wi-Fi clients toujours fonctionnel |
| Petits FAI / WISP | Surveiller des dizaines de points d'accès |
| Prestataires informatiques | Superviser plusieurs clients depuis un seul tableau de bord |

## Proposition de valeur

> « Xool vous prévient sur WhatsApp avant que votre réseau tombe. »

- Installation en 10 minutes, sans compétence réseau avancée.
- Interface en français, pensée pour le contexte local.
- Fonctionne malgré les coupures Internet (tampon local).
- Prix adapté au marché sénégalais.

## Modèle économique (hypothèse à valider)

- **Gratuit** : 3 équipements, alertes email.
- **Pro** : abonnement mensuel par paquet d'équipements, alertes WhatsApp/SMS, historique long.
- **Prestataire** : multi-clients, marque blanche.
- **Services** : installation et audit réseau sur site (YAFABiz Digital).

## Indicateurs de succès

- Phase 1 : 1 machine supervisée en continu pendant 7 jours sans perte de données.
- Phase 2 : 3 clients pilotes reçoivent de vraies alertes utiles.
- Phase 3 : au moins 1 anomalie détectée avant une panne réelle.
- Phase 4 : modèle entraîné sur ≥ 50 pannes réelles étiquetées.

## Ce que Xool n'est pas (pour l'instant)

- Pas un outil de sécurité / détection d'intrusion.
- Pas un outil de configuration des équipements (lecture seule).
- Pas d'application mobile native (le dashboard web responsive + WhatsApp suffisent).
