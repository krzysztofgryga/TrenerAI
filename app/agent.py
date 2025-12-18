"""
TrenerAI Agent Module

This module implements the LangGraph workflow for generating training plans.
It consists of two main nodes:
1. Retrieve - fetches exercise candidates from Qdrant vector database
2. Plan - generates a structured training plan using LLM (OpenAI or Ollama)

Usage:
    from app.agent import app_graph
    result = app_graph.invoke({"num_people": 5, "difficulty": "medium", ...})
"""

import os
import logging
from typing import List, TypedDict, Optional

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from qdrant_client import QdrantClient, models

from app.models.exercise import TrainingPlan

load_dotenv()

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises")

# LLM Configuration - supports OpenAI and Ollama
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


# =============================================================================
# LLM Factory
# =============================================================================

def get_llm() -> BaseChatModel:
    """
    Create and return an LLM instance based on configuration.

    Supports two providers:
    - 'ollama': Local LLM using Ollama server
    - 'openai': OpenAI API (requires OPENAI_API_KEY)

    Returns:
        BaseChatModel: Configured LLM instance ready for inference.

    Raises:
        ImportError: If required LLM package is not installed.
    """
    if LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        logger.info(f"Using Ollama LLM: {LLM_MODEL} at {OLLAMA_BASE_URL}")
        return ChatOllama(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            base_url=OLLAMA_BASE_URL,
        )
    else:
        from langchain_openai import ChatOpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not set - API calls will fail")
        logger.info(f"Using OpenAI LLM: {LLM_MODEL}")
        return ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)


# =============================================================================
# State Definition
# =============================================================================

class TrainerState(TypedDict):
    """
    State object passed between LangGraph nodes.

    Attributes:
        num_people: Number of participants in the training session.
        difficulty: Exercise difficulty level ('easy', 'medium', 'hard').
        rest_time: Rest time between exercises in seconds.
        mode: Training mode ('circuit' or 'common').
        warmup_candidates: Retrieved warmup exercises from vector DB.
        main_candidates: Retrieved main exercises from vector DB.
        cooldown_candidates: Retrieved cooldown exercises from vector DB.
        final_plan: Generated training plan dictionary.
    """
    num_people: int
    difficulty: str
    rest_time: int
    mode: str
    warmup_candidates: List[Document]
    main_candidates: List[Document]
    cooldown_candidates: List[Document]
    final_plan: dict


# =============================================================================
# Vector Store Connection
# =============================================================================

# Cached instances for lazy initialization
_embeddings: Optional[FastEmbedEmbeddings] = None
_vector_store: Optional[Qdrant] = None


def check_collection_exists() -> bool:
    """
    Check if the exercise collection exists in Qdrant.

    Returns:
        bool: True if collection exists, False otherwise.
    """
    try:
        client = QdrantClient(url=QDRANT_URL)
        collections = client.get_collections().collections
        return any(c.name == COLLECTION_NAME for c in collections)
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        return False


def get_vector_store() -> Qdrant:
    """
    Get or create a connection to the Qdrant vector store.

    Uses lazy initialization - creates connection on first call and
    caches it for subsequent calls.

    Returns:
        Qdrant: Connected vector store instance.

    Raises:
        ConnectionError: If Qdrant is not accessible.
        ValueError: If the exercise collection doesn't exist.
    """
    global _embeddings, _vector_store

    if _vector_store is not None:
        return _vector_store

    logger.info(f"Connecting to Qdrant at {QDRANT_URL}, collection: {COLLECTION_NAME}")

    # Check if collection exists first
    if not check_collection_exists():
        raise ValueError(
            f"Collection '{COLLECTION_NAME}' not found in Qdrant. "
            f"Please run 'python seed_database.py' first to create it."
        )

    try:
        _embeddings = FastEmbedEmbeddings()
        client = QdrantClient(url=QDRANT_URL)

        _vector_store = Qdrant(
            client=client,
            collection_name=COLLECTION_NAME,
            embeddings=_embeddings
        )

        # Check if vector store was created successfully
        if _vector_store is None:
            raise ValueError(
                f"Failed to connect to collection '{COLLECTION_NAME}'. "
                f"The collection may be empty or corrupted. "
                f"Try running 'python seed_database.py' again."
            )

        logger.info("Vector store initialized successfully")
        return _vector_store
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        raise ConnectionError(f"Cannot connect to Qdrant: {e}")


# =============================================================================
# LangGraph Nodes
# =============================================================================

