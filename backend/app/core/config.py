# backend/app/core/config.py - PostgreSQL Configuration
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path

class Settings(BaseSettings):
    # Database - PostgreSQL as per requirements
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/workflow_builder"
    
    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # Default to openai since you have the key
    OPENAI_API_KEY: Optional[str] = None
    
    # Search API Keys (added to fix validation error)
    SERPAPI_KEY: Optional[str] = None
    BRAVE_API_KEY: Optional[str] = None
    
    # ChromaDB Configuration
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    
    # Embedding Service
    EMBEDDING_PROVIDER: str = "openai"  # Use OpenAI embeddings
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    
    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "AI Workflow Builder"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    # Development
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create upload directory if it doesn't exist
        Path(self.UPLOAD_DIR).mkdir(exist_ok=True)
        
        # Log configuration status
        print(f"=== AI Workflow Builder Configuration ===")
        print(f"DATABASE_URL: {self.DATABASE_URL}")
        print(f"LLM_PROVIDER: {self.LLM_PROVIDER}")
        print(f"OPENAI_API_KEY: {'SET' if self.OPENAI_API_KEY else 'NOT SET'}")
        print(f"SERPAPI_KEY: {'SET' if self.SERPAPI_KEY else 'NOT SET'}")
        print(f"BRAVE_API_KEY: {'SET' if self.BRAVE_API_KEY else 'NOT SET'}")
        print(f"CHROMA_HOST: {self.CHROMA_HOST}:{self.CHROMA_PORT}")
        print(f"CORS_ORIGINS: {self.CORS_ORIGINS}")
        print(f"DEBUG: {self.DEBUG}")
        print("=" * 40)

settings = Settings()

# backend/app/core/db.py - PostgreSQL Database Setup
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create engine with PostgreSQL-specific settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    echo=settings.DEBUG  # Log SQL queries if in debug mode
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        raise

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False