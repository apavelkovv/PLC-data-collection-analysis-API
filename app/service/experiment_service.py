import csv
import io
from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Experiment, ExperimentStatus, EventSeverity, User, UserRole
import app.crud as crud


async def _assert_experiment_owner_or_teacher(
    experiment: Experiment, current_user: User
) -> None:
    """Only the owner (student) or a teacher/admin can manage an experiment."""
    if current_user.role == UserRole.student and experiment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your experiment")


async def create_experiment(
    db: AsyncSession,
    user_id: int,
    stand_id: int,
    title: str,
    description: Optional[str],
) -> Experiment:
    """FR-04: Create experiment, log creation event."""
    stand = await crud.get_stand_by_id(db, stand_id)
    if not stand or not stand.is_active:
        raise HTTPException(status_code=404, detail="Stand not found or inactive")

    experiment = await crud.create_experiment(db, user_id, stand_id, title, description)
    await crud.create_event(
        db,
        event_type="experiment_created",
        message=f"Experiment '{title}' created for stand '{stand.name}'",
        severity=EventSeverity.info,
        experiment_id=experiment.id,
        user_id=user_id,
    )
    return experiment


async def start_experiment(
    db: AsyncSession, experiment: Experiment, current_user: User
) -> Experiment:
    """FR-03: Start experiment (pending → running)."""
    await _assert_experiment_owner_or_teacher(experiment, current_user)
    if experiment.status not in (ExperimentStatus.pending, ExperimentStatus.paused):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start experiment in status '{experiment.status}'",
        )
    experiment = await crud.set_experiment_status(db, experiment, ExperimentStatus.running)
    await crud.create_event(
        db,
        event_type="experiment_started",
        message=f"Experiment '{experiment.title}' started",
        severity=EventSeverity.info,
        experiment_id=experiment.id,
        user_id=current_user.id,
    )
    return experiment


async def pause_experiment(
    db: AsyncSession, experiment: Experiment, current_user: User
) -> Experiment:
    """FR-03: Pause experiment (running → paused)."""
    await _assert_experiment_owner_or_teacher(experiment, current_user)
    if experiment.status != ExperimentStatus.running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only pause a running experiment",
        )
    experiment = await crud.set_experiment_status(db, experiment, ExperimentStatus.paused)
    await crud.create_event(
        db,
        event_type="experiment_paused",
        message=f"Experiment '{experiment.title}' paused",
        severity=EventSeverity.info,
        experiment_id=experiment.id,
        user_id=current_user.id,
    )
    return experiment


async def stop_experiment(
    db: AsyncSession, experiment: Experiment, current_user: User
) -> Experiment:
    """FR-03: Stop experiment (any active → finished)."""
    await _assert_experiment_owner_or_teacher(experiment, current_user)
    if experiment.status in (ExperimentStatus.finished, ExperimentStatus.aborted):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment is already finished",
        )
    experiment = await crud.set_experiment_status(db, experiment, ExperimentStatus.finished)
    await crud.create_event(
        db,
        event_type="experiment_finished",
        message=f"Experiment '{experiment.title}' finished",
        severity=EventSeverity.info,
        experiment_id=experiment.id,
        user_id=current_user.id,
    )
    return experiment


async def ingest_telemetry(
    db: AsyncSession,
    experiment: Experiment,
    parameter_name: str,
    value: float,
    unit: Optional[str],
) -> None:
    """FR-07, FR-08: Store telemetry and check thresholds."""
    if experiment.status != ExperimentStatus.running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telemetry can only be posted to a running experiment",
        )

    record = await crud.create_telemetry(db, experiment.id, parameter_name, value, unit)

    # FR-08: check against configured thresholds
    thresholds = await crud.get_thresholds_for_stand(db, experiment.stand_id)
    for threshold in thresholds:
        if threshold.parameter_name != parameter_name:
            continue
        breached = False
        direction = ""
        if threshold.min_value is not None and value < threshold.min_value:
            breached = True
            direction = f"below minimum ({threshold.min_value})"
        if threshold.max_value is not None and value > threshold.max_value:
            breached = True
            direction = f"above maximum ({threshold.max_value})"
        if breached:
            await crud.create_event(
                db,
                event_type="threshold_breach",
                message=(
                    f"Parameter '{parameter_name}' = {value} {unit or ''} "
                    f"is {direction} for stand_id={experiment.stand_id}"
                ),
                severity=threshold.severity,
                experiment_id=experiment.id,
            )


async def export_telemetry_csv(
    db: AsyncSession, experiment: Experiment
) -> str:
    """FR-12: Export telemetry for an experiment as CSV string."""
    records = await crud.get_telemetry(db, experiment.id, limit=100_000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "experiment_id", "parameter_name", "value", "unit", "recorded_at"])
    for r in records:
        writer.writerow([r.id, r.experiment_id, r.parameter_name, r.value, r.unit, r.recorded_at.isoformat()])
    return output.getvalue()
