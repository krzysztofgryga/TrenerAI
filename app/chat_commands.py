"""
Deterministic Chat Command System for TrenerAI.

NO LLM for commands - only regex parsing and direct DB operations.
LLM is only used for training generation and general questions.

Flow:
    1. Check confirmation (tak/anuluj)
    2. Parse command with regex (deterministic)
    3. Execute command (DB operation)
    4. If no command → pass to LLM/RAG
"""
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Session State Management
# =============================================================================

@dataclass
class PendingAction:
    """Action waiting for user confirmation."""
    command: str  # CREATE_USER, DELETE_USER, etc.
    payload: Dict[str, Any]
    preview_message: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=5))

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


# In-memory store for pending actions (per session)
# In production, use Redis
PENDING_ACTIONS: Dict[str, PendingAction] = {}


def get_pending_action(session_id: str) -> Optional[PendingAction]:
    """Get pending action for session, None if expired or not exists."""
    action = PENDING_ACTIONS.get(session_id)
    if action and action.is_expired():
        PENDING_ACTIONS.pop(session_id, None)
        return None
    return action


def set_pending_action(session_id: str, action: PendingAction):
    """Set pending action for session."""
    PENDING_ACTIONS[session_id] = action


def clear_pending_action(session_id: str):
    """Clear pending action for session."""
    PENDING_ACTIONS.pop(session_id, None)


# =============================================================================
# Command Types
# =============================================================================

class CommandType(str, Enum):
    # User management
    CREATE_USER = "CREATE_USER"
    LIST_USERS = "LIST_USERS"
    SHOW_USER = "SHOW_USER"
    DELETE_USER = "DELETE_USER"

    # Training
    CREATE_TRAINING = "CREATE_TRAINING"
    LIST_TRAININGS = "LIST_TRAININGS"

    # Help
    HELP = "HELP"

    # No command found
    NONE = "NONE"


# =============================================================================
# Deterministic Command Parser (NO LLM!)
# =============================================================================

@dataclass
class ParsedCommand:
    """Result of command parsing."""
    command: CommandType
    payload: Dict[str, Any] = field(default_factory=dict)
    raw_match: str = ""


def parse_user_data(text: str) -> Dict[str, Any]:
    """Extract user data from text like 'Jan Kowalski, 30 lat, 80kg, cel: schudnąć'"""
    payload = {}

    # Name - everything before first comma or number
    name_match = re.match(r'^([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]+?)(?:,|\d|$)', text.strip())
    if name_match:
        payload['name'] = name_match.group(1).strip()

    # Age
    age_match = re.search(r'(\d+)\s*(?:lat|lata|roku|rok|years?|l\.?)', text, re.IGNORECASE)
    if age_match:
        payload['age'] = int(age_match.group(1))

    # Weight
    weight_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:kg|kilo)', text, re.IGNORECASE)
    if weight_match:
        payload['weight'] = float(weight_match.group(1).replace(',', '.'))

    # Height
    height_match = re.search(r'(\d+)\s*(?:cm|centymetr)', text, re.IGNORECASE)
    if height_match:
        payload['height'] = float(height_match.group(1))

    # Goal
    goal_match = re.search(r'cel[:\s]+(.+?)(?:,|$)', text, re.IGNORECASE)
    if goal_match:
        payload['goals'] = goal_match.group(1).strip()

    return payload


def parse_training_params(text: str) -> Dict[str, Any]:
    """Extract training parameters from text."""
    payload = {}

    # Difficulty
    if re.search(r'\b(łatw|easy|pocz[aą]tkuj|beginner)\w*\b', text, re.IGNORECASE):
        payload['difficulty'] = 'easy'
    elif re.search(r'\b(trudn|hard|zaawans|advanced)\w*\b', text, re.IGNORECASE):
        payload['difficulty'] = 'hard'
    elif re.search(r'\b(średni|medium|intermediate)\w*\b', text, re.IGNORECASE):
        payload['difficulty'] = 'medium'

    # Mode
    if re.search(r'\b(circuit|obwod|obwód)\w*\b', text, re.IGNORECASE):
        payload['mode'] = 'circuit'
    elif re.search(r'\b(common|wspóln|wspoln)\w*\b', text, re.IGNORECASE):
        payload['mode'] = 'common'

    # Number of people
    people_match = re.search(r'(\d+)\s*(?:osob|osób|person|people|uczestnik)', text, re.IGNORECASE)
    if people_match:
        payload['num_people'] = int(people_match.group(1))

    # Duration
    duration_match = re.search(r'(\d+)\s*(?:minut|min)', text, re.IGNORECASE)
    if duration_match:
        payload['duration'] = int(duration_match.group(1))

    # For user
    for_match = re.search(r'(?:dla|for)\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+)', text, re.IGNORECASE)
    if for_match:
        payload['target_user'] = for_match.group(1).strip()

    return payload


