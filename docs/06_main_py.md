# Dokumentacja: app/main.py

## Spis treści
1. [Cel modułu](#cel-modułu)
2. [Importy](#importy)
3. [Konfiguracja FastAPI](#konfiguracja-fastapi)
4. [CORS Middleware](#cors-middleware)
5. [Modele Request/Response](#modele-requestresponse)
6. [Endpointy API](#endpointy-api)
7. [Uruchamianie](#uruchamianie)

---

## Cel modułu

Moduł `app/main.py` to **punkt wejścia** aplikacji - serwer HTTP:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          main.py - API LAYER                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  HTTP Request                      main.py                      agent.py
  ────────────                      ───────                      ────────

  POST /generate-training     ┌─────────────────┐
  {                           │                 │           ┌─────────────┐
    "num_people": 5,    ─────▶│   FastAPI       │──────────▶│  LangGraph  │
    "difficulty": "hard"      │                 │           │  Workflow   │
  }                           │  1. Walidacja   │           └──────┬──────┘
                              │  2. Logowanie   │                  │
                              │  3. Invoke      │◀─────────────────┘
                              └────────┬────────┘
                                       │
                                       ▼
                              {
                                "warmup": [...],
                                "main_part": [...],
                                "cooldown": [...]
                              }
```

---

## Importy

```python
import logging
import os
import traceback
from enum import Enum
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent import app_graph
```

| Import | Źródło | Rola |
|--------|--------|------|
| `FastAPI` | fastapi | Framework webowy |
| `HTTPException` | fastapi | Zwracanie błędów HTTP |
| `CORSMiddleware` | fastapi | Obsługa Cross-Origin |
| `BaseModel, Field` | pydantic | Walidacja requestów |
| `Annotated` | typing | Adnotacje typów z walidacją |
| `app_graph` | app.agent | Skompilowany workflow |

---

## Konfiguracja FastAPI

```python
app = FastAPI(
    title="TrenerAI API",
    description="AI-powered training plan generator...",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
```

### Automatyczna dokumentacja

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DOKUMENTACJA API                                       │
└─────────────────────────────────────────────────────────────────────────────┘

  http://localhost:8000/docs      ──▶  Swagger UI (interaktywna)
  http://localhost:8000/redoc     ──▶  ReDoc (czytelna dokumentacja)
```

---

## CORS Middleware

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Dozwolone originy (w produkcji: konkretne domeny)
    allow_credentials=True,   # Pozwól na cookies
    allow_methods=["*"],      # Wszystkie metody HTTP
    allow_headers=["*"],      # Wszystkie nagłówki
)
```

### Co to jest CORS?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CORS EXPLAINED                                       │
└─────────────────────────────────────────────────────────────────────────────┘

  BEZ CORS:                           Z CORS:
  ─────────                           ──────

  Frontend                            Frontend
  (localhost:3000)                    (localhost:3000)
        │                                   │
        ▼                                   ▼
  ┌─────────────────┐                 ┌─────────────────┐
  │ fetch(          │                 │ fetch(          │
  │  "localhost:8000│                 │  "localhost:8000│
  │  /generate..."  │                 │  /generate..."  │
  │ )               │                 │ )               │
  └────────┬────────┘                 └────────┬────────┘
           │                                   │
           ▼                                   ▼
  ┌─────────────────┐                 ┌─────────────────┐
  │    Browser      │                 │    Browser      │
  │    BLOKUJE!     │                 │    Przepuszcza  │
  │                 │                 │                 │
  │ "Origin not     │                 │ Access-Control- │
  │  allowed"       │                 │ Allow-Origin: * │
  └─────────────────┘                 └─────────────────┘
```

---

## Modele Request/Response

### Enum Difficulty

```python
class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
```

### Enum TrainingMode

```python
class TrainingMode(str, Enum):
    CIRCUIT = "circuit"   # Każdy robi co innego
    COMMON = "common"     # Wszyscy robią to samo
```

### TrainingRequest

```python
class TrainingRequest(BaseModel):
    num_people: Annotated[int, Field(ge=1, le=50)]
    difficulty: Difficulty
    rest_time: Annotated[int, Field(ge=10, le=300)]
    mode: TrainingMode
    warmup_count: Annotated[int, Field(ge=1, le=10)] = 3
    main_count: Annotated[int, Field(ge=1, le=20)] = 5
    cooldown_count: Annotated[int, Field(ge=1, le=10)] = 3
```

### Diagram walidacji

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WALIDACJA PYDANTIC                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  REQUEST JSON                        WALIDACJA                     WYNIK
  ────────────                        ─────────                     ─────

  {                                   num_people:
    "num_people": 5,          ──────▶ ge=1, le=50 ✓
    "difficulty": "hard",     ──────▶ Enum check ✓           TrainingRequest(
    "rest_time": 60,          ──────▶ ge=10, le=300 ✓            num_people=5,
    "mode": "circuit"         ──────▶ Enum check ✓               difficulty=HARD,
  }                                   warmup_count: default=3       ...)


  {
    "num_people": 100,        ──────▶ le=50 ✗              422 Validation Error
    ...                               "num_people must be ≤ 50"
  }


  {
    "difficulty": "extreme",  ──────▶ Enum check ✗         422 Validation Error
    ...                               "difficulty: 'extreme' is not valid"
  }
```

---

## Endpointy API

### GET /

```python
@app.get("/")
def read_root() -> dict:
    return {"status": "TrenerAI API Online", "version": "0.2.0"}
```

**Użycie:**
```bash
curl http://localhost:8000/
# {"status": "TrenerAI API Online", "version": "0.2.0"}
```

### GET /health

```python
@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy"}
```

**Cel:** Health check dla Docker/Kubernetes

### GET /debug/config

```python
@app.get("/debug/config")
def debug_config() -> dict:
    return {
        "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
        "llm_model": os.getenv("LLM_MODEL", "gpt-4o"),
        "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "qdrant_url": os.getenv("QDRANT_URL"),
        ...
    }
```

**Cel:** Debugging konfiguracji (wyłącz w produkcji!)

### POST /generate-training

```python
@app.post("/generate-training")
async def generate_training(request: TrainingRequest) -> dict:
    inputs = {
        "num_people": request.num_people,
        "difficulty": request.difficulty.value,
        "rest_time": request.rest_time,
        "mode": request.mode.value,
        "warmup_count": request.warmup_count,
        "main_count": request.main_count,
        "cooldown_count": request.cooldown_count
    }

    result = app_graph.invoke(inputs)
    return result["final_plan"]
```

### Diagram przepływu /generate-training

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POST /generate-training                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  1. REQUEST
  ──────────
  POST http://localhost:8000/generate-training
  Content-Type: application/json

  {
    "num_people": 5,
    "difficulty": "hard",
    "rest_time": 60,
    "mode": "circuit",
    "warmup_count": 3,
    "main_count": 5,
    "cooldown_count": 3
  }
         │
         ▼
  2. PYDANTIC VALIDATION
  ───────────────────────
  TrainingRequest.model_validate(json_data)
         │
         │ ✓ OK              ✗ BŁĄD
         ▼                       │
  TrainingRequest(...)           │
         │                       ▼
         │                  422 Validation Error
         │                  {"detail": [...]}
         │
         ▼
  3. PREPARE INPUTS
  ─────────────────
  inputs = {
    "num_people": 5,
    "difficulty": "hard",  ◀── .value (Enum → str)
    ...
  }
         │
         ▼
  4. INVOKE WORKFLOW
  ──────────────────
  result = app_graph.invoke(inputs)
         │
         │ ✓ OK              ✗ BŁĄD
         ▼                       │
  {"final_plan": {...}}          │
         │                       ▼
         │                  500 Internal Error
         │                  "Failed to generate..."
         │
         ▼
  5. RESPONSE
  ───────────
  return result["final_plan"]

  {
    "warmup": [...],
    "main_part": [...],
    "cooldown": [...],
    "mode": "circuit",
    "total_duration_minutes": 45
  }
```

---

## Uruchamianie

### Przez uvicorn (zalecane)

```bash
# Development (z auto-reload)
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Przez Python

```bash
python -m app.main
# lub
python app/main.py
```

### Testowanie API

```bash
# Status
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# Konfiguracja
curl http://localhost:8000/debug/config

# Generowanie planu
curl -X POST http://localhost:8000/generate-training \
  -H "Content-Type: application/json" \
  -d '{
    "num_people": 5,
    "difficulty": "hard",
    "rest_time": 60,
    "mode": "circuit"
  }'
```

---

**Poprzedni:** [05_agent_py.md](./05_agent_py.md) - LangGraph workflow

**Następny:** [07_configuration.md](./07_configuration.md) - Konfiguracja projektu
