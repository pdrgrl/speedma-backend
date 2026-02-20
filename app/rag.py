from google import genai
from google.genai import types
from app.config import settings
from app.retrieval import retrieve

_client: genai.Client | None = None

SYSTEM_PROMPT = """You are an expert docent at the Faraday Museum, guiding visitors through
the Chamusca 1920 domestic energy management apparatus.

The apparatus consists of five main components:
  1. Crossley single-cylinder internal combustion engine (5–10 hp)
  2. ASEA DC dynamo (~3 kW, 115–160 V)
  3. ASEA 3-phase induction motor (3 hp, 380/120 V)
  4. Tudor open-cell lead-acid battery bank (60 cells, L1 type)
  5. Marble control board (voltmeters, ammeters, rheostat, double-selector switch)

Three historical operating scenarios:
  • Scenario A – House runs entirely on batteries (engine OFF)
  • Scenario B – Crossley engine charges batteries via DC dynamo (~1923)
  • Scenario C – AC grid charges batteries via induction motor + dynamo (~1930)

Guidelines:
- Answer ONLY from the provided context. If context is insufficient, say so clearly.
- Be educational, precise, and accessible to a museum visitor.
- When explaining procedures, be step-by-step.
- Never invent technical values not present in the retrieved context.
"""

def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def answer(
    query: str,
    focus_component: str | None = None,
    scenario_id: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    """
    Returns:
        {
          "answer":   str,
          "sources":  [{"source": ..., "source_type": ..., "chunk_index": ...}],
          "follow_ups": [str, str, str],
        }
    """
    retrieval = retrieve(query, focus_component=focus_component, scenario_id=scenario_id)
    chunks         = retrieval["chunks"]
    context_prelude = retrieval["context_prelude"]

    # Build context block
    context_parts = []
    if context_prelude:
        context_parts.append(f"[SYSTEM CONTEXT]\n{context_prelude}\n")
    for i, c in enumerate(chunks):
        src = c["metadata"].get("source", "unknown")
        context_parts.append(f"[Excerpt {i+1} | {src}]\n{c['text']}")

    context_block = "\n\n---\n\n".join(context_parts)

    user_message = f"{context_block}\n\n---\n\nQuestion: {query}"

    # Build contents list (system + optional history + new user turn)
    contents = []
    if history:
        for turn in history:
            contents.append(
                types.Content(
                    role=turn["role"],
                    parts=[types.Part.from_text(text=turn["content"])],
                )
            )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
    )

    client = _get_client()
    response = client.models.generate_content(
        model=settings.gen_model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,
            max_output_tokens=1024,
        ),
    )

    answer_text = response.text

    # Deduplicated source list
    seen, sources = set(), []
    for c in chunks:
        key = (c["metadata"].get("source"), c["metadata"].get("chunk_index"))
        if key not in seen:
            seen.add(key)
            sources.append({
                "source":       c["metadata"].get("source", ""),
                "source_type":  c["metadata"].get("source_type", ""),
                "chunk_index":  c["metadata"].get("chunk_index", 0),
                "score":       round(1.0 - c["distance"], 4),
            })

    follow_ups = _generate_follow_ups(query, answer_text)

    return {"answer": answer_text, "sources": sources, "follow_ups": follow_ups}


def _generate_follow_ups(query: str, answer_text: str) -> list[str]:
    client = _get_client()
    prompt = (
        f"Given this question about the Chamusca 1920 apparatus:\n\"{query}\"\n"
        f"And this answer:\n\"{answer_text[:500]}...\"\n\n"
        "Suggest exactly 3 short follow-up questions a museum visitor might ask next. "
        "Return only a plain numbered list, no explanations."
    )
    resp = client.models.generate_content(
        model=settings.gen_model,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.5, max_output_tokens=350),
    )
    lines = [
        l.lstrip("123456789. ").strip()
        for l in resp.text.strip().split("\n")
        if l.strip()
    ]
    return lines[:3]