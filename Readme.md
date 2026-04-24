# SolarDim

Application web de dimensionnement d'installations photovoltaïques. L'utilisateur décrit ses charges électriques et ses coordonnées GPS ; l'application calcule le nombre de panneaux et de batteries nécessaires en s'appuyant sur les données d'irradiance solaire réelles fournies par l'API PVGIS de la Commission Européenne.

---

## Stack

| Composant        | Technologie                        |
|------------------|------------------------------------|
| Backend          | Python 3.11 · FastAPI · SQLAlchemy |
| Base de données  | PostgreSQL 16                      |
| Frontend         | Angular 21 · SSR                   |
| Reverse proxy    | Nginx                              |
| Conteneurisation | Docker · Docker Compose            |

---

## Architecture des services

```
┌─────────────────────────────────────────────┐
│  Navigateur                                 │
│  localhost/           → Angular (SPA)       │
│  localhost/api/*      → FastAPI             │
└──────────────┬──────────────────────────────┘
               │ :80
        ┌──────▼──────┐
        │   nginx     │  (frontend)
        │  port 80    │
        └──────┬──────┘
               │ proxy /api/ → :8000
        ┌──────▼──────┐      ┌──────────┐
        │   FastAPI   │──────│ Postgres │
        │  port 8000  │      │ port 5432│
        └─────────────┘      └──────────┘
```

> Le port 8000 (API) n'est pas exposé sur la machine hôte — tout passe par nginx.

---

## Démarrage rapide

**Prérequis** : Docker et Docker Compose.

```bash
# 1. Cloner le dépôt
git clone <url-du-repo> && cd solarDim

# 2. Créer le fichier d'environnement
cp .env.example .env

# 3. Lancer la stack complète (build inclus)
docker compose up --build -d

# 4. Appliquer les migrations (premier lancement)
docker compose run --rm migrate
```

| URL                           | Description           |
|-------------------------------|-----------------------|
| `http://localhost`            | Application Angular   |
| `http://localhost/api/health` | Santé de l'API        |
| `http://localhost/api/docs`   | Documentation Swagger |

---

## Structure du dépôt

```
solarDim/
├── backend/           Code source Python (Clean Architecture)
├── frontend/          Application Angular
├── tests/             Tests d'intégration
├── alembic/           Migrations de base de données
├── docker-compose.yml
├── Dockerfile         Image du backend
└── .env.example       Variables d'environnement à copier
```

Chaque sous-dossier contient son propre README détaillé.

---

## Commandes utiles

```bash
# Rebuild et redémarrer un service spécifique
docker compose up --build -d frontend
docker compose up --build -d api

# Voir les logs en temps réel
docker compose logs -f

# Lancer les tests backend
docker compose run --rm test

# Générer une migration après modification d'un modèle
docker compose run --rm migrate alembic revision --autogenerate -m "description"
docker compose run --rm migrate
```

---

## Variables d'environnement

Copier `.env.example` en `.env` et adapter si besoin.

| Variable        | Défaut                                     | Description                                              |
|-----------------|--------------------------------------------|----------------------------------------------------------|
| `DATABASE_URL`  | `postgresql://solar:solar@db:5432/solardb` | Connexion PostgreSQL                                     |
| `CORS_ORIGINS`  | `http://localhost`                         | Origines autorisées par le backend (séparées par virgule)|
