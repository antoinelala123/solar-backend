# SolarDim — API

API REST de dimensionnement photovoltaïque. À partir de charges électriques décrites heure par heure et de coordonnées GPS, elle calcule le nombre de panneaux et de batteries nécessaires. L'irradiance solaire est récupérée automatiquement via l'API PVGIS de la Commission Européenne.

---

## Stack technique

| Composant        | Technologie             |
|------------------|-------------------------|
| Backend          | Python 3.11 · FastAPI   |
| Base de données  | PostgreSQL 16           |
| ORM              | SQLAlchemy              |
| Migrations       | Alembic                 |
| Conteneurisation | Docker · Docker Compose |

---

## Architecture

Le projet suit les principes de la **Clean Architecture** — les dépendances vont uniquement vers l'intérieur.

```
backend/
├── domain/           Cœur métier — modèles et calculs (aucune dépendance externe)
│   ├── models.py     Entités SQLAlchemy : Project, Charge
│   └── calculator.py Algorithme de dimensionnement solaire
│
├── application/      Orchestration — cas d'usage et accès aux données
│   └── services.py   CRUD projets/charges, simulation, appel PVGIS en background
│
├── infrastructure/   Adaptateurs vers l'extérieur
│   ├── database.py   Connexion SQLAlchemy + session
│   └── pvgis.py      Client HTTP vers l'API PVGIS
│
└── api/              Couche HTTP
    ├── main.py       Point d'entrée FastAPI, CORS, routeurs
    ├── schemas.py    Schémas Pydantic (validation I/O)
    └── routes/       Endpoints REST
        ├── projects.py
        └── charges.py
```

---

## Modèles de données

**Project**

| Champ               | Type     | Description                                           |
|---------------------|----------|-------------------------------------------------------|
| `id`                | UUID     | Clé d'accès partageable                               |
| `name`              | string   | Nom du projet                                         |
| `gps_lat`           | float    | Latitude (-90 à 90)                                   |
| `gps_lon`           | float    | Longitude (-180 à 180)                                |
| `hourly_irradiance` | JSON     | 24 valeurs W/m² moyennes par heure (rempli via PVGIS) |
| `created_at`        | datetime | Date de création                                      |

**Charge**

| Champ             | Type   | Description                              |
|-------------------|--------|------------------------------------------|
| `id`              | UUID   | Identifiant                              |
| `project_id`      | UUID   | Référence au projet                      |
| `name`            | string | Nom de l'appareil                        |
| `max_power_w`     | float  | Puissance nominale (W)                   |
| `real_usage_rate` | float  | Taux d'usage réel (0.0 → 1.0)            |
| `hourly_slots`    | JSON   | 24 créneaux `{hour, state, custom_value_w}` |

États d'un créneau : `INACTIVE` · `ACTIVE` · `CUSTOM`

---

## Endpoints

> En production (Docker), tous les endpoints sont préfixés `/api/` par nginx.
> Exemple : `GET /projects` → `http://localhost/api/projects`

### Projets

| Méthode    | URL                           | Description                                             |
|------------|-------------------------------|---------------------------------------------------------|
| `POST`     | `/projects`                   | Créer un projet (récupère l'irradiance PVGIS en arrière-plan) |
| `GET`      | `/projects`                   | Lister tous les projets                                 |
| `GET`      | `/projects/{id}`              | Récupérer un projet avec ses charges                    |
| `DELETE`   | `/projects/{id}`              | Supprimer un projet                                     |
| `GET`      | `/projects/{id}/dimensioning` | Calculer le dimensionnement                             |

### Charges

| Méthode  | URL                      | Description                    |
|----------|--------------------------|--------------------------------|
| `POST`   | `/projects/{id}/charges` | Ajouter une charge à un projet |
| `GET`    | `/charges/{id}`          | Récupérer une charge           |
| `PUT`    | `/charges/{id}`          | Mettre à jour une charge       |
| `DELETE` | `/charges/{id}`          | Supprimer une charge           |

### Dimensionnement

```
GET /projects/{id}/dimensioning
    ?panel_peak_power_wp=400    # Puissance crête d'un panneau (Wc)
    &battery_capacity_wh=200    # Capacité d'une batterie (Wh)
    &battery_dod=0.8            # Profondeur de décharge (0.0 → 1.0)
    &system_efficiency=0.85     # Rendement global du système (0.0 → 1.0)
```

Réponse :
```json
{
  "recommended_panels": 3,
  "recommended_batteries": 2,
  "daily_load_wh": 4800.0,
  "daily_solar_wh": 5100.0,
  "energy_wasted_wh_per_day": 120.0,
  "energy_deficit_wh_per_day": 0.0,
  "is_oversized": false
}
```

> `hourly_irradiance` est `null` immédiatement après la création d'un projet — l'appel PVGIS s'effectue en arrière-plan (10-30 secondes). Le dimensionnement retourne `409` tant que l'irradiance n'est pas disponible.

---

## Lancement

```bash
# Démarrer la base de données, appliquer les migrations et lancer l'API
docker compose up -d db migrate api
```

L'API est disponible sur `http://localhost/api/` (via nginx) ou directement sur `http://localhost:8000` en développement local (sans Docker frontend).

La documentation Swagger est disponible sur `http://localhost/api/docs`.

---

## Tests

```bash
# Lancer tous les tests
docker compose run --rm test

# Rebuild avant de lancer (après modification du code)
docker compose run --rm --build test
```

Les tests sont organisés par couche :
```
tests/
├── domain/       Tests du calculator (calculs purs, sans mock)
├── application/  Tests des services (DB mockée)
└── api/          Tests des routes HTTP (TestClient + services mockés)
```

---

## Développement

**Générer une migration après modification d'un modèle**
```bash
docker compose run --rm migrate alembic revision --autogenerate -m "description"
docker compose run --rm migrate
```

**Variables d'environnement**

| Variable        | Défaut                                     | Description                                |
|-----------------|--------------------------------------------|--------------------------------------------|
| `DATABASE_URL`  | `postgresql://solar:solar@db:5432/solardb` | URL de connexion PostgreSQL                |
| `CORS_ORIGINS`  | `http://localhost`                         | Origines autorisées (séparées par virgule) |
