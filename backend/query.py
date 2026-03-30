import os
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

# Centralized configuration
from config import CHROMA_DB_PATH, GEMINI_API_KEY, LLM_MODEL, EMBED_MODEL

# 1. SETUP
Settings.llm = GoogleGenAI(model=LLM_MODEL, api_key=GEMINI_API_KEY)
Settings.embed_model = GoogleGenAIEmbedding(model=EMBED_MODEL, api_key=GEMINI_API_KEY)

# 2. LOAD DATABASE
db = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Get the collection we created earlier (assuming 'cortex_repo' exists for testing)
try:
    chroma_collection = db.get_collection("cortex_repo")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    # 3. CREATE QUERY ENGINE
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
    )

    query_engine = index.as_query_engine()

    # 4. ASK A QUESTION
    question = "How does this codebase handle ingestion?"
    print(f"\n❓ Question: {question}\n")

    response = query_engine.query(question)
    print(f"🤖 Answer:\n{response}")
except Exception as e:
    print(f"⚠️ Error loading collection: {e}")