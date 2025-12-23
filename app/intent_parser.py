"""
Intent Parser for TrenerAI Chat System.

Extracts structured intents from natural language chat messages.
Converts chat into deterministic system commands.

Flow:
    User message → LLM → Intent + Payload (JSON) → Command execution
"""
import json
import logging
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Intent Types
# =============================================================================

class IntentType(str, Enum):
    """Supported chat intents (commands)."""

    # User/Client management
    CREATE_USER = "CREATE_USER"
    LIST_USERS = "LIST_USERS"
    SHOW_USER = "SHOW_USER"
    UPDATE_USER = "UPDATE_USER"
    DELETE_USER = "DELETE_USER"

    # Training plan management
    CREATE_TRAINING_PLAN = "CREATE_TRAINING_PLAN"
    LIST_TRAINING_PLANS = "LIST_TRAINING_PLANS"
    SHOW_TRAINING_PLAN = "SHOW_TRAINING_PLAN"
    ASSIGN_PLAN_TO_USER = "ASSIGN_PLAN_TO_USER"

    # Tagging
    CREATE_TAG = "CREATE_TAG"
    TAG_ENTITY = "TAG_ENTITY"
    LIST_TAGS = "LIST_TAGS"

    # General
    GENERAL_CHAT = "GENERAL_CHAT"  # No specific command, just conversation
    HELP = "HELP"
    UNKNOWN = "UNKNOWN"


# =============================================================================
# Prompt Policy - Required Fields per Intent
# =============================================================================

PROMPT_POLICY: Dict[IntentType, Dict[str, Any]] = {
    IntentType.CREATE_USER: {
        "required": ["name"],
        "optional": ["age", "weight", "height", "goals", "email"],
        "defaults": {
            "email": lambda name: f"{name.lower().replace(' ', '.')}@placeholder.com"
        },
        "creative_allowed": True,
        "description": "Tworzenie nowego podopiecznego/użytkownika"
    },
    IntentType.CREATE_TRAINING_PLAN: {
        "required": ["difficulty"],
        "optional": ["mode", "duration", "num_people", "warmup_count", "main_count", "cooldown_count", "target_user", "target_group"],
        "defaults": {
            "mode": "circuit",
            "num_people": 1,
            "warmup_count": 3,
            "main_count": 5,
            "cooldown_count": 3,
            "rest_time": 60
        },
        "creative_allowed": True,
        "description": "Generowanie planu treningowego"
    },
    IntentType.ASSIGN_PLAN_TO_USER: {
        "required": ["plan_id", "user_id"],
        "optional": [],
        "defaults": {},
        "creative_allowed": False,
        "description": "Przypisanie planu do użytkownika"
    },
    IntentType.CREATE_TAG: {
        "required": ["name"],
        "optional": ["color"],
        "defaults": {"color": "#3B82F6"},
        "creative_allowed": False,
        "description": "Tworzenie nowego tagu"
    },
    IntentType.TAG_ENTITY: {
        "required": ["tag_name", "entity_type", "entity_id"],
        "optional": [],
        "defaults": {},
        "creative_allowed": False,
        "description": "Przypisanie tagu do encji"
    },
}


# =============================================================================
# Intent Payload Models
# =============================================================================

class ParsedIntent(BaseModel):
    """Result of intent parsing."""
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    payload: Dict[str, Any] = {}
    missing_required: List[str] = []
    requires_confirmation: bool = False
    follow_up_question: Optional[str] = None
    raw_message: str = ""


class CreateUserPayload(BaseModel):
    """Payload for CREATE_USER intent."""
    name: str
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    goals: Optional[str] = None
    email: Optional[str] = None
    contraindications: Optional[List[str]] = None


class CreateTrainingPlanPayload(BaseModel):
    """Payload for CREATE_TRAINING_PLAN intent."""
    difficulty: str  # easy, medium, hard
    mode: str = "circuit"  # circuit, common
    num_people: int = 1
    rest_time: int = 60
    warmup_count: int = 3
    main_count: int = 5
    cooldown_count: int = 3
    duration_minutes: Optional[int] = None
    target_user_id: Optional[int] = None
    target_user_name: Optional[str] = None
    generation_mode: str = "guided"  # guided, creative


