# Pełny przepływ: Request → Response

## Spis treści
1. [Przykładowy request](#przykładowy-request)
2. [Przepływ krok po kroku](#przepływ-krok-po-kroku)
3. [Diagram sekwencji](#diagram-sekwencji)
4. [Co może pójść nie tak](#co-może-pójść-nie-tak)
5. [Debugowanie](#debugowanie)

---

## Przykładowy request

```bash
curl -X POST http://localhost:8000/generate-training \
  -H "Content-Type: application/json" \
  -d '{
    "num_people": 5,
    "difficulty": "hard",
    "rest_time": 60,
    "mode": "circuit",
    "warmup_count": 3,
    "main_count": 5,
    "cooldown_count": 3
  }'
```

---

## Przepływ krok po kroku

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PEŁNY PRZEPŁYW REQUEST → RESPONSE                         │
└─────────────────────────────────────────────────────────────────────────────┘


  ══════════════════════════════════════════════════════════════════════════
  KROK 1: HTTP REQUEST
  ══════════════════════════════════════════════════════════════════════════

  curl -X POST http://localhost:8000/generate-training
       -d '{"num_people": 5, "difficulty": "hard", ...}'

                              │
                              ▼

  ══════════════════════════════════════════════════════════════════════════
  KROK 2: FASTAPI ROUTING (main.py)
  ══════════════════════════════════════════════════════════════════════════

  @app.post("/generate-training")
  async def generate_training(request: TrainingRequest):
      ...

  FastAPI:
  1. Znajduje endpoint dla POST /generate-training
  2. Parsuje JSON body
  3. Przekazuje do Pydantic

                              │
                              ▼

  ══════════════════════════════════════════════════════════════════════════
  KROK 3: WALIDACJA PYDANTIC (main.py)
  ══════════════════════════════════════════════════════════════════════════

  class TrainingRequest(BaseModel):
      num_people: Annotated[int, Field(ge=1, le=50)]
      difficulty: Difficulty  # Enum
      ...

  Pydantic sprawdza:
  ✓ num_people=5 → OK (1 ≤ 5 ≤ 50)
  ✓ difficulty="hard" → OK (jest w Enum)
  ✓ rest_time=60 → OK (10 ≤ 60 ≤ 300)
  ✓ mode="circuit" → OK (jest w Enum)

  Wynik: TrainingRequest(num_people=5, difficulty=Difficulty.HARD, ...)

                              │
                              ▼

  ══════════════════════════════════════════════════════════════════════════
  KROK 4: PRZYGOTOWANIE INPUTÓW (main.py)
  ══════════════════════════════════════════════════════════════════════════

  inputs = {
      "num_people": 5,
      "difficulty": "hard",      # .value (Enum → str)
      "rest_time": 60,
      "mode": "circuit",         # .value (Enum → str)
      "warmup_count": 3,
      "main_count": 5,
      "cooldown_count": 3
  }

                              │
                              ▼

  ══════════════════════════════════════════════════════════════════════════
  KROK 5: INVOKE WORKFLOW (main.py → agent.py)
  ══════════════════════════════════════════════════════════════════════════

  result = app_graph.invoke(inputs)

  LangGraph tworzy TrainerState:
  {
      num_people: 5,
      difficulty: "hard",
      rest_time: 60,
      mode: "circuit",
      warmup_count: 3,
      main_count: 5,
      cooldown_count: 3,
      warmup_candidates: [],     # ← puste
      main_candidates: [],       # ← puste
      cooldown_candidates: [],   # ← puste
      final_plan: {}             # ← pusty
  }

                              │
                              ▼

  ══════════════════════════════════════════════════════════════════════════
  KROK 6: NODE "retrieve" (agent.py)
  ══════════════════════════════════════════════════════════════════════════

  def retrieve_exercises(state):
      vector_store = get_vector_store()

      warmup = search("warmup", limit=5)
      main = search("main", filter_level="hard", limit=10)
      cooldown = search("cooldown", limit=5)

      return {
          "warmup_candidates": warmup,
          "main_candidates": main,
          "cooldown_candidates": cooldown
      }

  Qdrant wykonuje similarity_search:
  ┌─────────────────────────────────────────────────────────────────────┐
  │ Query: "best exercise"                                               │
  │ Filter: type=warmup                                                  │
  │                                                                      │
  │ Wynik:                                                               │
  │  - Jumping Jacks (score: 0.85)                                       │
  │  - High Knees (score: 0.82)                                          │
  │  - Boxing Run (score: 0.80)                                          │
  │  - Arm Circles (score: 0.78)                                         │
  │  - Hip Circles (score: 0.75)                                         │
  └─────────────────────────────────────────────────────────────────────┘

  Stan po retrieve:
  {
      ...
      warmup_candidates: [Doc("Jumping Jacks"), Doc("High Knees"), ...],
      main_candidates: [Doc("Burpees"), Doc("Pistol Squats"), ...],
      cooldown_candidates: [Doc("Child's Pose"), Doc("Cat-Cow"), ...],
      final_plan: {}
  }

                              │
                              ▼

  ══════════════════════════════════════════════════════════════════════════
  KROK 7: NODE "plan" (agent.py)
  ══════════════════════════════════════════════════════════════════════════

  def generate_plan(state):
      llm = get_llm()  # OpenAI lub Ollama

      prompt = """
      You are a professional trainer...

      CANDIDATES - WARMUP:
      - [ID: w1] Jumping Jacks: Jump with arm swings
      - [ID: w6] High Knees: Run in place lifting knees high
      ...

      CANDIDATES - MAIN:
      - [ID: m_h1] Burpees: Down, up, jump. Maximum tempo
      - [ID: m_h3] Pistol Squats: Single-leg squat
      ...

      Return JSON: {"warmup": [...], "main_part": [...], ...}
      """

      response = llm.invoke(prompt)

  LLM generuje:
  ┌─────────────────────────────────────────────────────────────────────┐
  │ {                                                                    │
  │   "warmup": [                                                        │
  │     {"id": "w1", "name": "Jumping Jacks", "description": "...", ...},│
  │     {"id": "w6", "name": "High Knees", ...},                         │
  │     {"id": "w2", "name": "Boxing Run", ...}                          │
  │   ],                                                                 │
  │   "main_part": [                                                     │
  │     {"id": "m_h1", "name": "Burpees", ...},                          │
  │     {"id": "m_h3", "name": "Pistol Squats", ...},                    │
  │     {"id": "m_h2", "name": "Diamond Push-ups", ...},                 │
  │     {"id": "m_h4", "name": "Man Maker", ...},                        │
  │     {"id": "m_h5", "name": "Muscle-ups", ...}                        │
  │   ],                                                                 │
  │   "cooldown": [                                                      │
  │     {"id": "c1", "name": "Child's Pose", ...},                       │
  │     {"id": "c2", "name": "Cat-Cow Stretch", ...},                    │
  │     {"id": "c3", "name": "Pigeon Pose", ...}                         │
  │   ],                                                                 │
  │   "mode": "circuit",                                                 │
  │   "total_duration_minutes": 45                                       │
  │ }                                                                    │
  └─────────────────────────────────────────────────────────────────────┘

      return {"final_plan": TrainingPlan(**json_response).model_dump()}

  Stan po plan:
  {
      ...
      final_plan: {
          "warmup": [...],
          "main_part": [...],
          "cooldown": [...],
          "mode": "circuit",
          "total_duration_minutes": 45
      }
  }

                              │
                              ▼

  ══════════════════════════════════════════════════════════════════════════
  KROK 8: RETURN RESPONSE (main.py)
  ══════════════════════════════════════════════════════════════════════════

  return result["final_plan"]

  HTTP Response:
  Status: 200 OK
  Content-Type: application/json

  {
    "warmup": [
      {
        "id": "w1",
        "name": "Jumping Jacks",
        "description": "Jump with arm swings. Great cardio warmup.",
        "muscle_group": "general",
        "difficulty": "easy",
        "type": "warmup"
      },
      ...
    ],
    "main_part": [
      {
        "id": "m_h1",
        "name": "Burpees",
        "description": "Down, up, jump. Maximum tempo.",
        "muscle_group": "full_body",
        "difficulty": "hard",
        "type": "main"
      },
      ...
    ],
    "cooldown": [...],
    "mode": "circuit",
    "total_duration_minutes": 45
  }
```

---

## Diagram sekwencji

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DIAGRAM SEKWENCJI                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  Client          FastAPI         LangGraph        Qdrant          LLM
    │                │                │               │              │
    │  POST /generate│                │               │              │
    │───────────────▶│                │               │              │
    │                │                │               │              │
    │                │  Validate      │               │              │
    │                │  (Pydantic)    │               │              │
    │                │                │               │              │
    │                │  invoke()      │               │              │
    │                │───────────────▶│               │              │
    │                │                │               │              │
    │                │                │  similarity   │              │
    │                │                │  _search()    │              │
    │                │                │──────────────▶│              │
    │                │                │               │              │
    │                │                │   Documents   │              │
    │                │                │◀──────────────│              │
    │                │                │               │              │
    │                │                │               │   invoke()   │
    │                │                │───────────────┼─────────────▶│
    │                │                │               │              │
    │                │                │               │ TrainingPlan │
    │                │                │◀──────────────┼──────────────│
    │                │                │               │              │
    │                │   final_plan   │               │              │
    │                │◀───────────────│               │              │
    │                │                │               │              │
    │  200 OK        │                │               │              │
    │  {warmup:...}  │                │               │              │
    │◀───────────────│                │               │              │
    │                │                │               │              │
```

---

## Co może pójść nie tak

### Błąd walidacji (422)

```
Request:
{"num_people": 100, "difficulty": "hard", ...}

Response:
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "num_people"],
      "msg": "Input should be less than or equal to 50",
      "input": 100
    }
  ]
}
```

### Brak kolekcji w Qdrant (500)

```
Response:
{
  "detail": "Collection 'gym_exercises' not found in Qdrant.
             Please run 'python seed_database.py' first to create it."
}

Rozwiązanie: python seed_database.py
```

### Błąd parsowania JSON z Ollama (500)

```
Response:
{
  "detail": "Failed to generate training plan:
             Could not parse JSON from LLM response..."
}

Rozwiązanie: Użyj lepszego modelu (qwen2.5:7b) lub OpenAI
```

---

## Debugowanie

### Sprawdź konfigurację

```bash
curl http://localhost:8000/debug/config
```

### Sprawdź logi

```bash
# Logi FastAPI
uvicorn app.main:app --reload

# Logi Qdrant
docker-compose logs -f qdrant

# Logi Ollama
docker-compose logs -f ollama
```

### Sprawdź czy baza jest seedowana

```bash
curl http://localhost:6333/collections/gym_exercises
```

### Test z minimalnym requestem

```bash
curl -X POST http://localhost:8000/generate-training \
  -H "Content-Type: application/json" \
  -d '{"num_people": 1, "difficulty": "easy", "rest_time": 30, "mode": "common"}'
```

---

## Podsumowanie

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PODSUMOWANIE PRZEPŁYWU                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. HTTP POST → FastAPI                                                     │
│  2. Pydantic waliduje dane                                                 │
│  3. LangGraph uruchamia workflow                                           │
│  4. retrieve: Qdrant szuka ćwiczeń                                         │
│  5. plan: LLM generuje plan                                                │
│  6. HTTP Response z TrainingPlan                                           │
│                                                                             │
│  Czas wykonania:                                                            │
│  • Walidacja: ~1ms                                                         │
│  • Qdrant search: ~50-100ms                                                │
│  • LLM generation: ~2-10s (zależy od modelu)                               │
│  • Całość: ~3-12s                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Poprzedni:** [07_configuration.md](./07_configuration.md) - Konfiguracja

**Powrót do początku:** [00_architecture.md](./00_architecture.md) - Architektura
