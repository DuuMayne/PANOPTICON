from fastapi import APIRouter

from app.schemas import HealthResponse
from app.scheduler import get_scheduler_status

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    running, heartbeat = get_scheduler_status()
    return HealthResponse(
        status="ok",
        scheduler_running=running,
        last_scheduler_heartbeat=heartbeat,
    )
