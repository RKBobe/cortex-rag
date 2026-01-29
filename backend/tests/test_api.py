from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import MagicMock

# SET ENV VARS BEFORE IMPORTING MAIN
os.environ["GEMINI_API_KEY"] = "fake_key"
os.environ["DATA_ROOT"] = "./test_data"

# Ensure we can import main
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Now import main
from main import app, ingest_repository, ingest_single_file

client = TestClient(app)

def test_get_contexts_empty(monkeypatch):
    # Mock os.path.exists to return False for DB
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    response = client.get("/contexts")
    assert response.status_code == 200
    assert response.json() == []

def test_get_contexts_with_data(monkeypatch):
    # Mock Chroma Client listing collections
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.name = "test-repo"
    mock_client.list_collections.return_value = [mock_collection]

    monkeypatch.setattr("chromadb.PersistentClient", lambda path: mock_client)
    monkeypatch.setattr(os.path, "exists", lambda p: True)

    response = client.get("/contexts")
    assert response.status_code == 200
    assert response.json() == ["test-repo"]

def test_ingest_repo_success(monkeypatch):
    # Mock ingest_repository function inside 'main'
    mock_ingest = MagicMock()
    monkeypatch.setattr("main.ingest_repository", mock_ingest)

    # Mock save_registry to avoid writing to disk
    mock_save = MagicMock()
    monkeypatch.setattr("main.save_registry", mock_save)

    payload = {"repo_url": "https://github.com/test/repo", "repo_name": "test-repo"}
    response = client.post("/ingest", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "success", "context_id": "test-repo"}
    mock_ingest.assert_called_once_with("https://github.com/test/repo", "test-repo")

def test_ingest_repo_sanitization(monkeypatch):
    mock_ingest = MagicMock()
    monkeypatch.setattr("main.ingest_repository", mock_ingest)

    # Mock save_registry
    monkeypatch.setattr("main.save_registry", MagicMock())

    payload = {"repo_url": "https://github.com/test/repo", "repo_name": "My Repo! @#$"}
    response = client.post("/ingest", json=payload)

    assert response.status_code == 200
    # "My Repo! @#$" -> "MyRepo" (alphanum + _-)
    assert response.json()["context_id"] == "MyRepo"

def test_chat_no_context(monkeypatch):
    # Mock get_chat_engine to return None
    monkeypatch.setattr("main.get_chat_engine", lambda id: None)

    response = client.post("/chat", json={"context_id": "missing", "message": "hello"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Context not found"
