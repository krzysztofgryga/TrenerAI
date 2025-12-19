"""
TrenerAI FastAPI Application

This module provides the REST API for the TrenerAI training plan generator.
It exposes endpoints for generating AI-powered workout plans.

Endpoints:
    GET  /                  - Status check
    GET  /health            - Health check for orchestration
    GET  /debug/config      - Show current configuration
    POST /generate-training - Generate a training plan

Usage:
    uvicorn app.main:app --reload
"""

import logging
import os
import traceback
from enum import Enum
from typing import Annotated, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent import app_graph, get_vector_store, get_llm, check_collection_exists

# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="TrenerAI API",
    description="AI-powered training plan generator for fitness trainers. "
                "Supports both OpenAI and local Ollama LLMs.",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allows frontend applications to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request/Response Models
# =============================================================================

class Difficulty(str, Enum):
    """
    Exercise difficulty levels.

    Attributes:
        EASY: Beginner-friendly exercises
        MEDIUM: Intermediate exercises
        HARD: Advanced/challenging exercises
    """
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TrainingMode(str, Enum):
    """
    Training session modes.

    Attributes:
        CIRCUIT: Each participant does a different exercise (rotating stations)
        COMMON: All participants do the same exercises together
    """
    CIRCUIT = "circuit"
    COMMON = "common"


class TrainingRequest(BaseModel):
    """
    Request model for training plan generation.

    Attributes:
        num_people: Number of participants (1-50)
        difficulty: Exercise difficulty level
        rest_time: Rest time between exercises in seconds (10-300)
        mode: Training mode (circuit or common)
        warmup_count: Number of warmup exercises (1-10)
        main_count: Number of main exercises (1-20)
        cooldown_count: Number of cooldown exercises (1-10)
    """
    num_people: Annotated[int, Field(
        ge=1,
        le=50,
        description="Number of participants (1-50)"
    )]
    difficulty: Difficulty = Field(
        description="Difficulty level: easy, medium, hard"
    )
    rest_time: Annotated[int, Field(
        ge=10,
        le=300,
        description="Rest time between exercises in seconds (10-300)"
    )]
    mode: TrainingMode = Field(
        description="Training mode: circuit or common"
    )
    warmup_count: Annotated[int, Field(
        ge=1,
        le=10,
        description="Number of warmup exercises (1-10)"
    )] = 3
    main_count: Annotated[int, Field(
        ge=1,
        le=20,
        description="Number of main exercises (1-20)"
    )] = 5
    cooldown_count: Annotated[int, Field(
        ge=1,
        le=10,
        description="Number of cooldown exercises (1-10)"
    )] = 3


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
def read_root() -> dict:
    """
    Root endpoint - basic API status check.

    Returns:
        dict: Status message and API version.
    """
    return {"status": "TrenerAI API Online", "version": "0.2.0"}


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

    WARNING: Disable this endpoint in production environments
    as it may expose sensitive configuration details.

    Returns:
        dict: Current configuration values.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    return {
        "llm_provider": provider,
        "llm_model": os.getenv("LLM_MODEL", "gpt-4o"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "qdrant_url": os.getenv("QDRANT_URL", "http://localhost:6333"),
        "collection_name": os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises"),
    }


@app.post("/generate-training")
async def generate_training(request: TrainingRequest) -> dict:
    """
    Generate a complete training plan using LangGraph agent.

    This endpoint invokes the AI workflow to:
    1. Retrieve relevant exercises from the vector database
    2. Generate a structured training plan using LLM

    Args:
        request: Training parameters (num_people, difficulty, rest_time, mode, counts)

    Returns:
        dict: Generated training plan with warmup, main_part, and cooldown sections.

    Raises:
        HTTPException: 500 error if plan generation fails.

    Example:
        POST /generate-training
        {
            "num_people": 5,
            "difficulty": "medium",
            "rest_time": 60,
            "mode": "circuit",
            "warmup_count": 3,
            "main_count": 5,
            "cooldown_count": 3
        }
    """
    logger.info(
        f"Generating training plan: num_people={request.num_people}, "
        f"difficulty={request.difficulty.value}, mode={request.mode.value}, "
        f"warmup={request.warmup_count}, main={request.main_count}, cooldown={request.cooldown_count}"
    )

    try:
        # Prepare input for LangGraph workflow
        inputs = {
            "num_people": request.num_people,
            "difficulty": request.difficulty.value,
            "rest_time": request.rest_time,
            "mode": request.mode.value,
            "warmup_count": request.warmup_count,
            "main_count": request.main_count,
            "cooldown_count": request.cooldown_count
        }

        # Invoke the AI workflow
        result = app_graph.invoke(inputs)
        logger.info("Training plan generated successfully")

        return result["final_plan"]

    except ValueError as e:
        # Handle known errors (e.g., collection not found)
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error generating training plan: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate training plan: {str(e)}"
        )


@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    """
    Chat endpoint with RAG - retrieves exercises from Qdrant and generates response.
    """
    logger.info(f"Chat request: {request.message[:100]}...")

    try:
        # Build context from Qdrant
        context = ""
        if check_collection_exists():
            vector_store = get_vector_store()
            docs = vector_store.similarity_search(request.message, k=10)
            if docs:
                context = "Dostępne ćwiczenia z bazy:\n" + "\n".join(
                    [f"- {d.page_content}" for d in docs]
                )

        # Build conversation history
        history_text = ""
        for msg in request.history[-6:]:
            role = "Użytkownik" if msg.role == "user" else "Asystent"
            history_text += f"{role}: {msg.content}\n\n"

        # System prompt
        system_prompt = """Jesteś prywatnym, technicznym asystentem Trenera Personalnego. Twoim zadaniem jest dostarczanie konkretnych, merytorycznych rozwiązań w formie "Raportów Operacyjnych".

ZASADY FORMATOWANIA:
1. KAŻDA ODPOWIEDŹ musi zaczynać się od głównego nagłówka Markdown (#).
2. Używaj separatorów sekcji (---) pomiędzy różnymi blokami informacji.
3. Sekcje podrzędne oznaczaj nagłówkami drugiego stopnia (##).
4. Dane liczbowe, serie i powtórzenia MUSZĄ być w tabelach Markdown.
5. Ważne parametry (RPE, Tempo) pogrubiaj.
6. Brak zbędnych wstępów i zakończeń.

{context}"""

        # Build full prompt
        full_prompt = f"{system_prompt.format(context=context)}\n\n{history_text}Użytkownik: {request.message}\n\nAsystent:"

        # Get LLM response
        llm = get_llm()
        response = llm.invoke(full_prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        return {"response": response_text}

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
