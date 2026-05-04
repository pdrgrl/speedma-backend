"""
app/sim_api.py
──────────────
FastAPI router that exposes the FMU simulation service to Unity WebGL.

Endpoints
─────────
  POST /sim/start          → { session_id }
  POST /sim/step           → { session_id, t, outputs }
  POST /sim/reset          → { ok }
  POST /sim/stop           → { ok }
  GET  /sim/state/{sid}    → { t, outputs }
  GET  /sim/variables/{sid}→ { variables: {name: type} }
  GET  /sim/health         → { status, fmu_ready, sessions }
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.sim import (
    DEFAULT_FMU,
    get_state,
    list_variables,
    reset_session,
    start_session,
    step_session,
    stop_session,
    _sessions,
)

router = APIRouter(prefix="/sim", tags=["simulation"])


# ── Pydantic models ────────────────────────────────────────────────────────

class StartRequest(BaseModel):
    fmu_path: Optional[str] = None  # override default FMU; omit to use default

class StartResponse(BaseModel):
    session_id: str

class StepRequest(BaseModel):
    session_id: str
    dt: float = 0.02                # seconds per step  (~50 Hz)
    inputs: dict[str, Any] = {}     # { variable_name: value }

class StepResponse(BaseModel):
    session_id: str
    t: float                        # simulation time after step
    outputs: dict[str, Any]

class SessionRequest(BaseModel):
    session_id: str

class OkResponse(BaseModel):
    ok: bool = True


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/start", response_model=StartResponse)
def sim_start(req: StartRequest = StartRequest()):
    """
    Allocate a new FMU instance.  Returns a session_id that must be
    included in every subsequent /sim/* call.
    """
    fmu_path = Path(req.fmu_path) if req.fmu_path else None
    try:
        sid = start_session(fmu_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FMU load error: {e}")
    return StartResponse(session_id=sid)


@router.post("/step", response_model=StepResponse)
def sim_step(req: StepRequest):
    """
    Advance the simulation by *dt* seconds.
    Optionally supply input variable values.
    Returns all output values after the step.
    """
    try:
        outputs = step_session(req.session_id, req.dt, req.inputs)
        from app.sim import _sessions
        t = _sessions[req.session_id]["t"]
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step error: {e}")
    return StepResponse(session_id=req.session_id, t=t, outputs=outputs)


@router.post("/reset", response_model=OkResponse)
def sim_reset(req: SessionRequest):
    """Re-initialise the FMU to t=0 without allocating a new instance."""
    try:
        reset_session(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset error: {e}")
    return OkResponse()


@router.post("/stop", response_model=OkResponse)
def sim_stop(req: SessionRequest):
    """Terminate the session and free all resources."""
    stop_session(req.session_id)  # idempotent
    return OkResponse()


@router.get("/state/{session_id}")
def sim_state(session_id: str):
    """Return last known outputs without stepping (polling / reconnect)."""
    try:
        return get_state(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/variables/{session_id}")
def sim_variables(session_id: str):
    """List all FMU variable names and their types (useful for debugging)."""
    try:
        return {"variables": list_variables(session_id)}
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/health")
def sim_health():
    """Quick liveness check; also reports FMU file presence and active sessions."""
    return {
        "status": "ok",
        "fmu_ready": DEFAULT_FMU.exists(),
        "fmu_path": str(DEFAULT_FMU),
        "active_sessions": len(_sessions),
    }
