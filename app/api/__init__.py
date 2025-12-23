"""
API module - FastAPI routers.

All routers are aggregated into `api_router` for easy inclusion in main app.
"""
from fastapi import APIRouter

from app.api.chat import router as chat_router
from app.api.clients import router as clients_router
from app.api.workouts import router as workouts_router
from app.api.trainings import router as trainings_router
from app.api.users import router as users_router
from app.api.feedback import router as feedback_router

# Aggregate all routers
api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(clients_router)
api_router.include_router(workouts_router)
api_router.include_router(trainings_router)
api_router.include_router(users_router)
api_router.include_router(feedback_router)

__all__ = [
    "api_router",
    "chat_router",
    "clients_router",
    "workouts_router",
    "trainings_router",
    "users_router",
    "feedback_router",
]
