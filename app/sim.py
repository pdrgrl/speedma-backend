"""
app/sim.py
──────────
Server-side FMU execution layer.

One FMU2Slave per session.  Unity drives via /sim/* HTTP endpoints.

Variable metadata exposed per variable:
  type        ─ Real | Boolean | Integer | String
  causality   ─ input | output | local | parameter | independent
  variability ─ continuous | discrete | fixed | tunable | constant
  start       ─ initial/default value (may be None)
  min         ─ declared minimum (may be None)
  max         ─ declared maximum (may be None)
  description ─ docstring from model (may be empty)
  unit        ─ physical unit string (may be empty)
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any, Optional

from fmpy import extract, read_model_description
from fmpy.fmi2 import FMU2Slave

# ── Paths ─────────────────────────────────────────────────────────────────
FMU_DIR     = Path("./fmu")
DEFAULT_FMU = FMU_DIR / "chamusca.fmu"

# ── Session store ───────────────────────────────────────────────────
# { session_id: { fmu, vrs, meta, tmpdir, t, outputs, fmu_path } }
_sessions: dict[str, dict] = {}


def _safe(value) -> Optional[float]:
    """Convert fmpy attribute to Python scalar; return None if absent/nan."""
    if value is None:
        return None
    try:
        f = float(value)
        import math
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return None


def _load_fmu(fmu_path: Path) -> dict:
    """Extract FMU, instantiate FMU2Slave, enter initialisation mode."""
    if not fmu_path.exists():
        raise FileNotFoundError(f"FMU not found: {fmu_path}")

    tmpdir = extract(str(fmu_path))
    desc   = read_model_description(str(fmu_path))

    vrs:  dict[str, int]  = {}
    meta: dict[str, dict] = {}

    for v in desc.modelVariables:
        vrs[v.name] = v.valueReference

        # Unit: walk the chain unit → displayUnit if needed
        unit_str = ""
        try:
            if v.unit:
                unit_str = str(v.unit)
            elif v.declaredType and hasattr(v.declaredType, "unit") and v.declaredType.unit:
                unit_str = str(v.declaredType.unit)
        except Exception:
            pass

        # start value
        start_val = None
        try:
            start_val = _safe(v.start)
        except Exception:
            pass

        # min / max — may live on the variable itself or its declaredType
        min_val = _safe(getattr(v, "min", None))
        max_val = _safe(getattr(v, "max", None))
        if min_val is None and v.declaredType:
            min_val = _safe(getattr(v.declaredType, "min", None))
        if max_val is None and v.declaredType:
            max_val = _safe(getattr(v.declaredType, "max", None))

        meta[v.name] = {
            "vr":          v.valueReference,
            "type":        v.type,
            "causality":   v.causality,
            "variability": v.variability or "",
            "start":       start_val,
            "min":         min_val,
            "max":         max_val,
            "description": (v.description or "").strip(),
            "unit":        unit_str,
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


# ── Public API ─────────────────────────────────────────────────────

def start_session(fmu_path: Path | None = None) -> str:
    path = fmu_path or DEFAULT_FMU
    sid  = str(uuid.uuid4())
    _sessions[sid] = _load_fmu(path)
    return sid


def step_session(sid: str, dt: float, inputs: dict[str, Any]) -> dict[str, Any]:
    s    = _get_session(sid)
    fmu  = s["fmu"]
    vrs  = s["vrs"]
    meta = s["meta"]
    t    = s["t"]

    for name, value in inputs.items():
        if name not in meta or meta[name]["causality"] != "input":
            continue
        vr  = [vrs[name]]
        typ = meta[name]["type"]
        if typ == "Boolean":
            fmu.setBoolean(vr, [bool(value)])
        elif typ == "Integer":
            fmu.setInteger(vr, [int(value)])
        else:
            fmu.setReal(vr, [float(value)])

    fmu.doStep(currentCommunicationPoint=t, communicationStepSize=dt)
    s["t"] = t + dt

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
    """
    Return full metadata per variable:
      { name: { type, causality, variability, start, min, max, description, unit } }
    """
    s = _get_session(sid)
    return {
        name: {
            "type":        m["type"],
            "causality":   m["causality"],
            "variability": m["variability"],
            "start":       m["start"],
            "min":         m["min"],
            "max":         m["max"],
            "description": m["description"],
            "unit":        m["unit"],
        }
        for name, m in s["meta"].items()
    }


def _get_session(sid: str) -> dict:
    s = _sessions.get(sid)
    if s is None:
        raise KeyError(f"Unknown session: {sid}")
    return s
