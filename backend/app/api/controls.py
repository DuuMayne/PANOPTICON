from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Control, ControlRun, ControlFailure, ControlCurrentState
from app.schemas import ControlSummary, ControlDetail, RunSummary, RunDetail
from app.scheduler import run_control


class UpdateCadenceRequest(BaseModel):
    cadence_seconds: int


class CreateControlRequest(BaseModel):
    key: str
    name: str
    description: str = ""
    owner: str = ""
    connector_type: str
    evaluator_type: str
    config_json: dict = {}
    cadence_seconds: int = 21600
    enabled: bool = True


class UpdateControlRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    owner: str | None = None
    connector_type: str | None = None
    evaluator_type: str | None = None
    config_json: dict | None = None
    cadence_seconds: int | None = None
    enabled: bool | None = None

router = APIRouter(prefix="/controls", tags=["controls"])


@router.get("", response_model=list[ControlSummary])
def list_controls(db: Session = Depends(get_db)):
    controls = (
        db.query(Control)
        .options(joinedload(Control.current_state))
        .order_by(Control.key)
        .all()
    )
    return controls


@router.post("", response_model=ControlDetail, status_code=201)
def create_control(body: CreateControlRequest, db: Session = Depends(get_db)):
    """Create a new control definition."""
    existing = db.query(Control).filter(Control.key == body.key).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Control with key '{body.key}' already exists")

    control = Control(
        key=body.key,
        name=body.name,
        description=body.description,
        owner=body.owner,
        connector_type=body.connector_type,
        evaluator_type=body.evaluator_type,
        config_json=body.config_json,
        cadence_seconds=body.cadence_seconds,
        enabled=body.enabled,
    )
    db.add(control)
    db.flush()

    state = ControlCurrentState(control_id=control.id, current_status="pending")
    db.add(state)
    db.commit()
    db.refresh(control)
    return control


@router.get("/{control_id}", response_model=ControlDetail)
def get_control(control_id: UUID, db: Session = Depends(get_db)):
    control = (
        db.query(Control)
        .options(joinedload(Control.current_state))
        .filter(Control.id == control_id)
        .first()
    )
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@router.get("/{control_id}/runs", response_model=list[RunSummary])
def list_runs(control_id: UUID, limit: int = 50, db: Session = Depends(get_db)):
    runs = (
        db.query(ControlRun)
        .filter(ControlRun.control_id == control_id)
        .order_by(ControlRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return runs


@router.get("/{control_id}/runs/latest", response_model=RunDetail | None)
def get_latest_run(control_id: UUID, db: Session = Depends(get_db)):
    run = (
        db.query(ControlRun)
        .options(joinedload(ControlRun.failures))
        .filter(ControlRun.control_id == control_id)
        .order_by(ControlRun.started_at.desc())
        .first()
    )
    return run


@router.put("/{control_id}", response_model=ControlDetail)
def update_control(control_id: UUID, body: UpdateControlRequest, db: Session = Depends(get_db)):
    """Update a control's configuration."""
    control = db.query(Control).filter(Control.id == control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(control, field, value)
    control.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(control)
    return control


@router.delete("/{control_id}", response_model=dict)
def delete_control(control_id: UUID, db: Session = Depends(get_db)):
    """Delete a control and all its run history."""
    control = db.query(Control).filter(Control.id == control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    # Delete in order: failures -> runs -> state -> control
    run_ids = [r.id for r in db.query(ControlRun).filter(ControlRun.control_id == control_id).all()]
    if run_ids:
        db.query(ControlFailure).filter(ControlFailure.control_run_id.in_(run_ids)).delete(synchronize_session=False)
    db.query(ControlRun).filter(ControlRun.control_id == control_id).delete(synchronize_session=False)
    db.query(ControlCurrentState).filter(ControlCurrentState.control_id == control_id).delete(synchronize_session=False)
    db.delete(control)
    db.commit()
    return {"message": f"Deleted control {control.key}"}


@router.post("/{control_id}/run", response_model=dict)
def trigger_run(control_id: UUID, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    control = db.query(Control).filter(Control.id == control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    background_tasks.add_task(run_control, str(control_id))
    return {"message": f"Run triggered for control {control.key}"}


@router.patch("/{control_id}/cadence", response_model=dict)
def update_cadence(control_id: UUID, body: UpdateCadenceRequest, db: Session = Depends(get_db)):
    """Update the run cadence for a specific control."""
    control = db.query(Control).filter(Control.id == control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    if body.cadence_seconds < 60:
        raise HTTPException(status_code=400, detail="Cadence must be at least 60 seconds")
    control.cadence_seconds = body.cadence_seconds
    control.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": f"Cadence updated to {body.cadence_seconds}s for {control.key}", "cadence_seconds": body.cadence_seconds}


@router.delete("/{control_id}/runs", response_model=dict)
def delete_runs(control_id: UUID, before: str = None, db: Session = Depends(get_db)):
    """Delete run history for a control.

    Query params:
        before: ISO datetime — delete runs older than this. If omitted, deletes all runs.
    """
    control = db.query(Control).filter(Control.id == control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    query = db.query(ControlRun).filter(ControlRun.control_id == control_id)
    if before:
        try:
            cutoff = datetime.fromisoformat(before.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format for 'before' parameter")
        query = query.filter(ControlRun.started_at < cutoff)

    # Get IDs to delete (for cascade cleanup)
    run_ids = [r.id for r in query.all()]
    if not run_ids:
        return {"message": "No runs to delete", "deleted": 0}

    # Delete failures first (cascade should handle this but be explicit)
    db.query(ControlFailure).filter(ControlFailure.control_run_id.in_(run_ids)).delete(synchronize_session=False)
    deleted = query.delete(synchronize_session=False)

    # If we deleted the latest run, update current state
    state = db.query(ControlCurrentState).filter(ControlCurrentState.control_id == control_id).first()
    if state and state.last_run_id in run_ids:
        latest = (
            db.query(ControlRun)
            .filter(ControlRun.control_id == control_id)
            .order_by(ControlRun.started_at.desc())
            .first()
        )
        if latest:
            state.last_run_id = latest.id
            state.last_run_at = latest.started_at
            state.current_status = latest.status
        else:
            state.last_run_id = None
            state.last_run_at = None
            state.current_status = "pending"
            state.consecutive_failures = 0
            state.failing_resource_count = 0
            state.first_failed_at = None

    db.commit()
    return {"message": f"Deleted {deleted} runs for {control.key}", "deleted": deleted}
