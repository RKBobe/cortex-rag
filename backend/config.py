import os
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv

# Base directory of the backend folder
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from the root .env file
# This assumes the .env is in the project root (one level up from backend/)
load_dotenv(BASE_DIR.parent / ".env")

# --- Path Management ---
# DATA_ROOT is the base directory for all stored data (ChromaDB, registry, etc.)
# Defaults to the backend folder if not specified.
DATA_ROOT = os.getenv("CORTEX_DATA_ROOT", str(BASE_DIR))

# ChromaDB storage path
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(DATA_ROOT, "chroma_db"))

# Base directory for temporary clones
TEMP_BASE_DIR = os.getenv("TEMP_BASE_DIR", os.path.join(DATA_ROOT, "temp_repos"))

# Registry file for repo-to-context mapping
REGISTRY_FILE = os.getenv("REGISTRY_FILE", os.path.join(DATA_ROOT, "repo_registry.json"))

# --- Model Settings ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "models/gemini-1.5-flash-latest")
EMBED_MODEL = os.getenv("EMBED_MODEL", "models/text-embedding-004")

# --- Security ---
# A simple shared secret for API authentication
CORTEX_API_KEY = os.getenv("CORTEX_API_KEY", "dev-secret-key")

# --- Initialization ---
# Ensure core directories exist on startup
os.makedirs(CHROMA_DB_PATH, exist_ok=True)
os.makedirs(TEMP_BASE_DIR, exist_ok=True)

def get_unique_temp_dir() -> str:
    """Generates a unique subdirectory path within TEMP_BASE_DIR."""
    unique_id = str(uuid4())
    path = os.path.join(TEMP_BASE_DIR, unique_id)
    os.makedirs(path, exist_ok=True)
    return path

if not GEMINI_API_KEY:
    import logging
    logging.warning("GEMINI_API_KEY not found in environment variables. Gemini features will fail.")
