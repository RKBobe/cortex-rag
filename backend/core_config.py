"""
CoreTexAI Configuration Engine
Proprietary product of Treelight Innovations. 
Responsible for tiered memory pathing and Gemini 3.1 Pro orchestration.
"""
from pydantic_settings import BaseSettings
from pathlib import Path
import os

class CoreTexSettings(BaseSettings):
    """
    Standardized configuration for the CoreTexAI Memory Orchestration Engine.
    Prioritizes Gemini 3.1 Pro with three-tier thinking (Low/Medium/High).
    """
    # Brand Identity
    PROJECT_NAME: str = "CoreTexAI"
    ORGANIZATION: str = "Treelight Innovations"
    VERSION: str = "1.0.0-Flagship"

    # Memory Tiers (Pathing)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_ROOT: Path = Path(os.getenv("CORETEX_DATA_ROOT", str(BASE_DIR / "vault")))
    CHROMA_PATH: str = str(DATA_ROOT / "vector_tier")
    SQL_PATH: str = f"sqlite:///{DATA_ROOT}/registry.sqlite"
    
    # Model Orchestration (Gemini 3.1 Pro)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # Gemini 3.1 Pro is the new flagship series
    LLM_MODEL: str = "models/gemini-3.1-pro-preview"
    EMBED_MODEL: str = "models/text-embedding-004"
    
    # Thinking Modes: 'low', 'medium', 'high'
    THINKING_MODE: str = os.getenv("CORETEX_THINKING", "medium")

    # Security Gateway
    CORETEX_API_KEY: str = os.getenv("CORETEX_API_KEY", "treelight-innovation-secure-vault")

    class Config:
        # Load .env from project root (base_dir)
        env_file = Path(__file__).resolve().parent.parent / ".env"
        extra = "ignore"

settings = CoreTexSettings()

# Ensure Vault Hierarchy Exists
os.makedirs(settings.CHROMA_PATH, exist_ok=True)
