"""
TrenerAI FastAPI Application

This module provides the REST API for the TrenerAI training plan generator.
It exposes endpoints for generating AI-powered workout plans.

Endpoints:
    GET  /                  - Status check
    GET  /health            - Health check for orchestration
    GET  /debug/config      - Show current configuration
    POST /generate-training - Generate a training plan

Usage:
    uvicorn app.main:app --reload
"""

import json
import logging
import os
import re
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.agent import app_graph, get_vector_store, get_llm, check_collection_exists

# Database imports
try:
    from app.database import (
        get_db, init_db,
        User as DBUser,
        GeneratedTraining,
        Feedback as DBFeedback,
        DifficultyLevel
    )
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logging.warning("Database module not available. Running without persistence.")

    # Dummy get_db when database is not available
    def get_db():
        raise HTTPException(status_code=503, detail="Database not available")

    def init_db():
        pass

    DBUser = None
    GeneratedTraining = None
    DBFeedback = None
    DifficultyLevel = None

# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# Client Storage
# =============================================================================

DATA_DIR = Path(__file__).parent.parent / "data"
CLIENTS_FILE = DATA_DIR / "clients.json"
WORKOUTS_FILE = DATA_DIR / "workouts.json"


def load_clients() -> List[dict]:
    if not CLIENTS_FILE.exists():
        return []
    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_clients(clients: List[dict]):
    DATA_DIR.mkdir(exist_ok=True)
    with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)


def load_workouts() -> List[dict]:
    if not WORKOUTS_FILE.exists():
        return []
    with open(WORKOUTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_workouts(workouts: List[dict]):
    DATA_DIR.mkdir(exist_ok=True)
    with open(WORKOUTS_FILE, "w", encoding="utf-8") as f:
        json.dump(workouts, f, ensure_ascii=False, indent=2)


# =============================================================================
# FastAPI Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    if DB_AVAILABLE:
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}. Running without DB.")
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="TrenerAI API",
    description="AI-powered training plan generator for fitness trainers. "
                "Supports both OpenAI and local Ollama LLMs.",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware - allows frontend applications to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request/Response Models
# =============================================================================

class Difficulty(str, Enum):
    """
    Exercise difficulty levels.

    Attributes:
        EASY: Beginner-friendly exercises
        MEDIUM: Intermediate exercises
        HARD: Advanced/challenging exercises
    """
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TrainingMode(str, Enum):
    """
    Training session modes.

    Attributes:
        CIRCUIT: Each participant does a different exercise (rotating stations)
        COMMON: All participants do the same exercises together
    """
    CIRCUIT = "circuit"
    COMMON = "common"


class TrainingRequest(BaseModel):
    """
    Request model for training plan generation.

    Attributes:
        num_people: Number of participants (1-50)
        difficulty: Exercise difficulty level
        rest_time: Rest time between exercises in seconds (10-300)
        mode: Training mode (circuit or common)
        warmup_count: Number of warmup exercises (1-10)
        main_count: Number of main exercises (1-20)
        cooldown_count: Number of cooldown exercises (1-10)
    """
    num_people: Annotated[int, Field(
        ge=1,
        le=50,
        description="Number of participants (1-50)"
    )]
    difficulty: Difficulty = Field(
        description="Difficulty level: easy, medium, hard"
    )
    rest_time: Annotated[int, Field(
        ge=10,
        le=300,
        description="Rest time between exercises in seconds (10-300)"
    )]
    mode: TrainingMode = Field(
        description="Training mode: circuit or common"
    )
    warmup_count: Annotated[int, Field(
        ge=1,
        le=10,
        description="Number of warmup exercises (1-10)"
    )] = 3
    main_count: Annotated[int, Field(
        ge=1,
        le=20,
        description="Number of main exercises (1-20)"
    )] = 5
    cooldown_count: Annotated[int, Field(
        ge=1,
        le=10,
        description="Number of cooldown exercises (1-10)"
    )] = 3


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    session_id: Optional[str] = "default"  # For tracking pending confirmations


