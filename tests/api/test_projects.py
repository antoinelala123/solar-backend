from unittest.mock import MagicMock, patch
from uuid import uuid4

PROJECT_ID = uuid4()

FAKE_PROJECT = {
    "id": str(PROJECT_ID),
    "name": "Projet test",
    "gps_lat": 48.85,
    "gps_lon": 2.35,
    "hourly_irradiance": None,
    "created_at": "2026-01-01T00:00:00",
    "charges": [],
}

FAKE_DIMENSIONING = {
    "recommended_panels": 2,
    "recommended_batteries": 1,
    "daily_load_wh": 1200.0,
    "daily_solar_wh": 1400.0,
    "energy_wasted_wh_per_day": 50.0,
    "energy_deficit_wh_per_day": 0.0,
    "is_oversized": False,
}

DIMENSIONING_PARAMS = (
    "panel_peak_power_wp=400&battery_capacity_wh=200&battery_dod=0.8&system_efficiency=0.8"
)


def make_fake_project():
    fake = MagicMock()
    fake.id = PROJECT_ID
    fake.name = "Test"
    fake.gps_lat = 48.85
    fake.gps_lon = 2.35
    fake.hourly_irradiance = None
    fake.created_at = "2026-01-01T00:00:00"
    fake.charges = []
    return fake


# ── POST /projects ─────────────────────────────────────────────────────────────

def test_create_project_retourne_201(client):
    with patch("backend.api.routes.projects.services.create_project", return_value=make_fake_project()):
        response = client.post("/projects", json={"name": "Test", "gps_lat": 48.85, "gps_lon": 2.35})
    assert response.status_code == 201


def test_create_project_valide_les_coordonnees(client):
    response = client.post("/projects", json={"name": "Test", "gps_lat": 999.0, "gps_lon": 2.35})
    assert response.status_code == 422


# ── GET /projects ──────────────────────────────────────────────────────────────

def test_list_projects_retourne_200(client):
    with patch("backend.api.routes.projects.services.list_projects", return_value=[]):
        response = client.get("/projects")
    assert response.status_code == 200
    assert response.json() == []


# ── GET /projects/{id} ─────────────────────────────────────────────────────────

def test_get_project_retourne_404_si_absent(client):
    with patch("backend.api.routes.projects.services.get_project", return_value=None):
        response = client.get(f"/projects/{PROJECT_ID}")
    assert response.status_code == 404


def test_get_project_retourne_200_si_trouve(client):
    with patch("backend.api.routes.projects.services.get_project", return_value=make_fake_project()):
        response = client.get(f"/projects/{PROJECT_ID}")
    assert response.status_code == 200


# ── DELETE /projects/{id} ──────────────────────────────────────────────────────

def test_delete_project_retourne_204(client):
    with patch("backend.api.routes.projects.services.delete_project", return_value=True):
        response = client.delete(f"/projects/{PROJECT_ID}")
    assert response.status_code == 204


def test_delete_project_retourne_404_si_absent(client):
    with patch("backend.api.routes.projects.services.delete_project", return_value=False):
        response = client.delete(f"/projects/{PROJECT_ID}")
    assert response.status_code == 404


# ── GET /projects/{id}/dimensioning ───────────────────────────────────────────

def test_dimensioning_retourne_200(client):
    with patch("backend.api.routes.projects.services.get_dimensioning", return_value=FAKE_DIMENSIONING):
        response = client.get(f"/projects/{PROJECT_ID}/dimensioning?{DIMENSIONING_PARAMS}")
    assert response.status_code == 200
    assert response.json()["recommended_panels"] == 2


def test_dimensioning_retourne_404_si_projet_absent(client):
    with patch("backend.api.routes.projects.services.get_dimensioning", return_value=None):
        response = client.get(f"/projects/{PROJECT_ID}/dimensioning?{DIMENSIONING_PARAMS}")
    assert response.status_code == 404


def test_dimensioning_retourne_409_si_irradiance_absente(client):
    with patch(
        "backend.api.routes.projects.services.get_dimensioning",
        side_effect=ValueError("irradiance"),
    ):
        response = client.get(f"/projects/{PROJECT_ID}/dimensioning?{DIMENSIONING_PARAMS}")
    assert response.status_code == 409


def test_dimensioning_valide_battery_dod(client):
    response = client.get(
        f"/projects/{PROJECT_ID}/dimensioning"
        "?panel_peak_power_wp=400&battery_capacity_wh=200&battery_dod=1.5&system_efficiency=0.8"
    )
    assert response.status_code == 422