class CreateTagPayload(BaseModel):
    """Payload for CREATE_TAG intent."""
    name: str
    color: str = "#3B82F6"


class TagEntityPayload(BaseModel):
    """Payload for TAG_ENTITY intent."""
    tag_name: str
    entity_type: str  # user, plan, diet
    entity_id: int


# =============================================================================
# Intent Parser
# =============================================================================

INTENT_EXTRACTION_PROMPT = '''Jesteś parserem intencji dla systemu zarządzania treningami.
Twoim zadaniem jest wyekstrahować intencję i parametry z wiadomości użytkownika.

DOSTĘPNE INTENCJE:
- CREATE_USER: Tworzenie nowego podopiecznego (wymagane: name)
- LIST_USERS: Wyświetlenie listy podopiecznych
- SHOW_USER: Pokazanie szczegółów podopiecznego (wymagane: name lub id)
- UPDATE_USER: Aktualizacja danych podopiecznego
- DELETE_USER: Usunięcie podopiecznego

- CREATE_TRAINING_PLAN: Wygenerowanie planu treningowego (wymagane: difficulty)
- LIST_TRAINING_PLANS: Wyświetlenie planów treningowych
- SHOW_TRAINING_PLAN: Pokazanie szczegółów planu
- ASSIGN_PLAN_TO_USER: Przypisanie planu do użytkownika

- CREATE_TAG: Utworzenie nowego tagu
- TAG_ENTITY: Przypisanie tagu do encji
- LIST_TAGS: Lista tagów

- GENERAL_CHAT: Ogólna rozmowa, pytania o ćwiczenia, porady
- HELP: Prośba o pomoc
- UNKNOWN: Nie można określić intencji

PARAMETRY DLA CREATE_USER:
- name (string, wymagane): Imię i nazwisko
- age (int): Wiek
- weight (float): Waga w kg
- height (float): Wzrost w cm
- goals (string): Cele treningowe
- email (string): Email

PARAMETRY DLA CREATE_TRAINING_PLAN:
- difficulty (string, wymagane): easy/medium/hard
- mode (string): circuit/common (domyślnie: circuit)
- num_people (int): Liczba osób (domyślnie: 1)
- duration_minutes (int): Czas trwania w minutach
- warmup_count (int): Liczba ćwiczeń rozgrzewkowych
- main_count (int): Liczba ćwiczeń głównych
- cooldown_count (int): Liczba ćwiczeń końcowych
- target_user_name (string): Dla kogo plan (imię)
- generation_mode (string): guided/creative

WIADOMOŚĆ UŻYTKOWNIKA:
{message}

HISTORIA KONWERSACJI:
{history}

Odpowiedz TYLKO w formacie JSON:
{{
  "intent": "INTENT_TYPE",
  "confidence": 0.0-1.0,
  "payload": {{...extracted parameters...}},
  "missing_required": ["field1", "field2"],
  "reasoning": "krótkie wyjaśnienie"
}}'''


