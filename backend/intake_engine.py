"""
CoreTexAI Memory Intake Engine
Proprietary product of Treelight Innovations.
Responsible for high-fidelity ingestion of external repositories into Memory Tiers.
"""
import os
import shutil
import git
import stat
import chromadb
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore

from core_config import settings
from database import SessionLocal, MemoryTier

def _on_rm_error(func, path, exc_info):
    """
    Treelight Innovations Proprietary Fix:
    Handles read-only file deletion errors on Windows (common in .git folders).
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

class MemoryIntakeEngine:
    """
    Handles the high-performance intake of data into the CoreTexAI vault.
    Optimized for Gemini 3.1 Pro embedding tiers.
    """

    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _update_status(self, tier_id: str, status: str, error: str = None):
        """Updates the relational registry with the current intake status."""
        db = SessionLocal()
        tier = db.query(MemoryTier).filter(MemoryTier.tier_id == tier_id).first()
        if tier:
            tier.status = status
            tier.error_log = error
            tier.last_synced = datetime.utcnow()
            db.commit()
        db.close()

    async def intake_repository(self, repo_url: str, tier_id: str):
        """
        Orchestrates the asynchronous intake of a Git repository.
        """
        self._update_status(tier_id, "ingesting")
        
        # Run the blocking Git/IO operations in a thread pool
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                self.executor, 
                self._process_repo_sync, 
                repo_url, 
                tier_id
            )
            self._update_status(tier_id, "completed")
        except Exception as e:
            self._update_status(tier_id, "failed", str(e))

    def _process_repo_sync(self, repo_url: str, tier_id: str):
        """
        Synchronous worker for cloning and indexing.
        Implements the Treelight Incremental Sync pattern.
        """
        temp_dir = os.path.join(settings.DATA_ROOT, "temp", tier_id)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, onerror=_on_rm_error)
        
        try:
            # 1. Secure Intake
            git.Repo.clone_from(repo_url, temp_dir, depth=1)

            # 2. Intelligence Extraction
            reader = SimpleDirectoryReader(
                input_dir=temp_dir,
                recursive=True,
                required_exts=[".py", ".ts", ".js", ".md", ".json", ".txt"]
            )
            documents = reader.load_data()

            # 3. Metadata Provenance Injection
            for doc in documents:
                doc.metadata.update({
                    "owner": "Treelight Innovations",
                    "engine": "CoreTexAI",
                    "tier": tier_id,
                    "source_url": repo_url
                })

            # 4. Vector Tier Persistence (Incremental Upsert)
            collection = self.chroma_client.get_or_create_collection(tier_id)
            vector_store = ChromaVectorStore(chroma_collection=collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Using Gemini 3.1 Pro via Settings (configured in main.py/orchestrator.py)
            VectorStoreIndex.from_documents(
                documents, 
                storage_context=storage_context
            )

        finally:
            # Low-overhead cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, onerror=_on_rm_error)
