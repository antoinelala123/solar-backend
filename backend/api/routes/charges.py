from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.schemas import ChargeCreate, ChargeRead
from backend.application import services
from backend.application.services import ChargeData
from backend.infrastructure.database import get_db
from backend.infrastructure.repositories import ChargeRepository

router = APIRouter(tags=["charges"])


def get_repo(db: Session = Depends(get_db)) -> ChargeRepository:
    return ChargeRepository(db)


def _to_charge_data(data: ChargeCreate) -> ChargeData:
    return ChargeData(
        name=data.name,
        max_power_w=data.max_power_w,
        real_usage_rate=data.real_usage_rate,
        hourly_slots=[slot.model_dump() for slot in data.hourly_slots],
    )


@router.post("/projects/{project_id}/charges", response_model=ChargeRead, status_code=201)
def create_charge(
    project_id: UUID,
    data: ChargeCreate,
    repo: ChargeRepository = Depends(get_repo),
):
    charge = services.create_charge(repo, project_id, _to_charge_data(data))
    if not charge:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return charge


@router.get("/charges/{charge_id}", response_model=ChargeRead)
def get_charge(charge_id: UUID, repo: ChargeRepository = Depends(get_repo)):
    charge = services.get_charge(repo, charge_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Charge introuvable")
    return charge


@router.put("/charges/{charge_id}", response_model=ChargeRead)
def update_charge(charge_id: UUID, data: ChargeCreate, repo: ChargeRepository = Depends(get_repo)):
    charge = services.update_charge(repo, charge_id, _to_charge_data(data))
    if not charge:
        raise HTTPException(status_code=404, detail="Charge introuvable")
    return charge


@router.delete("/charges/{charge_id}", status_code=204)
def delete_charge(charge_id: UUID, repo: ChargeRepository = Depends(get_repo)):
    if not services.delete_charge(repo, charge_id):
        raise HTTPException(status_code=404, detail="Charge introuvable")
