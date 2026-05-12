"""
app/sim_api.py
──────────────
FastAPI router that exposes the FMU simulation service to Unity WebGL.

Endpoints
─────────
  GET  /sim/list           → { fmus: ["name.fmu", ...] }
  POST /sim/start          → { session_id }
  POST /sim/step           → { session_id, t, outputs }
  POST /sim/reset          → { ok }
  POST /sim/stop           → { ok }
  GET  /sim/state/{sid}    → { t, outputs }
  GET  /sim/variables/{sid}→ { variables: {name: {type, causality}} }
  GET  /sim/health         → { status, fmu_ready, sessions }
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.sim import (
    DEFAULT_FMU,
    FMU_DIR,
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
    fmu_name: Optional[str] = None   # filename inside fmu/ folder, e.g. "chamusca.fmu"

class StartResponse(BaseModel):
    session_id: str
    fmu_name: str

class StepRequest(BaseModel):
    session_id: str
    dt: float = 0.02
    inputs: dict[str, Any] = {}

class StepResponse(BaseModel):
    session_id: str
    t: float
    outputs: dict[str, Any]

class SessionRequest(BaseModel):
    session_id: str

class OkResponse(BaseModel):
    ok: bool = True


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/list")
def sim_list():
    """Return all .fmu files found in the fmu/ directory."""
    fmus = sorted(p.name for p in FMU_DIR.glob("*.fmu"))
    return {"fmus": fmus}


@router.post("/start", response_model=StartResponse)
def sim_start(req: StartRequest = StartRequest()):
    """
    Allocate a new FMU instance.
    Pass fmu_name to select a specific FMU, omit to use the default.
    """
    if req.fmu_name:
        fmu_path = FMU_DIR / req.fmu_name
    else:
        fmu_path = DEFAULT_FMU
    try:
        sid = start_session(fmu_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FMU load error: {e}")
    return StartResponse(session_id=sid, fmu_name=fmu_path.name)


@router.post("/step", response_model=StepResponse)
def sim_step(req: StepRequest):
    try:
        outputs = step_session(req.session_id, req.dt, req.inputs)
        t = _sessions[req.session_id]["t"]
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step error: {e}")
    return StepResponse(session_id=req.session_id, t=t, outputs=outputs)


@router.post("/reset", response_model=OkResponse)
def sim_reset(req: SessionRequest):
    try:
        reset_session(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset error: {e}")
    return OkResponse()


@router.post("/stop", response_model=OkResponse)
def sim_stop(req: SessionRequest):
    stop_session(req.session_id)
    return OkResponse()


@router.get("/state/{session_id}")
def sim_state(session_id: str):
    try:
        return get_state(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/variables/{session_id}")
def sim_variables(session_id: str):
    """Return {name: {type, causality}} for every FMU variable."""
    try:
        return {"variables": list_variables(session_id)}
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/health")
def sim_health():
    return {
        "status": "ok",
        "fmu_dir": str(FMU_DIR),
        "default_fmu_ready": DEFAULT_FMU.exists(),
        "active_sessions": len(_sessions),
    }
