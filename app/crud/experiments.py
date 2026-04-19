from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Experiment, ExperimentStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def get_experiment_by_id(db: AsyncSession, experiment_id: int) -> Optional[Experiment]:
    result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    return result.scalar_one_or_none()


async def get_experiments(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    stand_id: Optional[int] = None,
    status: Optional[ExperimentStatus] = None,
) -> List[Experiment]:
    query = select(Experiment)
    if user_id is not None:
        query = query.where(Experiment.user_id == user_id)
    if stand_id is not None:
        query = query.where(Experiment.stand_id == stand_id)
    if status is not None:
        query = query.where(Experiment.status == status)
    query = query.order_by(Experiment.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_experiment(
    db: AsyncSession,
    user_id: int,
    stand_id: int,
    title: str,
    description: Optional[str] = None,
) -> Experiment:
    experiment = Experiment(
        user_id=user_id,
        stand_id=stand_id,
        title=title,
        description=description,
        status=ExperimentStatus.pending,
    )
    db.add(experiment)
    await db.flush()
    await db.refresh(experiment)
    return experiment


async def set_experiment_status(
    db: AsyncSession,
    experiment: Experiment,
    status: ExperimentStatus,
) -> Experiment:
    experiment.status = status
    if status == ExperimentStatus.running and experiment.started_at is None:
        experiment.started_at = _utcnow()
    elif status == ExperimentStatus.paused:
        experiment.paused_at = _utcnow()
    elif status in (ExperimentStatus.finished, ExperimentStatus.aborted):
        experiment.finished_at = _utcnow()
    await db.flush()
    await db.refresh(experiment)
    return experiment


async def update_experiment(
    db: AsyncSession,
    experiment: Experiment,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> Experiment:
    if title is not None:
        experiment.title = title
    if description is not None:
        experiment.description = description
    await db.flush()
    await db.refresh(experiment)
    return experiment


async def delete_experiment(db: AsyncSession, experiment: Experiment) -> None:
    await db.delete(experiment)
    await db.flush()
