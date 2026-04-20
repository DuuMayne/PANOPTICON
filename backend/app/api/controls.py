from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Control, ControlRun, ControlCurrentState
from app.schemas import ControlSummary, ControlDetail, RunSummary, RunDetail
from app.scheduler import run_control

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


@router.post("/{control_id}/run", response_model=dict)
def trigger_run(control_id: UUID, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    control = db.query(Control).filter(Control.id == control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    background_tasks.add_task(run_control, str(control_id))
    return {"message": f"Run triggered for control {control.key}"}
