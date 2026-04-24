.PHONY: test test-verbose up down logs

IMAGE = python:3.11-slim
RUN   = docker run --rm -v $(PWD):/app -w /app $(IMAGE)

## Lance les tests (77 tests, aucune base de données requise)
test:
	$(RUN) bash -c "pip install -q -r requirements.txt && python3 -m pytest tests/ -q"

## Idem avec détail par test
test-verbose:
	$(RUN) bash -c "pip install -q -r requirements.txt && python3 -m pytest tests/ -v"

## Démarre toute l'application (API + DB + Frontend)
up:
	docker compose up --build -d

## Arrête l'application
down:
	docker compose down

## Affiche les logs de l'API
logs:
	docker compose logs -f api
