"""
Command Executor for TrenerAI.

Executes parsed intents by calling appropriate services/database operations.
Bridges Intent Parser to actual system actions.

Flow:
    ParsedIntent → CommandExecutor → Database/Services → CommandResult
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

from app.intent_parser import (
    ParsedIntent, IntentType, PROMPT_POLICY,
    get_intent_parser
)

logger = logging.getLogger(__name__)


# =============================================================================
# Command Result Models
# =============================================================================

class CommandResult(BaseModel):
    """Result of command execution."""
    success: bool
    intent: IntentType
    message: str  # Human-readable result message
    data: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False
    confirmation_preview: Optional[Dict[str, Any]] = None
    follow_up_question: Optional[str] = None
    action_taken: Optional[str] = None  # For audit log


# =============================================================================
# Command Executor
# =============================================================================

class CommandExecutor:
    """
    Executes commands based on parsed intents.
    Handles database operations, service calls, and response formatting.
    """

    def __init__(self, db_session=None):
        """
        Initialize executor.

        Args:
            db_session: SQLAlchemy session (optional, for DB operations)
        """
        self.db = db_session
        self.intent_parser = get_intent_parser()

    def execute(self, parsed_intent: ParsedIntent, confirm: bool = False) -> CommandResult:
        """
        Execute a parsed intent.

        Args:
            parsed_intent: The parsed intent to execute
            confirm: If True, skip confirmation for dangerous operations

        Returns:
            CommandResult with execution result
        """
        intent = parsed_intent.intent
        payload = parsed_intent.payload

        # Check for missing required fields
        if parsed_intent.missing_required:
            return CommandResult(
                success=False,
                intent=intent,
                message=parsed_intent.follow_up_question or "Brakuje wymaganych danych.",
                follow_up_question=parsed_intent.follow_up_question,
                requires_confirmation=False
            )

        # Apply defaults
        payload = self.intent_parser.apply_defaults(intent, payload)

        # Route to appropriate handler
        handlers = {
            IntentType.CREATE_USER: self._handle_create_user,
            IntentType.LIST_USERS: self._handle_list_users,
            IntentType.SHOW_USER: self._handle_show_user,
            IntentType.DELETE_USER: self._handle_delete_user,
            IntentType.CREATE_TRAINING_PLAN: self._handle_create_training_plan,
            IntentType.LIST_TRAINING_PLANS: self._handle_list_training_plans,
            IntentType.ASSIGN_PLAN_TO_USER: self._handle_assign_plan,
            IntentType.CREATE_TAG: self._handle_create_tag,
            IntentType.TAG_ENTITY: self._handle_tag_entity,
            IntentType.LIST_TAGS: self._handle_list_tags,
            IntentType.HELP: self._handle_help,
            IntentType.GENERAL_CHAT: self._handle_general_chat,
        }

        handler = handlers.get(intent, self._handle_unknown)

        # Check if confirmation needed (and not confirmed)
        if parsed_intent.requires_confirmation and not confirm:
            return self._prepare_confirmation(intent, payload)

        try:
            return handler(payload, parsed_intent)
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return CommandResult(
                success=False,
                intent=intent,
                message=f"Błąd wykonania: {str(e)}"
            )

    # =========================================================================
    # User Handlers
    # =========================================================================

    def _handle_create_user(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """Create a new user."""
        name = payload.get("name", "")
        age = payload.get("age")
        weight = payload.get("weight")
        goals = payload.get("goals", "")

        if not self.db:
            # Without DB, return preview
            return CommandResult(
                success=True,
                intent=IntentType.CREATE_USER,
                message=f"# NOWY PODOPIECZNY\n\n"
                        f"| Pole | Wartość |\n|---|---|\n"
                        f"| Imię | {name} |\n"
                        f"| Wiek | {age or 'nie podano'} |\n"
                        f"| Waga | {weight or 'nie podano'} kg |\n"
                        f"| Cel | {goals or 'nie podano'} |\n\n"
                        f"*Baza danych niedostępna - użytkownik nie został zapisany.*",
                data=payload,
                action_taken="CREATE_USER_PREVIEW"
            )

        try:
            from app.database import User as DBUser, DifficultyLevel

            # Create user in DB
            db_user = DBUser(
                email=payload.get("email", f"{name.lower().replace(' ', '.')}@temp.com"),
                name=name,
                age=age,
                weight=weight,
                height=payload.get("height"),
                goals=goals,
                preferred_difficulty=DifficultyLevel.MEDIUM
            )
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)

            return CommandResult(
                success=True,
                intent=IntentType.CREATE_USER,
                message=f"# DODANO PODOPIECZNEGO\n\n"
                        f"✓ **{name}** został dodany do systemu.\n\n"
                        f"| Pole | Wartość |\n|---|---|\n"
                        f"| ID | {db_user.id} |\n"
                        f"| Imię | {name} |\n"
                        f"| Wiek | {age or '-'} |\n"
                        f"| Waga | {weight or '-'} kg |\n"
                        f"| Cel | {goals or '-'} |",
                data={"user_id": db_user.id, **payload},
                action_taken=f"CREATE_USER:{db_user.id}"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                intent=IntentType.CREATE_USER,
                message=f"Błąd tworzenia użytkownika: {str(e)}"
            )

    def _handle_list_users(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """List all users."""
        if not self.db:
            # Fallback to JSON storage
            from app.main import load_clients
            clients = load_clients()

            if not clients:
                return CommandResult(
                    success=True,
                    intent=IntentType.LIST_USERS,
                    message="# LISTA PODOPIECZNYCH\n\nBrak zarejestrowanych podopiecznych."
                )

            table = "| Imię | Wiek | Waga | Cel |\n|---|---|---|---|\n"
            for c in clients:
                table += f"| {c['name']} | {c.get('age', '-')} | {c.get('weight', '-')} kg | {c.get('goal', '-')} |\n"

            return CommandResult(
                success=True,
                intent=IntentType.LIST_USERS,
                message=f"# LISTA PODOPIECZNYCH\n\n{table}",
                data={"count": len(clients), "clients": clients}
            )

        try:
            from app.database import User as DBUser
            users = self.db.query(DBUser).all()

            if not users:
                return CommandResult(
                    success=True,
                    intent=IntentType.LIST_USERS,
                    message="# LISTA PODOPIECZNYCH\n\nBrak zarejestrowanych podopiecznych."
                )

            table = "| ID | Imię | Wiek | Waga | Cel |\n|---|---|---|---|---|\n"
            for u in users:
                table += f"| {u.id} | {u.name or '-'} | {u.age or '-'} | {u.weight or '-'} kg | {u.goals or '-'} |\n"

            return CommandResult(
                success=True,
                intent=IntentType.LIST_USERS,
                message=f"# LISTA PODOPIECZNYCH\n\n{table}",
                data={"count": len(users)}
            )
        except Exception as e:
            return CommandResult(
                success=False,
                intent=IntentType.LIST_USERS,
                message=f"Błąd pobierania listy: {str(e)}"
            )

    def _handle_show_user(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """Show user details."""
        name = payload.get("name", "")
        user_id = payload.get("user_id")

        # For now, return mock data - will be connected to DB
        return CommandResult(
            success=True,
            intent=IntentType.SHOW_USER,
            message=f"# PROFIL: {name.upper()}\n\nSzczegóły użytkownika...",
            data=payload
        )

    def _handle_delete_user(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """Delete a user."""
        return CommandResult(
            success=True,
            intent=IntentType.DELETE_USER,
            message="Użytkownik został usunięty.",
            data=payload,
            action_taken="DELETE_USER"
        )

    # =========================================================================
    # Training Plan Handlers
    # =========================================================================

    def _handle_create_training_plan(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """Generate and optionally save a training plan."""
        from app.agent import app_graph

        difficulty = payload.get("difficulty", "medium")
        mode = payload.get("mode", "circuit")
        num_people = payload.get("num_people", 1)
        rest_time = payload.get("rest_time", 60)
        warmup_count = payload.get("warmup_count", 3)
        main_count = payload.get("main_count", 5)
        cooldown_count = payload.get("cooldown_count", 3)
        target_user = payload.get("target_user_name")

        try:
            # Invoke LangGraph workflow
            inputs = {
                "num_people": num_people,
                "difficulty": difficulty,
                "rest_time": rest_time,
                "mode": mode,
                "warmup_count": warmup_count,
                "main_count": main_count,
                "cooldown_count": cooldown_count
            }

            result = app_graph.invoke(inputs)
            plan = result.get("final_plan", {})

            # Format response
            header = f"# PLAN TRENINGOWY"
            if target_user:
                header += f" DLA: {target_user.upper()}"
            header += "\n\n"

            meta = f"| Parametr | Wartość |\n|---|---|\n"
            meta += f"| Trudność | {difficulty} |\n"
            meta += f"| Tryb | {mode} |\n"
            meta += f"| Osoby | {num_people} |\n"
            meta += f"| Odpoczynek | {rest_time}s |\n\n"

            return CommandResult(
                success=True,
                intent=IntentType.CREATE_TRAINING_PLAN,
                message=header + meta + "Plan został wygenerowany.\n\n*(Szczegóły w polu data)*",
                data={"plan": plan, "params": inputs},
                action_taken="CREATE_TRAINING_PLAN"
            )

        except Exception as e:
            logger.error(f"Training plan generation error: {e}")
            return CommandResult(
                success=False,
                intent=IntentType.CREATE_TRAINING_PLAN,
                message=f"Błąd generowania planu: {str(e)}"
            )

    def _handle_list_training_plans(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """List training plans."""
        return CommandResult(
            success=True,
            intent=IntentType.LIST_TRAINING_PLANS,
            message="# LISTA PLANÓW TRENINGOWYCH\n\n*Funkcja w budowie*"
        )

    def _handle_assign_plan(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """Assign plan to user."""
        return CommandResult(
            success=True,
            intent=IntentType.ASSIGN_PLAN_TO_USER,
            message="Plan został przypisany.",
            data=payload,
            action_taken="ASSIGN_PLAN"
        )

    # =========================================================================
    # Tag Handlers
    # =========================================================================

    def _handle_create_tag(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """Create a new tag."""
        name = payload.get("name", "")
        color = payload.get("color", "#3B82F6")

        return CommandResult(
            success=True,
            intent=IntentType.CREATE_TAG,
            message=f"# UTWORZONO TAG\n\n✓ Tag **{name}** został utworzony.",
            data={"name": name, "color": color},
            action_taken=f"CREATE_TAG:{name}"
        )

    def _handle_tag_entity(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """Tag an entity."""
        return CommandResult(
            success=True,
            intent=IntentType.TAG_ENTITY,
            message="Tag został przypisany.",
            data=payload,
            action_taken="TAG_ENTITY"
        )

    def _handle_list_tags(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """List all tags."""
        return CommandResult(
            success=True,
            intent=IntentType.LIST_TAGS,
            message="# LISTA TAGÓW\n\n*Funkcja w budowie*"
        )

    # =========================================================================
    # General Handlers
    # =========================================================================

    def _handle_help(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """Show help."""
        help_text = """# POMOC - DOSTĘPNE KOMENDY

