import React, { useState, useEffect } from 'react';
import './App.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function App() {
  const [contexts, setContexts] = useState([]);
  const [activeContext, setActiveContext] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // 1. Load available contexts (Sidebar)
  useEffect(() => {
    fetchContexts();
  }, []);

  const fetchContexts = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/contexts");
      const data = await res.json();
      setContexts(data);
    } catch (err) {
      console.error("Failed to load contexts:", err);
    }
  };

  // 2. Send Message (Includes context_id!)
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
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          context_id: activeContext, // <--- This fixes the 422 Error
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

  // 3. Ingest New Repo
  const handleNewIngest = async () => {
    const url = prompt("Git Repo URL (e.g. https://github.com/pallets/flask):");
    if (!url) return;
    const name = prompt("Name this Context (e.g. flask-core):");
    if (!name) return;

    try {
      const res = await fetch("http://127.0.0.1:8000/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: url, repo_name: name }),
      });
      if (res.ok) {
        alert("Ingestion Started! This may take a minute...");
        fetchContexts(); // Refresh sidebar list
      }
    } catch (err) {
      console.error(err);
      alert("Ingestion failed");
    }
  };

  return (
    <div className="app-container">
      {/* SIDEBAR */}
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>Cortex</h2>
          <button onClick={handleNewIngest} className="new-chat-btn">+ New Context</button>
        </div>
        
        <div className="context-list">
          {contexts.length === 0 && <p className="empty-msg">No contexts found.</p>}
          {contexts.map((ctx) => (
            <div 
              key={ctx} 
              className={`context-item ${activeContext === ctx ? 'active' : ''}`}
              onClick={() => {
                setActiveContext(ctx);
                setMessages([]); // Clear chat on switch
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