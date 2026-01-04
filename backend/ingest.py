import os
import shutil
import git
from dotenv import load_dotenv

# LlamaIndex Imports
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Setup Models
Settings.llm = GoogleGenAI(
    model="models/gemini-flash-latest", 
    api_key=GEMINI_API_KEY
)

Settings.embed_model = GoogleGenAIEmbedding(
    model="models/text-embedding-004", 
    api_key=GEMINI_API_KEY
)

CHROMA_DB_PATH = "./chroma_db"
TEMP_CLONE_DIR = "./temp_repos"

def clean_temp_dir():
    """Cleans up the temporary repo folder, handling Windows read-only git files."""
    if os.path.exists(TEMP_CLONE_DIR):
        try:
            def on_rm_error(func, path, exc_info):
                os.chmod(path, 0o777)
                func(path)
            shutil.rmtree(TEMP_CLONE_DIR, onerror=on_rm_error)
        except Exception as e:
            print(f"Warning: Could not clean up temp dir: {e}")

def ingest_repository(repo_url: str, collection_name: str):
    """Clones a repo and ingests it into a SPECIFIC Chroma collection."""
    print(f"🚀 Starting ingestion for: {repo_url} -> Collection: {collection_name}")
    
    clean_temp_dir()
    
    try:
        # A. CLONE REPO
        print("📦 Cloning repository...")
        git.Repo.clone_from(repo_url, TEMP_CLONE_DIR)
        
        # B. LOAD DATA
        required_exts = [
            ".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", 
            ".md", ".json", ".yaml", ".toml", ".txt"
        ]
        
        print("📂 Loading files...")
        reader = SimpleDirectoryReader(
            input_dir=TEMP_CLONE_DIR,
            recursive=True,
            required_exts=required_exts,
            exclude=["*.git*", "*node_modules*", "*__pycache__*", "*.lock"]
        )
        documents = reader.load_data()
        
        # Tag documents with metadata
        for doc in documents:
            doc.metadata["repo_url"] = repo_url
            doc.metadata["collection_name"] = collection_name

        print(f"📄 Loaded {len(documents)} documents.")

        # C. SETUP DATABASE (Targeting specific collection)
        print(f"💾 Setting up Vector Database in collection: {collection_name}...")
        db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        chroma_collection = db.get_or_create_collection(collection_name)
        
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # D. INDEXING
        print("🧠 Creating embeddings and indexing...")
        VectorStoreIndex.from_documents(
            documents, 
            storage_context=storage_context,
            show_progress=True
        )
        
        print(f"✅ Ingestion Complete! Stored in collection: '{collection_name}'")

    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        raise e
    finally:
        clean_temp_dir()