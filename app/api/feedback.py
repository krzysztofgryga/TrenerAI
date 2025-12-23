"""
Feedback API router - Postgres database.
"""
import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas import FeedbackCreate, FeedbackResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Database"])


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


@router.post("/feedback", response_model=FeedbackResponse)
def create_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db_session)):
    """Submit feedback for a training."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    from app.database import GeneratedTraining, Feedback as DBFeedback

    # Check training exists
    training = db.query(GeneratedTraining).filter(
        GeneratedTraining.id == feedback.training_id
    ).first()
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")

    # Check if feedback already exists
    existing = db.query(DBFeedback).filter(
        DBFeedback.training_id == feedback.training_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Feedback already exists for this training")

    db_feedback = DBFeedback(
        training_id=feedback.training_id,
        rating=feedback.rating,
        comment=feedback.comment,
        was_too_hard=1 if feedback.was_too_hard else 0,
        was_too_easy=1 if feedback.was_too_easy else 0,
        exercises_liked=feedback.exercises_liked,
        exercises_disliked=feedback.exercises_disliked
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)

    return db_feedback


@router.get("/feedback/{training_id}", response_model=FeedbackResponse)
def get_feedback(training_id: int, db: Session = Depends(get_db_session)):
    """Get feedback for a training."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    from app.database import Feedback as DBFeedback

    feedback = db.query(DBFeedback).filter(DBFeedback.training_id == training_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback
