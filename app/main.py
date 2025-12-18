import logging
import traceback
from enum import Enum
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent import app_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TrenerAI API",
    description="AI-powered training plan generator for fitness trainers",
    version="0.1.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TrainingMode(str, Enum):
    CIRCUIT = "circuit"
    COMMON = "common"


class TrainingRequest(BaseModel):
    num_people: Annotated[int, Field(ge=1, le=50, description="Number of participants (1-50)")]
    difficulty: Difficulty = Field(description="Difficulty level: easy, medium, hard")
    rest_time: Annotated[int, Field(ge=10, le=300, description="Rest time between exercises in seconds (10-300)")]
    mode: TrainingMode = Field(description="Training mode: circuit or common")


@app.get("/")
def read_root():
    """Root endpoint - basic status check."""
    return {"status": "TrenerAI API Online", "version": "0.1.0"}


@app.get("/health")
def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy"}


@app.get("/debug/config")
def debug_config():
    """Debug endpoint to check configuration (disable in production)."""
    import os
    return {
        "qdrant_url": os.getenv("QDRANT_URL", "http://localhost:6333"),
        "collection_name": os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises"),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.post("/generate-training")
async def generate_training(request: TrainingRequest):
    """
    Generate a complete training plan using LangGraph agent.

    Returns a structured training plan with warmup, main exercises, and cooldown.
    """
    logger.info(
        f"Generating training plan: num_people={request.num_people}, "
        f"difficulty={request.difficulty.value}, mode={request.mode.value}"
    )

    try:
        inputs = {
            "num_people": request.num_people,
            "difficulty": request.difficulty.value,
            "rest_time": request.rest_time,
            "mode": request.mode.value
        }

        result = app_graph.invoke(inputs)
        logger.info("Training plan generated successfully")

        return result["final_plan"]

    except Exception as e:
        logger.error(f"Error generating training plan: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate training plan: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
