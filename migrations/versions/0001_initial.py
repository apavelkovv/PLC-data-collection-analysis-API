"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stands",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("plc_host", sa.String(256), nullable=False),
        sa.Column("plc_port", sa.Integer(), nullable=False, server_default="502"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_stands_id", "stands", ["id"])
    op.create_index("ix_stands_name", "stands", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("email", sa.String(256), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="student"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("stand_id", sa.Integer(), sa.ForeignKey("stands.id"), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_experiments_id", "experiments", ["id"])
    op.create_index("ix_experiments_user_id", "experiments", ["user_id"])
    op.create_index("ix_experiments_stand_id", "experiments", ["stand_id"])

    op.create_table(
        "parameter_thresholds",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stand_id", sa.Integer(), sa.ForeignKey("stands.id"), nullable=False),
        sa.Column("parameter_name", sa.String(128), nullable=False),
        sa.Column("min_value", sa.Float(), nullable=True),
        sa.Column("max_value", sa.Float(), nullable=True),
        sa.Column("severity", sa.String(32), nullable=False, server_default="warning"),
    )
    op.create_index("ix_parameter_thresholds_id", "parameter_thresholds", ["id"])
    op.create_index("ix_parameter_thresholds_stand_id", "parameter_thresholds", ["stand_id"])

    op.create_table(
        "event_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("severity", sa.String(32), nullable=False, server_default="info"),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_event_logs_id", "event_logs", ["id"])
    op.create_index("ix_event_logs_experiment_id", "event_logs", ["experiment_id"])
    op.create_index("ix_event_logs_user_id", "event_logs", ["user_id"])
    op.create_index("ix_event_logs_event_type", "event_logs", ["event_type"])
    op.create_index("ix_event_logs_created_at", "event_logs", ["created_at"])

    op.create_table(
        "telemetry_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parameter_name", sa.String(128), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_telemetry_records_id", "telemetry_records", ["id"])
    op.create_index("ix_telemetry_records_experiment_id", "telemetry_records", ["experiment_id"])
    op.create_index("ix_telemetry_records_parameter_name", "telemetry_records", ["parameter_name"])
    op.create_index("ix_telemetry_records_recorded_at", "telemetry_records", ["recorded_at"])


def downgrade() -> None:
    op.drop_table("telemetry_records")
    op.drop_table("event_logs")
    op.drop_table("parameter_thresholds")
    op.drop_table("experiments")
    op.drop_table("users")
    op.drop_table("stands")