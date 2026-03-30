import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './App.css';

// CoreTexAI Flagship API Configuration
const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const CORETEX_API_KEY = import.meta.env.VITE_CORETEX_API_KEY || "treelight-innovation-secure-vault";

function App() {
  // --- STATE ---
  const [tiers, setTiers] = useState([]);
  const [activeTier, setActiveTier] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestStatusMsg, setIngestStatusMsg] = useState("");
  const [ingestError, setIngestError] = useState(null);
  const [pendingTier, setPendingTier] = useState(null);
  const [thinkingMode, setThinkingMode] = useState("medium");

  // Intake Form State
  const [showIntakeForm, setShowIntakeForm] = useState(false);
  const [newRepoUrl, setNewRepoUrl] = useState("");
  const [newTierId, setNewTierId] = useState("");

  // Helper for fetch with Treelight Auth
  const authFetch = (url, options = {}) => {
    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        "X-CoreTex-Key": CORETEX_API_KEY,
      }
    });
  };

  // --- 1. LOAD MEMORY TIERS ---
  useEffect(() => {
    fetchTiers();
  }, []);

  // Poll for status if a tier is intaking
  useEffect(() => {
    let interval;
    if (isIngesting && pendingTier) {
      interval = setInterval(async () => {
        try {
          const res = await authFetch(`${API_BASE}/intake/status/${pendingTier}`);
          const data = await res.json();
          
          if (data.status === "completed") {
            setIsIngesting(false);
            setIngestStatusMsg("");
            setPendingTier(null);
            fetchTiers();
          } else if (data.status === "failed") {
            setIsIngesting(false);
            setIngestError(data.error);
            setIngestStatusMsg("Failed");
            setPendingTier(null);
          } else {
            setIngestStatusMsg(data.status);
          }
        } catch (err) {
          console.error("Status poll failed:", err);
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [isIngesting, pendingTier]);

  const fetchTiers = async () => {
    try {
      const res = await authFetch(`${API_BASE}/tiers`);
      const data = await res.json();
      setTiers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load memory tiers:", err);
    }
  };

  // --- 2. HANDLE REASONING (CHAT) ---
  const handleSendMessage = async () => {
    if (!input.trim() || !activeTier) return;

    const userMessage = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await authFetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tier_id: activeTier,
          message: userMessage.text,
          thinking_mode: thinkingMode
        }),
      });

      if (!res.ok) throw new Error("Reasoning engine failed");

      const data = await res.json();
      setMessages((prev) => [...prev, { role: "ai", text: data.response }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "error", text: "CoreTexAI Error: " + err.message }]);
    } finally {
      setIsLoading(false);
    }
  };

  // --- 3. HANDLE MEMORY INTAKE ---
  const handleNewIntake = async (e) => {
    e.preventDefault();
    if (!newRepoUrl || !newTierId) return;

    const safeId = newTierId.replace(/[^a-z0-9_-]/gi, "");
    setIsIngesting(true);
    setIngestStatusMsg("starting");
    setIngestError(null);
    setPendingTier(safeId);
    setShowIntakeForm(false);

    try {
      const res = await authFetch(`${API_BASE}/intake`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: newRepoUrl, tier_id: safeId }),
      });
      
      if (!res.ok) {
        alert("Treelight Gateway rejected intake request.");
        setIsIngesting(false);
        setPendingTier(null);
      } else {
        setNewRepoUrl("");
        setNewTierId("");
      }
    } catch (err) {
      console.error(err);
      alert("CoreTexAI Connection failed.");
      setIsIngesting(false);
      setPendingTier(null);
    }
  };

  // --- UI RENDER ---
  return (
    <div className="app-container">
      {/* SIDEBAR */}
      <div className="sidebar">
        
        <div className="sidebar-header">
          <h2>CoreTexAI</h2>
          <button 
            onClick={() => setShowIntakeForm(!showIntakeForm)} 
            className="new-chat-btn"
            disabled={isIngesting}
          >
            {showIntakeForm ? "Cancel" : "+ New Tier"}
          </button>
        </div>

        {/* Intake Form */}
        {showIntakeForm && (
          <form className="ingest-form" onSubmit={handleNewIntake}>
            <input 
              type="text" 
              placeholder="Tier ID (e.g. backend-core)" 
              value={newTierId}
              onChange={(e) => setNewTierId(e.target.value)}
              required
            />
            <input 
              type="url" 
              placeholder="Git Repository URL" 
              value={newRepoUrl}
              onChange={(e) => setNewRepoUrl(e.target.value)}
              required
            />
            <button type="submit">Start Intake</button>
          </form>
        )}

        <div className="thinking-mode-selector" style={{ padding: '10px', borderBottom: '1px solid #333' }}>
          <label style={{ fontSize: '12px', color: '#888' }}>Thinking Mode:</label>
          <select 
            value={thinkingMode} 
            onChange={(e) => setThinkingMode(e.target.value)}
            style={{ background: '#222', color: '#fff', border: '1px solid #444', width: '100%', marginTop: '5px' }}
          >
            <option value="low">Low (Fast)</option>
            <option value="medium">Medium (Balanced)</option>
            <option value="high">High (Deep Reasoning)</option>
          </select>
        </div>
        
        {/* Memory Tier List */}
        <div className="context-list">
          {isIngesting && (
            <div className="ingest-indicator">
              <span className="pulse-dot"></span>
              <span style={{ textTransform: 'capitalize' }}>Intaking {ingestStatusMsg}...</span>
            </div>
          )}

          {ingestError && (
            <div className="ingest-error-box">
              <p>Provenance Error: {ingestError}</p>
              <button onClick={() => setIngestError(null)}>Dismiss</button>
            </div>
          )}

          {tiers.length === 0 && !isIngesting && <p className="empty-msg">No active memory tiers.</p>}
          
          {tiers.map((tier) => (
            <div 
              key={tier.tier_id} 
              className={`context-item ${activeTier === tier.tier_id ? 'active' : ''}`}
              onClick={() => {
                setActiveTier(tier.tier_id);
                setMessages([]); 
              }}
            >
              # {tier.tier_id}
              <span style={{ fontSize: '10px', display: 'block', color: '#666' }}>{tier.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* CHAT AREA */}
      <div className="chat-area">
        <div className="chat-header">
          {activeTier ? (
            <h3>Memory Tier: <span className="highlight">{activeTier}</span></h3>
          ) : (
            <h3>Select a CoreTexAI Memory Tier</h3>
          )}
        </div>

        <div className="messages-container">
          {messages.length === 0 && !activeTier && (
            <div className="welcome-msg">
              <h1>CoreTexAI Flagship</h1>
              <p>Proprietary Memory Orchestration Engine by Treelight Innovations.</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {msg.text}
                </ReactMarkdown>
              </div>
            </div>
          ))}
          {isLoading && <div className="message ai">CoreTexAI is thinking...</div>}
        </div>

        <div className="input-area">
          <input 
            type="text" 
            placeholder={activeTier ? `Query ${activeTier} vault...` : "Select a tier to begin reasoning..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            disabled={!activeTier}
          />
          <button onClick={handleSendMessage} disabled={!activeTier}>Query Vault</button>
        </div>
      </div>
      <div className="proprietary-footer" style={{ 
        textAlign: 'center', 
        fontSize: '10px', 
        color: '#444', 
        padding: '10px', 
        borderTop: '1px solid #222',
        background: '#0a0a0a'
      }}>
        Proprietary Product of Treelight Innovations &copy; 2026 | CoreTexAI v1.0.0-Flagship
      </div>
    </div>
  );
}

export default App;
