from typing import Optional
from app.embeddings import embed_query
from app.vector_store import get_collection
from app.config import settings
from graph.context_graph import summarize_subgraph, chroma_filters

# Canonical component slug → node ID in the graph
COMPONENT_MAP = {
    "crossley_engine":       "crossley_engine",
    "asea_dynamo":           "asea_dynamo",
    "asea_motor":            "asea_motor",
    "tudor_battery_bank":    "tudor_battery_bank",
    "marble_control_board":  "marble_control_board",
}

SCENARIO_MAP = {
    "A": "scenario_a",
    "B": "scenario_b",
    "C": "scenario_c",
}

def retrieve(
    query: str,
    focus_component: Optional[str] = None,
    scenario_id: Optional[str] = None,
    top_k: Optional[int] = None,
) -> dict:
    """
    Returns:
        {
          "chunks":          [{"text": ..., "metadata": ..., "distance": ...}, ...],
          "context_prelude": "Active components: ...",
        }
    """
    k = top_k or settings.top_k

    # 1. Resolve graph node IDs from API hints
    node_ids: list[str] = []
    if focus_component and focus_component in COMPONENT_MAP:
        node_ids.append(COMPONENT_MAP[focus_component])
    if scenario_id and scenario_id.upper() in SCENARIO_MAP:
        node_ids.append(SCENARIO_MAP[scenario_id.upper()])

    # 2. Build graph context prelude and optional Chroma filter
    context_prelude = summarize_subgraph(node_ids) if node_ids else ""
    where_filter    = chroma_filters(node_ids) if node_ids else None

    # 3. Embed the query
    q_embedding = embed_query(query)

    # 4. Query Chroma
    col = get_collection()
    query_kwargs = dict(
        query_embeddings=[q_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    if where_filter:
        query_kwargs["where"] = where_filter

    results = col.query(**query_kwargs)

    chunks = [
        {
            "text":     doc,
            "metadata": meta,
            "distance": dist,
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]

    return {"chunks": chunks, "context_prelude": context_prelude}