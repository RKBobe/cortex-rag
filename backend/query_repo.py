import os
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

# Centralized configuration
from config import CHROMA_DB_PATH, GEMINI_API_KEY, LLM_MODEL, EMBED_MODEL

# 1. SETUP
Settings.llm = GoogleGenAI(model=LLM_MODEL, api_key=GEMINI_API_KEY)
Settings.embed_model = GoogleGenAIEmbedding(model=EMBED_MODEL, api_key=GEMINI_API_KEY)

COLLECTION_NAME = "cortex_repo"

def start_chat():
    print(f"🔌 Connecting to Vector Store at {CHROMA_DB_PATH}...")

    # 2. CONNECT TO DATABASE
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    try:
        chroma_collection = db.get_collection(COLLECTION_NAME)
    except Exception as e:
        print(f"❌ Collection '{COLLECTION_NAME}' not found. Did you run ingestion.py?")
        return

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    
    # 3. LOAD INDEX
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=Settings.embed_model
    )

    # 4. CREATE CHAT ENGINE
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
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit', 'q']:
                break
            
            # Streaming response feels faster
            response = chat_engine.stream_chat(user_input)
            print("\nAI: ", end="", flush=True)
            for token in response.response_gen:
                print(token, end="", flush=True)
            print("\n" + "-"*50 + "\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    start_chat()