import pytest
from unittest.mock import patch, MagicMock
import httpx

from backend.infrastructure.pvgis import fetch_hourly_irradiance, PVGISError


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_response(hourly_data: list[dict]) -> MagicMock:
    """Construit un faux objet response httpx avec les données fournies."""
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {"outputs": {"hourly": hourly_data}}
    return mock


def make_hourly_data(values_by_hour: dict[int, list[float]]) -> list[dict]:
    """
    Construit une liste de records PVGIS à partir d'un dict {heure: [valeurs]}.
    Exemple : {14: [600.0, 800.0]} → 2 records pour 14h avec G(i)=600 puis 800.
    """
    records = []
    for hour, values in values_by_hour.items():
        for day, val in enumerate(values, start=1):
            records.append({
                "time": f"2005{day:04d}:{hour:02d}10",
                "G(i)": val,
            })
    return records


# ── Tests nominaux ─────────────────────────────────────────────────────────────

def test_retourne_exactement_24_valeurs():
    """Le résultat doit toujours contenir 24 éléments (heures 0 à 23)."""
    data = [{"time": f"20050101:{h:02d}10", "G(i)": float(h * 10)} for h in range(24)]

    with patch("app.infrastructure.pvgis.httpx.get") as mock_get:
        mock_get.return_value = make_response(data)
        result = fetch_hourly_irradiance(48.85, 2.35)

    assert len(result) == 24


def test_moyenne_calculee_correctement():
    """Vérifie que la moyenne par heure est bien calculée sur plusieurs jours."""
    # Heure 14 : G(i) = 600 jour 1, 800 jour 2 → moyenne attendue = 700.0
    # Heure 6  : G(i) = 100 jour 1, 300 jour 2 → moyenne attendue = 200.0
    data = make_hourly_data({14: [600.0, 800.0], 6: [100.0, 300.0]})

    # On complète avec les heures manquantes (0.0) pour éviter une KeyError
    heures_presentes = {14, 6}
    for h in range(24):
        if h not in heures_presentes:
            data.append({"time": f"20050101:{h:02d}10", "G(i)": 0.0})

    with patch("app.infrastructure.pvgis.httpx.get") as mock_get:
        mock_get.return_value = make_response(data)
        result = fetch_hourly_irradiance(48.85, 2.35)

    assert result[14] == 700.0
    assert result[6] == 200.0


def test_valeurs_nulles_la_nuit():
    """Les heures nocturnes doivent avoir une irradiance de 0."""
    data = [{"time": f"20050101:{h:02d}10", "G(i)": 0.0} for h in range(24)]

    with patch("app.infrastructure.pvgis.httpx.get") as mock_get:
        mock_get.return_value = make_response(data)
        result = fetch_hourly_irradiance(48.85, 2.35)

    for h in [0, 1, 2, 3, 4, 22, 23]:
        assert result[h] == 0.0


def test_valeurs_arrondies_a_2_decimales():
    """Les valeurs retournées sont arrondies à 2 décimales."""
    # 1/3 ≈ 0.333... → arrondi à 0.33
    data = make_hourly_data({10: [1.0, 0.0, 0.0]})
    for h in range(24):
        if h != 10:
            data.append({"time": f"20050101:{h:02d}10", "G(i)": 0.0})

    with patch("app.infrastructure.pvgis.httpx.get") as mock_get:
        mock_get.return_value = make_response(data)
        result = fetch_hourly_irradiance(48.85, 2.35)

    assert result[10] == round(result[10], 2)


# ── Tests d'erreur ─────────────────────────────────────────────────────────────

def test_timeout_leve_pvgis_error():
    """Un timeout réseau doit lever PVGISError, pas une exception httpx brute."""
    with patch("app.infrastructure.pvgis.httpx.get") as mock_get:
        mock_get.side_effect = httpx.TimeoutException("timeout")

        with pytest.raises(PVGISError, match="délais"):
            fetch_hourly_irradiance(48.85, 2.35)


def test_erreur_http_leve_pvgis_error():
    """Une erreur HTTP (ex: 400 coordonnées invalides) doit lever PVGISError."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "bad request", request=MagicMock(), response=mock_response
    )

    with patch("app.infrastructure.pvgis.httpx.get") as mock_get:
        mock_get.return_value = mock_response

        with pytest.raises(PVGISError, match="HTTP 400"):
            fetch_hourly_irradiance(48.85, 2.35)


def test_json_invalide_leve_pvgis_error():
    """Une réponse JSON sans la clé 'outputs' doit lever PVGISError."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"unexpected": "structure"}

    with patch("app.infrastructure.pvgis.httpx.get") as mock_get:
        mock_get.return_value = mock_response

        with pytest.raises(PVGISError, match="inattendue"):
            fetch_hourly_irradiance(48.85, 2.35)


def test_erreur_reseau_leve_pvgis_error():
    """Une erreur réseau générique doit lever PVGISError."""
    with patch("app.infrastructure.pvgis.httpx.get") as mock_get:
        mock_get.side_effect = httpx.RequestError("connection refused")

        with pytest.raises(PVGISError, match="joindre PVGIS"):
            fetch_hourly_irradiance(48.85, 2.35)
