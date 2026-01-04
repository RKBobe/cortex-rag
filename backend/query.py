import os
import chromadb
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

# 1. SETUP
load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

Settings.llm = GoogleGenAI(model="models/gemini-2.5-flash", api_key=GEMINI_API_KEY)
Settings.embed_model = GoogleGenAIEmbedding(model="models/text-embedding-004", api_key=GEMINI_API_KEY)

# 2. LOAD DATABASE
# We point to the SAME folder where ingest.py saved the data
CHROMA_DB_PATH = "./chroma_db"
db = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Get the collection we created earlier
chroma_collection = db.get_or_create_collection("cortex_repo")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

# 3. CREATE QUERY ENGINE
# This loads the index from disk without re-embedding everything
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_vector_store(
    vector_store,
    storage_context=storage_context,
)

query_engine = index.as_query_engine()

# 4. ASK A QUESTION
question = "How does Flask handle request context?"
print(f"\n❓ Question: {question}\n")

response = query_engine.query(question)
print(f"🤖 Answer:\n{response}")