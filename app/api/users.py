"""
Users API router - Postgres database.
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas import UserCreate, UserResponse

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


@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db_session)):
    """Create a new user in the database."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    from app.database import User as DBUser, DifficultyLevel

    # Check if email already exists
    existing = db.query(DBUser).filter(DBUser.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Map difficulty string to enum
    difficulty = DifficultyLevel.MEDIUM
    if user.preferred_difficulty:
        difficulty = DifficultyLevel(user.preferred_difficulty.upper())

    db_user = DBUser(
        email=user.email,
        name=user.name,
        age=user.age,
        weight=user.weight,
        height=user.height,
        goals=user.goals,
        contraindications=user.contraindications,
        preferred_difficulty=difficulty
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db_session)):
    """Get user by ID."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    from app.database import User as DBUser

    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users", response_model=List[UserResponse])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    """List all users."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    from app.database import User as DBUser

    users = db.query(DBUser).offset(skip).limit(limit).all()
    return users
