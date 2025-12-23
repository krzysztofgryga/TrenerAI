"""
Command executor - handles database operations.

NO LLM involved - direct database/storage operations.
"""
import logging
from typing import Dict, Optional
from datetime import datetime

from app.commands.types import CommandType, ParsedCommand, CommandResult
from app.commands.session import PendingAction, set_pending_action, get_pending_action, clear_pending_action

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Executes commands - direct DB operations, no LLM."""

    def __init__(self, db_session=None):
        """
        Initialize executor.

        Args:
            db_session: SQLAlchemy session (optional, for DB operations)
        """
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

        action = PendingAction(
            command="CREATE_USER",
            payload=payload,
            preview_message=preview
        )
        set_pending_action(session_id, action)

        return CommandResult(
            success=True,
            message=preview,
            needs_confirmation=True
        )

    def _do_create_user(self, payload: Dict) -> CommandResult:
        """Actually create the user in DB/storage."""
        name = payload.get('name', 'Nieznany')

        if self.db:
            try:
                from app.database import User as DBUser, DifficultyLevel

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

        # Fallback to JSON storage
        from app.storage import add_client

        new_client = add_client({
            "name": name,
            "age": payload.get('age', 0),
            "weight": payload.get('weight', 0),
            "goal": payload.get('goals', ''),
            "notes": "",
        })

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
                    return CommandResult(success=True, message="Brak zarejestrowanych podopiecznych.")

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

        # Fallback to JSON storage
        from app.storage import load_clients
        clients = load_clients()

        if not clients:
            return CommandResult(success=True, message="Brak zarejestrowanych podopiecznych.")

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

        from app.storage import get_client_by_name
        client = get_client_by_name(name)

        if not client:
            return CommandResult(success=False, message=f"Nie znaleziono podopiecznego: **{name}**")

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
            needs_confirmation=True
        )

    def _do_delete_user(self, payload: Dict) -> CommandResult:
        """Actually delete the user."""
        name = payload.get('name', '')

        from app.storage import delete_client_by_name
        deleted = delete_client_by_name(name)

        if not deleted:
            return CommandResult(success=False, message=f"Nie znaleziono: {name}")

        return CommandResult(
            success=True,
            message=f"✓ Usunięto podopiecznego **{deleted['name']}**"
        )

    # =========================================================================
    # Training Commands
    # =========================================================================

    def _create_training(self, payload: Dict, session_id: str) -> CommandResult:
        """Create training - this triggers LangGraph (handled in chat endpoint)."""
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
- `dodaj Jana 30 lat` *(skrócona forma)*
- `lista podopiecznych`
- `pokaż dane Jan`
- `usuń podopiecznego Jan`

**Treningi:**
- `wygeneruj trening, trudność: hard`
- `circuit dla 5 osób`

**Inne:**
- `pomoc` - ta lista"""

        return CommandResult(success=True, message=help_text)
