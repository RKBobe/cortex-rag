import sys
import os
from unittest.mock import MagicMock
import pytest

# Add backend to python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# MOCK EXTERNAL DEPENDENCIES BEFORE IMPORTING APP MODULES
# This prevents them from trying to connect to real services

# Mock llama_index
mock_llama = MagicMock()
sys.modules["llama_index"] = mock_llama
sys.modules["llama_index.core"] = mock_llama
sys.modules["llama_index.embeddings.google_genai"] = MagicMock()
sys.modules["llama_index.llms.google_genai"] = MagicMock()
sys.modules["llama_index.vector_stores.chroma"] = MagicMock()

# Mock chromadb
mock_chroma = MagicMock()
sys.modules["chromadb"] = mock_chroma

# Mock git
mock_git = MagicMock()
sys.modules["git"] = mock_git

# DO NOT MOCK 'ingest' OR 'main' MODULES THEMSELVES
# We want to test their logic, using the mocked dependencies above.

@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    monkeypatch.setenv("DATA_ROOT", "./test_data")

    # Mock Git
    monkeypatch.setattr("git.Repo.clone_from", MagicMock())

    # Mock Chroma
    monkeypatch.setattr("chromadb.PersistentClient", MagicMock())

    # Mock LlamaIndex components
    monkeypatch.setattr("llama_index.core.VectorStoreIndex.from_documents", MagicMock())
    monkeypatch.setattr("llama_index.core.SimpleDirectoryReader", MagicMock())
    monkeypatch.setattr("llama_index.core.StorageContext.from_defaults", MagicMock())

    # Mock GoogleGenAIEmbedding to avoid API calls
    monkeypatch.setattr("llama_index.embeddings.google_genai.GoogleGenAIEmbedding", MagicMock())
    monkeypatch.setattr("llama_index.llms.google_genai.GoogleGenAI", MagicMock())
