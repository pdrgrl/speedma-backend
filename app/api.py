from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from app.rag import answer as rag_answer
from app.sim_api import router as sim_router

app = FastAPI(title="SPEEDMA Backend", version="0.2.0")

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # narrow to your domain in production
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# ── Mount simulation router ───────────────────────────────────────────────
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


# ── RAG endpoints ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "speedma-backend", "version": "0.2.0"}


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