class ProgressEntry(BaseModel):
    id: str
    date: str
    weight: float
    bodyFat: Optional[float] = None
    waist: Optional[float] = None
    notes: Optional[str] = None


class Client(BaseModel):
    id: str
    name: str
    age: int
    weight: float
    goal: str
    notes: str = ""
    createdAt: str
    progress: List[ProgressEntry] = []


class SavedWorkout(BaseModel):
    id: str
    clientId: Optional[str] = None
    title: str
    content: str
    date: str


# =============================================================================
# Database Request/Response Models
# =============================================================================

class UserCreate(BaseModel):
    """Create a new user."""
    email: str
    name: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    goals: Optional[str] = None
    contraindications: Optional[List[str]] = None
    preferred_difficulty: Optional[str] = "medium"


class UserResponse(BaseModel):
    """User response model."""
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


class TrainingHistoryResponse(BaseModel):
    """Training history entry."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    input_params: dict
    plan: dict
    model_name: Optional[str]
    prompt_version: Optional[str]
    created_at: datetime


class FeedbackCreate(BaseModel):
    """Create feedback for a training."""
    training_id: int
    rating: int = Field(ge=1, le=5, description="Rating 1-5")
    comment: Optional[str] = None
    was_too_hard: bool = False
    was_too_easy: bool = False
    exercises_liked: Optional[List[str]] = None
    exercises_disliked: Optional[List[str]] = None


class FeedbackResponse(BaseModel):
    """Feedback response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    training_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
def read_root() -> dict:
    """
    Root endpoint - basic API status check.

    Returns:
        dict: Status message and API version.
    """
    return {"status": "TrenerAI API Online", "version": "0.2.0"}


@app.get("/health")
def health_check() -> dict:
    """
    Health check endpoint for container orchestration (K8s, Docker).

    Returns:
        dict: Health status.
    """
    return {"status": "healthy"}


