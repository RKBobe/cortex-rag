import os
import shutil
import git
from pathlib import Path
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings, Document
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

Settings.embed_model = GoogleGenAIEmbedding(
    model="models/text-embedding-004", 
    api_key=GEMINI_API_KEY
)

CHROMA_DB_PATH = "./chroma_db"
TEMP_CLONE_DIR = "./temp_repos"

def get_chroma_vector_store(collection_name):
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    chroma_collection = db.get_or_create_collection(collection_name)
    return ChromaVectorStore(chroma_collection=chroma_collection)

def ingest_repository(repo_url: str, collection_name: str):
    if os.path.exists(TEMP_CLONE_DIR):
        try:
            shutil.rmtree(TEMP_CLONE_DIR)
        except:
            pass

    print(f"?? Ingesting Repo: {repo_url} -> {collection_name}")
    try:
        git.Repo.clone_from(repo_url, TEMP_CLONE_DIR)
        
        required_exts = [".py", ".js", ".ts", ".html", ".css", ".md", ".json", ".txt", ".java", ".cpp"]
        reader = SimpleDirectoryReader(
            input_dir=TEMP_CLONE_DIR,
            recursive=True,
            required_exts=required_exts,
            exclude=["*.git*", "*node_modules*"]
        )
        documents = reader.load_data()
        
        for doc in documents:
            doc.metadata.update({"source_type": "git_repo", "repo_url": repo_url, "collection": collection_name})

        db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        try:
            db.delete_collection(collection_name)
        except:
            pass 
            
        vector_store = get_chroma_vector_store(collection_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        print(f"? Repo synced to {collection_name}")
        
    except Exception as e:
        print(f"? Repo Ingestion Error: {e}")
        raise e
    finally:
        if os.path.exists(TEMP_CLONE_DIR):
            try:
                shutil.rmtree(TEMP_CLONE_DIR)
            except:
                pass

def ingest_single_file(file_path: str, collection_name: str, original_filename: str):
    print(f"?? Injecting file: {original_filename} -> {collection_name}")
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
        print(f"? File injected into {collection_name}")
        
    except Exception as e:
        print(f"? File Ingestion Error: {e}")
        raise e
