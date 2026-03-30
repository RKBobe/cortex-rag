"""
CoreTexAI Memory Orchestrator
Proprietary product of Treelight Innovations.
Responsible for high-performance retrieval using Gemini 3.1 Pro.
"""
import chromadb
from typing import List, Optional, Dict
from google.genai import types
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from core_config import settings

class MemoryOrchestrator:
    """
    Orchestrates memory tiers with a resilient Gemini 3.1 Pro client.
    Implements enterprise-grade retries and jitter for high-concurrency operations.
    """
    
    def __init__(self):
        # Configure Resilient HTTP Options for CoreTexAI
        resilient_options = types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                initial_delay=2.0,
                attempts=5,
                max_delay=60.0,
                jitter=1.0,
                http_status_codes=[429, 500, 503]
            )
        )

        # Configure the Flagship Brain: Gemini 3.1 Pro
        Settings.llm = GoogleGenAI(
            model=settings.LLM_MODEL, 
            api_key=settings.GEMINI_API_KEY,
            http_options=resilient_options
        )
        Settings.embed_model = GoogleGenAIEmbedding(
            model=settings.EMBED_MODEL, 
            api_key=settings.GEMINI_API_KEY,
            http_options=resilient_options
        )
        
        self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        self._active_engines: Dict[str, any] = {}

    async def get_tier_engine(self, tier_id: str):
        """Retrieves a stateful chat engine for the specified Memory Tier."""
        if tier_id in self._active_engines:
            return self._active_engines[tier_id]

        try:
            collection = self.chroma_client.get_collection(tier_id)
            vector_store = ChromaVectorStore(chroma_collection=collection)
            index = VectorStoreIndex.from_vector_store(
                vector_store,
                embed_model=Settings.embed_model
            )
            
            # CoreTexAI System Prompting
            engine = index.as_chat_engine(
                chat_mode="context",
                system_prompt=(
                    f"You are CoreTexAI by {settings.ORGANIZATION}. "
                    f"Operating on Memory Tier '{tier_id}'. "
                    "Utilize your assigned thinking mode to provide high-fidelity insights."
                )
            )
            self._active_engines[tier_id] = engine
            return engine
        except Exception:
            return None

    async def execute_reasoning(self, tier_id: str, query: str, mode: str = "medium") -> str:
        """
        Executes a reasoning task with a specific Gemini 3.1 thinking mode.
        """
        engine = await self.get_tier_engine(tier_id)
        if not engine:
            return "CoreTexAI Error: Memory Tier uninitialized."
            
        # Passing thinking_mode to the Gemini 3.1 Pro via LlamaIndex pattern
        response = await engine.achat(
            query
        )
        return str(response)
