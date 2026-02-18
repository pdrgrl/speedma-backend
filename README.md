# SPEEDMA - RAG System

**Retrieval-Augmented Generation system for the SPEEDMA Digital Twin Project**

---

## 📖 About

This repository contains the RAG (Retrieval-Augmented Generation) system for **SPEEDMA** — **S**imulation **P**latform for **E**arly 20th-Century **D**omestic **E**nergy **M**anagement **A**pparatus.

The RAG component provides intelligent query and retrieval capabilities for historical documentation, technical specifications, and museum archives related to a rare 1920s domestic hybrid energy system from Portugal.

---

## 🎯 Purpose

This system enables:

- **Historical Documentation Retrieval**: Query technical reports, equipment specifications, and historical records from Museu Faraday archives
- **Interactive Knowledge Base**: Natural language access to information about the thermal-electric hybrid system components
- **Research Support**: Assist historians, engineers, and students exploring early 20th-century electrification technology
- **Educational Content**: Provide contextual information within the Unity simulation environment

---

## 🏛️ Historical Context

The system documents a unique domestic energy installation originally located in Chamusca, Portugal, comprising:

1. **Crossley Thermal Engine** - Single-cylinder internal combustion engine (pre-1918)
2. **ASEA DC Dynamo** - 115V-160V generator, belt-driven (c.1918)
3. **ASEA Three-Phase Motor** - 3hp, 380V induction motor (c.1929)
4. **Tudor Lead-Acid Battery Bank** - 60 open-cell batteries in series
5. **Marble Control Board** - Voltmeters, ammeters, switches, and rheostats

The system evolved through three technological phases:
- **Mechanical Phase** (pre-1918): Crossley engine only
- **DC Electrification** (1918-1923): Addition of dynamo and battery bank
- **AC Integration** (c.1929): Integration with public electrical grid

---

## 🔗 Related Repositories

This RAG system is part of the larger SPEEDMA Digital Twin project:

- **[speedma-unity](https://github.com/Dreadfxl/speedma-unity)** - Interactive simulation and runtime environment (Unity)
- **speedma-blender** *(coming soon)* - 3D modeling and digital restoration (Blender)

---

## 🗂️ Knowledge Base Sources

Primary documentation from Museu Faraday, Instituto Superior Técnico:

- Technical inventories and component specifications
- Historical photographs of the original installation
- Equipment nameplate transcriptions (dates, serial numbers, electrical ratings)
- Schematic diagrams of DC distribution and battery regulation topology
- Conservation and restoration reports

---

## 🛠️ Technology Stack

*(To be implemented)*

- **Vector Database**: For document embeddings and semantic search
- **Embedding Model**: For text vectorization
- **LLM Integration**: For natural language query processing
- **API Layer**: RESTful interface for Unity integration

---

## 🚀 Planned Features

- [ ] Document ingestion pipeline for PDF technical reports
- [ ] Vector database setup and indexing
- [ ] Natural language query interface
- [ ] API endpoints for Unity simulation queries
- [ ] Historical context retrieval by component
- [ ] Temporal search (by date/era)
- [ ] Citation and source tracking

---

## 📚 Documentation

Detailed documentation will be added as the system develops, including:

- Architecture overview
- API reference
- Query examples
- Integration guide for Unity

---

## 🤝 Collaboration

This project is developed in collaboration with:

- **Museu Faraday** - Instituto Superior Técnico (IST), Universidade de Lisboa
- **ISEL** - Instituto Superior de Engenharia de Lisboa

---

## 📄 License

*(To be determined)*

---

## 🙏 Acknowledgements

Special thanks to Eng. Miguel Tavares Pestana for donating the Chamusca estate equipment to Museu Faraday, and to the museum team for technical documentation and restoration expertise.

---

**Project Lead**: Pedro Grilo  
**Institution**: Instituto Superior de Engenharia de Lisboa (ISEL)  
**Date**: February 2026