# Command patterns - order matters (more specific first)
COMMAND_PATTERNS: List[Tuple[str, CommandType, callable]] = [
    # Help
    (r'^(?:pomoc|help|komendy|commands|\?)$', CommandType.HELP, lambda m: {}),

    # Create user - various forms
    (r'(?:dodaj|utwórz|stwórz|nowy|add|create)\s+(?:podopieczn\w*|klient\w*|użytkownik\w*|user\w*)[\s:]*(.+)',
     CommandType.CREATE_USER, lambda m: parse_user_data(m.group(1))),

    # List users
    (r'(?:lista|pokaż|wyświetl|list|show)\s+(?:podopieczn\w*|klient\w*|użytkownik\w*|wszystk\w*)',
     CommandType.LIST_USERS, lambda m: {}),

    (r'(?:podopieczni|klienci|użytkownicy)$',
     CommandType.LIST_USERS, lambda m: {}),

    # Show specific user
    (r'(?:pokaż|dane|info|szczegóły|profil)\s+(?:podopieczn\w*|klient\w*)?\s*[:\-]?\s*([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+)',
     CommandType.SHOW_USER, lambda m: {'name': m.group(1).strip()}),

    # Delete user
    (r'(?:usuń|usun|skasuj|delete|remove)\s+(?:podopieczn\w*|klient\w*|użytkownik\w*)?\s*[:\-]?\s*([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+)',
     CommandType.DELETE_USER, lambda m: {'name': m.group(1).strip()}),

    # Create training
    (r'(?:wygeneruj|stwórz|zrób|utwórz|generuj|create)\s+(?:plan\s+)?(?:trening\w*|training|circuit|obwód)',
     CommandType.CREATE_TRAINING, lambda m: parse_training_params(m.string)),

    (r'(?:trening|circuit|obwód)\s+(?:dla|na|for)\s+(\d+)',
     CommandType.CREATE_TRAINING, lambda m: {'num_people': int(m.group(1))}),

    # List trainings
    (r'(?:lista|pokaż|historia)\s+(?:trening\w*|plan\w*)',
     CommandType.LIST_TRAININGS, lambda m: {}),
]


def parse_command(message: str) -> ParsedCommand:
    """
    Parse message into command using regex patterns.
    NO LLM - fully deterministic.
    """
    msg = message.strip()

    for pattern, command_type, payload_extractor in COMMAND_PATTERNS:
        match = re.search(pattern, msg, re.IGNORECASE)
        if match:
            try:
                payload = payload_extractor(match)
                logger.info(f"Parsed command: {command_type.value}, payload: {payload}")
                return ParsedCommand(
                    command=command_type,
                    payload=payload,
                    raw_match=match.group(0)
                )
            except Exception as e:
                logger.error(f"Error extracting payload: {e}")
                continue

    return ParsedCommand(command=CommandType.NONE)


# =============================================================================
# Confirmation Check
# =============================================================================

def is_confirmation(message: str) -> Optional[bool]:
    """
    Check if message is a confirmation.
    Returns: True (confirm), False (cancel), None (not a confirmation)
    """
    msg = message.lower().strip()

    # Confirmations
    if msg in ['tak', 'yes', 'ok', 'potwierdź', 'potwierdzam', 'dawaj', 'jasne', 'sure', 'y']:
        return True

    # Cancellations
    if msg in ['nie', 'no', 'anuluj', 'cancel', 'stop', 'rezygnuję', 'n']:
        return False

    return None


# =============================================================================
# Command Executor (DB operations, NO LLM!)
# =============================================================================

@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    needs_confirmation: bool = False
    pending_action: Optional[PendingAction] = None


