"""
API module - FastAPI routers.

All routers are aggregated into `api_router` for easy inclusion in main app.
"""
from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.trainer import router as trainer_router
from app.api.chat import router as chat_router
from app.api.clients import router as clients_router
from app.api.workouts import router as workouts_router
from app.api.trainings import router as trainings_router
from app.api.users import router as users_router
from app.api.feedback import router as feedback_router
from app.api.invitations import router as invitations_router

# Aggregate all routers
api_router = APIRouter()

# Authentication (no prefix - already has /api/auth)
api_router.include_router(auth_router)

# Role-based endpoints
api_router.include_router(trainer_router)

# Legacy/shared endpoints
api_router.include_router(chat_router)
api_router.include_router(clients_router)
api_router.include_router(workouts_router)
api_router.include_router(trainings_router)
api_router.include_router(users_router)
api_router.include_router(feedback_router)
api_router.include_router(invitations_router)

__all__ = [
    "api_router",
    "auth_router",
    "trainer_router",
    "chat_router",
    "clients_router",
    "workouts_router",
    "trainings_router",
    "users_router",
    "feedback_router",
    "invitations_router",
]
