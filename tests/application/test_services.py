import pytest
from unittest.mock import MagicMock, patch, call
from uuid import uuid4

from fastapi import BackgroundTasks

from app.application.services import (
    create_project, get_project, list_projects, delete_project,
    create_charge, get_charge, update_charge, delete_charge,
    _update_irradiance,
)
from app.api.schemas import ProjectCreate, ChargeCreate, HourlySlot, SlotState
from app.infrastructure.pvgis import PVGISError


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_db():
    """Fausse session SQLAlchemy."""
    return MagicMock()


def make_background_tasks():
    return MagicMock(spec=BackgroundTasks)


def make_project_data(**kwargs):
    defaults = {"name": "Projet test", "gps_lat": 48.85, "gps_lon": 2.35}
    return ProjectCreate(**{**defaults, **kwargs})


def make_24_slots(state: SlotState = SlotState.INACTIVE) -> list[HourlySlot]:
    return [HourlySlot(hour=h, state=state) for h in range(24)]


def make_charge_data(**kwargs):
    defaults = {
        "name": "Climatiseur",
        "max_power_w": 1500.0,
        "real_usage_rate": 0.8,
        "hourly_slots": make_24_slots(),
    }
    return ChargeCreate(**{**defaults, **kwargs})


# ── Tests create_project ───────────────────────────────────────────────────────

def test_create_project_ajoute_et_commit():
    db = make_db()
    bt = make_background_tasks()

    create_project(db, make_project_data(), bt)

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_create_project_enregistre_background_task():
    """Le background task PVGIS doit être enregistré, pas appelé directement."""
    db = make_db()
    bt = make_background_tasks()

    create_project(db, make_project_data(gps_lat=48.85, gps_lon=2.35), bt)

    bt.add_task.assert_called_once()
    args = bt.add_task.call_args[0]
    assert args[0] is _update_irradiance
    assert args[2] == 48.85  # lat
    assert args[3] == 2.35   # lon


def test_create_project_retourne_le_projet():
    db = make_db()
    fake_project = MagicMock()
    db.refresh.side_effect = lambda p: None
    db.add.side_effect = lambda p: setattr(p, "id", uuid4())

    result = create_project(db, make_project_data(), make_background_tasks())

    assert result is not None


# ── Tests get_project ──────────────────────────────────────────────────────────

def test_get_project_retourne_le_projet_si_trouve():
    db = make_db()
    pid = uuid4()
    fake_project = MagicMock()
    db.get.return_value = fake_project

    result = get_project(db, pid)

    db.get.assert_called_once()
    assert result is fake_project


def test_get_project_retourne_none_si_absent():
    db = make_db()
    db.get.return_value = None

    result = get_project(db, uuid4())

    assert result is None


# ── Tests list_projects ────────────────────────────────────────────────────────

def test_list_projects_retourne_tous_les_projets():
    db = make_db()
    fake_list = [MagicMock(), MagicMock()]
    db.query.return_value.all.return_value = fake_list

    result = list_projects(db)

    assert result == fake_list


# ── Tests delete_project ───────────────────────────────────────────────────────

def test_delete_project_supprime_et_retourne_true():
    db = make_db()
    db.get.return_value = MagicMock()

    result = delete_project(db, uuid4())

    db.delete.assert_called_once()
    db.commit.assert_called_once()
    assert result is True


def test_delete_project_retourne_false_si_absent():
    db = make_db()
    db.get.return_value = None

    result = delete_project(db, uuid4())

    db.delete.assert_not_called()
    assert result is False


# ── Tests create_charge ────────────────────────────────────────────────────────

def test_create_charge_retourne_none_si_projet_absent():
    db = make_db()
    db.get.return_value = None

    result = create_charge(db, uuid4(), make_charge_data())

    assert result is None
    db.add.assert_not_called()


def test_create_charge_serialise_les_slots_en_dict():
    """hourly_slots doit être stocké en dict (JSON), pas en objets Pydantic."""
    db = make_db()
    db.get.return_value = MagicMock()  # projet trouvé

    added_charge = None
    def capture_add(obj):
        nonlocal added_charge
        added_charge = obj
    db.add.side_effect = capture_add

    create_charge(db, uuid4(), make_charge_data())

    assert isinstance(added_charge.hourly_slots[0], dict)
    assert "hour" in added_charge.hourly_slots[0]
    assert "state" in added_charge.hourly_slots[0]


def test_create_charge_ajoute_et_commit():
    db = make_db()
    db.get.return_value = MagicMock()

    create_charge(db, uuid4(), make_charge_data())

    db.add.assert_called_once()
    db.commit.assert_called_once()


# ── Tests update_charge ────────────────────────────────────────────────────────

def test_update_charge_retourne_none_si_absent():
    db = make_db()
    db.get.return_value = None

    result = update_charge(db, uuid4(), make_charge_data())

    assert result is None


def test_update_charge_modifie_les_champs():
    db = make_db()
    fake_charge = MagicMock()
    db.get.return_value = fake_charge

    new_data = make_charge_data(name="Pompe", max_power_w=500.0, real_usage_rate=0.5)
    update_charge(db, uuid4(), new_data)

    assert fake_charge.name == "Pompe"
    assert fake_charge.max_power_w == 500.0
    assert fake_charge.real_usage_rate == 0.5
    db.commit.assert_called_once()


# ── Tests delete_charge ────────────────────────────────────────────────────────

def test_delete_charge_supprime_et_retourne_true():
    db = make_db()
    db.get.return_value = MagicMock()

    result = delete_charge(db, uuid4())

    db.delete.assert_called_once()
    assert result is True


def test_delete_charge_retourne_false_si_absent():
    db = make_db()
    db.get.return_value = None

    result = delete_charge(db, uuid4())

    assert result is False


# ── Tests _update_irradiance (background task) ─────────────────────────────────

def test_update_irradiance_met_a_jour_le_projet():
    pid = uuid4()
    fake_project = MagicMock()
    fake_irradiance = [float(i) for i in range(24)]

    with patch("app.application.services.SessionLocal") as mock_session_cls, \
         patch("app.application.services.fetch_hourly_irradiance", return_value=fake_irradiance):

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.get.return_value = fake_project

        _update_irradiance(pid, 48.85, 2.35)

        assert fake_project.hourly_irradiance == fake_irradiance
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()


def test_update_irradiance_ne_plante_pas_si_pvgis_echoue():
    """Si PVGIS échoue, le projet reste avec hourly_irradiance=null sans erreur."""
    pid = uuid4()

    with patch("app.application.services.SessionLocal") as mock_session_cls, \
         patch("app.application.services.fetch_hourly_irradiance", side_effect=PVGISError("timeout")):

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        _update_irradiance(pid, 48.85, 2.35)  # ne doit pas lever d'exception

        mock_db.commit.assert_not_called()
        mock_db.close.assert_called_once()  # la session est toujours fermée


def test_update_irradiance_ne_plante_pas_si_projet_supprime_entre_temps():
    """Le projet peut avoir été supprimé entre la création et la fin de l'appel PVGIS."""
    pid = uuid4()

    with patch("app.application.services.SessionLocal") as mock_session_cls, \
         patch("app.application.services.fetch_hourly_irradiance", return_value=[0.0] * 24):

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.get.return_value = None  # projet introuvable

        _update_irradiance(pid, 48.85, 2.35)  # ne doit pas planter

        mock_db.commit.assert_not_called()
