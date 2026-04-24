from __future__ import annotations

from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session

from backend.domain.entities import Charge, Project
from backend.infrastructure.database import SessionLocal
from backend.infrastructure.mappers import ChargeMapper, ProjectMapper
from backend.infrastructure.models import ChargeORM, ProjectORM
from backend.infrastructure.pvgis import PVGISError, fetch_hourly_irradiance


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(self) -> list[Project]:
        orms = self._db.query(ProjectORM).all()
        return [ProjectMapper.to_entity(o) for o in orms]

    def get(self, project_id: UUID) -> Optional[Project]:
        orm = self._db.get(ProjectORM, project_id)
        return ProjectMapper.to_entity(orm) if orm else None

    def create(self, name: str, gps_lat: float, gps_lon: float) -> Project:
        orm = ProjectORM(name=name, gps_lat=gps_lat, gps_lon=gps_lon)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return ProjectMapper.to_entity(orm)

    def delete(self, project_id: UUID) -> bool:
        orm = self._db.get(ProjectORM, project_id)
        if not orm:
            return False
        self._db.delete(orm)
        self._db.commit()
        return True

    def update_irradiance(self, project_id: UUID, irradiance: list[float]) -> None:
        orm = self._db.get(ProjectORM, project_id)
        if orm:
            orm.hourly_irradiance = irradiance
            self._db.commit()


class ChargeRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, charge_id: UUID) -> Optional[Charge]:
        orm = self._db.get(ChargeORM, charge_id)
        return ChargeMapper.to_entity(orm) if orm else None

    def create(
        self,
        project_id: UUID,
        name: str,
        max_power_w: float,
        real_usage_rate: float,
        hourly_slots: list[dict],
    ) -> Optional[Charge]:
        if not self._db.get(ProjectORM, project_id):
            return None
        orm = ChargeORM(
            project_id=project_id,
            name=name,
            max_power_w=max_power_w,
            real_usage_rate=real_usage_rate,
            hourly_slots=hourly_slots,
        )
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return ChargeMapper.to_entity(orm)

    def update(
        self,
        charge_id: UUID,
        name: str,
        max_power_w: float,
        real_usage_rate: float,
        hourly_slots: list[dict],
    ) -> Optional[Charge]:
        orm = self._db.get(ChargeORM, charge_id, with_for_update=True)
        if not orm:
            return None
        orm.name = name
        orm.max_power_w = max_power_w
        orm.real_usage_rate = real_usage_rate
        orm.hourly_slots = hourly_slots
        self._db.commit()
        self._db.refresh(orm)
        return ChargeMapper.to_entity(orm)

    def delete(self, charge_id: UUID) -> bool:
        orm = self._db.get(ChargeORM, charge_id)
        if not orm:
            return False
        self._db.delete(orm)
        self._db.commit()
        return True


# ── Background task ───────────────────────────────────────────────────────────

def update_irradiance_background(project_id: UUID, lat: float, lon: float) -> None:
    """Ouvre sa propre session car la session HTTP est déjà fermée."""
    db = SessionLocal()
    try:
        irradiance = fetch_hourly_irradiance(lat, lon)
        ProjectRepository(db).update_irradiance(project_id, irradiance)
    except PVGISError:
        pass
    finally:
        db.close()
