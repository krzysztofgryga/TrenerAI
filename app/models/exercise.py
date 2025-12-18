from pydantic import BaseModel, Field
from typing import List


class Exercise(BaseModel):
    """Single exercise data model."""
    id: str = Field(description="Unique exercise identifier")
    name: str = Field(description="Exercise name")
    description: str = Field(description="Brief instruction for the trainer")
    muscle_group: str = Field(default="general", description="Primary muscle group targeted")
    difficulty: str = Field(description="Level: easy, medium, hard")
    type: str = Field(description="Exercise type: warmup, main, cooldown")


class TrainingPlan(BaseModel):
    """Complete training plan output structure."""
    warmup: List[Exercise] = Field(description="List of warmup exercises")
    main_part: List[Exercise] = Field(description="Main training exercises")
    cooldown: List[Exercise] = Field(description="Cooldown and stretching exercises")
    mode: str = Field(description="Training mode: circuit or common")
    total_duration_minutes: int = Field(description="Estimated total training duration")
