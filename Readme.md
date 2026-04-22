# SolarDim — Contexte projet

## Objectif
Exposé une API qui permette de créer un projet de dimenionnement solaire.
Cette API recupereras les donnée irradiation via PVGIS avec les coordonnées fourni par l'utilisateur et permettras de faire tout les calculs de besoins en panneaux solaires et batterie suivant les charges entrées par l'utilisateur.

## Stack
- Backend : Python + FastAPI
- BDD : PostgreSQL (Docker)
- Frontend : Angular (plus tard)
- Architecture : Clean Architecture

## Modèles
- Project[id, name, gps_lat, gps_lon, irradiance, created_at]
- Charge[id, project_id, name, max_power_w, real_usage_rate, hourly_slots(JSON)]

## Choix techniques
- UUID pour les IDs projet (pas d'authentification, l'UUID fait office de clé d'accès)
- hourly_slots : JSON de 24 slots {hour, state, custom_value_w}
- state : INACTIVE | ACTIVE | CUSTOM
- PVGIS API pour récupérer l'irradiance depuis les coordonnées GPS
- Pas de compte utilisateur, accès par UUID partageable