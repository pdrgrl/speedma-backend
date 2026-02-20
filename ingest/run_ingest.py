"""Run once: python -m ingest.run_ingest"""
from ingest.index import build_chunks_from_file
from app.vector_store import get_collection
from app.embeddings import embed_texts

SOURCES = [
    # (path, source_type, component, scenario, phase)
    ("corpus/pdfs/Baterias-TUDOR.pdf",                 "battery_manual",  "tudor_battery_bank",    "",  "dc"),
    ("corpus/pdfs/Energia-Domestica-1920-Parte-I.pdf", "museum_report",   "",                      "",  ""),
    ("corpus/pdfs/Energia-Domestica-1920-11_04_23.pdf","museum_report",   "",                      "",  ""),
    ("corpus/pdfs/Simulation_Platform_for_an_Early_20th_Century_Domestic_Energy_Management_Apparatus.pdf",
                                                        "paper",           "",                      "",  ""),
]

def main():
    col = get_collection()
    for path, stype, comp, scen, phase in SOURCES:
        chunks = build_chunks_from_file(path, stype, comp, scen, phase)
        texts   = [c["text"]     for c in chunks]
        ids     = [c["id"]       for c in chunks]
        metas   = [c["metadata"] for c in chunks]
        embeddings = embed_texts(texts)
        col.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metas)
        print(f"  Indexed {len(chunks)} chunks from {path}")
    print("✓ Ingest complete")

if __name__ == "__main__":
    main()