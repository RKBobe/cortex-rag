import os
import chromadb
import nest_asyncio
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LlamaIndex Imports
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

# Import Ingestion Script
try:
    from ingest import ingest_repository
except ImportError:
    ingest_repository = None
    print("⚠️ Warning: ingest.py not found.")

# --- 1. SETUP ---
# Patch asyncio for nested loops
nest_asyncio.apply()

# Load Env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found! Please check your .env file.")

# Configure Models
Settings.llm = GoogleGenAI(model="models/gemini-flash-latest", api_key=api_key)
Settings.embed_model = GoogleGenAIEmbedding(model="models/text-embedding-004", api_key=api_key)

CHROMA_DB_PATH = "./chroma_db"

app = FastAPI(title="Cortex API - Multi-Context")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"],
)

# --- 2. CONTEXT MANAGER ---
active_engines = {}

def get_chat_engine(context_id: str):
    """Lazy loader for chat engines."""
    if context_id in active_engines:
        return active_engines[context_id]
    
    if not os.path.exists(CHROMA_DB_PATH):
        return None

    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    try:
        chroma_collection = db.get_collection(context_id)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        index = VectorStoreIndex.from_vector_store(
            vector_store,
            embed_model=Settings.embed_model
        )
        
        engine = index.as_chat_engine(
            chat_mode="context",
            system_prompt=f"You are a specialized assistant for the '{context_id}' codebase."
        )
        active_engines[context_id] = engine
        return engine
    except Exception as e:
        print(f"⚠️ Context '{context_id}' not found: {e}")
        return None

# --- 3. DATA MODELS ---
class IngestRequest(BaseModel):
    repo_url: str
    repo_name: str

class ChatRequest(BaseModel):
    context_id: str  # <--- This is what was missing!
    message: str

# --- 4. ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "Cortex API is running"}

@app.get("/contexts")
def get_contexts():
    """Returns a list of all persistent repositories from disk."""
    try:
        if not os.path.exists(CHROMA_DB_PATH):
            return []
        
        db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        collections = db.list_collections()
        return [c.name for c in collections]
    except Exception as e:
        print(f"Error listing contexts: {e}")
        return []

@app.post("/ingest")
async def ingest_endpoint(request: IngestRequest):
    if not ingest_repository:
        raise HTTPException(status_code=500, detail="Ingestion script missing.")

    safe_name = "".join(c for c in request.repo_name if c.isalnum() or c in "_-")
    
    try:
        ingest_repository(request.repo_url, safe_name)
        
        # Reset engine if it exists to force reload
        if safe_name in active_engines:
            del active_engines[safe_name]
            
        return {"status": "success", "context_id": safe_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    engine = get_chat_engine(request.context_id)
    
    if not engine:
        raise HTTPException(status_code=404, detail="Context not found. Please ingest first.")

    try:
        response = await engine.achat(request.message)
        return {"response": str(response)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)