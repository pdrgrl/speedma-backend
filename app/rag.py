from google import genai
from google.genai import types
from app.config import settings
from app.retrieval import retrieve

_client: genai.Client | None = None

SYSTEM_PROMPTS = {
    "en": """You are an expert docent at the Faraday Museum, guiding visitors through
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
""",
    "pt": """É um guia especializado do Museu Faraday, orientando os visitantes através
do aparelho de gestão de energia doméstica da Chamusca de 1920.

O aparelho é composto por cinco componentes principais:
  1. Motor de combustão interna monocilíndrico Crossley (5–10 hp)
  2. Dínamo CC ASEA (~3 kW, 115–160 V)
  3. Motor de indução trifásico ASEA (3 hp, 380/120 V)
  4. Banco de baterias de chumbo-ácido de célula aberta Tudor (60 células, tipo L1)
  5. Painel de controlo de mármore (voltímetros, amperímetros, reóstato, interruptor seletor duplo)

Três cenários históricos de operação:
  • Cenário A – A casa funciona inteiramente com baterias (motor DESLIGADO)
  • Cenário B – O motor Crossley carrega as baterias através do dínamo CC (~1923)
  • Cenário C – A rede CA carrega as baterias através do motor de indução + dínamo (~1930)

Orientações:
- Responda APENAS com base no contexto fornecido. Se o contexto for insuficiente, diga-o claramente.
- Seja educativo, preciso e acessível a um visitante de museu.
- Ao explicar procedimentos, faça-o passo a passo.
- Nunca invente valores técnicos não presentes no contexto recuperado.
"""
}

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
    language: str = "en", # New parameter
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
    try:
        response = client.models.generate_content(
            model=settings.gen_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en"]), # Use dynamic system prompt
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )
        answer_text = response.text
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error generating main content from Gemini: {e}")
        # Return a generic error message to the user
        return {"answer": "Desculpe, ocorreu um erro ao processar a sua pergunta. Por favor, tente novamente mais tarde." if language == "pt" else "Sorry, an error occurred while processing your request. Please try again later.", "sources": [], "follow_ups": []}

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

    try:
        follow_ups = _generate_follow_ups(query, answer_text, language) # Pass language to follow-ups
    except Exception as e:
        print(f"Error generating follow-up questions from Gemini: {e}")
        follow_ups = [] # Return empty follow-ups if there's an error

    return {"answer": answer_text, "sources": sources, "follow_ups": follow_ups}


def _generate_follow_ups(query: str, answer_text: str, language: str) -> list[str]:
    client = _get_client()
    if language == "pt":
        prompt = (
            f"Dada esta pergunta sobre o aparelho Chamusca 1920:\n\"{query}\"\n"
            f"E esta resposta:\n\"{answer_text[:500]}...\"\n\n"
            "Sugira exatamente 3 perguntas de acompanhamento curtas que um visitante do museu poderia fazer a seguir. "
            "Retorne apenas uma lista numerada simples, sem explicações."
        )
    else: # default to en
        prompt = (
            f"Given this question about the Chamusca 1920 apparatus:\n\"{query}\"\n"
            f"And this answer:\n\"{answer_text[:500]}...\"\n\n"
            "Suggest exactly 3 short follow-up questions a museum visitor might ask next. "
            "Return only a plain numbered list, no explanations."
        )
    try:
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
    except Exception as e:
        print(f"Error in _generate_follow_ups: {e}")
        raise # Re-raise to be caught by the outer try-except in 'answer'