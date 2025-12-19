# Dokumentacja: app/agent.py

## Spis treści
1. [Cel modułu](#cel-modułu)
2. [Architektura workflow](#architektura-workflow)
3. [Importy](#importy)
4. [Konfiguracja](#konfiguracja)
5. [TrainerState](#trainerstate)
6. [Funkcja get_llm](#funkcja-get_llm)
7. [Funkcja get_vector_store](#funkcja-get_vector_store)
8. [Węzeł retrieve_exercises](#węzeł-retrieve_exercises)
9. [Węzeł generate_plan](#węzeł-generate_plan)
10. [Funkcja build_workflow](#funkcja-build_workflow)
11. [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## Cel modułu

Moduł `app/agent.py` implementuje **LangGraph workflow** - serce systemu TrenerAI:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        agent.py - SERCE SYSTEMU                              │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │    main.py      │
                              │  (HTTP request) │
                              └────────┬────────┘
                                       │
                                       ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                            agent.py                                     │
  │                                                                         │
  │    app_graph.invoke(state) ──▶ workflow execution ──▶ TrainingPlan    │
  │                                                                         │
  │    ┌───────────────┐         ┌───────────────┐                         │
  │    │   retrieve    │────────▶│     plan      │                         │
  │    │               │         │               │                         │
  │    │  Qdrant DB    │         │  OpenAI/Ollama│                         │
  │    └───────────────┘         └───────────────┘                         │
  │                                                                         │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## Architektura workflow

### Diagram grafu

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LANGGRAPH WORKFLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   START     │
                              └──────┬──────┘
                                     │
                 TrainerState:       │
                 {                   │
                   num_people: 5,    │
                   difficulty: "hard",
                   mode: "circuit",  │
                   warmup_count: 3,  │
                   main_count: 5,    │
                   cooldown_count: 3,│
                   warmup_candidates: [],  ◀── puste
                   main_candidates: [],    ◀── puste
                   cooldown_candidates: [],◀── puste
                   final_plan: {}          ◀── pusty
                 }                   │
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │      retrieve         │
                         │  ─────────────────    │
                         │  similarity_search()  │
                         │  → Qdrant             │
                         └───────────┬───────────┘
                                     │
                 TrainerState:       │
                 {                   │
                   ...               │
                   warmup_candidates: [Doc1, Doc2, Doc3],     ◀── WYPEŁNIONE
                   main_candidates: [Doc4, Doc5, ...],        ◀── WYPEŁNIONE
                   cooldown_candidates: [Doc10, Doc11, Doc12],◀── WYPEŁNIONE
                   final_plan: {}
                 }                   │
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │        plan           │
                         │  ─────────────────    │
                         │  prompt + LLM         │
                         │  → OpenAI/Ollama      │
                         └───────────┬───────────┘
                                     │
                 TrainerState:       │
                 {                   │
                   ...               │
                   final_plan: {                              ◀── WYPEŁNIONY
                     warmup: [...],
                     main_part: [...],
                     cooldown: [...],
                     mode: "circuit",
                     total_duration_minutes: 45
                   }
                 }                   │
                                     │
                                     ▼
                              ┌─────────────┐
                              │    END      │
                              └─────────────┘
```

---

## Importy

```python
import json
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
```

### Wyjaśnienie kluczowych importów

| Import | Źródło | Rola |
|--------|--------|------|
| `StateGraph, END` | langgraph | Budowanie grafu workflow |
| `Document` | langchain_core | Format dokumentu z Qdrant |
| `ChatPromptTemplate` | langchain_core | Szablon promptu dla LLM |
| `BaseChatModel` | langchain_core | Typ bazowy dla LLM |
| `Qdrant` | langchain_community | Wrapper na bazę wektorową |
| `FastEmbedEmbeddings` | langchain_community | Model embeddingów |
| `QdrantClient, models` | qdrant_client | Natywny klient + filtry |
| `TrainingPlan` | app.models | Model odpowiedzi |

---

## Konfiguracja

```python
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
```

### Diagram konfiguracji

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KONFIGURACJA                                         │
└─────────────────────────────────────────────────────────────────────────────┘

  .env                                   agent.py
  ────                                   ────────

  # Qdrant
  QDRANT_URL=http://localhost:6333  ──▶  połączenie z bazą wektorową
  QDRANT_COLLECTION_NAME=gym_ex...  ──▶  nazwa kolekcji

  # LLM
  LLM_PROVIDER=ollama               ──▶  wybór: openai / ollama
  LLM_MODEL=llama3.2                ──▶  nazwa modelu
  LLM_TEMPERATURE=0.2               ──▶  0.0 = deterministyczny
  OLLAMA_BASE_URL=http://...        ──▶  adres serwera Ollama
```

---

## TrainerState

### Definicja

```python
class TrainerState(TypedDict):
    # Wejście (od użytkownika)
    num_people: int
    difficulty: str
    rest_time: int
    mode: str
    warmup_count: int
    main_count: int
    cooldown_count: int

    # Wypełniane przez retrieve
    warmup_candidates: List[Document]
    main_candidates: List[Document]
    cooldown_candidates: List[Document]

    # Wypełniane przez plan
    final_plan: dict
```

### Diagram stanu

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TrainerState                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  POLA WEJŚCIOWE (ustawiane przez main.py):                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ num_people: int       │ Liczba osób (1-50)                         │   │
│  │ difficulty: str       │ "easy" / "medium" / "hard"                 │   │
│  │ rest_time: int        │ Czas przerwy w sekundach                   │   │
│  │ mode: str             │ "circuit" / "common"                       │   │
│  │ warmup_count: int     │ Ile ćwiczeń warmup                         │   │
│  │ main_count: int       │ Ile ćwiczeń main                           │   │
│  │ cooldown_count: int   │ Ile ćwiczeń cooldown                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  POLA POŚREDNIE (wypełniane przez retrieve):                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ warmup_candidates: List[Document]    │ Kandydaci z Qdrant          │   │
│  │ main_candidates: List[Document]      │                             │   │
│  │ cooldown_candidates: List[Document]  │                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  POLA WYJŚCIOWE (wypełniane przez plan):                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ final_plan: dict     │ TrainingPlan jako słownik                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Funkcja get_llm

### Kod

```python
def get_llm() -> BaseChatModel:
    if LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            base_url=OLLAMA_BASE_URL,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
```

### Diagram wyboru LLM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           get_llm()                                          │
└─────────────────────────────────────────────────────────────────────────────┘

                         LLM_PROVIDER?
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
        "ollama"                          "openai"
              │                               │
              ▼                               ▼
  ┌─────────────────────┐         ┌─────────────────────┐
  │    ChatOllama       │         │    ChatOpenAI       │
  │                     │         │                     │
  │ model: llama3.2     │         │ model: gpt-4o       │
  │ temp: 0.2           │         │ temp: 0.2           │
  │ url: localhost:11434│         │ api_key: OPENAI_... │
  └─────────────────────┘         └─────────────────────┘
```

---

## Funkcja get_vector_store

### Lazy initialization

```python
_embeddings: Optional[FastEmbedEmbeddings] = None
_vector_store: Optional[Qdrant] = None

def get_vector_store() -> Qdrant:
    global _embeddings, _vector_store

    if _vector_store is not None:
        return _vector_store  # Zwróć z cache

    # Sprawdź czy kolekcja istnieje
    if not check_collection_exists():
        raise ValueError("Collection not found. Run seed_database.py")

    # Utwórz połączenie
    _embeddings = FastEmbedEmbeddings()
    client = QdrantClient(url=QDRANT_URL)

    _vector_store = Qdrant(
        client=client,
        collection_name=COLLECTION_NAME,
        embeddings=_embeddings
    )

    return _vector_store
```

### Co to jest lazy initialization?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LAZY INITIALIZATION                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  PIERWSZE WYWOŁANIE:                 KOLEJNE WYWOŁANIA:
  ───────────────────                 ──────────────────

  get_vector_store()                  get_vector_store()
        │                                   │
        ▼                                   ▼
  _vector_store == None?              _vector_store == None?
        │                                   │
        │ TAK                               │ NIE
        ▼                                   ▼
  ┌─────────────────┐                 ┌─────────────────┐
  │ Utwórz nowe     │                 │ Zwróć z cache   │
  │ połączenie      │                 │ (szybkie!)      │
  │ (wolne ~500ms)  │                 │ (0ms)           │
  └─────────────────┘                 └─────────────────┘
```

---

## Węzeł retrieve_exercises

### Kod (uproszczony)

```python
def retrieve_exercises(state: TrainerState) -> dict:
    vector_store = get_vector_store()
    difficulty = state["difficulty"]

    def search_category(category_type, limit, filter_level=None):
        # Buduj filtry
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

    return {
        "warmup_candidates": search_category("warmup", limit=5),
        "main_candidates": search_category("main", limit=10, filter_level=difficulty),
        "cooldown_candidates": search_category("cooldown", limit=5)
    }
```

### Diagram działania

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      retrieve_exercises()                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  state["difficulty"] = "hard"
         │
         ├────────────────┬────────────────┬────────────────┐
         │                │                │                │
         ▼                ▼                ▼                ▼
   search_category   search_category   search_category
   ("warmup", 5)     ("main", 10,      ("cooldown", 5)
                      "hard")
         │                │                │
         │                │                │
         ▼                ▼                ▼
  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
  │   Qdrant    │  │   Qdrant    │  │   Qdrant    │
  │             │  │             │  │             │
  │ type=warmup │  │ type=main   │  │ type=       │
  │             │  │ level=hard  │  │ cooldown    │
  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
         │                │                │
         ▼                ▼                ▼
   5 Documents       10 Documents    5 Documents
         │                │                │
         └────────────────┼────────────────┘
                          │
                          ▼
                   return {
                     "warmup_candidates": [...],
                     "main_candidates": [...],
                     "cooldown_candidates": [...]
                   }
```

---

## Węzeł generate_plan

### Prompt systemowy

```python
system_prompt = """You are a professional personal trainer.
Create a training plan using ONLY exercises from the provided list.

REQUIREMENTS:
- Select exactly {warmup_count} exercises for warmup
- Select exactly {main_count} exercises for main_part
- Select exactly {cooldown_count} exercises for cooldown
- Training mode: {mode_desc}
- Use ONLY exercises from the candidates below

CANDIDATES - WARMUP:
{warmup}

CANDIDATES - MAIN:
{main}

CANDIDATES - COOLDOWN:
{cooldown}

Return ONLY valid JSON in this exact format:
{"warmup": [...], "main_part": [...], "cooldown": [...], "mode": "...", "total_duration_minutes": 45}"""
```

### Różnica OpenAI vs Ollama

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OPENAI vs OLLAMA                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  OPENAI:                             OLLAMA:
  ───────                             ──────

  llm.with_structured_output(         chain = prompt | llm
      TrainingPlan                    response = chain.invoke(...)
  )
        │                                   │
        ▼                                   ▼
  ┌─────────────────┐                 ┌─────────────────┐
  │ LLM wie że      │                 │ LLM zwraca      │
  │ musi zwrócić    │                 │ tekst (może     │
  │ dokładnie       │                 │ być JSON w      │
  │ TrainingPlan    │                 │ markdown)       │
  └────────┬────────┘                 └────────┬────────┘
           │                                   │
           ▼                                   ▼
  TrainingPlan (gotowy)               Ręczne parsowanie:
                                      1. Spróbuj json.loads()
                                      2. Szukaj ```json...```
                                      3. Szukaj {...}
                                            │
                                            ▼
                                      TrainingPlan(**data)
```

---

## Funkcja build_workflow

### Kod

```python
def build_workflow() -> StateGraph:
    workflow = StateGraph(TrainerState)

    # Dodaj węzły
    workflow.add_node("retrieve", retrieve_exercises)
    workflow.add_node("plan", generate_plan)

    # Definiuj przepływ
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "plan")
    workflow.add_edge("plan", END)

    return workflow.compile()

# Eksportowany obiekt
app_graph = build_workflow()
```

### Użycie

```python
# W main.py:
from app.agent import app_graph

result = app_graph.invoke({
    "num_people": 5,
    "difficulty": "hard",
    "mode": "circuit",
    "warmup_count": 3,
    "main_count": 5,
    "cooldown_count": 3,
    "warmup_candidates": [],
    "main_candidates": [],
    "cooldown_candidates": [],
    "final_plan": {}
})

plan = result["final_plan"]  # TrainingPlan jako dict
```

---

## Rozwiązywanie problemów

### Błąd: Collection not found

```
ValueError: Collection 'gym_exercises' not found in Qdrant.
Please run 'python seed_database.py' first to create it.
```

**Rozwiązanie:** Uruchom seedowanie bazy

### Błąd: Could not parse JSON from LLM

```
ValueError: Could not parse JSON from LLM response: ...
```

**Przyczyna:** Ollama zwróciła tekst który nie jest validnym JSON

**Rozwiązanie:**
- Użyj lepszego modelu (qwen2.5:7b)
- Lub przełącz na OpenAI

### Błąd: OPENAI_API_KEY not set

```
WARNING: OPENAI_API_KEY not set - API calls will fail
```

**Rozwiązanie:** Ustaw klucz w .env lub przełącz na Ollama

---

**Poprzedni:** [04_seed_database_py.md](./04_seed_database_py.md)

**Następny:** [06_main_py.md](./06_main_py.md) - FastAPI endpoints
