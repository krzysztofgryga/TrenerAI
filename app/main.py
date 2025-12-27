"""
TrenerAI FastAPI Application

This module provides the REST API for the TrenerAI training plan generator.
It uses modular architecture with routers for different domains.

Endpoints:
    GET  /                  - Status check
    GET  /health            - Health check for orchestration
    GET  /debug/config      - Show current configuration
    POST /chat              - Chat with AI assistant
    POST /generate-training - Generate a training plan
    GET/POST/PUT/DELETE /clients - Client management
    GET/POST/DELETE /workouts    - Workout management
    GET/POST /api/users     - User database management
    POST /api/trainings     - Generate and save training
    POST /api/feedback      - Submit feedback

Usage:
    uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core import setup_logging, get_settings

# =============================================================================
# Logging Configuration
# =============================================================================

setup_logging()
logger = logging.getLogger(__name__)


# =============================================================================
# Database Initialization
# =============================================================================

def init_database():
    """Initialize database - create all tables if they don't exist."""
    try:
        from app.database.connection import engine, Base
        from app.database.models import (
            User, ClientProfile, TrainerClient,
            Group, GroupMember, GeneratedTraining, Feedback
        )
        # Create all tables automatically
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
        return True
    except ImportError as e:
        logger.warning(f"Database module not available: {e}")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    return False


def seed_test_accounts():
    """
    Create test accounts for development/testing.

    Test accounts (password for both: test123):
    - Client: test@client.pl
    - Trainer: test@trainer.pl
    """
    try:
        from app.database.connection import SessionLocal
        from app.database.models import User, UserRole, ClientProfile
        from app.services.auth_service import hash_password

        db = SessionLocal()

        # Test Client Account
        client_email = "test@client.pl"
        if not db.query(User).filter(User.email == client_email).first():
            client = User(
                email=client_email,
                password_hash=hash_password("test123"),
                name="Test Klient",
                role="client",
                is_active=True
            )
            db.add(client)
            db.commit()
            db.refresh(client)

            # Create client profile
            profile = ClientProfile(
                user_id=client.id,
                age=30,
                weight=75.0,
                height=175.0,
                goals="Budowa masy mięśniowej"
            )
            db.add(profile)
            db.commit()
            logger.info(f"Created test client account: {client_email}")

        # Test Trainer Account
        trainer_email = "test@trainer.pl"
        if not db.query(User).filter(User.email == trainer_email).first():
            trainer = User(
                email=trainer_email,
                password_hash=hash_password("test123"),
                name="Test Trener",
                role="trainer",
                is_active=True
            )
            db.add(trainer)
            db.commit()
            logger.info(f"Created test trainer account: {trainer_email}")

        db.close()

    except Exception as e:
        logger.error(f"Failed to seed test accounts: {e}")


# =============================================================================
# FastAPI Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    if init_database():
        seed_test_accounts()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="TrenerAI API",
    description="AI-powered training plan generator for fitness trainers. "
                "Supports both OpenAI and local Ollama LLMs.",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware - allows frontend applications to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers
app.include_router(api_router)


# =============================================================================
# Core Endpoints
# =============================================================================

@app.get("/")
def read_root() -> dict:
    """
    Root endpoint - basic API status check.

    Returns:
        dict: Status message and API version.
    """
    return {"status": "TrenerAI API Online", "version": "0.3.0"}


@app.get("/health")
def health_check() -> dict:
    """
    Health check endpoint for container orchestration (K8s, Docker).

    Returns:
        dict: Health status.
    """
    return {"status": "healthy"}


@app.get("/debug/config")
def debug_config() -> dict:
    """
    Debug endpoint to check current configuration.

    WARNING: Disable this endpoint in production environments.

    Returns:
        dict: Current configuration values.
    """
    settings = get_settings()
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "ollama_base_url": settings.ollama_base_url,
        "openai_api_key_set": bool(settings.openai_api_key),
        "qdrant_url": settings.qdrant_url,
        "collection_name": settings.qdrant_collection_name,
    }


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
