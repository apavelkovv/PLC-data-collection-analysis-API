import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class ExperimentStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    paused = "paused"
    finished = "finished"
    aborted = "aborted"


class EventSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="student", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    experiments: Mapped[list["Experiment"]] = relationship("Experiment", back_populates="user")
    events: Mapped[list["EventLog"]] = relationship("EventLog", back_populates="user")


class Stand(Base):
    __tablename__ = "stands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    plc_host: Mapped[str] = mapped_column(String(256), nullable=False)
    plc_port: Mapped[int] = mapped_column(Integer, default=502, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    experiments: Mapped[list["Experiment"]] = relationship("Experiment", back_populates="stand")
    thresholds: Mapped[list["ParameterThreshold"]] = relationship("ParameterThreshold", back_populates="stand")


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    stand_id: Mapped[int] = mapped_column(Integer, ForeignKey("stands.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="experiments")
    stand: Mapped["Stand"] = relationship("Stand", back_populates="experiments")
    telemetry: Mapped[list["TelemetryRecord"]] = relationship("TelemetryRecord", back_populates="experiment", cascade="all, delete-orphan")
    events: Mapped[list["EventLog"]] = relationship("EventLog", back_populates="experiment", cascade="all, delete-orphan")


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experiment_id: Mapped[int] = mapped_column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    parameter_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="telemetry")


class ParameterThreshold(Base):
    __tablename__ = "parameter_thresholds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stand_id: Mapped[int] = mapped_column(Integer, ForeignKey("stands.id"), nullable=False, index=True)
    parameter_name: Mapped[str] = mapped_column(String(128), nullable=False)
    min_value: Mapped[float] = mapped_column(Float, nullable=True)
    max_value: Mapped[float] = mapped_column(Float, nullable=True)
    severity: Mapped[str] = mapped_column(String(32), default="warning", nullable=False)

    stand: Mapped["Stand"] = relationship("Stand", back_populates="thresholds")


class EventLog(Base):
    __tablename__ = "event_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experiment_id: Mapped[int] = mapped_column(Integer, ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String(32), default="info", nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="events")
    user: Mapped["User"] = relationship("User", back_populates="events")