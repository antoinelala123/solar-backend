from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from backend.domain.calculator import compute_dimensioning
from backend.domain.entities import Charge, Project


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


# ── Projects ───────────────────────────────────────────────────────────────────

def list_projects(repo) -> list[Project]:
    return repo.list()


def get_project(repo, project_id: UUID) -> Optional[Project]:
    return repo.get(project_id)


def create_project(repo, name: str, gps_lat: float, gps_lon: float) -> Project:
    return repo.create(name, gps_lat, gps_lon)


def delete_project(repo, project_id: UUID) -> bool:
    return repo.delete(project_id)


def get_dimensioning(repo, project_id: UUID, params: DimensioningParams) -> Optional[dict]:
    project = repo.get(project_id)
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

def create_charge(repo, project_id: UUID, data: ChargeData) -> Optional[Charge]:
    return repo.create(
        project_id=project_id,
        name=data.name,
        max_power_w=data.max_power_w,
        real_usage_rate=data.real_usage_rate,
        hourly_slots=data.hourly_slots,
    )


def get_charge(repo, charge_id: UUID) -> Optional[Charge]:
    return repo.get(charge_id)


def update_charge(repo, charge_id: UUID, data: ChargeData) -> Optional[Charge]:
    return repo.update(
        charge_id=charge_id,
        name=data.name,
        max_power_w=data.max_power_w,
        real_usage_rate=data.real_usage_rate,
        hourly_slots=data.hourly_slots,
    )


def delete_charge(repo, charge_id: UUID) -> bool:
    return repo.delete(charge_id)
