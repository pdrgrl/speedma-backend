from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.routing import Route
from starlette.types import Scope, Receive, Send
from pydantic import BaseModel
from typing import Optional
from app.rag import answer as rag_answer
from app.sim_api import router as sim_router


# ── Paths ───────────────────────────────────────────────────────────────────
WEBGL_DIR = Path("./webgl")   # drop your Unity WebGL build here


# ── Custom static file handler with correct compression headers ─────────────
# Unity WebGL uses Brotli (.br) or gzip (.gz) compressed assets.
# Browsers require the correct Content-Encoding header to decode them;
# FastAPI's built-in StaticFiles does NOT add these headers automatically.

COMPRESSION_TYPES: dict[str, str] = {
    ".br":  "br",
    ".gz":  "gzip",
}

# Map the inner extension (after stripping .br/.gz) to its MIME type
MIME_OVERRIDE: dict[str, str] = {
    ".js":      "application/javascript",
    ".wasm":    "application/wasm",
    ".data":    "application/octet-stream",
    ".symbols.json": "application/json",
}


class UnityStaticFiles(StaticFiles):
    """StaticFiles subclass that injects Content-Encoding for .br/.gz files."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)

        full_path = Path(path)
        suffix     = full_path.suffix.lower()          # e.g. ".br"
        inner_name = full_path.stem.lower()            # e.g. "build.framework.js"
        inner_ext  = Path(inner_name).suffix.lower()   # e.g. ".js"

        if suffix in COMPRESSION_TYPES:
            response.headers["Content-Encoding"] = COMPRESSION_TYPES[suffix]
            # Override MIME so browser knows what to do after decompression
            mime = MIME_OVERRIDE.get(inner_ext, "application/octet-stream")
            response.headers["Content-Type"] = mime

        # Unity requires SharedArrayBuffer for threading; these headers enable it
        response.headers["Cross-Origin-Opener-Policy"]   = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        return response


# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(title="SPEEDMA Backend", version="0.3.0")

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# ── Simulation router ────────────────────────────────────────────────────
app.include_router(sim_router)


# ── RAG models ────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    history: Optional[list[Message]] = None
    focus_component: Optional[str] = None
    scenario_id: Optional[str] = None

class SourceRef(BaseModel):
    source: str
    source_type: str
    chunk_index: int
    score: float = 0.0

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceRef]
    follow_ups: list[str]


# ── RAG + health endpoints ────────────────────────────────────────────────────

@app.get("/health")
def health():
    webgl_ready = (WEBGL_DIR / "index.html").exists()
    return {
        "status": "ok",
        "service": "speedma-backend",
        "version": "0.3.0",
        "webgl_ready": webgl_ready,
    }


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")
    history = (
        [{"role": m.role, "content": m.content} for m in req.history]
        if req.history else None
    )
    result = rag_answer(
        query=req.query,
        focus_component=req.focus_component,
        scenario_id=req.scenario_id,
        history=history,
    )
    return QueryResponse(
        answer=result["answer"],
        sources=[SourceRef(**s) for s in result["sources"]],
        follow_ups=result["follow_ups"],
    )


# ── Serve landing page at / ──────────────────────────────────────────────────
# This must come AFTER all API routes so it doesn't shadow them.

@app.get("/", include_in_schema=False)
def serve_index():
    index = WEBGL_DIR / "index.html"
    if not index.exists():
        raise HTTPException(
            status_code=503,
            detail="WebGL build not deployed yet. Drop your Unity build into the webgl/ folder."
        )
    return FileResponse(str(index))


# Mount static files last – catches everything not matched by API routes above.
if WEBGL_DIR.exists():
    app.mount(
        "/",
        UnityStaticFiles(directory=str(WEBGL_DIR), html=True),
        name="webgl",
    )
