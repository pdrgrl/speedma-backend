from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.rag import answer as rag_answer

app = FastAPI(title="Chamusca RAG API", version="0.1.0")


# ── Request / Response models ──────────────────────────────────────────────

class Message(BaseModel):
    role: str       # "user" | "model"
    content: str

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    history: Optional[list[Message]] = None
    focus_component: Optional[str] = None   # e.g. "tudor_battery_bank"
    scenario_id: Optional[str] = None       # "A" | "B" | "C"

class SourceRef(BaseModel):
    source: str
    source_type: str
    chunk_index: int

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceRef]
    follow_ups: list[str]


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "chamusca-rag"}


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