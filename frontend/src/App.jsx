import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './App.css';

// Dynamic API URL (falls back to localhost for dev)
const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  // --- STATE ---
  const [contexts, setContexts] = useState([]);
  const [activeContext, setActiveContext] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);

  // New State for Single File Upload
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContextName, setFileContextName] = useState("");

  // --- 1. LOAD CONTEXTS ON STARTUP ---
  useEffect(() => {
    fetchContexts();
  }, []);

  const fetchContexts = async () => {
    try {
      const res = await fetch(`${API_BASE}/contexts`);
      const data = await res.json();
      setContexts(data);
    } catch (err) {
      console.error("Failed to load contexts:", err);
    }
  };

  // --- 2. HANDLE CHAT MESSAGES ---
  const handleSendMessage = async () => {
    if (!input.trim()) return;
    if (!activeContext) {
      alert("Please select a repository from the sidebar first!");
      return;
    }

    const userMessage = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          context_id: activeContext,
          message: userMessage.text
        }),
      });

      if (!res.ok) throw new Error("Chat failed");

      const data = await res.json();
      setMessages((prev) => [...prev, { role: "ai", text: data.response }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "error", text: "Error: " + err.message }]);
    } finally {
      setIsLoading(false);
    }
  };

  // --- 3. HANDLE GIT REPO INGESTION ---
  const handleNewIngest = async () => {
    const url = prompt("Git Repo URL (e.g. https://github.com/pallets/flask):");
    if (!url) return;
    const name = prompt("Name this Context (e.g. flask-core):");
    if (!name) return;

    setIsIngesting(true);

    try {
      const res = await fetch(`${API_BASE}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: url, repo_name: name }),
      });
      
      if (res.ok) {
        await fetchContexts(); // Refresh sidebar list
        alert("Repo Ingestion Complete!");
      } else {
        alert("Ingestion failed on server.");
      }
    } catch (err) {
      console.error(err);
      alert("Connection failed.");
    } finally {
      setIsIngesting(false);
    }
  };

  // --- 4. HANDLE SINGLE FILE UPLOAD ---
  const handleFileUpload = async () => {
    if (!selectedFile) return alert("Please select a file first.");
    if (!fileContextName) return alert("Please enter a Context Name.");

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("context_id", fileContextName);

    setIsIngesting(true);

    try {
      const res = await fetch(`${API_BASE}/ingest/file`, {
        method: "POST",
        body: formData, // No Content-Type needed for FormData
      });

      if (res.ok) {
        alert("File Ingested Successfully!");
        setSelectedFile(null);
        setFileContextName("");
        await fetchContexts(); // Refresh sidebar
      } else {
        const err = await res.json();
        alert("Error: " + (err.detail || "Upload failed"));
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert("Upload failed.");
    } finally {
      setIsIngesting(false);
    }
  };

  // --- UI RENDER ---
  return (
    <div className="app-container">
      {/* SIDEBAR */}
      <div className="sidebar">
        
        {/* Header with Git Ingest Button */}
        <div className="sidebar-header">
          <h2>Cortex</h2>
          <button 
            onClick={handleNewIngest} 
            className="new-chat-btn"
            disabled={isIngesting}
          >
            {isIngesting ? "⏳ Ingesting..." : "+ New Context"}
          </button>
        </div>

        {/* File Upload Section */}
        <div style={{ padding: '10px', borderBottom: '1px solid #444', marginBottom: '10px' }}>
          <input
            type="text"
            placeholder="Context Name..."
            value={fileContextName}
            onChange={(e) => setFileContextName(e.target.value)}
            style={{ width: '90%', marginBottom: '5px', padding: '5px' }}
          />
          <input
            type="file"
            onChange={(e) => setSelectedFile(e.target.files[0])}
            style={{ color: 'white', maxWidth: '180px', marginBottom: '5px' }}
          />
          <button 
            onClick={handleFileUpload} 
            disabled={isIngesting || !selectedFile || !fileContextName}
            style={{ width: '100%', padding: '5px', cursor: 'pointer' }}
          >
            Upload File
          </button>
        </div>
        
        {/* Context List */}
        <div className="context-list">
          {isIngesting && (
            <div className="ingest-indicator">
              <span className="pulse-dot"></span>
              <span>Cloning & Indexing...</span>
            </div>
          )}

          {contexts.length === 0 && !isIngesting && <p className="empty-msg">No contexts found.</p>}
          
          {contexts.map((ctx) => (
            <div 
              key={ctx} 
              className={`context-item ${activeContext === ctx ? 'active' : ''}`}
              onClick={() => {
                setActiveContext(ctx);
                setMessages([]); 
              }}
            >
              # {ctx}
            </div>
          ))}
        </div>
      </div>

      {/* CHAT AREA */}
      <div className="chat-area">
        <div className="chat-header">
          {activeContext ? (
            <h3>Context: <span className="highlight">{activeContext}</span></h3>
          ) : (
            <h3>Select a repository to start</h3>
          )}
        </div>

        <div className="messages-container">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {msg.text}
                </ReactMarkdown>
              </div>
            </div>
          ))}
          {isLoading && <div className="message ai">Thinking...</div>}
        </div>

        <div className="input-area">
          <input 
            type="text" 
            placeholder={activeContext ? `Ask about ${activeContext}...` : "Select a repo from sidebar..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            disabled={!activeContext}
          />
          <button onClick={handleSendMessage} disabled={!activeContext}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;