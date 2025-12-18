"""
TrenerAI Data Models

This module defines Pydantic models for exercises and training plans.
These models are used for:
- LLM structured output (ensures valid JSON responses)
- API response serialization
- Data validation

Models:
    Exercise: Single exercise with metadata
    TrainingPlan: Complete training plan with three phases
"""

from pydantic import BaseModel, Field
from typing import List


class Exercise(BaseModel):
    """
    Single exercise data model.

    Represents one exercise in a training plan with all necessary
    metadata for trainers to understand and execute it.

    Attributes:
        id: Unique exercise identifier (e.g., 'w1', 'm_e1', 'c3')
        name: Human-readable exercise name
        description: Brief instruction for the trainer
        muscle_group: Primary muscle group targeted (default: 'general')
        difficulty: Exercise difficulty ('easy', 'medium', 'hard')
        type: Exercise category ('warmup', 'main', 'cooldown')

    Example:
        {
            "id": "m_m1",
            "name": "Classic Push-ups",
            "description": "Chest to ground, body straight",
            "muscle_group": "chest",
            "difficulty": "medium",
            "type": "main"
        }
    """
    id: str = Field(description="Unique exercise identifier")
    name: str = Field(description="Exercise name")
    description: str = Field(description="Brief instruction for the trainer")
    muscle_group: str = Field(
        default="general",
        description="Primary muscle group targeted"
    )
    difficulty: str = Field(description="Level: easy, medium, hard")
    type: str = Field(description="Exercise type: warmup, main, cooldown")


class TrainingPlan(BaseModel):
    """
    Complete training plan output structure.

    Represents a full training session divided into three phases:
    warmup, main workout, and cooldown. This model is used as
    the structured output format for the LLM.

    Attributes:
        warmup: List of warmup exercises (typically 3-5 exercises)
        main_part: Main training exercises (varies by mode and num_people)
        cooldown: Cooldown and stretching exercises (typically 3-5 exercises)
        mode: Training mode ('circuit' or 'common')
        total_duration_minutes: Estimated total training duration

    Example:
        {
            "warmup": [...],
            "main_part": [...],
            "cooldown": [...],
            "mode": "circuit",
            "total_duration_minutes": 45
        }
    """
    warmup: List[Exercise] = Field(
        description="List of warmup exercises"
    )
    main_part: List[Exercise] = Field(
        description="Main training exercises"
    )
    cooldown: List[Exercise] = Field(
        description="Cooldown and stretching exercises"
    )
    mode: str = Field(
        description="Training mode: circuit or common"
    )
    total_duration_minutes: int = Field(
        description="Estimated total training duration"
    )
