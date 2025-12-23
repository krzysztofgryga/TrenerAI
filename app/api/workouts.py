"""
Workouts API router - JSON storage.
"""
from typing import List
from fastapi import APIRouter

from app.schemas import SavedWorkout
from app.storage import load_workouts, save_workouts

router = APIRouter(tags=["Workouts"])


@router.get("/workouts")
def get_workouts() -> List[dict]:
    """Get all workouts."""
    return load_workouts()


@router.post("/workouts")
def add_workout(workout: SavedWorkout) -> dict:
    """Add a new workout."""
    workouts = load_workouts()
    workouts.append(workout.model_dump())
    save_workouts(workouts)
    return {"status": "ok", "workout": workout.model_dump()}


@router.delete("/workouts/{workout_id}")
def delete_workout(workout_id: str) -> dict:
    """Delete a workout."""
    workouts = load_workouts()
    workouts = [w for w in workouts if w["id"] != workout_id]
    save_workouts(workouts)
    return {"status": "ok"}