class CommandExecutor:
    """Executes commands - direct DB operations, no LLM."""

    def __init__(self, db_session=None):
        self.db = db_session

    def execute(self, command: ParsedCommand, session_id: str = "default") -> CommandResult:
        """Execute a parsed command."""
        handlers = {
            CommandType.CREATE_USER: self._create_user,
            CommandType.LIST_USERS: self._list_users,
            CommandType.SHOW_USER: self._show_user,
            CommandType.DELETE_USER: self._delete_user,
            CommandType.CREATE_TRAINING: self._create_training,
            CommandType.LIST_TRAININGS: self._list_trainings,
            CommandType.HELP: self._help,
        }

        handler = handlers.get(command.command)
        if handler:
            return handler(command.payload, session_id)

        return CommandResult(success=False, message="Nieznana komenda")

    def execute_pending(self, session_id: str) -> CommandResult:
        """Execute pending action after confirmation."""
        action = get_pending_action(session_id)
        if not action:
            return CommandResult(success=False, message="Brak oczekującej akcji do potwierdzenia.")

        clear_pending_action(session_id)

        # Re-create command and execute without confirmation
        command = ParsedCommand(
            command=CommandType(action.command),
            payload=action.payload
        )

        # Execute the actual operation
        if action.command == "CREATE_USER":
            return self._do_create_user(action.payload)
        elif action.command == "DELETE_USER":
            return self._do_delete_user(action.payload)

        return CommandResult(success=False, message="Nieobsługiwana akcja")

    # =========================================================================
    # User Commands
    # =========================================================================

    def _create_user(self, payload: Dict, session_id: str) -> CommandResult:
        """Prepare user creation - ask for confirmation."""
        name = payload.get('name', 'Nieznany')
        age = payload.get('age', '-')
        weight = payload.get('weight', '-')
        goals = payload.get('goals', '-')

        preview = f"""Dodać podopiecznego?

| Pole | Wartość |
|------|---------|
| Imię | {name} |
| Wiek | {age} |
| Waga | {weight} kg |
| Cel | {goals} |

Potwierdź: **tak** / **anuluj**"""

        # Store pending action
        action = PendingAction(
            command="CREATE_USER",
            payload=payload,
            preview_message=preview
        )
        set_pending_action(session_id, action)

        return CommandResult(
            success=True,
            message=preview,
            needs_confirmation=True,
            pending_action=action
        )

    def _do_create_user(self, payload: Dict) -> CommandResult:
        """Actually create the user in DB."""
        name = payload.get('name', 'Nieznany')

        if self.db:
            try:
                from app.database import User as DBUser, DifficultyLevel

                # Generate email from name
                email = f"{name.lower().replace(' ', '.')}@trenerai.local"

                db_user = DBUser(
                    email=email,
                    name=name,
                    age=payload.get('age'),
                    weight=payload.get('weight'),
                    height=payload.get('height'),
                    goals=payload.get('goals'),
                    preferred_difficulty=DifficultyLevel.MEDIUM
                )
                self.db.add(db_user)
                self.db.commit()
                self.db.refresh(db_user)

                return CommandResult(
                    success=True,
                    message=f"✓ Dodano podopiecznego **{name}** (ID: {db_user.id})",
                    data={"user_id": db_user.id, "name": name}
                )
            except Exception as e:
                logger.error(f"DB error: {e}")
                return CommandResult(success=False, message=f"Błąd bazy danych: {e}")
        else:
            # Fallback to JSON storage
            from app.main import load_clients, save_clients

            new_client = {
                "id": str(int(datetime.now().timestamp() * 1000)),
                "name": name,
                "age": payload.get('age', 0),
                "weight": payload.get('weight', 0),
                "goal": payload.get('goals', ''),
                "notes": "",
                "createdAt": datetime.now().strftime("%d.%m.%Y"),
                "progress": []
            }

            clients = load_clients()
            clients.append(new_client)
            save_clients(clients)

            return CommandResult(
                success=True,
                message=f"✓ Dodano podopiecznego **{name}** (ID: {new_client['id']})",
                data={"user_id": new_client['id'], "name": name}
            )

    def _list_users(self, payload: Dict, session_id: str) -> CommandResult:
        """List all users."""
        if self.db:
            try:
                from app.database import User as DBUser
                users = self.db.query(DBUser).all()

                if not users:
                    return CommandResult(
                        success=True,
                        message="Brak zarejestrowanych podopiecznych."
                    )

                table = "| ID | Imię | Wiek | Waga | Cel |\n|---|---|---|---|---|\n"
                for u in users:
                    table += f"| {u.id} | {u.name or '-'} | {u.age or '-'} | {u.weight or '-'} kg | {u.goals or '-'} |\n"

                return CommandResult(
                    success=True,
                    message=f"**Lista podopiecznych ({len(users)}):**\n\n{table}",
                    data={"count": len(users)}
                )
            except Exception as e:
                logger.error(f"DB error: {e}")

        # Fallback to JSON
        from app.main import load_clients
        clients = load_clients()

        if not clients:
            return CommandResult(
                success=True,
                message="Brak zarejestrowanych podopiecznych."
            )

        table = "| Imię | Wiek | Waga | Cel |\n|---|---|---|---|\n"
        for c in clients:
            table += f"| {c['name']} | {c.get('age', '-')} | {c.get('weight', '-')} kg | {c.get('goal', '-')} |\n"

        return CommandResult(
            success=True,
            message=f"**Lista podopiecznych ({len(clients)}):**\n\n{table}",
            data={"count": len(clients)}
        )

    def _show_user(self, payload: Dict, session_id: str) -> CommandResult:
        """Show user details."""
        name = payload.get('name', '')

        # Search in DB or JSON
        from app.main import load_clients
        clients = load_clients()
        client = next((c for c in clients if name.lower() in c['name'].lower()), None)

        if not client:
            return CommandResult(
                success=False,
                message=f"Nie znaleziono podopiecznego: **{name}**"
            )

        msg = f"""**Profil: {client['name']}**

| Pole | Wartość |
|------|---------|
| Wiek | {client.get('age', '-')} |
| Waga | {client.get('weight', '-')} kg |
| Cel | {client.get('goal', '-')} |
| Dodany | {client.get('createdAt', '-')} |"""

        return CommandResult(success=True, message=msg, data=client)

    def _delete_user(self, payload: Dict, session_id: str) -> CommandResult:
        """Prepare user deletion - ask for confirmation."""
        name = payload.get('name', '')

        preview = f"""Usunąć podopiecznego **{name}**?

⚠️ Ta operacja jest nieodwracalna.

Potwierdź: **tak** / **anuluj**"""

        action = PendingAction(
            command="DELETE_USER",
            payload=payload,
            preview_message=preview
        )
        set_pending_action(session_id, action)

        return CommandResult(
            success=True,
            message=preview,
            needs_confirmation=True,
            pending_action=action
        )

    def _do_delete_user(self, payload: Dict) -> CommandResult:
        """Actually delete the user."""
        name = payload.get('name', '')

        from app.main import load_clients, save_clients
        clients = load_clients()
        client = next((c for c in clients if name.lower() in c['name'].lower()), None)

        if not client:
            return CommandResult(success=False, message=f"Nie znaleziono: {name}")

        clients = [c for c in clients if c['id'] != client['id']]
        save_clients(clients)

        return CommandResult(
            success=True,
            message=f"✓ Usunięto podopiecznego **{client['name']}**"
        )

    # =========================================================================
    # Training Commands
    # =========================================================================

    def _create_training(self, payload: Dict, session_id: str) -> CommandResult:
        """Create training - this DOES use LLM via LangGraph."""
        # Return special result that tells chat endpoint to use LangGraph
        return CommandResult(
            success=True,
            message="",
            data={"use_langgraph": True, "params": payload}
        )

    def _list_trainings(self, payload: Dict, session_id: str) -> CommandResult:
        """List training history."""
        return CommandResult(
            success=True,
            message="**Historia treningów:**\n\n*Funkcja w budowie*"
        )

    # =========================================================================
    # Help
    # =========================================================================

    def _help(self, payload: Dict, session_id: str) -> CommandResult:
        """Show available commands."""
        help_text = """**Dostępne komendy:**

**Podopieczni:**
- `dodaj podopiecznego Jan Kowalski, 30 lat, 80kg`
- `lista podopiecznych`
- `pokaż dane Jan`
- `usuń podopiecznego Jan`

**Treningi:**
- `wygeneruj trening, trudność: hard`
- `circuit dla 5 osób`
- `trening dla Jana, średni poziom`

**Inne:**
- `pomoc` - ta lista"""

        return CommandResult(success=True, message=help_text)
