from datetime import datetime
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TelemetryRecord, ParameterThreshold, EventLog, EventSeverity


async def create_telemetry(
    db: AsyncSession,
    experiment_id: int,
    parameter_name: str,
    value: float,
    unit: Optional[str] = None,
) -> TelemetryRecord:
    record = TelemetryRecord(
        experiment_id=experiment_id,
        parameter_name=parameter_name,
        value=value,
        unit=unit,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_telemetry(
    db: AsyncSession,
    experiment_id: int,
    parameter_name: Optional[str] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 1000,
) -> List[TelemetryRecord]:
    query = select(TelemetryRecord).where(TelemetryRecord.experiment_id == experiment_id)
    if parameter_name:
        query = query.where(TelemetryRecord.parameter_name == parameter_name)
    if from_dt:
        query = query.where(TelemetryRecord.recorded_at >= from_dt)
    if to_dt:
        query = query.where(TelemetryRecord.recorded_at <= to_dt)
    query = query.order_by(TelemetryRecord.recorded_at.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_thresholds_for_stand(
    db: AsyncSession, stand_id: int
) -> List[ParameterThreshold]:
    result = await db.execute(
        select(ParameterThreshold).where(ParameterThreshold.stand_id == stand_id)
    )
    return list(result.scalars().all())


async def create_threshold(
    db: AsyncSession,
    stand_id: int,
    parameter_name: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    severity: EventSeverity = EventSeverity.warning,
) -> ParameterThreshold:
    threshold = ParameterThreshold(
        stand_id=stand_id,
        parameter_name=parameter_name,
        min_value=min_value,
        max_value=max_value,
        severity=severity,
    )
    db.add(threshold)
    await db.flush()
    await db.refresh(threshold)
    return threshold


async def delete_threshold(db: AsyncSession, threshold: ParameterThreshold) -> None:
    await db.delete(threshold)
    await db.flush()


async def create_event(
    db: AsyncSession,
    event_type: str,
    message: str,
    severity: EventSeverity = EventSeverity.info,
    experiment_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> EventLog:
    event = EventLog(
        event_type=event_type,
        message=message,
        severity=severity,
        experiment_id=experiment_id,
        user_id=user_id,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


async def get_events(
    db: AsyncSession,
    experiment_id: Optional[int] = None,
    user_id: Optional[int] = None,
    severity: Optional[EventSeverity] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 200,
) -> List[EventLog]:
    query = select(EventLog)
    if experiment_id is not None:
        query = query.where(EventLog.experiment_id == experiment_id)
    if user_id is not None:
        query = query.where(EventLog.user_id == user_id)
    if severity is not None:
        query = query.where(EventLog.severity == severity)
    if from_dt:
        query = query.where(EventLog.created_at >= from_dt)
    if to_dt:
        query = query.where(EventLog.created_at <= to_dt)
    query = query.order_by(EventLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
