# SolarDim — Frontend

Application Angular 21 pour le dimensionnement d'installations photovoltaïques. L'interface permet de gérer des projets, de décrire des charges électriques heure par heure et d'afficher le résultat du dimensionnement sous forme de graphiques.

---

## Stack

| Composant       | Technologie                        |
|-----------------|------------------------------------|
| Framework       | Angular 21 (standalone components) |
| Rendu           | SSR activé (`@angular/ssr`)        |
| Tests           | Vitest                             |
| Serveur de prod | Nginx (via Docker)                 |

---

## Pages et routes

| Route                        | Composant                 | Description                                        |
|------------------------------|---------------------------|----------------------------------------------------|
| `/`                          | → redirect                | Redirige vers `/projects`                          |
| `/projects`                  | `ProjectListComponent`    | Liste de tous les projets                          |
| `/projects/:id`              | `ProjectDetailComponent`  | Détail d'un projet — charges et créneaux horaires  |
| `/projects/:id/dimensioning` | `DimensioningComponent`   | Résultat du dimensionnement avec graphique         |

---

## Architecture

```
src/app/
├── core/
│   ├── models/           Interfaces TypeScript (Project, Charge, DimensioningResult…)
│   └── services/         Services HTTP injectables (ProjectService, ChargeService)
│
├── features/
│   ├── projects/         Pages et composants liés aux projets
│   │   ├── project-list/           Liste des projets
│   │   ├── project-detail/         Détail projet + charges
│   │   ├── create-project-dialog/  Formulaire de création
│   │   ├── create-charge-dialog/   Formulaire d'ajout de charge
│   │   ├── custom-value-dialog/    Saisie de valeur personnalisée
│   │   └── hourly-chart/           Graphique de consommation horaire
│   │
│   └── dimensioning/     Page de résultat
│       ├── dimensioning/     Composant principal (paramètres + résultat)
│       └── energy-chart/     Graphique d'énergie
│
├── app.routes.ts         Définition des routes (lazy-loaded)
└── app.config.ts         Configuration Angular (HttpClient, Router…)
```

Les composants utilisent **Signals** pour la gestion d'état et `ChangeDetectionStrategy.OnPush`.

---

## Communication avec le backend

Tous les appels API passent par le préfixe `/api/` :

| Service           | Méthodes                                             | Endpoints appelés                                  |
|-------------------|------------------------------------------------------|----------------------------------------------------|
| `ProjectService`  | `list`, `get`, `create`, `delete`, `getDimensioning` | `/api/projects/*`                                  |
| `ChargeService`   | `create`, `update`, `delete`                         | `/api/projects/:id/charges`, `/api/charges/:id`    |

En développement local, un proxy (`proxy.conf.json`) redirige `/api/` vers `http://localhost:8000/`.
En Docker, nginx proxifie `/api/` vers le container `api`.

---

## Développement local

**Prérequis** : Node.js 20, npm.

```bash
cd frontend
npm install

# Lancer le backend en parallèle (nécessaire pour les appels API)
docker compose up -d db migrate api

# Lancer le serveur de développement (avec proxy vers l'API)
npm start          # ou : ng serve
```

L'application est accessible sur `http://localhost:4200`.

---

## Build et Docker

```bash
# Build de production (génère dist/frontend/browser/ et dist/frontend/server/)
npm run build

# Rebuild le container Docker frontend
docker compose up --build -d frontend
```

> Le build Angular avec SSR génère `index.csr.html` (et non `index.html`).
> Le `nginx.conf` est configuré en conséquence.

---

## Tests

```bash
ng test
```
