from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.schemas import DimensioningResult, ProjectCreate, ProjectRead
from backend.application import services
from backend.application.ports import TaskDispatcher
from backend.application.services import DimensioningParams
from backend.infrastructure.celery_dispatcher import CeleryTaskDispatcher
from backend.infrastructure.database import get_db
from backend.infrastructure.repositories import ProjectRepository

router = APIRouter(prefix="/projects", tags=["projects"])


def get_repo(db: Session = Depends(get_db)) -> ProjectRepository:
    return ProjectRepository(db)


def get_dispatcher() -> TaskDispatcher:
    return CeleryTaskDispatcher()


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(
    data: ProjectCreate,
    repo: ProjectRepository = Depends(get_repo),
    dispatcher: TaskDispatcher = Depends(get_dispatcher),
):
    project = services.create_project(repo, data.name, data.gps_lat, data.gps_lon)
    dispatcher.dispatch_irradiance_update(project.id, data.gps_lat, data.gps_lon)
    return project


@router.get("", response_model=list[ProjectRead])
def list_projects(repo: ProjectRepository = Depends(get_repo)):
    return services.list_projects(repo)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: UUID, repo: ProjectRepository = Depends(get_repo)):
    project = services.get_project(repo, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: UUID, repo: ProjectRepository = Depends(get_repo)):
    if not services.delete_project(repo, project_id):
        raise HTTPException(status_code=404, detail="Projet introuvable")


@router.get("/{project_id}/dimensioning", response_model=DimensioningResult)
def get_dimensioning(
    project_id: UUID,
    panel_peak_power_wp: float = Query(..., gt=0, description="Puissance crête d'un panneau (Wc)"),
    battery_capacity_wh: float = Query(..., gt=0, description="Capacité d'une batterie (Wh)"),
    battery_dod: float = Query(..., gt=0, le=1.0, description="Depth of discharge (0.0 → 1.0)"),
    system_efficiency: float = Query(..., gt=0, le=1.0, description="Rendement global (0.0 → 1.0)"),
    repo: ProjectRepository = Depends(get_repo),
):
    try:
        result = services.get_dimensioning(
            repo,
            project_id,
            DimensioningParams(
                panel_peak_power_wp=panel_peak_power_wp,
                battery_capacity_wh=battery_capacity_wh,
                battery_dod=battery_dod,
                system_efficiency=system_efficiency,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not result:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return DimensioningResult(**result)
