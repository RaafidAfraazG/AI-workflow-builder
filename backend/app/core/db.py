# backend/app/core/db.py - OPTIMIZED PostgreSQL Database Setup
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# OPTIMIZATION: Better connection pool settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=20,          # Increase pool size
    max_overflow=30,       # Allow more overflow connections
    pool_timeout=30,       # Connection timeout
    echo=False             # Turn off SQL logging in production
    # Removed problematic connect_args for now
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False,    # Don't auto-flush - manual control for better performance
    bind=engine
)

Base = declarative_base()

def get_db():
    """Dependency to get database session - OPTIMIZED"""
    db = SessionLocal()
    try:
        # OPTIMIZATION: Set session-level optimizations (removed problematic setting)
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
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False