def retrieve_exercises(state: TrainerState) -> dict:
    """
    Node 1: Retrieve exercise candidates from Qdrant vector database.

    Searches for exercises in three categories:
    - Warmup: 5 exercises (no difficulty filter)
    - Main: Variable count based on num_people and mode, filtered by difficulty
    - Cooldown: 5 exercises (no difficulty filter)

    Args:
        state: Current workflow state containing search parameters.

    Returns:
        dict: Updated state with exercise candidates for each category.

    Raises:
        ValueError: If vector store connection fails.
    """
    logger.info("Searching exercise database (Qdrant)...")

    vector_store = get_vector_store()
    difficulty = state["difficulty"]

    def search_category(category_type: str, limit: int = 10, filter_level: str = None) -> List[Document]:
        """
        Search for exercises in a specific category.

        Args:
            category_type: Exercise type ('warmup', 'main', 'cooldown').
            limit: Maximum number of results to return.
            filter_level: Optional difficulty filter ('easy', 'medium', 'hard').

        Returns:
            List of Document objects with exercise data.
        """
        must_conditions = [
            models.FieldCondition(
                key="metadata.type",
                match=models.MatchValue(value=category_type)
            )
        ]

        if filter_level:
            must_conditions.append(
                models.FieldCondition(
                    key="metadata.level",
                    match=models.MatchValue(value=filter_level)
                )
            )

        filter_obj = models.Filter(must=must_conditions)

        return vector_store.similarity_search(
            query="best exercise",
            k=limit,
            filter=filter_obj
        )

    # Calculate main exercise count based on mode
    # Circuit mode: one exercise per person (minimum 10)
    # Common mode: fixed 10 exercises
    main_limit = max(state["num_people"], 10) if state["mode"] == "circuit" else 10

    return {
        "warmup_candidates": search_category("warmup", limit=5),
        "main_candidates": search_category("main", limit=main_limit, filter_level=difficulty),
        "cooldown_candidates": search_category("cooldown", limit=5)
    }


def generate_plan(state: TrainerState) -> dict:
    """
    Node 2: Generate a structured training plan using LLM.

    Takes the exercise candidates from the retrieve step and uses
    an LLM to create a coherent training plan with proper structure.

    Args:
        state: Current workflow state with exercise candidates.

    Returns:
        dict: Updated state with final_plan containing the generated plan.

    Raises:
        Exception: If LLM call fails or returns invalid response.
    """
    logger.info(f"Generating training plan with {LLM_PROVIDER.upper()} LLM...")

    llm = get_llm()

    def format_docs(docs: List[Document]) -> str:
        """
        Format exercise documents as a readable string for LLM prompt.

        Args:
            docs: List of exercise documents.

        Returns:
            Formatted string with exercise IDs and descriptions.
        """
        return "\n".join([f"- [ID: {d.metadata['id']}] {d.page_content}" for d in docs])

    # Determine target exercise count for main part
    target_main_count = state["num_people"] if state["mode"] == "circuit" else 5

    system_prompt = """
    You are a professional personal trainer. Your task is to create a training plan.
    You have access to a list of exercises (CANDIDATES) retrieved from the database.

    GUIDELINES:
    1. Select exercises ONLY from the provided candidate list.
    2. Match the number of exercises in the main part: {target_count}.
    3. Training mode: {mode_desc}.

    CANDIDATES - WARMUP:
    {warmup}

    CANDIDATES - MAIN:
    {main}

    CANDIDATES - COOLDOWN:
    {cooldown}

    Format the result exactly as JSON.
    """

    prompt = ChatPromptTemplate.from_template(system_prompt)

    # Create chain with structured output for type safety
    chain = prompt | llm.with_structured_output(TrainingPlan)

    mode_description = (
        "Circuit stations (each person does different exercise)"
        if state["mode"] == "circuit"
        else "Everyone does the same exercise"
    )

    result = chain.invoke({
        "target_count": target_main_count,
        "mode_desc": mode_description,
        "warmup": format_docs(state["warmup_candidates"]),
        "main": format_docs(state["main_candidates"]),
        "cooldown": format_docs(state["cooldown_candidates"])
    })

    return {"final_plan": result.model_dump()}


# =============================================================================
# Workflow Definition
# =============================================================================

def build_workflow() -> StateGraph:
    """
    Build and compile the LangGraph workflow.

    Creates a two-node workflow:
    1. retrieve: Fetch exercise candidates from vector DB
    2. plan: Generate training plan using LLM

    Returns:
        Compiled StateGraph ready for invocation.
    """
    workflow = StateGraph(TrainerState)

    # Add nodes
    workflow.add_node("retrieve", retrieve_exercises)
    workflow.add_node("plan", generate_plan)

    # Define flow: retrieve -> plan -> END
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "plan")
    workflow.add_edge("plan", END)

    return workflow.compile()


# Create the compiled workflow for export
app_graph = build_workflow()
