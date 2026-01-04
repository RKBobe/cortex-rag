import os
import shutil
import git
from pathlib import Path
from dotenv import load_dotenv

# LlamaIndex Imports
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
# NEW IMPORTS for the V2 SDK
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# Load environment variables
load_dotenv()

# 1. SETUP: Configure Gemini and Embeddings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Use the new GoogleGenAI class
Settings.llm = GoogleGenAI(
    model="models/gemini-2.5-flash", 
    api_key=GEMINI_API_KEY
)

# Use the new GoogleGenAIEmbedding class
Settings.embed_model = GoogleGenAIEmbedding(
    model="models/text-embedding-004", 
    api_key=GEMINI_API_KEY
)

# Configuration
CHROMA_DB_PATH = "./chroma_db"
TEMP_CLONE_DIR = "./temp_repos"

def clean_temp_dir():
    """Cleans up the temporary repo folder."""
    if os.path.exists(TEMP_CLONE_DIR):
        try:
            def on_rm_error(func, path, exc_info):
                os.chmod(path, 0o777)
                func(path)
            shutil.rmtree(TEMP_CLONE_DIR, onerror=on_rm_error)
        except Exception as e:
            print(f"Warning: Could not clean up temp dir: {e}")

def ingest_repository(repo_url: str):
    """Clones a repo, ingests the code, and stores it in ChromaDB."""
    print(f"🚀 Starting ingestion for: {repo_url}")
    
    clean_temp_dir()
    
    try:
        # A. CLONE REPO
        print("📦 Cloning repository...")
        git.Repo.clone_from(repo_url, TEMP_CLONE_DIR)
        
        # B. LOAD DATA
        required_exts = [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp"]
        
        print("📂 Loading files...")
        reader = SimpleDirectoryReader(
            input_dir=TEMP_CLONE_DIR,
            recursive=True,
            required_exts=required_exts,
            exclude=["*.git*", "*node_modules*", "*__pycache__*"]
        )
        documents = reader.load_data()
        print(f"📄 Loaded {len(documents)} documents.")

        # C. SETUP DATABASE
        print("💾 Setting up Vector Database...")
        db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        chroma_collection = db.get_or_create_collection("cortex_repo")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # D. INDEXING
        print("🧠 Creating embeddings and indexing...")
        VectorStoreIndex.from_documents(
            documents, 
            storage_context=storage_context,
            show_progress=True
        )
        
        print("✅ Ingestion Complete! Repository stored in ChromaDB.")

    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
    finally:
        clean_temp_dir()

if __name__ == "__main__":
    # Test with Flask
    TEST_REPO = "https://github.com/pallets/flask"
    ingest_repository(TEST_REPO)