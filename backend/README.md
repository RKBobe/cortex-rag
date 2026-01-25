# Cortex-RAG Backend

This directory contains the core intelligence of the **Cortex-RAG** system. It is a high-performance **Flask API** that orchestrates document processing, vector embeddings, and the Retrieval-Augmented Generation (RAG) pipeline.

---

## 🏗 Backend Architecture

The backend is designed for modularity, separating the data ingestion flow from the conversational retrieval logic.

### 1. Ingestion Pipeline
* **Document Processing:** Handles PDF and text parsing.
* **Chunking Strategy:** Recursive character splitting to maintain semantic context.
* **Vectorization:** Converts text chunks into high-dimensional embeddings.
* **Storage:** Manages the indexing and retrieval via a local vector database.

### 2. RAG Logic
* **Context Retrieval:** Performs similarity searches to find relevant data for user queries.
* **Prompt Engineering:** Dynamically injects retrieved context into LLM system prompts.
* **Generation:** Interfaces with LLMs to produce grounded, hallucination-minimized responses.

---

## 🛠 API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/upload` | `POST` | Upload and index new documents. |
| `/api/chat` | `POST` | Send a query to receive a context-aware response. |
| `/api/documents` | `GET` | Retrieve a list of currently indexed files. |
| `/api/health` | `GET` | System and Vector DB status check. |

---

## 📋 Configuration & Environment
Create a `.env` file in the `backend/` root directory:

```bash
# LLM Provider Configuration
OPENAI_API_KEY=your_api_key_
