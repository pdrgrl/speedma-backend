"""
app/sim.py
──────────
Server-side FMU execution layer.

One FMU2Slave instance is kept alive per session (identified by a UUID).
Unity drives it via the /sim/* HTTP endpoints.

Session lifecycle
─────────────────
  POST /sim/start   → allocates FMU instance, returns session_id
  POST /sim/step    → advances simulation by dt, exchanges I/O
  POST /sim/reset   → re-initialises the FMU without freeing it
  POST /sim/stop    → terminates + frees the FMU instance
  GET  /sim/state   → returns last known outputs (no step)
  GET  /sim/list    → lists .fmu files in FMU_DIR
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

from fmpy import extract, read_model_description
from fmpy.fmi2 import FMU2Slave

# ── Paths ─────────────────────────────────────────────────────────────────
FMU_DIR     = Path("./fmu")
DEFAULT_FMU = FMU_DIR / "chamusca.fmu"

# ── In-memory session store ──────────────────────────────────────────
# { session_id: { "fmu", "vrs", "meta", "tmpdir", "t", "outputs", "fmu_path" } }
_sessions: dict[str, dict] = {}


def _load_fmu(fmu_path: Path) -> dict:
    """Extract FMU, instantiate FMU2Slave, enter initialisation mode."""
    if not fmu_path.exists():
        raise FileNotFoundError(f"FMU not found: {fmu_path}")

    tmpdir = extract(str(fmu_path))
    desc   = read_model_description(str(fmu_path))

    # Build variable metadata: { name: { vr, type, causality } }
    # causality: 'input' | 'output' | 'parameter' | 'local' | 'independent'
    vrs:  dict[str, int] = {}
    meta: dict[str, dict] = {}
    for v in desc.modelVariables:
        vrs[v.name] = v.valueReference
        meta[v.name] = {
            "vr":        v.valueReference,
            "type":      v.type,        # 'Real' | 'Boolean' | 'Integer' | 'String'
            "causality": v.causality,   # 'input' | 'output' | 'parameter' | 'local'
        }

    fmu = FMU2Slave(
        guid=desc.guid,
        unzipDirectory=tmpdir,
        modelIdentifier=desc.coSimulation.modelIdentifier,
        instanceName=str(uuid.uuid4()),
    )
    fmu.instantiate()
    fmu.setupExperiment(startTime=0.0)
    fmu.enterInitializationMode()
    fmu.exitInitializationMode()

    return {
        "fmu":      fmu,
        "vrs":      vrs,
        "meta":     meta,
        "tmpdir":   tmpdir,
        "t":        0.0,
        "outputs":  {},
        "fmu_path": fmu_path,
    }


def start_session(fmu_path: Path | None = None) -> str:
    path = fmu_path or DEFAULT_FMU
    sid  = str(uuid.uuid4())
    _sessions[sid] = _load_fmu(path)
    return sid


def step_session(sid: str, dt: float, inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Apply inputs, advance by dt, return all readable variable values.
    Only variables with causality 'input' are written.
    """
    s    = _get_session(sid)
    fmu  = s["fmu"]
    vrs  = s["vrs"]
    meta = s["meta"]
    t    = s["t"]

    # ── Apply inputs (only causality == 'input') ─────────────────────────
    for name, value in inputs.items():
        if name not in meta:
            continue
        if meta[name]["causality"] != "input":
            continue
        vr  = [vrs[name]]
        typ = meta[name]["type"]
        if typ == "Boolean":
            fmu.setBoolean(vr, [bool(value)])
        elif typ == "Integer":
            fmu.setInteger(vr, [int(value)])
        else:
            fmu.setReal(vr, [float(value)])

    # ── Advance ─────────────────────────────────────────────────────────
    fmu.doStep(currentCommunicationPoint=t, communicationStepSize=dt)
    s["t"] = t + dt

    # ── Read all output + local Reals/Booleans/Integers ───────────────────
    outputs: dict[str, Any] = {}
    for name, m in meta.items():
        if m["causality"] not in ("output", "local"):
            continue
        try:
            vr  = [m["vr"]]
            typ = m["type"]
            if typ == "Boolean":
                outputs[name] = fmu.getBoolean(vr)[0]
            elif typ == "Integer":
                outputs[name] = fmu.getInteger(vr)[0]
            elif typ == "Real":
                outputs[name] = fmu.getReal(vr)[0]
        except Exception:
            pass

    s["outputs"] = outputs
    return outputs


def reset_session(sid: str) -> None:
    s   = _get_session(sid)
    fmu = s["fmu"]
    fmu.reset()
    fmu.setupExperiment(startTime=0.0)
    fmu.enterInitializationMode()
    fmu.exitInitializationMode()
    s["t"]       = 0.0
    s["outputs"] = {}


def stop_session(sid: str) -> None:
    s = _sessions.pop(sid, None)
    if s is None:
        return
    try:
        s["fmu"].terminate()
        s["fmu"].freeInstance()
    except Exception:
        pass
    shutil.rmtree(s["tmpdir"], ignore_errors=True)


def get_state(sid: str) -> dict[str, Any]:
    s = _get_session(sid)
    return {"t": s["t"], "outputs": s["outputs"]}


def list_variables(sid: str) -> dict[str, dict]:
    """Return full metadata { name: {type, causality} } for the editor."""
    s = _get_session(sid)
    return {
        name: {"type": m["type"], "causality": m["causality"]}
        for name, m in s["meta"].items()
    }


def _get_session(sid: str) -> dict:
    s = _sessions.get(sid)
    if s is None:
        raise KeyError(f"Unknown session: {sid}")
    return s
