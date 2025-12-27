"""
Database module for TrenerAI.
"""
from app.database.connection import (
    Base,
    engine,
    SessionLocal,
    get_db,
    get_db_session,
    init_db,
    DATABASE_URL,
    DB_AVAILABLE
)
from app.database.models import (
    User,
    UserRole,
    ClientProfile,
    TrainerClient,
    Group,
    GroupMember,
    GeneratedTraining,
    Feedback,
    DifficultyLevel,
    ChatMessage,
    Invitation
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_session",
    "init_db",
    "DATABASE_URL",
    "DB_AVAILABLE",
    "User",
    "UserRole",
    "ClientProfile",
    "TrainerClient",
    "Group",
    "GroupMember",
    "GeneratedTraining",
    "Feedback",
    "DifficultyLevel",
    "ChatMessage",
    "Invitation",
]
