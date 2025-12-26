"""
Pydantic schemas for TrenerAI API.

This module contains all request/response models used by the API.
"""
from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field, ConfigDict, EmailStr


# =============================================================================
# Enums
# =============================================================================

class UserRole(str, Enum):
    """User role in the system."""
    TRAINER = "trainer"
    CLIENT = "client"


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
# Authentication Schemas
# =============================================================================

class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters")
    name: str = Field(min_length=2)
    role: UserRole = UserRole.CLIENT


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: UserRole


# =============================================================================
# User Schemas
# =============================================================================

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    name: str
    role: UserRole


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    """User response from database."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None


# =============================================================================
# Client Profile Schemas
# =============================================================================

class ClientProfileBase(BaseModel):
    """Base client profile schema."""
    age: Optional[int] = Field(None, ge=10, le=120)
    weight: Optional[float] = Field(None, ge=20, le=300, description="Weight in kg")
    height: Optional[float] = Field(None, ge=100, le=250, description="Height in cm")
    goals: Optional[str] = None
    contraindications: Optional[List[str]] = None
    preferred_difficulty: Optional[Difficulty] = Difficulty.MEDIUM


class ClientProfileCreate(ClientProfileBase):
    """Schema for creating client profile."""
    pass


class ClientProfileUpdate(ClientProfileBase):
    """Schema for updating client profile."""
    trainer_notes: Optional[str] = None


class ClientProfileResponse(ClientProfileBase):
    """Client profile response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    trainer_notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class ClientWithProfile(UserResponse):
    """Client with their profile."""
    profile: Optional[ClientProfileResponse] = None


# =============================================================================
# Trainer-Client Relationship Schemas
# =============================================================================

class TrainerClientCreate(BaseModel):
    """Schema for creating trainer-client relationship."""
    client_id: int
    can_generate_training: bool = False
    can_view_history: bool = True


class TrainerClientUpdate(BaseModel):
    """Schema for updating trainer-client relationship."""
    can_generate_training: Optional[bool] = None
    can_view_history: Optional[bool] = None
    is_active: Optional[bool] = None


class TrainerClientResponse(BaseModel):
    """Trainer-client relationship response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    trainer_id: int
    client_id: int
    can_generate_training: bool
    can_view_history: bool
    is_active: bool
    created_at: datetime

    # Nested data (optional, populated when needed)
    client: Optional[UserResponse] = None
    trainer: Optional[UserResponse] = None


# =============================================================================
# Group Schemas
# =============================================================================

class GroupBase(BaseModel):
    """Base group schema."""
    name: str = Field(min_length=2)
    description: Optional[str] = None
    max_members: Optional[int] = Field(None, ge=1)


class GroupCreate(GroupBase):
    """Schema for creating a group."""
    pass


class GroupUpdate(BaseModel):
    """Schema for updating a group."""
    name: Optional[str] = None
    description: Optional[str] = None
    max_members: Optional[int] = None
    is_active: Optional[bool] = None


class GroupResponse(GroupBase):
    """Group response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    trainer_id: int
    is_active: bool
    created_at: datetime
    member_count: Optional[int] = None


class GroupMemberAdd(BaseModel):
    """Schema for adding member to group."""
    client_id: int


class GroupMemberResponse(BaseModel):
    """Group member response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    client_id: int
    joined_at: datetime
    is_active: bool

    # Nested client data
    client: Optional[UserResponse] = None


class GroupWithMembers(GroupResponse):
    """Group with its members."""
    members: List[GroupMemberResponse] = []


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

    # Optional: generate for specific client or group
    client_id: Optional[int] = None
    group_id: Optional[int] = None


class TrainingHistoryResponse(BaseModel):
    """Training history entry from database."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int]
    created_by_id: Optional[int]
    group_id: Optional[int]
    input_params: dict
    plan: dict
    model_name: Optional[str]
    prompt_version: Optional[str]
    created_at: datetime


# =============================================================================
# Saved Workout Schemas (JSON storage - legacy)
# =============================================================================

class SavedWorkout(BaseModel):
    """Saved workout schema."""
    id: str
    clientId: Optional[str] = None
    title: str
    content: str
    date: str


class ProgressEntry(BaseModel):
    """Client progress measurement entry."""
    id: str
    date: str
    weight: float
    bodyFat: Optional[float] = None
    waist: Optional[float] = None
    notes: Optional[str] = None


# =============================================================================
# Feedback Schemas
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


# =============================================================================
# Dashboard Schemas (Trainer view)
# =============================================================================

class TrainerDashboard(BaseModel):
    """Trainer dashboard data."""
    total_clients: int
    active_clients: int
    total_groups: int
    trainings_this_week: int
    recent_clients: List[ClientWithProfile] = []


class ClientDashboard(BaseModel):
    """Client dashboard data."""
    trainer: Optional[UserResponse] = None
    upcoming_trainings: int
    completed_trainings: int
    groups: List[GroupResponse] = []