@app.get("/debug/config")
def debug_config() -> dict:
    """
    Debug endpoint to check current configuration.

    WARNING: Disable this endpoint in production environments
    as it may expose sensitive configuration details.

    Returns:
        dict: Current configuration values.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    return {
        "llm_provider": provider,
        "llm_model": os.getenv("LLM_MODEL", "gpt-4o"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "qdrant_url": os.getenv("QDRANT_URL", "http://localhost:6333"),
        "collection_name": os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises"),
    }


@app.post("/generate-training")
async def generate_training(request: TrainingRequest) -> dict:
    """
    Generate a complete training plan using LangGraph agent.

    This endpoint invokes the AI workflow to:
    1. Retrieve relevant exercises from the vector database
    2. Generate a structured training plan using LLM

    Args:
        request: Training parameters (num_people, difficulty, rest_time, mode, counts)

    Returns:
        dict: Generated training plan with warmup, main_part, and cooldown sections.

    Raises:
        HTTPException: 500 error if plan generation fails.

    Example:
        POST /generate-training
        {
            "num_people": 5,
            "difficulty": "medium",
            "rest_time": 60,
            "mode": "circuit",
            "warmup_count": 3,
            "main_count": 5,
            "cooldown_count": 3
        }
    """
    logger.info(
        f"Generating training plan: num_people={request.num_people}, "
        f"difficulty={request.difficulty.value}, mode={request.mode.value}, "
        f"warmup={request.warmup_count}, main={request.main_count}, cooldown={request.cooldown_count}"
    )

    try:
        # Prepare input for LangGraph workflow
        inputs = {
            "num_people": request.num_people,
            "difficulty": request.difficulty.value,
            "rest_time": request.rest_time,
            "mode": request.mode.value,
            "warmup_count": request.warmup_count,
            "main_count": request.main_count,
            "cooldown_count": request.cooldown_count
        }

        # Invoke the AI workflow
        result = app_graph.invoke(inputs)
        logger.info("Training plan generated successfully")

        return result["final_plan"]

    except ValueError as e:
        # Handle known errors (e.g., collection not found)
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error generating training plan: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate training plan: {str(e)}"
        )


# =============================================================================
# Client CRUD Endpoints
# =============================================================================

@app.get("/clients")
def get_clients() -> List[dict]:
    return load_clients()


@app.post("/clients")
def add_client(client: Client) -> dict:
    clients = load_clients()
    clients.append(client.model_dump())
    save_clients(clients)
    return {"status": "ok", "client": client.model_dump()}


@app.put("/clients/{client_id}")
def update_client(client_id: str, client: Client) -> dict:
    clients = load_clients()
    for i, c in enumerate(clients):
        if c["id"] == client_id:
            clients[i] = client.model_dump()
            save_clients(clients)
            return {"status": "ok", "client": client.model_dump()}
    raise HTTPException(status_code=404, detail="Client not found")


@app.delete("/clients/{client_id}")
def delete_client(client_id: str) -> dict:
    clients = load_clients()
    clients = [c for c in clients if c["id"] != client_id]
    save_clients(clients)
    return {"status": "ok"}


# =============================================================================
# Workout CRUD Endpoints
# =============================================================================

@app.get("/workouts")
def get_workouts() -> List[dict]:
    return load_workouts()


@app.post("/workouts")
def add_workout(workout: SavedWorkout) -> dict:
    workouts = load_workouts()
    workouts.append(workout.model_dump())
    save_workouts(workouts)
    return {"status": "ok", "workout": workout.model_dump()}


@app.delete("/workouts/{workout_id}")
def delete_workout(workout_id: str) -> dict:
    workouts = load_workouts()
    workouts = [w for w in workouts if w["id"] != workout_id]
    save_workouts(workouts)
    return {"status": "ok"}


# =============================================================================
# Database User Endpoints (Postgres)
# =============================================================================

@app.post("/api/users", response_model=UserResponse, tags=["Database"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user in the database."""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")

    # Check if email already exists
    existing = db.query(DBUser).filter(DBUser.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Map difficulty string to enum
    difficulty = DifficultyLevel.MEDIUM
    if user.preferred_difficulty:
        difficulty = DifficultyLevel(user.preferred_difficulty.upper())

    db_user = DBUser(
        email=user.email,
        name=user.name,
        age=user.age,
        weight=user.weight,
        height=user.height,
        goals=user.goals,
        contraindications=user.contraindications,
        preferred_difficulty=difficulty
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["Database"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID."""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")

    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/users", response_model=List[UserResponse], tags=["Database"])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all users."""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")

    users = db.query(DBUser).offset(skip).limit(limit).all()
    return users


# =============================================================================
# Training History Endpoints (Postgres)
# =============================================================================

@app.post("/api/trainings", tags=["Database"])
def save_training(
    request: TrainingRequest,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Generate and save a training plan to database.
    Like /generate-training but persists the result.
    """
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")

    logger.info(f"Generating and saving training for user_id={user_id}")

    try:
        inputs = {
            "num_people": request.num_people,
            "difficulty": request.difficulty.value,
            "rest_time": request.rest_time,
            "mode": request.mode.value,
            "warmup_count": request.warmup_count,
            "main_count": request.main_count,
            "cooldown_count": request.cooldown_count
        }

        result = app_graph.invoke(inputs)
        plan = result["final_plan"]

        # Save to database
        db_training = GeneratedTraining(
            user_id=user_id,
            input_params=inputs,
            plan=plan,
            model_name=os.getenv("LLM_MODEL", "unknown"),
            prompt_version="v1.0",
            retrieved_exercises=result.get("retrieved_exercises", [])
        )
        db.add(db_training)
        db.commit()
        db.refresh(db_training)

        logger.info(f"Training saved with id={db_training.id}")

        return {
            "training_id": db_training.id,
            "plan": plan
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trainings/{training_id}", response_model=TrainingHistoryResponse, tags=["Database"])
def get_training(training_id: int, db: Session = Depends(get_db)):
    """Get a specific training by ID."""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")

    training = db.query(GeneratedTraining).filter(GeneratedTraining.id == training_id).first()
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    return training


@app.get("/api/users/{user_id}/trainings", response_model=List[TrainingHistoryResponse], tags=["Database"])
def get_user_trainings(user_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Get all trainings for a user."""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")

    trainings = db.query(GeneratedTraining)\
        .filter(GeneratedTraining.user_id == user_id)\
        .order_by(GeneratedTraining.created_at.desc())\
        .offset(skip).limit(limit).all()
    return trainings


# =============================================================================
# Feedback Endpoints (Postgres)
# =============================================================================

@app.post("/api/feedback", response_model=FeedbackResponse, tags=["Database"])
def create_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """Submit feedback for a training."""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")

    # Check training exists
    training = db.query(GeneratedTraining).filter(
        GeneratedTraining.id == feedback.training_id
    ).first()
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")

    # Check if feedback already exists
    existing = db.query(DBFeedback).filter(
        DBFeedback.training_id == feedback.training_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Feedback already exists for this training")

    db_feedback = DBFeedback(
        training_id=feedback.training_id,
        rating=feedback.rating,
        comment=feedback.comment,
        was_too_hard=1 if feedback.was_too_hard else 0,
        was_too_easy=1 if feedback.was_too_easy else 0,
        exercises_liked=feedback.exercises_liked,
        exercises_disliked=feedback.exercises_disliked
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)

    return db_feedback


@app.get("/api/feedback/{training_id}", response_model=FeedbackResponse, tags=["Database"])
def get_feedback(training_id: int, db: Session = Depends(get_db)):
    """Get feedback for a training."""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")

    feedback = db.query(DBFeedback).filter(DBFeedback.training_id == training_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback


# =============================================================================
# Chat Command Parser
# =============================================================================

def parse_chat_command(message: str) -> Optional[dict]:
    """Parse chat message for client management commands."""
    msg = message.lower().strip()

    # List clients
    if any(x in msg for x in ["lista klientów", "pokaż klientów", "wszyscy podopieczni", "lista podopiecznych", "pokaż podopiecznych"]):
        return {"action": "list_clients"}

    # Show client details
    match = re.search(r"(?:pokaż|dane|info|szczegóły)\s+(?:klienta|podopiecznego)?\s*[:\-]?\s*(.+)", msg)
    if match:
        return {"action": "show_client", "name": match.group(1).strip()}

    # Add client: "dodaj klienta: Jan Kowalski, 30 lat, 80kg, cel: schudnąć"
    match = re.search(r"dodaj\s+(?:klienta|podopiecznego)\s*[:\-]?\s*(.+)", msg, re.IGNORECASE)
    if match:
        data = match.group(1)
        return {"action": "add_client", "data": data}

    # Delete client
    match = re.search(r"(?:usuń|usun|skasuj)\s+(?:klienta|podopiecznego)\s*[:\-]?\s*(.+)", msg)
    if match:
        return {"action": "delete_client", "name": match.group(1).strip()}

    # Show client workouts
    match = re.search(r"(?:treningi|plany)\s+(?:dla|klienta|podopiecznego)?\s*[:\-]?\s*(.+)", msg)
    if match:
        return {"action": "show_workouts", "name": match.group(1).strip()}

    return None


def execute_chat_command(cmd: dict) -> str:
    """Execute parsed chat command and return response."""
    action = cmd["action"]

    if action == "list_clients":
        clients = load_clients()
        if not clients:
            return "# BAZA PODOPIECZNYCH\n\nBrak zarejestrowanych podopiecznych. Użyj komendy:\n`dodaj klienta: Imię Nazwisko, wiek lat, wagakg, cel: opis celu`"

        result = "# BAZA PODOPIECZNYCH\n\n| Imię | Wiek | Waga | Cel |\n|---|---|---|---|\n"
        for c in clients:
            result += f"| {c['name']} | {c['age']} | {c['weight']}kg | {c['goal']} |\n"
        return result

    elif action == "show_client":
        name = cmd["name"]
        clients = load_clients()
        client = next((c for c in clients if name.lower() in c["name"].lower()), None)
        if not client:
            return f"# BŁĄD\n\nNie znaleziono podopiecznego: **{name}**"

        result = f"# PROFIL: {client['name'].upper()}\n\n"
        result += f"## Dane podstawowe\n"
        result += f"| Parametr | Wartość |\n|---|---|\n"
        result += f"| Wiek | {client['age']} lat |\n"
        result += f"| Waga | {client['weight']} kg |\n"
        result += f"| Cel | {client['goal']} |\n"
        if client.get('notes'):
            result += f"\n## Notatki\n{client['notes']}\n"
        if client.get('progress'):
            result += f"\n## Historia pomiarów\n"
            result += "| Data | Waga | Body Fat | Pas |\n|---|---|---|---|\n"
            for p in client['progress'][-5:]:
                result += f"| {p['date']} | {p['weight']}kg | {p.get('bodyFat', '-')}% | {p.get('waist', '-')}cm |\n"
        return result

    elif action == "add_client":
        data = cmd["data"]
        # Parse: "Jan Kowalski, 30 lat, 80kg, cel: schudnąć"
        parts = [p.strip() for p in data.split(",")]
        name = parts[0] if parts else "Nieznany"

        age = 25
        weight = 70.0
        goal = "Poprawa kondycji"

        for part in parts[1:]:
            part_lower = part.lower()
            if "lat" in part_lower:
                match = re.search(r"(\d+)", part)
                if match:
                    age = int(match.group(1))
            elif "kg" in part_lower:
                match = re.search(r"(\d+(?:\.\d+)?)", part)
                if match:
                    weight = float(match.group(1))
            elif "cel" in part_lower:
                goal = part.split(":", 1)[-1].strip() if ":" in part else part

        new_client = {
            "id": str(int(datetime.now().timestamp() * 1000)),
            "name": name,
            "age": age,
            "weight": weight,
            "goal": goal,
            "notes": "",
            "createdAt": datetime.now().strftime("%d.%m.%Y"),
            "progress": []
        }

        clients = load_clients()
        clients.append(new_client)
        save_clients(clients)

        return f"# DODANO PODOPIECZNEGO\n\n✓ **{name}** został dodany do bazy.\n\n| Parametr | Wartość |\n|---|---|\n| Wiek | {age} lat |\n| Waga | {weight} kg |\n| Cel | {goal} |"

    elif action == "delete_client":
        name = cmd["name"]
        clients = load_clients()
        client = next((c for c in clients if name.lower() in c["name"].lower()), None)
        if not client:
            return f"# BŁĄD\n\nNie znaleziono podopiecznego: **{name}**"

        clients = [c for c in clients if c["id"] != client["id"]]
        save_clients(clients)
        return f"# USUNIĘTO PODOPIECZNEGO\n\n✓ **{client['name']}** został usunięty z bazy."

    elif action == "show_workouts":
        name = cmd["name"]
        clients = load_clients()
        client = next((c for c in clients if name.lower() in c["name"].lower()), None)
        if not client:
            return f"# BŁĄD\n\nNie znaleziono podopiecznego: **{name}**"

        workouts = load_workouts()
        client_workouts = [w for w in workouts if w.get("clientId") == client["id"]]

        if not client_workouts:
            return f"# TRENINGI: {client['name'].upper()}\n\nBrak zapisanych treningów dla tego podopiecznego."

        result = f"# TRENINGI: {client['name'].upper()}\n\n"
        for w in client_workouts[-5:]:
            result += f"## {w['title']} ({w['date']})\n{w['content'][:200]}...\n\n---\n"
        return result

    return None


@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    """
    Chat endpoint with deterministic command parsing.

    Flow:
    1. Check if message is confirmation (tak/anuluj)
    2. Parse command with regex (NO LLM)
    3. Execute command (direct DB operation)
    4. If no command → use RAG for general questions
    """
    logger.info(f"Chat request: {request.message[:100]}...")
    session_id = request.session_id or "default"

    try:
        from app.chat_commands import (
            is_confirmation, parse_command, CommandType,
            CommandExecutor, get_pending_action, clear_pending_action
        )

        # Get DB session
        db_session = None
        if DB_AVAILABLE:
            from app.database import SessionLocal
            db_session = SessionLocal()

        try:
            executor = CommandExecutor(db_session)

            # ================================================================
            # STEP 1: Check for confirmation (tak/anuluj)
            # ================================================================
            confirmation = is_confirmation(request.message)

            if confirmation is True:
                # User confirmed - execute pending action
                pending = get_pending_action(session_id)
                if pending:
                    result = executor.execute_pending(session_id)
                    return {
                        "response": result.message,
                        "command": pending.command,
                        "data": result.data
                    }
                else:
                    return {"response": "Nie mam nic do potwierdzenia."}

            elif confirmation is False:
                # User cancelled
                clear_pending_action(session_id)
                return {"response": "Anulowano."}

            # ================================================================
            # STEP 2: Parse command with regex (NO LLM!)
            # ================================================================
            parsed = parse_command(request.message)

            if parsed.command != CommandType.NONE:
                logger.info(f"Parsed command: {parsed.command.value}")

                result = executor.execute(parsed, session_id)

                # Special case: CREATE_TRAINING needs LangGraph
                if result.data and result.data.get("use_langgraph"):
                    # Use LangGraph for training generation
                    params = result.data.get("params", {})
                    inputs = {
                        "num_people": params.get("num_people", 1),
                        "difficulty": params.get("difficulty", "medium"),
                        "rest_time": 60,
                        "mode": params.get("mode", "circuit"),
                        "warmup_count": 3,
                        "main_count": 5,
                        "cooldown_count": 3
                    }

                    try:
                        plan_result = app_graph.invoke(inputs)
                        plan = plan_result.get("final_plan", {})
                        return {
                            "response": f"**Plan treningowy wygenerowany!**\n\n*(szczegóły w data)*",
                            "command": "CREATE_TRAINING",
                            "data": {"plan": plan, "params": inputs}
                        }
                    except Exception as e:
                        return {"response": f"Błąd generowania planu: {e}"}

                return {
                    "response": result.message,
                    "command": parsed.command.value if result.success else None,
                    "data": result.data,
                    "needs_confirmation": result.needs_confirmation
                }

            # ================================================================
            # STEP 3: No command found → RAG for general questions
            # ================================================================
            context = ""
            if check_collection_exists():
                vector_store = get_vector_store()
                docs = vector_store.similarity_search(request.message, k=10)
                if docs:
                    context = "Dostępne ćwiczenia z bazy:\n" + "\n".join(
                        [f"- {d.page_content}" for d in docs]
                    )

            # Build conversation history
            history_text = ""
            for msg in (request.history or [])[-6:]:
                role = "Użytkownik" if msg.role == "user" else "Asystent"
                history_text += f"{role}: {msg.content}\n\n"

            # System prompt for general questions
            system_prompt = """Jesteś asystentem trenera personalnego. Odpowiadaj krótko i konkretnie.
Używaj formatowania Markdown. Nie wymyślaj danych - używaj tylko tego co wiesz.

{context}"""

            full_prompt = f"{system_prompt.format(context=context)}\n\n{history_text}Użytkownik: {request.message}\n\nAsystent:"

            llm = get_llm()
            response = llm.invoke(full_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            return {"response": response_text}

        finally:
            if db_session:
                db_session.close()

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
