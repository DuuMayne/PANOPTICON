"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "controls",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("owner", sa.String(255)),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("cadence_seconds", sa.Integer, nullable=False, server_default=sa.text("21600")),
        sa.Column("connector_type", sa.String(50), nullable=False),
        sa.Column("evaluator_type", sa.String(50), nullable=False),
        sa.Column("config_json", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "control_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("control_id", UUID(as_uuid=True), sa.ForeignKey("controls.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("summary", sa.Text),
        sa.Column("evidence_json", JSONB),
        sa.Column("error_message", sa.Text),
        sa.Column("run_metadata_json", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_control_runs_control_id", "control_runs", ["control_id"])
    op.create_index("idx_control_runs_started_at", "control_runs", ["started_at"])

    op.create_table(
        "control_failures",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("control_run_id", UUID(as_uuid=True), sa.ForeignKey("control_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_identifier", sa.String(500), nullable=False),
        sa.Column("details_json", JSONB),
    )
    op.create_index("idx_control_failures_run_id", "control_failures", ["control_run_id"])

    op.create_table(
        "control_current_state",
        sa.Column("control_id", UUID(as_uuid=True), sa.ForeignKey("controls.id"), primary_key=True),
        sa.Column("current_status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("last_run_id", UUID(as_uuid=True), sa.ForeignKey("control_runs.id")),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("first_failed_at", sa.DateTime(timezone=True)),
        sa.Column("last_status_changed_at", sa.DateTime(timezone=True)),
        sa.Column("consecutive_failures", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("failing_resource_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("control_current_state")
    op.drop_table("control_failures")
    op.drop_table("control_runs")
    op.drop_table("controls")
