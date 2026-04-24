from __future__ import annotations

from uuid import UUID

from backend.infrastructure.tasks import update_irradiance


class CeleryTaskDispatcher:
    def dispatch_irradiance_update(self, project_id: UUID, lat: float, lon: float) -> None:
        update_irradiance.delay(str(project_id), lat, lon)
