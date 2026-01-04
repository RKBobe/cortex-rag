import os
import shutil
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# LlamaIndex Imports
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
import chromadb

# Import our Ingestion logic (ensure ingest.py is in the same folder)
from ingest import ingest_repository

# 1. SETUP
load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI(title="Cortex RAG API")

# Allow the frontend to talk to us (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to hold the active "Brain"
query_engine = None

#Configure AI Models
Settings.llm = GoogleGenAI(model="models/gemini-2.5-flash", api_key=GEMINI_API_KEY)
Settings.embed_model = GoogleGenAIEmbedding(model="models/text-embedding-004", api_key=GEMINI_API_KEY)

# 2. HELPER: Load the Database
def load_chat_engine():
    """Loads the vector DB and prepares the chat engine."""
    global query_engine
    try:
        db = chromadb.PersistentClient(path="./chroma_db")
        # Check if collection exists
        chroma_collection = db.get_collection("cortex_repo")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context,
        )
        # Create the query engine (chat interface)
        query_engine = index.as_query_engine()
        print("Chat Engine Loaded and Ready!")
    except Exception:
        print("No existing database found. Please ingest a repository first.")
        query_engine = None
    except Exception as e:
        print(f"Error Loading Chat Engine: {e}")
        
# Load on startup
load_chat_engine()

#------ API MODELS ------
class IngestRequest(BaseModel):
    repo_url: str
    
class ChatRequest(BaseModel):
    message: str
    
#------API ENDPOINTS ------
@app.get("/")
def read_root():
    return {"status": "Cortex RAG API is running."}

@app.post("/ingest")
def endpoint_ingest(request: IngestRequest):
    """Endpoint to ingest a GitHub repository."""
    try: 
        # 1. Run the ingestion (this re-creates the DB)
        ingest_repository(request.repo_url)
        # 2. Reload the chat engine with the new data
        load_chat_engine()
        
        return {"message": f"Successfully ingested {request.repo_url}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/chat")
def endpoint_chat(request: ChatRequest):
    """Endpoint to chat with the ingested data."""
    global query_engine
    if not query_engine:
        raise HTTPException(status_code=400, detail="No ingested data found. Please ingest a repository first.")
    
    try: 
        response = query_engine.query(request.message)
        return {"response": str(response)}
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    