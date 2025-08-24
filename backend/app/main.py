from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
import time

from app.core.config import settings
from app.core.db import create_tables, test_connection
from app.api import workflows, health, kb

# Import all models to ensure they're registered with SQLAlchemy
from app.models import workflow, document, chat  # This ensures tables are created

# Set up logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Workflow Builder", version="1.0.0")

# ADD REQUEST TIMING MIDDLEWARE - This goes BEFORE CORS
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"🚀 INCOMING: {request.method} {request.url.path}")
    if request.method == "POST":
        logger.info(f"📄 Content-Type: {request.headers.get('content-type', 'not set')}")
        logger.info(f"📊 Content-Length: {request.headers.get('content-length', 'not set')}")
    
    # Process request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(f"✅ COMPLETED: {request.method} {request.url.path} in {process_time:.3f}s - Status: {response.status_code}")
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ FAILED: {request.method} {request.url.path} after {process_time:.3f}s - Error: {str(e)}")
        raise

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(kb.router, prefix="/api/kb", tags=["knowledge-base"])

# Serve uploaded files
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    logger.info("=== AI Workflow Builder Configuration ===")
    logger.info(f"DATABASE_URL: {settings.DATABASE_URL}")
    logger.info(f"LLM_PROVIDER: {settings.LLM_PROVIDER}")
    logger.info(f"OPENAI_API_KEY: {'SET' if settings.OPENAI_API_KEY else 'NOT SET'}")
    logger.info(f"SERPAPI_KEY: {'SET' if settings.SERPAPI_KEY else 'NOT SET'}")
    logger.info(f"BRAVE_API_KEY: {'SET' if settings.BRAVE_API_KEY else 'NOT SET'}")
    logger.info(f"CHROMA_HOST: {settings.CHROMA_HOST}")
    logger.info(f"CORS_ORIGINS: {settings.CORS_ORIGINS}")
    logger.info(f"DEBUG: {settings.DEBUG}")
    logger.info("=" * 40)

    # Test database connection
    if not test_connection():
        logger.error("Database connection failed!")
        raise Exception("Cannot connect to database")
    
    # Create tables
    try:
        create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise

@app.get("/")
async def root():
    return {"message": "AI Workflow Builder API", "version": "1.0.0"}