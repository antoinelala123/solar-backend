import httpx
from collections import defaultdict

PVGIS_URL = "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"


class PVGISError(Exception):
    pass


def fetch_hourly_irradiance(lat: float, lon: float) -> list[float]:
    """
    Retourne l'irradiance moyenne par heure du jour (liste de 24 valeurs en W/m²),
    calculée à partir des données horaires annuelles PVGIS.
    """
    params = {
        "lat": lat,
        "lon": lon,
        "outputformat": "json",
        "pvcalculation": 1,
        "peakpower": 1,   # valeur de référence, n'affecte pas G(i)
        "loss": 14,
    }

    try:
        response = httpx.get(PVGIS_URL, params=params, timeout=60)
        response.raise_for_status()
    except httpx.TimeoutException:
        raise PVGISError("PVGIS n'a pas répondu dans les délais")
    except httpx.HTTPStatusError as e:
        raise PVGISError(f"PVGIS a retourné une erreur HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        raise PVGISError(f"Impossible de joindre PVGIS : {e}")

    try:
        hourly_data = response.json()["outputs"]["hourly"]
    except (KeyError, TypeError):
        raise PVGISError("Réponse PVGIS inattendue — structure JSON introuvable")

    # Accumule G(i) par heure du jour (0-23) sur toute l'année
    # Format du timestamp PVGIS : "20050101:0010" → heure = caractères 9-10 après ":"
    sums: dict[int, float] = defaultdict(float)
    counts: dict[int, int] = defaultdict(int)

    for record in hourly_data:
        hour = int(record["time"].split(":")[1][:2])
        sums[hour] += record["G(i)"]
        counts[hour] += 1

    return [round(sums[h] / counts[h], 2) for h in range(24)]
