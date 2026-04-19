from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Stand


async def get_stand_by_id(db: AsyncSession, stand_id: int) -> Optional[Stand]:
    result = await db.execute(select(Stand).where(Stand.id == stand_id))
    return result.scalar_one_or_none()


async def get_stands(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Stand]:
    result = await db.execute(select(Stand).offset(skip).limit(limit))
    return list(result.scalars().all())


async def create_stand(
    db: AsyncSession,
    name: str,
    plc_host: str,
    plc_port: int = 502,
    description: Optional[str] = None,
) -> Stand:
    stand = Stand(name=name, plc_host=plc_host, plc_port=plc_port, description=description)
    db.add(stand)
    await db.flush()
    await db.refresh(stand)
    return stand


async def update_stand(
    db: AsyncSession,
    stand: Stand,
    name: Optional[str] = None,
    description: Optional[str] = None,
    plc_host: Optional[str] = None,
    plc_port: Optional[int] = None,
    is_active: Optional[bool] = None,
) -> Stand:
    if name is not None:
        stand.name = name
    if description is not None:
        stand.description = description
    if plc_host is not None:
        stand.plc_host = plc_host
    if plc_port is not None:
        stand.plc_port = plc_port
    if is_active is not None:
        stand.is_active = is_active
    await db.flush()
    await db.refresh(stand)
    return stand


async def delete_stand(db: AsyncSession, stand: Stand) -> None:
    await db.delete(stand)
    await db.flush()
