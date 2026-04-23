from dataclasses import dataclass
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session


@dataclass
class ProjectData:
    name: str
    gps_lat: float
    gps_lon: float


@dataclass
class ChargeData:
    name: str
    max_power_w: float
    real_usage_rate: float
    hourly_slots: list[dict]


@dataclass
class DimensioningParams:
    panel_peak_power_wp: float
    battery_capacity_wh: float
    battery_dod: float
    system_efficiency: float

from backend.domain.models import Project, Charge
from backend.infrastructure.database import SessionLocal
from backend.infrastructure.pvgis import fetch_hourly_irradiance, PVGISError
from backend.domain.calculator import compute_dimensioning


# ── Background task ────────────────────────────────────────────────────────────

def _update_irradiance(project_id: UUID, lat: float, lon: float) -> None:
    """
    Appelé en arrière-plan après la création d'un projet.
    Ouvre sa propre session DB car la session HTTP est déjà fermée.
    """
    db = SessionLocal()
    try:
        irradiance = fetch_hourly_irradiance(lat, lon)
        project = db.get(Project, project_id)
        if project:
            project.hourly_irradiance = irradiance
            db.commit()
    except PVGISError:
        pass  # hourly_irradiance reste null, le client peut réessayer via GET
    finally:
        db.close()


# ── Projects ───────────────────────────────────────────────────────────────────

def create_project(
    db: Session, data: ProjectData, background_tasks: BackgroundTasks
) -> Project:
    project = Project(name=data.name, gps_lat=data.gps_lat, gps_lon=data.gps_lon)
    db.add(project)
    db.commit()
    db.refresh(project)
    background_tasks.add_task(_update_irradiance, project.id, data.gps_lat, data.gps_lon)
    return project


def get_project(db: Session, project_id: UUID) -> Project | None:
    return db.get(Project, project_id)


def list_projects(db: Session) -> list[Project]:
    return db.query(Project).all()


def delete_project(db: Session, project_id: UUID) -> bool:
    project = db.get(Project, project_id)
    if not project:
        return False
    db.delete(project)
    db.commit()
    return True


def get_dimensioning(
    db: Session, project_id: UUID, params: DimensioningParams
) -> dict | None:
    project = db.get(Project, project_id)
    if not project:
        return None
    if not project.hourly_irradiance:
        raise ValueError("L'irradiance du projet n'est pas encore disponible (PVGIS en cours)")
    return compute_dimensioning(
        project.charges,
        project.hourly_irradiance,
        params.panel_peak_power_wp,
        params.battery_capacity_wh,
        params.battery_dod,
        params.system_efficiency,
    )

# ── Charges ────────────────────────────────────────────────────────────────────

def create_charge(db: Session, project_id: UUID, data: ChargeData) -> Charge | None:
    if not db.get(Project, project_id):
        return None
    charge = Charge(
        project_id=project_id,
        name=data.name,
        max_power_w=data.max_power_w,
        real_usage_rate=data.real_usage_rate,
        hourly_slots=data.hourly_slots,
    )
    db.add(charge)
    db.commit()
    db.refresh(charge)
    return charge


def get_charge(db: Session, charge_id: UUID) -> Charge | None:
    return db.get(Charge, charge_id)


def update_charge(db: Session, charge_id: UUID, data: ChargeData) -> Charge | None:
    charge = db.get(Charge, charge_id, with_for_update=True)
    if not charge:
        return None
    charge.name = data.name
    charge.max_power_w = data.max_power_w
    charge.real_usage_rate = data.real_usage_rate
    charge.hourly_slots = data.hourly_slots
    db.commit()
    db.refresh(charge)
    return charge


def delete_charge(db: Session, charge_id: UUID) -> bool:
    charge = db.get(Charge, charge_id)
    if not charge:
        return False
    db.delete(charge)
    db.commit()
    return True
