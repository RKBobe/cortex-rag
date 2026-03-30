import os
import shutil
import git
import stat
import chromadb
from pathlib import Path
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings, Document
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

# Centralized configuration
from config import CHROMA_DB_PATH, GEMINI_API_KEY, EMBED_MODEL, get_unique_temp_dir

Settings.embed_model = GoogleGenAIEmbedding(
    model=EMBED_MODEL, 
    api_key=GEMINI_API_KEY
)

# --- HELPER: Windows-safe directory deletion ---
def remove_readonly(func, path, excinfo):
    """
    Error handler for shutil.rmtree.
    If the file is read-only (common in .git folders), change it to writeable and try again.
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)

def cleanup_temp_dir(path: str):
    """Surgically deletes a specific temporary directory."""
    if os.path.exists(path):
        try:
            shutil.rmtree(path, onerror=remove_readonly)
        except Exception as e:
            print(f"Warning: Failed to clean up temp dir {path}: {e}")
# -----------------------------------------------

def get_chroma_vector_store(collection_name):
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    chroma_collection = db.get_or_create_collection(collection_name)
    return ChromaVectorStore(chroma_collection=chroma_collection)

def ingest_repository(repo_url: str, collection_name: str):
    # Create a unique temporary directory for this specific ingestion
    temp_dir = get_unique_temp_dir()

    print(f"🚀 Ingesting Repo: {repo_url} -> {collection_name} (Temp: {temp_dir})")
    try:
        git.Repo.clone_from(repo_url, temp_dir)
        
        required_exts = [".py", ".js", ".ts", ".html", ".css", ".md", ".json", ".txt", ".java", ".cpp"]
        reader = SimpleDirectoryReader(
            input_dir=temp_dir,
            recursive=True,
            required_exts=required_exts,
            exclude=["*.git*", "*node_modules*"]
        )
        documents = reader.load_data()
        
        for doc in documents:
            # Get relative path for cleaner display
            abs_path = doc.metadata.get("file_path", "")
            rel_path = os.path.relpath(abs_path, temp_dir) if abs_path else "unknown"
            
            doc.metadata.update({
                "source_type": "git_repo", 
                "repo_url": repo_url, 
                "collection": collection_name,
                "file_path": rel_path
            })

        db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        try:
            db.delete_collection(collection_name)
        except:
            pass 
            
        vector_store = get_chroma_vector_store(collection_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        print(f"✅ Repo synced to {collection_name}")
        
    except Exception as e:
        print(f"❌ Repo Ingestion Error: {e}")
        raise e
    finally:
        # Clean up ONLY this specific temporary directory
        cleanup_temp_dir(temp_dir)

def ingest_single_file(file_path: str, collection_name: str, original_filename: str):
    print(f"📂 Injecting file: {original_filename} -> {collection_name}")
    try:
        reader = SimpleDirectoryReader(input_files=[file_path])
        documents = reader.load_data()
        
        for doc in documents:
            doc.metadata.update({
                "source_type": "file_upload", 
                "filename": original_filename,
                "collection": collection_name
            })

        vector_store = get_chroma_vector_store(collection_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        print(f"✅ File injected into {collection_name}")
        
    except Exception as e:
        print(f"❌ File Ingestion Error: {e}")
        raise e