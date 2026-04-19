from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

from app.models import UserRole, ExperimentStatus, EventSeverity


# ──────────────────────────────────────────────────────────────────────────────
# User schemas
# ──────────────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.student

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Auth schemas
# ──────────────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class LoginRequest(BaseModel):
    username: str
    password: str


# ──────────────────────────────────────────────────────────────────────────────
# Stand schemas
# ──────────────────────────────────────────────────────────────────────────────

class StandCreate(BaseModel):
    name: str
    description: Optional[str] = None
    plc_host: str
    plc_port: int = 502


class StandUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    plc_host: Optional[str] = None
    plc_port: Optional[int] = None
    is_active: Optional[bool] = None


class StandResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    plc_host: str
    plc_port: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Experiment schemas
# ──────────────────────────────────────────────────────────────────────────────

class ExperimentCreate(BaseModel):
    stand_id: int
    title: str
    description: Optional[str] = None


class ExperimentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ExperimentResponse(BaseModel):
    id: int
    user_id: int
    stand_id: int
    title: str
    description: Optional[str]
    status: ExperimentStatus
    started_at: Optional[datetime]
    paused_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Telemetry schemas
# ──────────────────────────────────────────────────────────────────────────────

class TelemetryCreate(BaseModel):
    parameter_name: str
    value: float
    unit: Optional[str] = None


class TelemetryResponse(BaseModel):
    id: int
    experiment_id: int
    parameter_name: str
    value: float
    unit: Optional[str]
    recorded_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Threshold schemas
# ──────────────────────────────────────────────────────────────────────────────

class ThresholdCreate(BaseModel):
    stand_id: int
    parameter_name: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    severity: EventSeverity = EventSeverity.warning


class ThresholdResponse(BaseModel):
    id: int
    stand_id: int
    parameter_name: str
    min_value: Optional[float]
    max_value: Optional[float]
    severity: EventSeverity

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Event log schemas
# ──────────────────────────────────────────────────────────────────────────────

class EventLogResponse(BaseModel):
    id: int
    experiment_id: Optional[int]
    user_id: Optional[int]
    severity: EventSeverity
    event_type: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}
