"""
JSON file storage for TrenerAI.

Legacy storage system for clients and workouts.
Will be replaced by PostgreSQL in production.
"""
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from app.schemas import Client, SavedWorkout


# =============================================================================
# Storage Configuration
# =============================================================================

DATA_DIR = Path(__file__).parent.parent.parent / "data"
CLIENTS_FILE = DATA_DIR / "clients.json"
WORKOUTS_FILE = DATA_DIR / "workouts.json"


def _ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)


# =============================================================================
# Client Storage
# =============================================================================

def load_clients() -> List[dict]:
    """Load all clients from JSON file."""
    if not CLIENTS_FILE.exists():
        return []
    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_clients(clients: List[dict]):
    """Save all clients to JSON file."""
    _ensure_data_dir()
    with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)


def get_client_by_id(client_id: str) -> Optional[dict]:
    """Get a single client by ID."""
    clients = load_clients()
    return next((c for c in clients if c["id"] == client_id), None)


def get_client_by_name(name: str) -> Optional[dict]:
    """Get a single client by name (partial match)."""
    clients = load_clients()
    return next((c for c in clients if name.lower() in c["name"].lower()), None)


def add_client(client_data: dict) -> dict:
    """Add a new client and return it."""
    clients = load_clients()

    # Generate ID if not present
    if "id" not in client_data:
        client_data["id"] = str(int(datetime.now().timestamp() * 1000))

    # Add creation date if not present
    if "createdAt" not in client_data:
        client_data["createdAt"] = datetime.now().strftime("%d.%m.%Y")

    # Ensure progress list exists
    if "progress" not in client_data:
        client_data["progress"] = []

    clients.append(client_data)
    save_clients(clients)
    return client_data


def update_client(client_id: str, client_data: dict) -> Optional[dict]:
    """Update an existing client."""
    clients = load_clients()
    for i, c in enumerate(clients):
        if c["id"] == client_id:
            client_data["id"] = client_id  # Preserve ID
            clients[i] = client_data
            save_clients(clients)
            return client_data
    return None


def delete_client(client_id: str) -> bool:
    """Delete a client by ID. Returns True if deleted."""
    clients = load_clients()
    original_count = len(clients)
    clients = [c for c in clients if c["id"] != client_id]
    if len(clients) < original_count:
        save_clients(clients)
        return True
    return False


def delete_client_by_name(name: str) -> Optional[dict]:
    """Delete a client by name. Returns deleted client or None."""
    client = get_client_by_name(name)
    if client:
        delete_client(client["id"])
        return client
    return None


# =============================================================================
# Workout Storage
# =============================================================================

def load_workouts() -> List[dict]:
    """Load all workouts from JSON file."""
    if not WORKOUTS_FILE.exists():
        return []
    with open(WORKOUTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_workouts(workouts: List[dict]):
    """Save all workouts to JSON file."""
    _ensure_data_dir()
    with open(WORKOUTS_FILE, "w", encoding="utf-8") as f:
        json.dump(workouts, f, ensure_ascii=False, indent=2)


def get_workout_by_id(workout_id: str) -> Optional[dict]:
    """Get a single workout by ID."""
    workouts = load_workouts()
    return next((w for w in workouts if w["id"] == workout_id), None)


def get_workouts_by_client(client_id: str) -> List[dict]:
    """Get all workouts for a specific client."""
    workouts = load_workouts()
    return [w for w in workouts if w.get("clientId") == client_id]


def add_workout(workout_data: dict) -> dict:
    """Add a new workout and return it."""
    workouts = load_workouts()

    # Generate ID if not present
    if "id" not in workout_data:
        workout_data["id"] = str(int(datetime.now().timestamp() * 1000))

    # Add date if not present
    if "date" not in workout_data:
        workout_data["date"] = datetime.now().strftime("%d.%m.%Y")

    workouts.append(workout_data)
    save_workouts(workouts)
    return workout_data


def delete_workout(workout_id: str) -> bool:
    """Delete a workout by ID. Returns True if deleted."""
    workouts = load_workouts()
    original_count = len(workouts)
    workouts = [w for w in workouts if w["id"] != workout_id]
    if len(workouts) < original_count:
        save_workouts(workouts)
        return True
    return False
