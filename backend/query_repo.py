import os
import chromadb
from dotenv import load_dotenv

# LlamaIndex Imports
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# 1. SETUP: Must match the Ingestion config exactly
Settings.llm = GoogleGenAI(
    model="models/gemini-flash-latest", 
    api_key=GEMINI_API_KEY
)

Settings.embed_model = GoogleGenAIEmbedding(
    model="models/text-embedding-004", 
    api_key=GEMINI_API_KEY
)

CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "cortex_repo"

def start_chat():
    print(f"🔌 Connecting to Vector Store at {CHROMA_DB_PATH}...")

    # 2. CONNECT TO DATABASE
    # We initialize the client and get the EXISTING collection
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    try:
        chroma_collection = db.get_collection(COLLECTION_NAME)
    except ValueError:
        print(f"❌ Collection '{COLLECTION_NAME}' not found. Did you run ingestion.py?")
        return

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    
    # 3. LOAD INDEX
    # crucial: We use from_vector_store, NOT from_documents
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=Settings.embed_model
    )

    # 4. CREATE CHAT ENGINE
    # "context" mode retrieves relevant code snippets and inserts them into the chat
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        system_prompt=(
            "You are a specialized code assistant. You have access to a specific codebase. "
            "Always answer questions based on the provided context from the repository. "
            "If the answer isn't in the code, say so."
        )
    )

    print("✅ System Ready! (Type 'exit' to quit)\n")

    # 5. CHAT LOOP
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            break
        
        try:
            # Streaming response feels faster
            response = chat_engine.stream_chat(user_input)
            print("\nAI: ", end="", flush=True)
            for token in response.response_gen:
                print(token, end="", flush=True)
            print("\n" + "-"*50 + "\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    start_chat()