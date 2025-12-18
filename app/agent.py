import os
import logging
from typing import List, TypedDict, Optional

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from qdrant_client import models

from app.models.exercise import TrainingPlan

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises")

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()  # "openai" or "ollama"
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_llm() -> BaseChatModel:
    """Get LLM instance based on configuration."""
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


class TrainerState(TypedDict):
    num_people: int
    difficulty: str
    rest_time: int
    mode: str
    warmup_candidates: List[Document]
    main_candidates: List[Document]
    cooldown_candidates: List[Document]
    final_plan: dict


# Lazy initialization for vector store
_embeddings: Optional[FastEmbedEmbeddings] = None
_vector_store: Optional[QdrantVectorStore] = None


def get_vector_store() -> QdrantVectorStore:
    """Get or create vector store connection (lazy initialization)."""
    global _embeddings, _vector_store

    if _vector_store is None:
        logger.info(f"Connecting to Qdrant at {QDRANT_URL}, collection: {COLLECTION_NAME}")
        _embeddings = FastEmbedEmbeddings()
        _vector_store = QdrantVectorStore.from_existing_collection(
            embedding=_embeddings,
            collection_name=COLLECTION_NAME,
            url=QDRANT_URL
        )
        logger.info("Vector store initialized successfully")

    return _vector_store


def retrieve_exercises(state: TrainerState):
    """Node 1: Retrieve exercise candidates from vector database."""
    logger.info("Searching exercise database (Qdrant)...")

    vector_store = get_vector_store()
    difficulty = state["difficulty"]

    def search_category(category_type, limit=10, filter_level=None):
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

    main_limit = max(state["num_people"], 10) if state["mode"] == "circuit" else 10

    return {
        "warmup_candidates": search_category("warmup", limit=5),
        "main_candidates": search_category("main", limit=main_limit, filter_level=difficulty),
        "cooldown_candidates": search_category("cooldown", limit=5)
    }


def generate_plan(state: TrainerState):
    """Node 2: Generate training plan using LLM."""
    logger.info(f"Generating training plan with {LLM_PROVIDER.upper()} LLM...")

    llm = get_llm()

    def format_docs(docs):
        return "\n".join([f"- [ID: {d.metadata['id']}] {d.page_content}" for d in docs])

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


# Build LangGraph workflow
workflow = StateGraph(TrainerState)
workflow.add_node("retrieve", retrieve_exercises)
workflow.add_node("plan", generate_plan)
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "plan")
workflow.add_edge("plan", END)

app_graph = workflow.compile()
