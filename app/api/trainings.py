"""
Trainings API router - LangGraph generation + Postgres storage.
"""
import logging
import os
import traceback
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas import TrainingRequest, TrainingHistoryResponse
from app.agent import app_graph

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Trainings"])


def get_db_session():
    """Get optional DB session."""
    try:
        from app.database import SessionLocal, DB_AVAILABLE
        if DB_AVAILABLE:
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()
        else:
            yield None
    except ImportError:
        yield None


@router.post("/generate-training")
async def generate_training(request: TrainingRequest) -> dict:
    """
    Generate a training plan using LangGraph agent.

    This endpoint does NOT persist the result.
    Use POST /api/trainings to generate AND save.
    """
    logger.info(
        f"Generating training: num_people={request.num_people}, "
        f"difficulty={request.difficulty.value}, mode={request.mode.value}"
    )

    try:
        inputs = {
            "num_people": request.num_people,
            "difficulty": request.difficulty.value,
            "rest_time": request.rest_time,
            "mode": request.mode.value,
            "warmup_count": request.warmup_count,
            "main_count": request.main_count,
            "cooldown_count": request.cooldown_count
        }

        result = app_graph.invoke(inputs)
        logger.info("Training plan generated successfully")

        return result["final_plan"]

    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Error generating training plan: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate training plan: {str(e)}"
        )


@router.post("/api/trainings", tags=["Database"])
def save_training(
    request: TrainingRequest,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db_session)
):
    """
    Generate and save a training plan to database.
    Like /generate-training but persists the result.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    from app.database import GeneratedTraining

    logger.info(f"Generating and saving training for user_id={user_id}")

    try:
        inputs = {
            "num_people": request.num_people,
            "difficulty": request.difficulty.value,
            "rest_time": request.rest_time,
            "mode": request.mode.value,
            "warmup_count": request.warmup_count,
            "main_count": request.main_count,
            "cooldown_count": request.cooldown_count
        }

        result = app_graph.invoke(inputs)
        plan = result["final_plan"]

        db_training = GeneratedTraining(
            user_id=user_id,
            input_params=inputs,
            plan=plan,
            model_name=os.getenv("LLM_MODEL", "unknown"),
            prompt_version="v1.0",
            retrieved_exercises=result.get("retrieved_exercises", [])
        )
        db.add(db_training)
        db.commit()
        db.refresh(db_training)

        logger.info(f"Training saved with id={db_training.id}")

        return {
            "training_id": db_training.id,
            "plan": plan
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/trainings/{training_id}", response_model=TrainingHistoryResponse, tags=["Database"])
def get_training(training_id: int, db: Session = Depends(get_db_session)):
    """Get a specific training by ID."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    from app.database import GeneratedTraining

    training = db.query(GeneratedTraining).filter(GeneratedTraining.id == training_id).first()
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    return training


@router.get("/api/users/{user_id}/trainings", response_model=List[TrainingHistoryResponse], tags=["Database"])
def get_user_trainings(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_session)
):
    """Get all trainings for a user."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    from app.database import GeneratedTraining

    trainings = db.query(GeneratedTraining)\
        .filter(GeneratedTraining.user_id == user_id)\
        .order_by(GeneratedTraining.created_at.desc())\
        .offset(skip).limit(limit).all()
    return trainings
