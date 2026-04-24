from typing import Protocol
from uuid import UUID


class TaskDispatcher(Protocol):
    def dispatch_irradiance_update(self, project_id: UUID, lat: float, lon: float) -> None: ...
