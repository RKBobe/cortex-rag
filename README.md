# Cortex-RAG

**Cortex-RAG** is a sophisticated Retrieval-Augmented Generation (RAG) agent designed for context-aware chat. Developed by **Treelight Innovations**, it leverages a modern web stack and advanced vector retrieval to allow users to interact with their data in a natural, conversational manner.

---

## 🚀 Overview
The "Cortex" engine acts as a bridge between raw data and Large Language Models (LLMs). It processes documents, stores them in a vector database, and retrieves the most relevant information to augment the generation process, ensuring responses are grounded in specific, provided contexts.

### Key Features
* **Context-Aware Chat:** Intelligent responses based on retrieved document fragments.
* **Modern UI/UX:** A clean, responsive interface built with React and TypeScript.
* **Robust Backend:** A high-performance Flask API handling orchestration and retrieval logic.
* **Efficient Vector Search:** Optimized for fast similarity searches to provide near-instantaneous context injection.

---

## 🛠 Tech Stack
* **Frontend:** React, TypeScript
* **Backend:** Flask (Python)
* **Storage:** Vector Database (RAG)
* **Orchestration:** Python-based RAG pipeline

---

## 📁 Project Structure
To maintain a clean codebase, detailed technical documentation is split across the respective service directories:

```text
cortex-rag/
├── backend/            # Flask API, Vector DB & RAG Logic (See /backend/README.md)
├── frontend/           # React + TypeScript App (See /frontend/README.md)
├── data/               # Local vector storage and document cache
└── docs/               # Technical documentation and architecture logs
