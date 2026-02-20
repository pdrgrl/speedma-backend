import json
import networkx as nx
from typing import Optional
from app.config import settings

_G: Optional[nx.DiGraph] = None

def _load() -> nx.DiGraph:
    global _G
    if _G is None:
        with open(settings.graph_path) as f:
            data = json.load(f)
        G = nx.DiGraph()
        for n in data["nodes"]:
            G.add_node(n["id"], **{k: v for k, v in n.items() if k != "id"})
        for e in data["edges"]:
            G.add_edge(e["source"], e["target"], type=e["type"])
        _G = G
    return _G


def get_subgraph(node_ids: list[str], radius: int = 1) -> nx.DiGraph:
    """Return ego-graph around each node_id, merged."""
    G = _load()
    nodes = set()
    for nid in node_ids:
        if nid in G:
            ego = nx.ego_graph(G, nid, radius=radius, undirected=True)
            nodes |= set(ego.nodes())
    return G.subgraph(nodes)


def summarize_subgraph(node_ids: list[str], radius: int = 1) -> str:
    """
    Produce a compact natural-language paragraph describing the active
    subgraph — this becomes the 'context prelude' in the Gemini prompt.
    """
    sub = get_subgraph(node_ids, radius)
    G   = _load()

    components = [
        G.nodes[n]["label"]
        for n in sub.nodes()
        if G.nodes[n].get("type") == "Component"
    ]
    scenarios = [
        G.nodes[n]["label"]
        for n in sub.nodes()
        if G.nodes[n].get("type") == "Scenario"
    ]
    phases = [
        G.nodes[n]["label"]
        for n in sub.nodes()
        if G.nodes[n].get("type") == "Phase"
    ]
    procedures = [
        G.nodes[n]["label"]
        for n in sub.nodes()
        if G.nodes[n].get("type") == "Procedure"
    ]
    risks = [
        G.nodes[n]["label"]
        for n in sub.nodes()
        if G.nodes[n].get("type") == "Risk"
    ]

    parts = []
    if components:
        parts.append(f"Active components: {', '.join(components)}.")
    if scenarios:
        parts.append(f"Relevant scenarios: {', '.join(scenarios)}.")
    if phases:
        parts.append(f"Historical phases: {', '.join(phases)}.")
    if procedures:
        parts.append(f"Related procedures: {', '.join(procedures)}.")
    if risks:
        parts.append(f"Potential risks to keep in mind: {', '.join(risks)}.")

    return " ".join(parts) if parts else ""


def chroma_filters(node_ids: list[str]) -> Optional[dict]:
    """
    Derive Chroma `where` filter from the focused node set.
    Maps component node IDs to the `component` metadata field.
    Maps scenario labels ('scenario_a' → 'A') to the `scenario` field.
    """
    G = _load()
    comp_ids   = [nid for nid in node_ids if nid in G and G.nodes[nid].get("type") == "Component"]
    scen_ids   = [nid for nid in node_ids if nid in G and G.nodes[nid].get("type") == "Scenario"]

    filters: list[dict] = []
    if comp_ids:
        filters.append({"component": {"$in": comp_ids}})
    if scen_ids:
        letters = [sid.split("_")[-1].upper() for sid in scen_ids]
        filters.append({"scenario": {"$in": letters}})

    if not filters:
        return None
    if len(filters) == 1:
        return filters[0]
    return {"$or": filters}