from google import genai
from google.genai import types
from app.config import settings

_client: genai.Client | None = None

def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed up to 100 texts at once (Gemini API limit)."""
    client = _get_client()
    # Process in batches of 100
    all_embeddings = []
    for i in range(0, len(texts), 100):
        batch = texts[i : i + 100]
        resp = client.models.embed_content(
            model=settings.embed_model,
            contents=batch,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        all_embeddings.extend([e.values for e in resp.embeddings])
    return all_embeddings

def embed_query(text: str) -> list[float]:
    client = _get_client()
    resp = client.models.embed_content(
        model=settings.embed_model,
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return resp.embeddings[0].values