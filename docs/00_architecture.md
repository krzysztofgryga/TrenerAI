# Architektura TrenerAI

## Spis treści
1. [Przegląd systemu](#przegląd-systemu)
2. [Diagram architektury](#diagram-architektury)
3. [Przepływ danych](#przepływ-danych)
4. [Komponenty](#komponenty)
5. [Struktura plików](#struktura-plików)
6. [Słownik pojęć](#słownik-pojęć)

---

## Przegląd systemu

**TrenerAI** to generator planów treningowych wykorzystujący:
- **RAG** (Retrieval Augmented Generation) do wyszukiwania ćwiczeń
- **LLM** (Large Language Model) do generowania planów
- **Vector Database** do semantycznego wyszukiwania

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRENERAI - JEDNO ZDANIE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Użytkownik wysyła parametry treningu → System wyszukuje pasujące         │
│   ćwiczenia w bazie wektorowej → LLM generuje spersonalizowany plan        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Diagram architektury

### Widok wysokopoziomowy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ARCHITEKTURA                                    │
└─────────────────────────────────────────────────────────────────────────────┘


   KLIENT                    BACKEND                         ZEWNĘTRZNE
   ──────                    ───────                         ──────────

  ┌──────────┐          ┌─────────────────┐              ┌─────────────────┐
  │  curl /  │          │                 │              │                 │
  │  Flutter │─────────▶│    FastAPI      │              │     Qdrant      │
  │  Postman │  HTTP    │    (main.py)    │              │   (Vector DB)   │
  │          │  POST    │                 │              │   port: 6333    │
  └──────────┘          └────────┬────────┘              └────────▲────────┘
                                 │                                │
                                 │ invoke()                       │ similarity
                                 ▼                                │ _search()
                        ┌─────────────────┐                       │
                        │   LangGraph     │───────────────────────┘
                        │   (agent.py)    │
                        │                 │              ┌─────────────────┐
                        │  ┌───────────┐  │              │                 │
                        │  │ retrieve  │  │              │  OpenAI / Ollama│
                        │  │   node    │  │              │     (LLM)       │
                        │  └─────┬─────┘  │              │                 │
                        │        │        │              └────────▲────────┘
                        │        ▼        │                       │
                        │  ┌───────────┐  │                       │ invoke()
                        │  │   plan    │──┼───────────────────────┘
                        │  │   node    │  │
                        │  └───────────┘  │
                        └─────────────────┘
```

### Szczegółowy diagram komponentów

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SZCZEGÓŁOWA ARCHITEKTURA                             │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌───────────────────────┐
                              │      HTTP Request     │
                              │  POST /generate-      │
                              │       training        │
                              └───────────┬───────────┘
                                          │
  ┌───────────────────────────────────────┼───────────────────────────────────┐
  │ main.py                               │                                   │
  │                                       ▼                                   │
  │                          ┌────────────────────────┐                       │
  │                          │   TrainingRequest      │                       │
  │                          │   (Pydantic Model)     │                       │
  │                          │                        │                       │
  │                          │ • num_people: int      │                       │
  │                          │ • difficulty: Enum     │                       │
  │                          │ • rest_time: int       │                       │
  │                          │ • mode: Enum           │                       │
  │                          │ • warmup_count: int    │                       │
  │                          │ • main_count: int      │                       │
  │                          │ • cooldown_count: int  │                       │
  │                          └────────────┬───────────┘                       │
  │                                       │                                   │
  │                                       │ model_dump()                      │
  │                                       ▼                                   │
  │                          ┌────────────────────────┐                       │
  │                          │  workflow.invoke(      │                       │
  │                          │    initial_state       │                       │
  │                          │  )                     │                       │
  │                          └────────────┬───────────┘                       │
  └───────────────────────────────────────┼───────────────────────────────────┘
                                          │
  ┌───────────────────────────────────────┼───────────────────────────────────┐
  │ agent.py                              │                                   │
  │                                       ▼                                   │
  │                          ┌────────────────────────┐                       │
  │                          │    TrainerState        │                       │
  │                          │    (TypedDict)         │                       │
  │                          │                        │                       │
  │                          │ • num_people           │                       │
  │                          │ • difficulty           │                       │
  │                          │ • exercises: List      │◀── wypełnia retrieve  │
  │                          │ • plan: TrainingPlan   │◀── wypełnia plan      │
  │                          └────────────┬───────────┘                       │
  │                                       │                                   │
  │            ┌──────────────────────────┴──────────────────────────┐       │
  │            │                                                      │       │
  │            ▼                                                      ▼       │
  │  ┌───────────────────┐                              ┌───────────────────┐ │
  │  │  retrieve_        │                              │  generate_        │ │
  │  │  exercises()      │                              │  plan()           │ │
  │  │                   │                              │                   │ │
  │  │ 1. get_vector_    │                              │ 1. get_llm()      │ │
  │  │    store()        │                              │ 2. build_prompt() │ │
  │  │ 2. build_query()  │                              │ 3. llm.invoke()   │ │
  │  │ 3. similarity_    │─────────────────────────────▶│ 4. parse_json()   │ │
  │  │    search(k=20)   │                              │ 5. return plan    │ │
  │  └─────────┬─────────┘                              └─────────┬─────────┘ │
  │            │                                                  │           │
  └────────────┼──────────────────────────────────────────────────┼───────────┘
               │                                                  │
               ▼                                                  ▼
  ┌────────────────────────┐                         ┌────────────────────────┐
  │        Qdrant          │                         │    OpenAI / Ollama     │
  │                        │                         │                        │
  │ Collection:            │                         │ Model:                 │
  │ "gym_exercises"        │                         │ gpt-4o / llama3.2      │
  │                        │                         │                        │
  │ 100 punktów            │                         │ with_structured_output │
  │ (ćwiczeń)              │                         │ lub manual JSON parse  │
  └────────────────────────┘                         └────────────────────────┘
```

---

## Przepływ danych

### Sekwencja request → response

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRZEPŁYW DANYCH                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  CZAS
   │
   │  1. REQUEST
   │  ──────────────────────────────────────────────────────────────────────
   │
   │  curl -X POST http://localhost:8000/generate-training \
   │    -d '{"num_people": 5, "difficulty": "hard", "mode": "circuit"}'
   │
   ▼
   │  2. WALIDACJA (main.py)
   │  ──────────────────────────────────────────────────────────────────────
   │
   │  TrainingRequest.model_validate(json_data)
   │  → OK lub 422 Validation Error
   │
   ▼
   │  3. INVOKE WORKFLOW (agent.py)
   │  ──────────────────────────────────────────────────────────────────────
   │
   │  initial_state = {
   │      "num_people": 5,
   │      "difficulty": "hard",
   │      "mode": "circuit",
   │      "exercises": [],      ← puste
   │      "plan": None          ← puste
   │  }
   │
   ▼
   │  4. NODE: retrieve_exercises
   │  ──────────────────────────────────────────────────────────────────────
   │
   │  query = "hard workout exercises"
   │  docs = qdrant.similarity_search(query, k=20)
   │
   │  state["exercises"] = [Doc1, Doc2, ...]  ← wypełnione
   │
   ▼
   │  5. NODE: generate_plan
   │  ──────────────────────────────────────────────────────────────────────
   │
   │  prompt = build_prompt(state)
   │  response = llm.invoke(prompt)
   │  plan = parse_to_TrainingPlan(response)
   │
   │  state["plan"] = TrainingPlan(...)  ← wypełnione
   │
   ▼
   │  6. RESPONSE
   │  ──────────────────────────────────────────────────────────────────────
   │
   │  return state["plan"].model_dump()
   │
   │  {
   │    "warmup": [...],
   │    "main_part": [...],
   │    "cooldown": [...],
   │    "mode": "circuit",
   │    "total_duration_minutes": 45
   │  }
   │
   ▼
```

---

## Komponenty

### 1. FastAPI (main.py)

| Element | Opis |
|---------|------|
| **Rola** | HTTP API, walidacja, routing |
| **Endpointy** | `/`, `/health`, `/debug/config`, `/generate-training` |
| **Zależności** | Pydantic (walidacja), agent.py (logika) |

### 2. LangGraph Workflow (agent.py)

| Element | Opis |
|---------|------|
| **Rola** | Orkiestracja workflow AI |
| **Węzły** | `retrieve_exercises`, `generate_plan` |
| **Stan** | `TrainerState` (TypedDict) |
| **Zależności** | Qdrant, OpenAI/Ollama |

### 3. Qdrant (Vector Database)

| Element | Opis |
|---------|------|
| **Rola** | Przechowywanie i wyszukiwanie ćwiczeń |
| **Kolekcja** | `gym_exercises` (100 ćwiczeń) |
| **Wymiary** | 384 (FastEmbed) |
| **Port** | 6333 |

### 4. LLM (OpenAI / Ollama)

| Element | Opis |
|---------|------|
| **Rola** | Generowanie planów treningowych |
| **OpenAI** | `gpt-4o` (structured output) |
| **Ollama** | `llama3.2` (manual JSON parsing) |
| **Temperatura** | 0.2 (deterministyczne odpowiedzi) |

---

## Struktura plików

```
TrenerAI/
│
├── app/                          # Kod aplikacji
│   ├── __init__.py
│   ├── main.py                   # FastAPI endpoints
│   ├── agent.py                  # LangGraph workflow
│   └── models/
│       ├── __init__.py
│       └── exercise.py           # Pydantic models
│
├── data/
│   └── exercises.json            # 100 ćwiczeń (źródło)
│
├── docs/                         # Dokumentacja
│   ├── 00_architecture.md        # ← TEN PLIK
│   ├── 01_concepts/              # Koncepty (embedding, RAG...)
│   ├── 02_models_exercise_py.md
│   └── ...
│
├── seed_database.py              # Seedowanie Qdrant
├── docker-compose.yml            # Qdrant + Ollama
├── requirements.txt              # Zależności Python
├── pyproject.toml                # Konfiguracja projektu
├── .env.example                  # Przykładowa konfiguracja
└── README.md                     # Quickstart
```

---

## Słownik pojęć

| Pojęcie | Definicja |
|---------|-----------|
| **Embedding** | Wektor liczb reprezentujący znaczenie tekstu |
| **Vector Store** | Baza danych przechowująca i wyszukująca wektory |
| **Qdrant** | Open-source vector database (używana w projekcie) |
| **LangGraph** | Biblioteka do budowania workflow AI jako grafów |
| **RAG** | Retrieval Augmented Generation - wyszukaj + wygeneruj |
| **LLM** | Large Language Model (GPT-4, Llama) |
| **Pydantic** | Biblioteka do walidacji danych w Python |
| **FastAPI** | Framework do budowania REST API |
| **FastEmbed** | Lekki model do generowania embeddingów |
| **Ollama** | Narzędzie do uruchamiania LLM lokalnie |

---

## Następne kroki

Przeczytaj dokumentację w kolejności:

1. **Koncepty** (`01_concepts/`) - zrozum podstawy
2. **Models** (`02_models_exercise_py.md`) - struktury danych
3. **Exercises** (`03_exercises_json.md`) - dane ćwiczeń
4. **Seed Database** (`04_seed_database_py.md`) - wektoryzacja
5. **Agent** (`05_agent_py.md`) - logika AI
6. **Main** (`06_main_py.md`) - API
7. **Configuration** (`07_configuration.md`) - konfiguracja
8. **Flow Complete** (`08_flow_complete.md`) - pełny przepływ
