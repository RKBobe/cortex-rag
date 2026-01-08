import os
import json
import shutil
import chromadb
import nest_asyncio
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LlamaIndex Imports
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

# Import Ingestion Scripts
try:
    from ingest import ingest_repository, ingest_single_file
except ImportError:
    ingest_repository = None
    print("⚠️ Warning: ingest.py not found.")

# --- 1. SETUP ---
nest_asyncio.apply()

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found! Please check your .env file.")

# ---------------------------

if not api_key:
    raise ValueError("GEMINI_API_KEY not found!")

Settings.llm = GoogleGenAI(model="models/gemini-flash-latest", api_key=api_key)
Settings.embed_model = GoogleGenAIEmbedding(model="models/text-embedding-004", api_key=api_key)

DATA_DRIVE_ROOT = r"D:\cortex_archive"  # Adjust as needed
CHROMA_DB_PATH = os.path.join(DATA_DRIVE_ROOT, "chroma_db")
REGISTRY_FILE = "repo_registry.json" # Maps Repo URLs to Context IDs

app = FastAPI(title="Cortex API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"],
)

# --- 2. HELPERS ---
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

def save_registry(url, context_id):
    """Saves the mapping of Repo URL -> Context ID so webhooks work."""
    data = {}
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}
    
    data[url] = context_id
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f)

def get_context_by_url(url):
    """Finds which context belongs to a Git URL."""
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            data = json.load(f)
        # Try exact match, or match with/without .git suffix
        if url in data: return data[url]
        if url + ".git" in data: return data[url + ".git"]
        if url.replace(".git", "") in data: return data[url.replace(".git", "")]
    return None

async def reingest_background(url, context):
    """Background task to update repo without blocking the webhook response."""
    print(f"🔄 Auto-updating {context} from {url}...")
    try:
        ingest_repository(url, context)
        # Force reload of engine
        if context in active_engines:
            del active_engines[context]
        print(f"✅ Auto-update complete for {context}")
    except Exception as e:
        print(f"❌ Auto-update failed: {e}")

# --- 3. DATA MODELS ---
class IngestRequest(BaseModel):
    repo_url: str
    repo_name: str

class ChatRequest(BaseModel):
    context_id: str
    message: str

# --- 4. ENDPOINTS ---

@app.get("/contexts")
def get_contexts():
    try:
        if not os.path.exists(CHROMA_DB_PATH): return []
        db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        return [c.name for c in db.list_collections()]
    except: return []

@app.get("/context/{context_id}/files")
def get_context_files(context_id: str):
    """Lists files in a context."""
    if not os.path.exists(CHROMA_DB_PATH): return []
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    try:
        col = db.get_collection(context_id)
        result = col.get(include=["metadatas"])
        files = set()
        for meta in result['metadatas']:
            path = meta.get('file_path') or meta.get('file_name') or meta.get('filename') or "unknown"
            # Clean path presentation
            clean_path = path.replace("\\", "/").split("temp_repos/")[-1]
            files.add(clean_path)
        return sorted(list(files))
    except: return []

@app.post("/ingest")
async def ingest_endpoint(request: IngestRequest):
    safe_name = "".join(c for c in request.repo_name if c.isalnum() or c in "_-")
    try:
        ingest_repository(request.repo_url, safe_name)
        
        # SAVE TO REGISTRY FOR AUTO-UPDATES
        save_registry(request.repo_url, safe_name)
        
        if safe_name in active_engines:
            del active_engines[safe_name]
        return {"status": "success", "context_id": safe_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/file")
async def upload_file_endpoint(context_id: str = Form(...), file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        ingest_single_file(temp_path, context_id, file.filename)
        
        if context_id in active_engines:
            del active_engines[context_id]
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    engine = get_chat_engine(request.context_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Context not found")
    try:
        response = await engine.achat(request.message)
        return {"response": str(response)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives 'push' events from GitHub.
    Finds the context associated with the repo URL and triggers re-ingestion.
    """
    try:
        payload = await request.json()
        if 'repository' not in payload:
            return {"status": "ignored", "reason": "No repo data"}
            
        repo_url = payload['repository']['html_url']
        
        # Lookup Context ID from Registry
        context_id = get_context_by_url(repo_url)
        
        if not context_id:
            return {"status": "ignored", "reason": f"Repo {repo_url} not tracked"}
            
        # Trigger Background Update
        background_tasks.add_task(reingest_background, repo_url, context_id)
        
        return {"status": "accepted", "context": context_id}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)