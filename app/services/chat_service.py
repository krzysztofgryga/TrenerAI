"""
Chat service - handles all chat logic.

Responsibilities:
1. Check for confirmations (tak/anuluj)
2. Parse and execute commands
3. Fallback to RAG for general questions
"""
import logging
from typing import Optional, Dict, Any

from app.schemas import ChatRequest
from app.commands import (
    parse_command,
    CommandType,
    CommandExecutor,
    is_confirmation,
    get_pending_action,
    clear_pending_action,
)

logger = logging.getLogger(__name__)


class ChatService:
    """
    Handles chat messages.

    Flow:
    1. Check if message is confirmation (tak/anuluj)
    2. Parse command with regex (NO LLM)
    3. Execute command (direct DB operation)
    4. If no command → use RAG for general questions
    """

    def __init__(self, db_session=None):
        """
        Initialize chat service.

        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db = db_session
        self.executor = CommandExecutor(db_session)

    def handle_message(self, request: ChatRequest) -> Dict[str, Any]:
        """
        Process a chat message and return response.

        Args:
            request: ChatRequest with message, history, session_id

        Returns:
            Dict with response, command, data, needs_confirmation
        """
        session_id = request.session_id or "default"
        logger.info(f"Chat request: {request.message[:100]}...")

        # Step 1: Check for confirmation
        confirmation = is_confirmation(request.message)

        if confirmation is True:
            return self._handle_confirmation(session_id)
        elif confirmation is False:
            return self._handle_cancellation(session_id)

        # Step 2: Parse command
        parsed = parse_command(request.message)

        if parsed.command != CommandType.NONE:
            logger.info(f"Parsed command: {parsed.command.value}")
            return self._handle_command(parsed, session_id)

        # Step 3: No command → RAG
        return self._handle_general_chat(request)

    def _handle_confirmation(self, session_id: str) -> Dict[str, Any]:
        """Handle 'tak' confirmation."""
        pending = get_pending_action(session_id)
        if pending:
            result = self.executor.execute_pending(session_id)
            return {
                "response": result.message,
                "command": pending.command,
                "data": result.data
            }
        return {"response": "Nie mam nic do potwierdzenia."}

    def _handle_cancellation(self, session_id: str) -> Dict[str, Any]:
        """Handle 'anuluj' cancellation."""
        clear_pending_action(session_id)
        return {"response": "Anulowano."}

    def _handle_command(self, parsed, session_id: str) -> Dict[str, Any]:
        """Execute a parsed command."""
        result = self.executor.execute(parsed, session_id)

        # Special case: CREATE_TRAINING needs LangGraph
        if result.data and result.data.get("use_langgraph"):
            return self._generate_training(result.data.get("params", {}))

        return {
            "response": result.message,
            "command": parsed.command.value if result.success else None,
            "data": result.data,
            "needs_confirmation": result.needs_confirmation
        }

    def _generate_training(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate training plan using LangGraph."""
        try:
            from app.agent import app_graph

            inputs = {
                "num_people": params.get("num_people", 1),
                "difficulty": params.get("difficulty", "medium"),
                "rest_time": 60,
                "mode": params.get("mode", "circuit"),
                "warmup_count": 3,
                "main_count": 5,
                "cooldown_count": 3
            }

            plan_result = app_graph.invoke(inputs)
            plan = plan_result.get("final_plan", {})

            return {
                "response": "**Plan treningowy wygenerowany!**\n\n*(szczegóły w data)*",
                "command": "CREATE_TRAINING",
                "data": {"plan": plan, "params": inputs}
            }
        except Exception as e:
            logger.error(f"Training generation error: {e}")
            return {"response": f"Błąd generowania planu: {e}"}

    def _handle_general_chat(self, request: ChatRequest) -> Dict[str, Any]:
        """Handle general chat with RAG (multi-collection search)."""
        try:
            from app.agent import (
                get_llm,
                search_all_collections,
                format_rag_context,
                get_vector_store,
                check_collection_exists,
            )

            # Build context from all Qdrant collections
            context = ""

            # First try new multi-collection search
            results = search_all_collections(request.message, k=5)
            if results:
                context = format_rag_context(results, max_results=10)
                logger.info(f"Found {len(results)} results from trainer collections")

            # Fallback to old gym_exercises collection if no results
            if not context and check_collection_exists():
                try:
                    vector_store = get_vector_store()
                    docs = vector_store.similarity_search(request.message, k=10)
                    if docs:
                        context = "### ĆWICZENIA:\n" + "\n".join(
                            [f"- {d.page_content}" for d in docs]
                        )
                except Exception as e:
                    logger.warning(f"Old collection search failed: {e}")

            # Build conversation history
            history_text = ""
            for msg in (request.history or [])[-6:]:
                role = "Użytkownik" if msg.role == "user" else "Asystent"
                history_text += f"{role}: {msg.content}\n\n"

            # Enhanced system prompt
            system_prompt = """Jesteś profesjonalnym asystentem trenera personalnego.

ZASADY:
- Odpowiadaj po polsku, zwięźle i konkretnie
- Używaj formatowania Markdown (nagłówki, listy, tabele)
- Bazuj TYLKO na informacjach z kontekstu poniżej
- Jeśli nie masz informacji - powiedz to wprost
- Podawaj konkretne liczby (serie, powtórzenia, kalorie)
- Ostrzegaj o przeciwwskazaniach gdy to istotne

KONTEKST Z BAZY WIEDZY:
{context}

Jeśli kontekst jest pusty, odpowiedz na podstawie ogólnej wiedzy o treningu."""

            full_prompt = f"{system_prompt.format(context=context if context else '(brak danych w bazie)')}\n\n{history_text}Użytkownik: {request.message}\n\nAsystent:"

            llm = get_llm()
            response = llm.invoke(full_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            return {"response": response_text}

        except Exception as e:
            logger.error(f"RAG error: {e}")
            return {"response": f"Błąd: {e}"}
