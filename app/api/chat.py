"""
Chat API router.
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas import ChatRequest
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])


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


@router.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db_session)):
    """
    Chat endpoint with deterministic command parsing.

    Flow:
    1. Check if message is confirmation (tak/anuluj)
    2. Parse command with regex (NO LLM)
    3. Execute command (direct DB operation)
    4. If no command → use RAG for general questions
    """
    service = ChatService(db)
    return service.handle_message(request)
