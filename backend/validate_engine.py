"""
CoreTexAI Live Validation Script
Proprietary product of Treelight Innovations.
Tests the Gemini 3.1 Pro Reasoning Engine and Tiered Memory.
"""
import asyncio
import os
import sys
from pathlib import Path

# Ensure we can import from the backend directory
sys.path.append(str(Path(__file__).resolve().parent))

from core_config import settings
from orchestrator import MemoryOrchestrator
from database import init_db, SessionLocal, MemoryTier

async def validate_system():
    print(f"🚀 Initializing CoreTexAI Validation...")
    print(f"Branding Check: {settings.PROJECT_NAME} by {settings.ORGANIZATION}")
    
    # 1. Database Init
    init_db()
    print("✅ Relational Registry Initialized.")

    # 2. Orchestrator Init
    orchestrator = MemoryOrchestrator()
    print(f"✅ Orchestrator Ready (Model: {settings.LLM_MODEL})")

    # 3. Simulate Query (We'll use a known tier or a descriptive error check)
    print("\n--- Testing 'HIGH' Mode Reasoning ---")
    test_tier = "coretex_system_audit"
    test_query = "What are the core design principles of Treelight Innovations' flagship CoreTexAI engine?"
    
    print(f"Querying Tier: '{test_tier}' with High Reasoning...")
    
    # Note: Since the tier might not have documents yet, we expect a graceful 
    # CoreTexAI error message as defined in our refactor.
    response = await orchestrator.execute_reasoning(test_tier, test_query, mode="high")
    
    print(f"\nEngine Response:\n{response}")
    print("\n--- End of Validation ---")

if __name__ == "__main__":
    asyncio.run(validate_system())
