from pydantic import BaseModel, UUID4, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class SlotState(str, Enum):
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    CUSTOM = "CUSTOM"


class HourlySlot(BaseModel):
    hour: int                          # 0 à 23
    state: SlotState
    custom_value_w: Optional[float] = None  # utilisé seulement si state == CUSTOM

    @field_validator("hour")
    @classmethod
    def hour_in_range(cls, v: int) -> int:
        if not 0 <= v <= 23:
            raise ValueError("hour doit être entre 0 et 23")
        return v

    @field_validator("custom_value_w")
    @classmethod
    def custom_value_required_when_custom(cls, v, info):
        # On ne peut pas valider inter-champs facilement ici ; la vérif métier
        # sera dans le service. Le champ reste optionnel au niveau schéma.
        return v


# ── Charges ────────────────────────────────────────────────────────────────────

class ChargeCreate(BaseModel):
    name: str
    max_power_w: float
    real_usage_rate: float             # 0.0 → 1.0
    hourly_slots: list[HourlySlot]

    @field_validator("real_usage_rate")
    @classmethod
    def rate_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("real_usage_rate doit être entre 0.0 et 1.0")
        return v

    @field_validator("hourly_slots")
    @classmethod
    def exactly_24_slots(cls, v: list) -> list:
        if len(v) != 24:
            raise ValueError("hourly_slots doit contenir exactement 24 créneaux")
        hours = [s.hour for s in v]
        if sorted(hours) != list(range(24)):
            raise ValueError("hourly_slots doit couvrir les heures 0 à 23 sans doublon")
        return v


class ChargeRead(BaseModel):
    id: UUID4
    project_id: UUID4
    name: str
    max_power_w: float
    real_usage_rate: float
    hourly_slots: list[HourlySlot]

    model_config = {"from_attributes": True}  # permet de lire depuis un objet SQLAlchemy


# ── Projects ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    gps_lat: float
    gps_lon: float

    @field_validator("gps_lat")
    @classmethod
    def lat_in_range(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("gps_lat doit être entre -90 et 90")
        return v

    @field_validator("gps_lon")
    @classmethod
    def lon_in_range(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("gps_lon doit être entre -180 et 180")
        return v


# ── Dimensioning ───────────────────────────────────────────────────────────────

class DimensioningParams(BaseModel):
    panel_peak_power_wp: float     # Puissance crête d'un panneau (Wc)
    battery_capacity_wh: float     # Capacité d'une batterie (Wh)
    battery_dod: float             # Depth of discharge 0.0 → 1.0
    system_efficiency: float        # Rendement global de l'installation 0.0 → 1.0

    @field_validator("panel_peak_power_wp", "battery_capacity_wh")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("doit être strictement positif")
        return v

    @field_validator("battery_dod", "system_efficiency")
    @classmethod
    def dod_in_range(cls, v: float) -> float:
        if not 0.0 < v <= 1.0:
            raise ValueError("doit être entre 0.0 (exclu) et 1.0")
        return v


class DimensioningResult(BaseModel):
    recommended_panels: int
    recommended_batteries: int
    daily_load_wh: float           # Consommation journalière totale
    daily_solar_wh: float          # Production solaire journalière avec le dimensionnement
    energy_wasted_wh_per_day: float  # Énergie perdue (batterie pleine) en régime établi
    energy_deficit_wh_per_day: float # Énergie manquante (batterie vide) en régime établi
    is_oversized: bool             # Vrai si > 15% de la production est perdue


class ProjectRead(BaseModel):
    id: UUID4
    name: str
    gps_lat: float
    gps_lon: float
    hourly_irradiance: Optional[list[float]]  # 24 valeurs W/m², None tant que PVGIS n'a pas répondu
    created_at: datetime
    charges: list[ChargeRead] = []

    model_config = {"from_attributes": True}
