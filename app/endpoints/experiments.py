from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, UserRole, ExperimentStatus
from app.schemas import (
    ExperimentCreate, ExperimentUpdate, ExperimentResponse,
    TelemetryCreate, TelemetryResponse, EventLogResponse,
)
from app.service.auth_service import get_current_user
from app.service.experiment_service import (
    create_experiment, start_experiment, pause_experiment,
    stop_experiment, ingest_telemetry, export_telemetry_csv,
)
import app.crud as crud

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.post("/", response_model=ExperimentResponse, status_code=201)
async def create(
    data: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_experiment(
        db, user_id=current_user.id,
        stand_id=data.stand_id, title=data.title, description=data.description,
    )


@router.get("/", response_model=List[ExperimentResponse])
async def list_experiments(
    skip: int = 0,
    limit: int = 50,
    stand_id: Optional[int] = None,
    status: Optional[ExperimentStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id if current_user.role == UserRole.student else None
    return await crud.get_experiments(
        db, skip=skip, limit=limit,
        user_id=user_id, stand_id=stand_id, status=status,
    )


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = await crud.get_experiment_by_id(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if current_user.role == UserRole.student and exp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your experiment")
    return exp


@router.patch("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: int,
    data: ExperimentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = await crud.get_experiment_by_id(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if current_user.role == UserRole.student and exp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your experiment")
    return await crud.update_experiment(db, exp, title=data.title, description=data.description)


@router.post("/{experiment_id}/start", response_model=ExperimentResponse)
async def start(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = await crud.get_experiment_by_id(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return await start_experiment(db, exp, current_user)


@router.post("/{experiment_id}/pause", response_model=ExperimentResponse)
async def pause(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = await crud.get_experiment_by_id(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return await pause_experiment(db, exp, current_user)


@router.post("/{experiment_id}/stop", response_model=ExperimentResponse)
async def stop(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = await crud.get_experiment_by_id(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return await stop_experiment(db, exp, current_user)


@router.post("/{experiment_id}/telemetry", status_code=201)
async def post_telemetry(
    experiment_id: int,
    data: TelemetryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = await crud.get_experiment_by_id(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    await ingest_telemetry(db, exp, data.parameter_name, data.value, data.unit)
    records = await crud.get_telemetry(db, experiment_id, parameter_name=data.parameter_name, limit=1)
    return records[-1] if records else {}


@router.get("/{experiment_id}/telemetry", response_model=List[TelemetryResponse])
async def get_telemetry(
    experiment_id: int,
    parameter_name: Optional[str] = None,
    from_dt: Optional[datetime] = Query(default=None),
    to_dt: Optional[datetime] = Query(default=None),
    skip: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = await crud.get_experiment_by_id(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return await crud.get_telemetry(
        db, experiment_id,
        parameter_name=parameter_name,
        from_dt=from_dt, to_dt=to_dt,
        skip=skip, limit=limit,
    )


@router.get("/{experiment_id}/export/csv")
async def export_csv(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = await crud.get_experiment_by_id(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if current_user.role == UserRole.student and exp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your experiment")
    csv_data = await export_telemetry_csv(db, exp)
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=experiment_{experiment_id}.csv"},
    )


@router.get("/{experiment_id}/events", response_model=List[EventLogResponse])
async def get_events(
    experiment_id: int,
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = await crud.get_experiment_by_id(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return await crud.get_events(db, experiment_id=experiment_id, skip=skip, limit=limit)
