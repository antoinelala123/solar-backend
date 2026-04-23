from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.infrastructure.database import get_db
from backend.api.schemas import ProjectCreate, ProjectRead, DimensioningResult
from backend.application import services
from backend.application.services import ProjectData, DimensioningParams as ServiceDimensioningParams

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(
    data: ProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    return services.create_project(
        db,
        ProjectData(name=data.name, gps_lat=data.gps_lat, gps_lon=data.gps_lon),
        background_tasks,
    )


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return services.list_projects(db)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    project = services.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    if not services.delete_project(db, project_id):
        raise HTTPException(status_code=404, detail="Projet introuvable")


@router.get("/{project_id}/dimensioning", response_model=DimensioningResult)
def get_dimensioning(
    project_id: UUID,
    panel_peak_power_wp: float = Query(..., gt=0, description="Puissance crête d'un panneau (Wc)"),
    battery_capacity_wh: float = Query(..., gt=0, description="Capacité d'une batterie (Wh)"),
    battery_dod: float = Query(..., gt=0, le=1.0, description="Depth of discharge (0.0 → 1.0)"),
    system_efficiency: float = Query(..., gt=0, le=1.0, description="Rendement global de l'installation (0.0 → 1.0)"),
    db: Session = Depends(get_db),
):
    try:
        result = services.get_dimensioning(
            db,
            project_id,
            ServiceDimensioningParams(
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
