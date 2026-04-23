from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import projects, charges


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  # les tables sont créées via les migrations Alembic


app = FastAPI(title="SolarDim API", lifespan=lifespan)

# Origines autorisées — en prod, remplacer par l'URL réelle du frontend
_raw = os.getenv("CORS_ORIGINS", "http://localhost:4200")
CORS_ORIGINS = [o.strip() for o in _raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(charges.router)


@app.get("/health")
def health():
    return {"status": "ok"}
