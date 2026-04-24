from __future__ import annotations

from uuid import UUID

from backend.infrastructure.celery_app import celery_app
from backend.infrastructure.repositories import update_irradiance_background


@celery_app.task(name="solardim.update_irradiance")
def update_irradiance(project_id: str, lat: float, lon: float) -> None:
    update_irradiance_background(UUID(project_id), lat, lon)
