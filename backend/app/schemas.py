from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ControlCurrentStateSchema(BaseModel):
    current_status: str
    last_run_at: datetime | None = None
    first_failed_at: datetime | None = None
    last_status_changed_at: datetime | None = None
    consecutive_failures: int = 0
    failing_resource_count: int = 0

    model_config = {"from_attributes": True}


class ControlSummary(BaseModel):
    id: UUID
    key: str
    name: str
    description: str | None = None
    owner: str | None = None
    enabled: bool
    connector_type: str
    evaluator_type: str
    current_state: ControlCurrentStateSchema | None = None

    model_config = {"from_attributes": True}


class ControlDetail(ControlSummary):
    cadence_seconds: int
    config_json: dict
    created_at: datetime
    updated_at: datetime


class FailureSchema(BaseModel):
    id: UUID
    resource_type: str
    resource_identifier: str
    details_json: dict | None = None

    model_config = {"from_attributes": True}


class RunSummary(BaseModel):
    id: UUID
    control_id: UUID
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    summary: str | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}


class RunDetail(RunSummary):
    evidence_json: dict | None = None
    run_metadata_json: dict | None = None
    failures: list[FailureSchema] = []


class FailureWithControl(FailureSchema):
    control_run_id: UUID
    control_key: str
    control_name: str
    run_status: str
    run_started_at: datetime


class HealthResponse(BaseModel):
    status: str
    scheduler_running: bool
    last_scheduler_heartbeat: datetime | None = None
