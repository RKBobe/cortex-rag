"""
CoreTexAI Relational Registry
Proprietary product of Treelight Innovations.
Responsible for persistent storage of Memory Tier metadata.
"""
from sqlalchemy import Column, String, Integer, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from core_config import settings

Base = declarative_base()

class MemoryTier(Base):
    """
    Represents a persistent intelligence tier within the CoreTexAI vault.
    Maps Repository URLs to specialized context IDs and tracks intake status.
    """
    __tablename__ = "memory_tiers"
    
    id = Column(Integer, primary_key=True)
    tier_id = Column(String, unique=True, index=True) # The Context ID
    repo_url = Column(String, index=True)
    status = Column(String, default="pending") # pending, ingesting, completed, failed
    error_log = Column(String, nullable=True)
    last_synced = Column(DateTime, default=datetime.utcnow)
    owner = Column(String, default="Treelight Innovations")

# Initialize SQLite Engine
engine = create_engine(settings.SQL_PATH)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