class IntentParser:
    """
    Parses natural language into structured intents.
    Uses LLM for extraction, validates against Prompt Policy.
    """

    def __init__(self, llm=None):
        """
        Initialize parser.

        Args:
            llm: LangChain LLM instance. If None, will be loaded on first use.
        """
        self._llm = llm

    @property
    def llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            from app.agent import get_llm
            self._llm = get_llm()
        return self._llm

    def parse(self, message: str, history: List[Dict[str, str]] = None) -> ParsedIntent:
        """
        Parse user message into structured intent.

        Args:
            message: User's chat message
            history: Conversation history for context

        Returns:
            ParsedIntent with extracted intent and payload
        """
        history = history or []

        # Format history for prompt
        history_text = ""
        for msg in history[-6:]:
            role = "Użytkownik" if msg.get("role") == "user" else "Asystent"
            history_text += f"{role}: {msg.get('content', '')}\n"

        # Build prompt
        prompt = INTENT_EXTRACTION_PROMPT.format(
            message=message,
            history=history_text or "Brak historii"
        )

        try:
            # Get LLM response
            response = self.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Parse JSON from response
            parsed = self._extract_json(response_text)

            if not parsed:
                return self._fallback_intent(message)

            # Build ParsedIntent
            intent_type = self._map_intent(parsed.get("intent", "UNKNOWN"))
            payload = parsed.get("payload", {})
            confidence = float(parsed.get("confidence", 0.5))

            # Validate against Prompt Policy
            missing = self._check_required_fields(intent_type, payload)

            # Determine if confirmation needed
            requires_confirmation = intent_type in [
                IntentType.CREATE_USER,
                IntentType.CREATE_TRAINING_PLAN,
                IntentType.DELETE_USER,
                IntentType.ASSIGN_PLAN_TO_USER
            ]

            # Generate follow-up question if fields missing
            follow_up = None
            if missing:
                follow_up = self._generate_follow_up(intent_type, missing, payload)

            return ParsedIntent(
                intent=intent_type,
                confidence=confidence,
                payload=payload,
                missing_required=missing,
                requires_confirmation=requires_confirmation,
                follow_up_question=follow_up,
                raw_message=message
            )

        except Exception as e:
            logger.error(f"Intent parsing error: {e}")
            return self._fallback_intent(message)

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from LLM response."""
        try:
            # Try direct parse
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in text
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return None

    def _map_intent(self, intent_str: str) -> IntentType:
        """Map string to IntentType enum."""
        try:
            return IntentType(intent_str.upper())
        except ValueError:
            return IntentType.UNKNOWN

    def _check_required_fields(self, intent: IntentType, payload: Dict) -> List[str]:
        """Check which required fields are missing."""
        policy = PROMPT_POLICY.get(intent, {})
        required = policy.get("required", [])

        missing = []
        for field in required:
            if field not in payload or payload[field] is None:
                missing.append(field)

        return missing

    def _generate_follow_up(self, intent: IntentType, missing: List[str], payload: Dict) -> str:
        """Generate follow-up question for missing fields."""
        policy = PROMPT_POLICY.get(intent, {})
        creative_allowed = policy.get("creative_allowed", False)

        if intent == IntentType.CREATE_TRAINING_PLAN:
            questions = []
            if "difficulty" in missing:
                questions.append("poziom trudności (easy/medium/hard)")
            return f"Potrzebuję jeszcze: {', '.join(questions)}. Podaj lub napisz 'zaskocz mnie' a dobiorę sam."

        elif intent == IntentType.CREATE_USER:
            if "name" in missing:
                return "Jak ma na imię nowy podopieczny?"

        # Generic
        field_names = {
            "name": "imię",
            "difficulty": "poziom trudności",
            "plan_id": "ID planu",
            "user_id": "ID użytkownika"
        }

        readable = [field_names.get(f, f) for f in missing]
        suffix = " Możesz też napisać 'zaskocz mnie'." if creative_allowed else ""
        return f"Brakuje mi: {', '.join(readable)}.{suffix}"

    def _fallback_intent(self, message: str) -> ParsedIntent:
        """Return fallback when parsing fails."""
        return ParsedIntent(
            intent=IntentType.GENERAL_CHAT,
            confidence=0.3,
            payload={},
            missing_required=[],
            requires_confirmation=False,
            raw_message=message
        )

    def apply_defaults(self, intent: IntentType, payload: Dict) -> Dict:
        """Apply default values from Prompt Policy."""
        policy = PROMPT_POLICY.get(intent, {})
        defaults = policy.get("defaults", {})

        result = payload.copy()
        for field, default in defaults.items():
            if field not in result or result[field] is None:
                if callable(default):
                    # Dynamic default (e.g., generate email from name)
                    if field == "email" and "name" in result:
                        result[field] = default(result["name"])
                else:
                    result[field] = default

        return result

    def validate_payload(self, intent: IntentType, payload: Dict) -> tuple[bool, List[str]]:
        """
        Validate payload has all required fields.

        Returns:
            (is_valid, list_of_errors)
        """
        policy = PROMPT_POLICY.get(intent, {})
        required = policy.get("required", [])

        errors = []
        for field in required:
            if field not in payload or payload[field] is None:
                errors.append(f"Brak wymaganego pola: {field}")

        return len(errors) == 0, errors


# =============================================================================
# Singleton instance
# =============================================================================

_parser_instance: Optional[IntentParser] = None


def get_intent_parser() -> IntentParser:
    """Get or create singleton IntentParser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = IntentParser()
    return _parser_instance
