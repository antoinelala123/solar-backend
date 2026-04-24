from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime

from backend.infrastructure.mappers import ChargeMapper, ProjectMapper
from backend.domain.entities import Charge, HourlySlot, Project


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_charge_orm(**kwargs):
    orm = MagicMock()
    orm.id = kwargs.get("id", uuid4())
    orm.project_id = kwargs.get("project_id", uuid4())
    orm.name = kwargs.get("name", "Climatiseur")
    orm.max_power_w = kwargs.get("max_power_w", 1500.0)
    orm.real_usage_rate = kwargs.get("real_usage_rate", 0.8)
    orm.hourly_slots = kwargs.get(
        "hourly_slots",
        [{"hour": h, "state": "INACTIVE", "custom_value_w": None} for h in range(24)],
    )
    return orm


def make_project_orm(**kwargs):
    orm = MagicMock()
    orm.id = kwargs.get("id", uuid4())
    orm.name = kwargs.get("name", "Projet test")
    orm.gps_lat = kwargs.get("gps_lat", 48.85)
    orm.gps_lon = kwargs.get("gps_lon", 2.35)
    orm.created_at = kwargs.get("created_at", datetime(2026, 1, 1))
    orm.hourly_irradiance = kwargs.get("hourly_irradiance", None)
    orm.charges = kwargs.get("charges", [])
    return orm


# ── Tests ChargeMapper ─────────────────────────────────────────────────────────

def test_charge_mapper_retourne_une_charge():
    orm = make_charge_orm()
    result = ChargeMapper.to_entity(orm)
    assert isinstance(result, Charge)


def test_charge_mapper_copie_les_champs_scalaires():
    cid = uuid4()
    pid = uuid4()
    orm = make_charge_orm(id=cid, project_id=pid, name="Pompe", max_power_w=500.0, real_usage_rate=0.6)
    result = ChargeMapper.to_entity(orm)
    assert result.id == cid
    assert result.project_id == pid
    assert result.name == "Pompe"
    assert result.max_power_w == 500.0
    assert result.real_usage_rate == 0.6


def test_charge_mapper_convertit_24_slots():
    orm = make_charge_orm()
    result = ChargeMapper.to_entity(orm)
    assert len(result.hourly_slots) == 24
    assert all(isinstance(s, HourlySlot) for s in result.hourly_slots)


def test_charge_mapper_slot_actif():
    slots = [{"hour": h, "state": "ACTIVE" if h == 10 else "INACTIVE", "custom_value_w": None} for h in range(24)]
    orm = make_charge_orm(hourly_slots=slots)
    result = ChargeMapper.to_entity(orm)
    assert result.hourly_slots[10].state == "ACTIVE"
    assert result.hourly_slots[10].hour == 10


def test_charge_mapper_slot_custom():
    slots = [{"hour": h, "state": "CUSTOM" if h == 8 else "INACTIVE", "custom_value_w": 300.0 if h == 8 else None} for h in range(24)]
    orm = make_charge_orm(hourly_slots=slots)
    result = ChargeMapper.to_entity(orm)
    assert result.hourly_slots[8].state == "CUSTOM"
    assert result.hourly_slots[8].custom_value_w == 300.0


def test_charge_mapper_slots_vides():
    orm = make_charge_orm(hourly_slots=None)
    result = ChargeMapper.to_entity(orm)
    assert result.hourly_slots == []


# ── Tests ProjectMapper ────────────────────────────────────────────────────────

def test_project_mapper_retourne_un_project():
    orm = make_project_orm()
    result = ProjectMapper.to_entity(orm)
    assert isinstance(result, Project)


def test_project_mapper_copie_les_champs_scalaires():
    pid = uuid4()
    dt = datetime(2026, 3, 15)
    orm = make_project_orm(id=pid, name="Maison", gps_lat=43.3, gps_lon=5.4, created_at=dt)
    result = ProjectMapper.to_entity(orm)
    assert result.id == pid
    assert result.name == "Maison"
    assert result.gps_lat == 43.3
    assert result.gps_lon == 5.4
    assert result.created_at == dt


def test_project_mapper_irradiance_none():
    orm = make_project_orm(hourly_irradiance=None)
    result = ProjectMapper.to_entity(orm)
    assert result.hourly_irradiance is None


def test_project_mapper_irradiance_present():
    irr = [float(i) for i in range(24)]
    orm = make_project_orm(hourly_irradiance=irr)
    result = ProjectMapper.to_entity(orm)
    assert result.hourly_irradiance == irr


def test_project_mapper_sans_charges():
    orm = make_project_orm(charges=[])
    result = ProjectMapper.to_entity(orm)
    assert result.charges == []


def test_project_mapper_avec_charges():
    charge_orm = make_charge_orm()
    orm = make_project_orm(charges=[charge_orm])
    result = ProjectMapper.to_entity(orm)
    assert len(result.charges) == 1
    assert isinstance(result.charges[0], Charge)
