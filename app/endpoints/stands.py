from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import UserRole
from app.schemas import StandCreate, StandUpdate, StandResponse, ThresholdCreate, ThresholdResponse
from app.service.auth_service import get_current_user, require_role
from app.models import User
import app.crud as crud

router = APIRouter(prefix="/stands", tags=["Stands"])

_teacher_admin = require_role(UserRole.teacher, UserRole.admin)


@router.get("/", response_model=List[StandResponse])
async def list_stands(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await crud.get_stands(db, skip=skip, limit=limit)


@router.post("/", response_model=StandResponse, status_code=201)
async def create_stand(
    data: StandCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_teacher_admin),
):
    return await crud.create_stand(
        db, name=data.name, plc_host=data.plc_host,
        plc_port=data.plc_port, description=data.description,
    )


@router.get("/{stand_id}", response_model=StandResponse)
async def get_stand(
    stand_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stand = await crud.get_stand_by_id(db, stand_id)
    if not stand:
        raise HTTPException(status_code=404, detail="Stand not found")
    return stand


@router.patch("/{stand_id}", response_model=StandResponse)
async def update_stand(
    stand_id: int,
    data: StandUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_teacher_admin),
):
    stand = await crud.get_stand_by_id(db, stand_id)
    if not stand:
        raise HTTPException(status_code=404, detail="Stand not found")
    return await crud.update_stand(
        db, stand,
        name=data.name, description=data.description,
        plc_host=data.plc_host, plc_port=data.plc_port,
        is_active=data.is_active,
    )


@router.delete("/{stand_id}", status_code=204)
async def delete_stand(
    stand_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_teacher_admin),
):
    stand = await crud.get_stand_by_id(db, stand_id)
    if not stand:
        raise HTTPException(status_code=404, detail="Stand not found")
    # Удаляем все эксперименты этого стенда
    experiments = await crud.get_experiments(db, stand_id=stand_id, limit=10000)
    for exp in experiments:
        await crud.delete_experiment(db, exp)
    # Теперь удаляем стенд
    await crud.delete_stand(db, stand)


@router.get("/{stand_id}/thresholds", response_model=List[ThresholdResponse])
async def list_thresholds(
    stand_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await crud.get_thresholds_for_stand(db, stand_id)


@router.post("/{stand_id}/thresholds", response_model=ThresholdResponse, status_code=201)
async def create_threshold(
    stand_id: int,
    data: ThresholdCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_teacher_admin),
):
    stand = await crud.get_stand_by_id(db, stand_id)
    if not stand:
        raise HTTPException(status_code=404, detail="Stand not found")
    return await crud.create_threshold(
        db, stand_id=stand_id,
        parameter_name=data.parameter_name,
        min_value=data.min_value,
        max_value=data.max_value,
        severity=data.severity,
    )
