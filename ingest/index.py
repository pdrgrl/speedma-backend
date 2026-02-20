import re, uuid
from pathlib import Path
from typing import List, Dict, Any
from ingest.extract import extract_file

CHUNK_SIZE   = 1000   # target tokens (~750 words)
CHUNK_OVERLAP = 150

def _split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE,
                        overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Simple word-level sliding window chunker."""
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def build_chunks_from_file(
    file_path: str,
    source_type: str,       # "museum_report" | "battery_manual" | "paper" | "authored"
    component: str = "",    # e.g. "tudor_battery_bank"
    scenario: str = "",     # e.g. "B"
    phase: str = "",        # e.g. "dc"
) -> List[Dict[str, Any]]:
    text = extract_file(file_path)
    raw_chunks = _split_into_chunks(text)
    return [
        {
            "id":   str(uuid.uuid4()),
            "text": chunk,
            "metadata": {
                "source":       Path(file_path).name,
                "source_type":  source_type,
                "component":    component,
                "scenario":     scenario,
                "phase":        phase,
                "chunk_index":  idx,
            },
        }
        for idx, chunk in enumerate(raw_chunks)
    ]