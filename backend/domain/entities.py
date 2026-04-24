from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class HourlySlot:
    hour: int
    state: str  # 'INACTIVE' | 'ACTIVE' | 'CUSTOM'
    custom_value_w: Optional[float]


@dataclass
class Charge:
    id: UUID
    project_id: UUID
    name: str
    max_power_w: float
    real_usage_rate: float
    hourly_slots: list[HourlySlot]


@dataclass
class Project:
    id: UUID
    name: str
    gps_lat: float
    gps_lon: float
    created_at: datetime
    charges: list[Charge] = field(default_factory=list)
    hourly_irradiance: Optional[list[float]] = None
