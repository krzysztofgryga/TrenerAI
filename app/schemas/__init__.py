"""
Pydantic schemas for TrenerAI API.

This module contains all request/response models used by the API.
"""
from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Enums
# =============================================================================

class Difficulty(str, Enum):
    """Exercise difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TrainingMode(str, Enum):
    """Training session modes."""
    CIRCUIT = "circuit"
    COMMON = "common"


# =============================================================================
# Chat Schemas
# =============================================================================

class ChatMessage(BaseModel):
    """Single chat message."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Chat endpoint request."""
    message: str
    history: Optional[List[ChatMessage]] = []
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    """Chat endpoint response."""
    response: str
    command: Optional[str] = None
    data: Optional[dict] = None
    needs_confirmation: bool = False


# =============================================================================
# Client Schemas (JSON storage)
# =============================================================================

class ProgressEntry(BaseModel):
    """Client progress measurement entry."""
    id: str
    date: str
    weight: float
    bodyFat: Optional[float] = None
    waist: Optional[float] = None
    notes: Optional[str] = None


class ClientBase(BaseModel):
    """Base client schema."""
    name: str
    age: int
    weight: float
    goal: str
    notes: str = ""


class ClientCreate(ClientBase):
    """Schema for creating a client."""
    pass


class Client(ClientBase):
    """Full client schema with all fields."""
    id: str
    createdAt: str
    progress: List[ProgressEntry] = []


# =============================================================================
# Training Schemas
# =============================================================================

class TrainingRequest(BaseModel):
    """Request for training plan generation."""
    num_people: Annotated[int, Field(ge=1, le=50, description="Number of participants")]
    difficulty: Difficulty
    rest_time: Annotated[int, Field(ge=10, le=300, description="Rest time in seconds")]
    mode: TrainingMode
    warmup_count: Annotated[int, Field(ge=1, le=10)] = 3
    main_count: Annotated[int, Field(ge=1, le=20)] = 5
    cooldown_count: Annotated[int, Field(ge=1, le=10)] = 3


class SavedWorkout(BaseModel):
    """Saved workout schema."""
    id: str
    clientId: Optional[str] = None
    title: str
    content: str
    date: str


# =============================================================================
# User Schemas (Database)
# =============================================================================

class UserCreate(BaseModel):
    """Schema for creating a user in database."""
    email: str
    name: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    goals: Optional[str] = None
    contraindications: Optional[List[str]] = None
    preferred_difficulty: Optional[str] = "medium"


class UserResponse(BaseModel):
    """User response from database."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: Optional[str]
    age: Optional[int]
    weight: Optional[float]
    height: Optional[float]
    goals: Optional[str]
    preferred_difficulty: Optional[str]
    created_at: datetime


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    goals: Optional[str] = None
    contraindications: Optional[List[str]] = None
    preferred_difficulty: Optional[str] = None


# =============================================================================
# Training History Schemas (Database)
# =============================================================================

class TrainingHistoryResponse(BaseModel):
    """Training history entry from database."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    input_params: dict
    plan: dict
    model_name: Optional[str]
    prompt_version: Optional[str]
    created_at: datetime


# =============================================================================
# Feedback Schemas (Database)
# =============================================================================

class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""
    training_id: int
    rating: int = Field(ge=1, le=5, description="Rating 1-5")
    comment: Optional[str] = None
    was_too_hard: bool = False
    was_too_easy: bool = False
    exercises_liked: Optional[List[str]] = None
    exercises_disliked: Optional[List[str]] = None


class FeedbackResponse(BaseModel):
    """Feedback response from database."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    training_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