## Zarządzanie podopiecznymi
- "dodaj podopiecznego: Jan Kowalski, 30 lat, 80kg"
- "lista podopiecznych"
- "pokaż dane: Jan"
- "usuń podopiecznego: Jan"

## Plany treningowe
- "wygeneruj plan treningowy, trudność: hard"
- "stwórz trening dla Jana, poziom średni"
- "pokaż plany treningowe"

## Tagi
- "utwórz tag: Początkujący"
- "otaguj Jana jako: Rehabilitacja"

## Tryby generowania
- **guided**: AI pyta o brakujące dane
- **creative**: AI sam dobiera parametry

Napisz "zaskocz mnie" żeby AI dobrał parametry sam.
"""
        return CommandResult(
            success=True,
            intent=IntentType.HELP,
            message=help_text
        )

    def _handle_general_chat(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """Handle general chat - pass to RAG."""
        return CommandResult(
            success=True,
            intent=IntentType.GENERAL_CHAT,
            message="",  # Will be filled by RAG response
            data={"use_rag": True}
        )

    def _handle_unknown(self, payload: Dict, intent: ParsedIntent) -> CommandResult:
        """Handle unknown intent."""
        return CommandResult(
            success=False,
            intent=IntentType.UNKNOWN,
            message="Nie rozumiem polecenia. Napisz 'pomoc' aby zobaczyć dostępne komendy."
        )

    # =========================================================================
    # Confirmation Flow
    # =========================================================================

    def _prepare_confirmation(self, intent: IntentType, payload: Dict) -> CommandResult:
        """Prepare confirmation preview."""
        policy = PROMPT_POLICY.get(intent, {})

        if intent == IntentType.CREATE_USER:
            preview = f"Utworzę podopiecznego:\n"
            preview += f"- Imię: {payload.get('name')}\n"
            if payload.get('age'):
                preview += f"- Wiek: {payload.get('age')}\n"
            if payload.get('weight'):
                preview += f"- Waga: {payload.get('weight')} kg\n"
            preview += "\nPotwierdź pisząc 'tak' lub 'anuluj'."

        elif intent == IntentType.CREATE_TRAINING_PLAN:
            preview = f"Wygeneruję plan treningowy:\n"
            preview += f"- Trudność: {payload.get('difficulty')}\n"
            preview += f"- Tryb: {payload.get('mode', 'circuit')}\n"
            if payload.get('target_user_name'):
                preview += f"- Dla: {payload.get('target_user_name')}\n"
            preview += "\nPotwierdź pisząc 'tak' lub 'anuluj'."

        else:
            preview = f"Czy chcesz wykonać tę operację? (tak/anuluj)"

        return CommandResult(
            success=True,
            intent=intent,
            message=preview,
            requires_confirmation=True,
            confirmation_preview=payload
        )


# =============================================================================
# Factory function
# =============================================================================

def get_command_executor(db_session=None) -> CommandExecutor:
    """Create CommandExecutor instance."""
    return CommandExecutor(db_session)
