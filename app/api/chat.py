"""
Chat API router with history persistence.
"""
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.schemas import ChatRequest
from app.services.chat_service import ChatService
from app.database.connection import get_db
from app.services.auth_service import get_current_user, get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Chat"])


# =============================================================================
# Schemas
# =============================================================================

class ChatMessageResponse(BaseModel):
    """Single chat message."""
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Chat history response."""
    messages: List[ChatMessageResponse]
    total: int


# =============================================================================
# Helper Functions
# =============================================================================

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


def save_chat_message(db: Session, user_id: int, role: str, content: str):
    """Save a chat message to database."""
    if db is None:
        return None

    try:
        from app.database import ChatMessage
        message = ChatMessage(
            user_id=user_id,
            role=role,
            content=content
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    except Exception as e:
        logger.error(f"Failed to save chat message: {e}")
        db.rollback()
        return None


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user_optional)
):
    """
    Chat endpoint with deterministic command parsing.
    Saves messages to history if user is authenticated.

    Flow:
    1. Save user message to history (if authenticated)
    2. Check if message is confirmation (tak/anuluj)
    3. Parse command with regex (NO LLM)
    4. Execute command (direct DB operation)
    5. If no command → use RAG for general questions
    6. Save AI response to history (if authenticated)
    """
    # Save user message if authenticated
    if current_user and db:
        save_chat_message(db, current_user.id, "user", request.message)

    # Process message
    service = ChatService(db)
    result = service.handle_message(request)

    # Save AI response if authenticated
    if current_user and db:
        response_text = result.get("response", "") if isinstance(result, dict) else str(result)
        save_chat_message(db, current_user.id, "assistant", response_text)

    return result


@router.get("/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get chat history for current user.
    Returns messages in chronological order (oldest first).
    """
    from app.database import ChatMessage

    # Get total count
    total = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).count()

    # Get messages
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(
        ChatMessage.created_at.asc()
    ).offset(offset).limit(limit).all()

    return ChatHistoryResponse(
        messages=[ChatMessageResponse.model_validate(m) for m in messages],
        total=total
    )


@router.delete("/chat/history")
async def clear_chat_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Clear all chat history for current user.
    """
    from app.database import ChatMessage

    deleted = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).delete()

    db.commit()

    return {"deleted": deleted, "message": "Historia chatu została wyczyszczona"}
