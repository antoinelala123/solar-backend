import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime

from backend.application.services import (
    create_project, get_project, list_projects, delete_project,
    create_charge, get_charge, update_charge, delete_charge,
    get_dimensioning,
    ChargeData, DimensioningParams,
)
from backend.domain.entities import Charge, HourlySlot, Project
from backend.infrastructure.pvgis import PVGISError
from backend.infrastructure.repositories import update_irradiance_background


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_repo():
    return MagicMock()


def make_24_slots(state: str = "INACTIVE") -> list[dict]:
    return [{"hour": h, "state": state, "custom_value_w": None} for h in range(24)]


def make_charge_data(**kwargs) -> ChargeData:
    defaults = {
        "name": "Climatiseur",
        "max_power_w": 1500.0,
        "real_usage_rate": 0.8,
        "hourly_slots": make_24_slots(),
    }
    return ChargeData(**{**defaults, **kwargs})


def make_fake_project(**kwargs) -> Project:
    defaults = {
        "id": uuid4(),
        "name": "Projet test",
        "gps_lat": 48.85,
        "gps_lon": 2.35,
        "created_at": datetime(2026, 1, 1),
        "charges": [],
        "hourly_irradiance": None,
    }
    return Project(**{**defaults, **kwargs})


def make_params(**kwargs) -> DimensioningParams:
    defaults = {
        "panel_peak_power_wp": 400.0,
        "battery_capacity_wh": 200.0,
        "battery_dod": 0.8,
        "system_efficiency": 0.8,
    }
    return DimensioningParams(**{**defaults, **kwargs})


# ── Tests create_project ───────────────────────────────────────────────────────

def test_create_project_appelle_repo_create():
    repo = make_repo()
    create_project(repo, "Test", 48.85, 2.35)
    repo.create.assert_called_once_with("Test", 48.85, 2.35)


def test_create_project_retourne_le_projet():
    repo = make_repo()
    repo.create.return_value = make_fake_project()
    result = create_project(repo, "Test", 48.85, 2.35)
    assert result is not None


# ── Tests get_project ──────────────────────────────────────────────────────────

def test_get_project_retourne_le_projet_si_trouve():
    repo = make_repo()
    fake = make_fake_project()
    repo.get.return_value = fake
    assert get_project(repo, fake.id) is fake


def test_get_project_retourne_none_si_absent():
    repo = make_repo()
    repo.get.return_value = None
    assert get_project(repo, uuid4()) is None


# ── Tests list_projects ────────────────────────────────────────────────────────

def test_list_projects_retourne_tous_les_projets():
    repo = make_repo()
    fake_list = [make_fake_project(), make_fake_project()]
    repo.list.return_value = fake_list
    assert list_projects(repo) == fake_list


# ── Tests delete_project ───────────────────────────────────────────────────────

def test_delete_project_retourne_true():
    repo = make_repo()
    repo.delete.return_value = True
    assert delete_project(repo, uuid4()) is True
    repo.delete.assert_called_once()


def test_delete_project_retourne_false_si_absent():
    repo = make_repo()
    repo.delete.return_value = False
    assert delete_project(repo, uuid4()) is False


# ── Tests create_charge ────────────────────────────────────────────────────────

def test_create_charge_retourne_none_si_projet_absent():
    repo = make_repo()
    repo.create.return_value = None
    assert create_charge(repo, uuid4(), make_charge_data()) is None


def test_create_charge_appelle_repo_create():
    repo = make_repo()
    pid = uuid4()
    data = make_charge_data()
    create_charge(repo, pid, data)
    repo.create.assert_called_once_with(
        project_id=pid,
        name=data.name,
        max_power_w=data.max_power_w,
        real_usage_rate=data.real_usage_rate,
        hourly_slots=data.hourly_slots,
    )


# ── Tests get_charge / update_charge / delete_charge ──────────────────────────

def test_get_charge_delègue_au_repo():
    repo = make_repo()
    cid = uuid4()
    get_charge(repo, cid)
    repo.get.assert_called_once_with(cid)


def test_update_charge_delègue_au_repo():
    repo = make_repo()
    cid = uuid4()
    data = make_charge_data(name="Pompe", max_power_w=500.0)
    update_charge(repo, cid, data)
    repo.update.assert_called_once_with(
        charge_id=cid,
        name="Pompe",
        max_power_w=500.0,
        real_usage_rate=data.real_usage_rate,
        hourly_slots=data.hourly_slots,
    )


def test_delete_charge_retourne_false_si_absent():
    repo = make_repo()
    repo.delete.return_value = False
    assert delete_charge(repo, uuid4()) is False


# ── Tests get_dimensioning ─────────────────────────────────────────────────────

def test_get_dimensioning_retourne_none_si_projet_absent():
    repo = make_repo()
    repo.get.return_value = None
    assert get_dimensioning(repo, uuid4(), make_params()) is None


def test_get_dimensioning_leve_valueerror_si_irradiance_absente():
    repo = make_repo()
    repo.get.return_value = make_fake_project(hourly_irradiance=None)
    with pytest.raises(ValueError, match="irradiance"):
        get_dimensioning(repo, uuid4(), make_params())


def test_get_dimensioning_retourne_un_dict_avec_les_bons_champs():
    repo = make_repo()
    repo.get.return_value = make_fake_project(hourly_irradiance=[100.0] * 24, charges=[])
    result = get_dimensioning(repo, uuid4(), make_params())
    assert isinstance(result, dict)
    assert "recommended_panels" in result
    assert "recommended_batteries" in result


# ── Tests update_irradiance_background ────────────────────────────────────────

def test_update_irradiance_background_met_a_jour_le_projet():
    pid = uuid4()
    fake_irradiance = [float(i) for i in range(24)]

    with patch("backend.infrastructure.repositories.SessionLocal") as mock_session_cls, \
         patch("backend.infrastructure.repositories.fetch_hourly_irradiance", return_value=fake_irradiance), \
         patch("backend.infrastructure.repositories.ProjectRepository") as mock_repo_cls:
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        update_irradiance_background(pid, 48.85, 2.35)

        mock_repo.update_irradiance.assert_called_once_with(pid, fake_irradiance)
        mock_db.close.assert_called_once()


def test_update_irradiance_background_ne_plante_pas_si_pvgis_echoue():
    pid = uuid4()
    with patch("backend.infrastructure.repositories.SessionLocal") as mock_session_cls, \
         patch("backend.infrastructure.repositories.fetch_hourly_irradiance", side_effect=PVGISError("timeout")):
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        update_irradiance_background(pid, 48.85, 2.35)

        mock_db.close.assert_called_once()


def test_update_irradiance_background_ne_plante_pas_si_projet_supprime():
    pid = uuid4()
    with patch("backend.infrastructure.repositories.SessionLocal") as mock_session_cls, \
         patch("backend.infrastructure.repositories.fetch_hourly_irradiance", return_value=[0.0] * 24), \
         patch("backend.infrastructure.repositories.ProjectRepository") as mock_repo_cls:
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_repo = MagicMock()
        mock_repo.update_irradiance.return_value = None  # projet introuvable → no-op dans le repo
        mock_repo_cls.return_value = mock_repo

        update_irradiance_background(pid, 48.85, 2.35)

        mock_db.close.assert_called_once()
