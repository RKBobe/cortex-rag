import os
import sys
import pytest
from unittest.mock import MagicMock

# Set env vars before import
os.environ["GEMINI_API_KEY"] = "fake_key"
os.environ["DATA_ROOT"] = "./test_data"

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import ingest module
import ingest

def test_git_terminal_prompt_disabled():
    # Verify that the environment variable is set in the module scope
    assert os.environ.get("GIT_TERMINAL_PROMPT") == "0"

def test_data_drive_root_config():
    # Ingest.py uses os.getenv("DATA_ROOT") directly if present.
    # It does not force abspath on the env var value.
    expected = "./test_data"
    assert ingest.DATA_DRIVE_ROOT == expected

def test_ingest_repository_calls_git_clone(monkeypatch):
    # Mock git.Repo.clone_from
    mock_clone = MagicMock()
    monkeypatch.setattr("git.Repo.clone_from", mock_clone)

    # Mock SimpleDirectoryReader
    mock_reader_cls = MagicMock()
    mock_reader_instance = MagicMock()
    mock_reader_instance.load_data.return_value = []
    mock_reader_cls.return_value = mock_reader_instance
    monkeypatch.setattr("llama_index.core.SimpleDirectoryReader", mock_reader_cls)

    # Mock VectorStoreIndex
    monkeypatch.setattr("llama_index.core.VectorStoreIndex.from_documents", MagicMock())

    # Mock Chroma
    monkeypatch.setattr("chromadb.PersistentClient", MagicMock())

    # Call function
    ingest.ingest_repository("https://github.com/fake/repo", "fake-collection")

    # Verify clone was called with correct URL and temp dir
    mock_clone.assert_called_once()
    args, _ = mock_clone.call_args
    assert args[0] == "https://github.com/fake/repo"
    assert "temp_repos" in args[1]
