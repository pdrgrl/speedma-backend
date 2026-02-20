# SPEEDMA - AI & Context Graph Engine

**Context-Aware Retrieval-Augmented Generation (RAG) backend for the SPEEDMA Digital Twin Project**

---

## 📖 About

This repository contains the intelligence layer for **SPEEDMA** — **S**imulation **P**latform for **E**arly 20th-Century **D**omestic **E**nergy **M**anagement **A**pparatus.

Initially conceived as a pure RAG system, this backend has evolved into a **Context Graph-Augmented RAG**. It uses an explicit domain ontology (graph) of the Chamusca 1920 hybrid energy system to actively steer semantic retrieval and structure LLM reasoning. This ensures historical accuracy, multi-hop reasoning, and coherent narrative generation for users exploring the Unity 3D digital twin.

---

## 🏗️ Architecture

The backend follows an "Infrastructure before Interface" philosophy, serving as a headless REST API for the Unity frontend.

1. **Context Graph Layer (NetworkX):** Models the static ontology (Components, Scenarios, Phases, Procedures, Risks) and their relationships (`ACTIVE_IN`, `REQUIRES`, `CAUSES`, etc.).
2. **Vector Store (ChromaDB):** Stores chunked historical reports, battery manuals, and authored museum docent content.
3. **Embeddings & LLM (Google Gemini 2.0 Flash):** Uses `gemini-embedding-001` for vectorization and `gemini-2.0-flash` for high-speed, educational answer generation.
4. **API Layer (FastAPI):** Exposes `/query` endpoints for Unity to consume without exposing API keys to the client.

---

## 🏛️ Historical Context

The system documents a unique domestic energy installation originally located in Chamusca, Portugal, comprising:

1. **Crossley Thermal Engine** - Single-cylinder internal combustion engine (5-10 hp)
2. **ASEA DC Dynamo** - 3kW, 115V-160V generator, belt-driven
3. **ASEA Three-Phase Motor** - 3hp, 380V induction motor
4. **Tudor Lead-Acid Battery Bank** - 60 open-cell batteries in series
5. **Marble Control Board** - Voltmeters, ammeters, switches, and rheostats

### Operational Scenarios Supported
- **Scenario A:** House runs entirely on batteries (engine OFF)
- **Scenario B:** Crossley engine charges batteries via DC dynamo (c.1923)
- **Scenario C:** AC grid charges batteries via induction motor + dynamo (c.1930)

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.11+
- `google-genai` SDK
- `chromadb`
- `fastapi` & `uvicorn`
- `networkx`
- `pypdf`

### 2. Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key
EMBED_MODEL=gemini-embedding-001
GEN_MODEL=gemini-2.0-flash
CHROMA_PATH=./chroma_db
GRAPH_PATH=./graph/static_graph.json
CORPUS_PATH=./corpus
TOP_K=6
```

### 4. Running the Server
```bash
uvicorn app.api:app --reload --port 8000
```
*API documentation will be available at `http://localhost:8000/docs`*

---

## 🔗 Related Repositories

This backend is part of the larger SPEEDMA Digital Twin project:

- **[speedma-unity](https://github.com/Dreadfxl/speedma-unity)** - Interactive simulation and runtime environment (Unity)
- **speedma-blender** *(coming soon)* - 3D modeling and digital restoration (Blender)

---

## 🤝 Collaboration

This project is developed in collaboration with:
- **Museu Faraday** - Instituto Superior Técnico (IST), Universidade de Lisboa
- **ISEL** - Instituto Superior de Engenharia de Lisboa

**Project Lead**: Pedro Grilo  
**Institution**: Instituto Superior de Engenharia de Lisboa (ISEL)  
**Date**: February 2026
