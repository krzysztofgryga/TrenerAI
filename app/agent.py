import os
from typing import List, TypedDict, Literal
from dotenv import load_dotenv

# LangChain & LangGraph
from langgraph.graph import StateGraph, END
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser

# Qdrant & Embeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from qdrant_client import QdrantClient, models

# Nasz model danych
from app.models.exercise import TrainingPlan

load_dotenv()

# --- KONFIGURACJA ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# 1. Definicja Stanu
class TrainerState(TypedDict):
    num_people: int
    difficulty: str
    rest_time: int
    mode: str

    warmup_candidates: List[Document]
    main_candidates: List[Document]
    cooldown_candidates: List[Document]

    final_plan: dict


# 2. Inicjalizacja narzędzi
embeddings = FastEmbedEmbeddings()

# ✅ POPRAWKA: Używamy metody from_existing_collection zamiast konstruktora
# To zapobiega błędowi "TypeError: QdrantVectorStore() takes no arguments"
vector_store = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    collection_name=COLLECTION_NAME,
    url=QDRANT_URL
)


# --- WĘZEŁ 1: RETRIEVER (Wyszukiwarka) ---
def retrieve_exercises(state: TrainerState):
    print("🔍 [Agent] Przeszukuję bazę wiedzy (Qdrant)...")

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

    # Logika ilościowa
    main_limit = max(state["num_people"], 10) if state["mode"] == "circuit" else 10

    return {
        "warmup_candidates": search_category("warmup", limit=5),
        "main_candidates": search_category("main", limit=main_limit, filter_level=difficulty),
        "cooldown_candidates": search_category("cooldown", limit=5)
    }


# --- WĘZEŁ 2: PLANNER (LLM) ---
def generate_plan(state: TrainerState):
    print("🧠 [Agent] Układam plan treningowy...")

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

    def format_docs(docs):
        return "\n".join([f"- [ID: {d.metadata['id']}] {d.page_content}" for d in docs])

    target_main_count = state["num_people"] if state["mode"] == "circuit" else 5

    system_prompt = """
    Jesteś profesjonalnym trenerem personalnym. Twoim zadaniem jest ułożenie planu treningowego.
    Masz dostępną listę ćwiczeń (KANDYDACI) pobraną z bazy danych.

    WYTYCZNE:
    1. Wybierz ćwiczenia TYLKO z podanej listy kandydatów.
    2. Dopasuj ilość ćwiczeń w części głównej: {target_count}.
    3. Tryb treningu: {mode_desc}.

    KANDYDACI - ROZGRZEWKA:
    {warmup}

    KANDYDACI - GŁÓWNA:
    {main}

    KANDYDACI - RELAKS:
    {cooldown}

    Sformatuj wynik dokładnie jako JSON.
    """

    prompt = ChatPromptTemplate.from_template(system_prompt)

    chain = prompt | llm.with_structured_output(TrainingPlan)

    mode_description = "Stacje obwodowe (każda osoba robi co innego)" if state[
                                                                             "mode"] == "circuit" else "Wszyscy robią to samo"

    result = chain.invoke({
        "target_count": target_main_count,
        "mode_desc": mode_description,
        "warmup": format_docs(state["warmup_candidates"]),
        "main": format_docs(state["main_candidates"]),
        "cooldown": format_docs(state["cooldown_candidates"])
    })

    return {"final_plan": result.dict()}


# --- BUDOWA GRAFU ---
workflow = StateGraph(TrainerState)

workflow.add_node("retrieve", retrieve_exercises)
workflow.add_node("plan", generate_plan)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "plan")
workflow.add_edge("plan", END)

app_graph = workflow.compile()