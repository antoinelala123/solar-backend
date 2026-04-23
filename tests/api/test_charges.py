import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4


PROJECT_ID = uuid4()
CHARGE_ID = uuid4()


def make_fake_charge():
    fake = MagicMock()
    fake.id = CHARGE_ID
    fake.project_id = PROJECT_ID
    fake.name = "Climatiseur"
    fake.max_power_w = 1500.0
    fake.real_usage_rate = 0.8
    fake.hourly_slots = [
        {"hour": h, "state": "INACTIVE", "custom_value_w": None} for h in range(24)
    ]
    return fake


def make_charge_payload():
    return {
        "name": "Climatiseur",
        "max_power_w": 1500.0,
        "real_usage_rate": 0.8,
        "hourly_slots": [
            {"hour": h, "state": "INACTIVE", "custom_value_w": None} for h in range(24)
        ],
    }


# ── POST /projects/{id}/charges ────────────────────────────────────────────────

def test_create_charge_retourne_201(client):
    with patch("app.api.routes.charges.services.create_charge", return_value=make_fake_charge()):
        response = client.post(f"/projects/{PROJECT_ID}/charges", json=make_charge_payload())
    assert response.status_code == 201


def test_create_charge_retourne_404_si_projet_absent(client):
    with patch("app.api.routes.charges.services.create_charge", return_value=None):
        response = client.post(f"/projects/{PROJECT_ID}/charges", json=make_charge_payload())
    assert response.status_code == 404


def test_create_charge_valide_real_usage_rate(client):
    payload = make_charge_payload()
    payload["real_usage_rate"] = 1.5  # invalide
    response = client.post(f"/projects/{PROJECT_ID}/charges", json=payload)
    assert response.status_code == 422


def test_create_charge_valide_24_slots(client):
    payload = make_charge_payload()
    payload["hourly_slots"] = payload["hourly_slots"][:10]  # seulement 10 slots
    response = client.post(f"/projects/{PROJECT_ID}/charges", json=payload)
    assert response.status_code == 422


# ── GET /charges/{id} ─────────────────────────────────────────────────────────

def test_get_charge_retourne_200(client):
    with patch("app.api.routes.charges.services.get_charge", return_value=make_fake_charge()):
        response = client.get(f"/charges/{CHARGE_ID}")
    assert response.status_code == 200


def test_get_charge_retourne_404_si_absent(client):
    with patch("app.api.routes.charges.services.get_charge", return_value=None):
        response = client.get(f"/charges/{CHARGE_ID}")
    assert response.status_code == 404


# ── PUT /charges/{id} ─────────────────────────────────────────────────────────

def test_update_charge_retourne_200(client):
    with patch("app.api.routes.charges.services.update_charge", return_value=make_fake_charge()):
        response = client.put(f"/charges/{CHARGE_ID}", json=make_charge_payload())
    assert response.status_code == 200


def test_update_charge_retourne_404_si_absent(client):
    with patch("app.api.routes.charges.services.update_charge", return_value=None):
        response = client.put(f"/charges/{CHARGE_ID}", json=make_charge_payload())
    assert response.status_code == 404


# ── DELETE /charges/{id} ──────────────────────────────────────────────────────

def test_delete_charge_retourne_204(client):
    with patch("app.api.routes.charges.services.delete_charge", return_value=True):
        response = client.delete(f"/charges/{CHARGE_ID}")
    assert response.status_code == 204


def test_delete_charge_retourne_404_si_absent(client):
    with patch("app.api.routes.charges.services.delete_charge", return_value=False):
        response = client.delete(f"/charges/{CHARGE_ID}")
    assert response.status_code == 404
