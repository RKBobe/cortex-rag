"""
CoreTexAI Gateway
Proprietary product of Treelight Innovations.
High-performance API entry point for the flagship Memory Orchestration Engine.
"""
from fastapi import FastAPI, HTTPException, Security, Depends, Request, BackgroundTasks
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from core_config import settings
from database import init_db, SessionLocal, MemoryTier
from orchestrator import MemoryOrchestrator
from intake_engine import MemoryIntakeEngine

# Initialize Core Services
init_db()
orchestrator = MemoryOrchestrator()
intake_engine = MemoryIntakeEngine()

app = FastAPI(title=f"{settings.PROJECT_NAME} Gateway", version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from vault_manager import vault

# Security Tier
api_key_header = APIKeyHeader(name="X-CoreTex-Key", auto_error=False)

async def validate_key(api_key: str = Security(api_key_header)):
    # Retrieve decrypted secret from the proprietary vault
    stored_secret = vault.retrieve_secret()
    if api_key != stored_secret:
        raise HTTPException(status_code=403, detail="Unauthorized: CoreTexAI Vault Access Denied")
    return api_key

# --- Data Models ---
class ChatRequest(BaseModel):
    tier_id: str
    message: str
    thinking_mode: str = "medium"

class IntakeRequest(BaseModel):
    repo_url: str
    tier_id: str

# --- Endpoints ---
@app.get("/health")
def health():
    return {"status": "online", "engine": settings.PROJECT_NAME, "version": settings.VERSION}

@app.get("/tiers", dependencies=[Depends(validate_key)])
def list_tiers():
    db = SessionLocal()
    tiers = db.query(MemoryTier).all()
    db.close()
    return [{"tier_id": t.tier_id, "repo_url": t.repo_url, "status": t.status, "last_synced": t.last_synced} for t in tiers]

@app.get("/intake/status/{tier_id}", dependencies=[Depends(validate_key)])
async def get_intake_status(tier_id: str):
    """Returns the persistent intake status from the relational tier."""
    db = SessionLocal()
    tier = db.query(MemoryTier).filter(MemoryTier.tier_id == tier_id).first()
    db.close()
    
    if not tier:
        raise HTTPException(status_code=404, detail="Memory Tier not found")
        
    return {
        "tier_id": tier.tier_id,
        "status": tier.status,
        "last_synced": tier.last_synced,
        "error": tier.error_log
    }

@app.post("/intake", dependencies=[Depends(validate_key)])
async def trigger_intake(request: IntakeRequest, background_tasks: BackgroundTasks):
    db = SessionLocal()
    existing = db.query(MemoryTier).filter(MemoryTier.tier_id == request.tier_id).first()
    if not existing:
        new_tier = MemoryTier(tier_id=request.tier_id, repo_url=request.repo_url)
        db.add(new_tier)
        db.commit()
    else:
        existing.status = "pending"
        db.commit()
    db.close()

    background_tasks.add_task(intake_engine.intake_repository, request.repo_url, request.tier_id)
    return {"status": "accepted", "tier_id": request.tier_id}

@app.post("/chat", dependencies=[Depends(validate_key)])
async def chat_endpoint(request: ChatRequest):
    if request.thinking_mode not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="Invalid thinking_mode. Use 'low', 'medium', or 'high'.")
        
    response = await orchestrator.execute_reasoning(
        request.tier_id, 
        request.message, 
        mode=request.thinking_mode
    )
    return {
        "engine": settings.PROJECT_NAME,
        "mode": request.thinking_mode,
        "response": response
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
