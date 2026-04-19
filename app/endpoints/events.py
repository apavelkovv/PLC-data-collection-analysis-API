from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, UserRole, EventSeverity
from app.schemas import EventLogResponse
from app.service.auth_service import require_role
import app.crud as crud

router = APIRouter(prefix="/events", tags=["Events"])

_teacher_admin = require_role(UserRole.teacher, UserRole.admin)


@router.get("/", response_model=List[EventLogResponse])
async def list_events(
    from_dt: Optional[datetime] = Query(default=None),
    to_dt: Optional[datetime] = Query(default=None),
    severity: Optional[EventSeverity] = None,
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_teacher_admin),
):
    """FR-10: Teacher/admin can view global event journal for any period."""
    return await crud.get_events(
        db,
        severity=severity,
        from_dt=from_dt,
        to_dt=to_dt,
        skip=skip,
        limit=limit,
    )
