from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import ControlRun, ControlFailure, Control
from app.schemas import RunDetail, FailureWithControl

router = APIRouter(tags=["runs"])


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: UUID, db: Session = Depends(get_db)):
    run = (
        db.query(ControlRun)
        .options(joinedload(ControlRun.failures))
        .filter(ControlRun.id == run_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/failures", response_model=list[FailureWithControl])
def list_current_failures(db: Session = Depends(get_db)):
    """List all failing resources from the latest run of each failing control."""
    from app.models import ControlCurrentState

    failing_states = (
        db.query(ControlCurrentState)
        .filter(ControlCurrentState.current_status == "fail")
        .all()
    )

    results = []
    for state in failing_states:
        if not state.last_run_id:
            continue
        failures = (
            db.query(ControlFailure)
            .filter(ControlFailure.control_run_id == state.last_run_id)
            .all()
        )
        run = db.query(ControlRun).filter(ControlRun.id == state.last_run_id).first()
        control = db.query(Control).filter(Control.id == state.control_id).first()
        if not run or not control:
            continue

        for f in failures:
            results.append(FailureWithControl(
                id=f.id,
                resource_type=f.resource_type,
                resource_identifier=f.resource_identifier,
                details_json=f.details_json,
                control_run_id=f.control_run_id,
                control_key=control.key,
                control_name=control.name,
                run_status=run.status,
                run_started_at=run.started_at,
            ))

    return results
