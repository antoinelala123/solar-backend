from fastapi import FastAPI, HTTPException
from app.infrastructure.database import engine, Base
from app.infrastructure.pvgis import fetch_hourly_irradiance, PVGISError

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SolarDim API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/pvgis")
def debug_pvgis():
    """Endpoint temporaire pour tester l'appel PVGIS sur Paris."""
    try:
        irradiance = fetch_hourly_irradiance(lat=48.8566, lon=2.3522)
        return {"location": "Paris", "hourly_irradiance": irradiance}
    except PVGISError as e:
        raise HTTPException(status_code=502, detail=str(e))