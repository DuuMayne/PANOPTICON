from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import HealthResponse
from app.scheduler import get_scheduler_status
from app.connectors.base import get_registered_connectors
from app.evaluators.registry import EVALUATOR_REGISTRY
from app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    running, heartbeat = get_scheduler_status()
    return HealthResponse(
        status="ok",
        scheduler_running=running,
        last_scheduler_heartbeat=heartbeat,
    )


@router.get("/connectors")
def list_connectors():
    """List all registered connector types and their credential status."""
    registry = get_registered_connectors()
    result = []
    for ctype, cls in sorted(registry.items()):
        configured = all(getattr(settings, env_key, None) for env_key in cls.required_env)
        result.append({
            "connector_type": ctype,
            "required_env": cls.required_env,
            "configured": configured,
            "has_mock_data": bool(cls.mock_data),
        })
    return result


@router.post("/connectors/{connector_type}/test")
def test_connector(connector_type: str):
    """Test connectivity for a registered connector."""
    registry = get_registered_connectors()
    cls = registry.get(connector_type)
    if not cls:
        raise HTTPException(404, f"Unknown connector type: {connector_type}")

    configured = all(getattr(settings, env_key, None) for env_key in cls.required_env)
    if not configured:
        return {"connector_type": connector_type, "success": False, "message": "Credentials not configured", "using_mock": True}

    try:
        connector = cls()
        success = connector.test_connection()
        return {"connector_type": connector_type, "success": success, "message": "Connected" if success else "Connection failed", "using_mock": False}
    except Exception as e:
        return {"connector_type": connector_type, "success": False, "message": str(e), "using_mock": False}


@router.get("/evaluators")
def list_evaluators():
    """List all registered evaluator types."""
    return [
        {"evaluator_type": key, "class_name": cls.__name__, "description": (cls.__doc__ or "").split("\n")[0].strip()}
        for key, cls in sorted(EVALUATOR_REGISTRY.items())
    ]
