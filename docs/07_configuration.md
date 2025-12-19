# Dokumentacja: Konfiguracja projektu

## Spis treści
1. [Przegląd](#przegląd)
2. [Plik .env](#plik-env)
3. [docker-compose.yml](#docker-composeyml)
4. [pyproject.toml](#pyprojecttoml)
5. [requirements.txt](#requirementstxt)
6. [Uruchamianie projektu](#uruchamianie-projektu)

---

## Przegląd

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PLIKI KONFIGURACYJNE                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  .env                    ──▶  Zmienne środowiskowe (sekrety, URL-e)
  docker-compose.yml      ──▶  Definicja usług (Qdrant, Ollama)
  pyproject.toml          ──▶  Metadane projektu, zależności
  requirements.txt        ──▶  Lista zależności dla pip
```

---

## Plik .env

### Przykładowa konfiguracja (.env.example)

```bash
# =============================================================================
# LLM Configuration
# =============================================================================

# Provider: 'openai' or 'ollama'
LLM_PROVIDER=ollama

# Model name (e.g., 'gpt-4o' for OpenAI, 'llama3.2' for Ollama)
LLM_MODEL=llama3.2

# Temperature (0.0 = deterministic, 1.0 = creative)
LLM_TEMPERATURE=0.2

# OpenAI API key (required if LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-your-api-key-here

# Ollama server URL (required if LLM_PROVIDER=ollama)
OLLAMA_BASE_URL=http://localhost:11434

# =============================================================================
# Qdrant Configuration
# =============================================================================

# Qdrant server URL
QDRANT_URL=http://localhost:6333

# Collection name for exercises
QDRANT_COLLECTION_NAME=gym_exercises
```

### Tabela zmiennych

| Zmienna | Opis | Domyślna | Wymagana |
|---------|------|----------|----------|
| `LLM_PROVIDER` | Wybór LLM: `openai` lub `ollama` | `openai` | ✓ |
| `LLM_MODEL` | Nazwa modelu | `gpt-4o` | ✓ |
| `LLM_TEMPERATURE` | Temperatura (0.0-1.0) | `0.2` | ✗ |
| `OPENAI_API_KEY` | Klucz API OpenAI | - | Tylko dla OpenAI |
| `OLLAMA_BASE_URL` | URL serwera Ollama | `http://localhost:11434` | Tylko dla Ollama |
| `QDRANT_URL` | URL serwera Qdrant | `http://localhost:6333` | ✓ |
| `QDRANT_COLLECTION_NAME` | Nazwa kolekcji | `gym_exercises` | ✓ |

### Konfiguracja dla OpenAI

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-your-key-here
```

### Konfiguracja dla Ollama (lokalne)

```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

---

## docker-compose.yml

### Pełna konfiguracja

```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: trainer_qdrant
    ports:
      - "6333:6333"   # REST API
      - "6334:6334"   # gRPC
    volumes:
      - qdrant_storage:/qdrant/storage
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    container_name: trainer_ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    restart: unless-stopped

volumes:
  qdrant_storage:
  ollama_models:
```

### Diagram usług

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOCKER COMPOSE                                       │
└─────────────────────────────────────────────────────────────────────────────┘

  docker-compose.yml
         │
         ├──────────────────────────────────────┐
         │                                      │
         ▼                                      ▼
  ┌─────────────────────┐              ┌─────────────────────┐
  │      qdrant         │              │      ollama         │
  │                     │              │                     │
  │  Image: qdrant/     │              │  Image: ollama/     │
  │         qdrant      │              │         ollama      │
  │                     │              │                     │
  │  Ports:             │              │  Ports:             │
  │   6333 (REST)       │              │   11434             │
  │   6334 (gRPC)       │              │                     │
  │                     │              │  Volumes:           │
  │  Volumes:           │              │   ollama_models     │
  │   qdrant_storage    │              │   (pobrane modele)  │
  │   (dane wektorowe)  │              │                     │
  └─────────────────────┘              └─────────────────────┘
         ▲                                      ▲
         │                                      │
         │                                      │
         └──────────────┬───────────────────────┘
                        │
                 ┌──────┴──────┐
                 │   Python    │
                 │   Backend   │
                 └─────────────┘
```

### Komendy Docker

```bash
# Uruchom wszystkie usługi
docker-compose up -d

# Uruchom tylko Qdrant (bez Ollama, gdy używasz OpenAI)
docker-compose up -d qdrant

# Sprawdź status
docker-compose ps

# Logi
docker-compose logs -f qdrant
docker-compose logs -f ollama

# Zatrzymaj
docker-compose down

# Zatrzymaj i usuń dane
docker-compose down -v
```

### Pobieranie modelu Ollama

```bash
# Po uruchomieniu ollama
docker exec trainer_ollama ollama pull llama3.2
docker exec trainer_ollama ollama pull qwen2.5:7b
```

---

## pyproject.toml

```toml
[project]
name = "trener-ai"
version = "0.2.0"
description = "AI-powered training plan generator"
requires-python = ">=3.10"

dependencies = [
    "fastapi>=0.110.0",
    "uvicorn>=0.27.0",
    "pydantic>=2.6.0",
    "python-dotenv>=1.0.0",
    "langchain>=0.2.0",
    "langchain-core>=0.2.0",
    "langchain-community>=0.2.0",
    "langchain-openai>=0.1.0",
    "langchain-ollama>=0.1.0",
    "langgraph>=0.0.30",
    "qdrant-client>=1.7.0",
    "fastembed>=0.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
]
```

### Wyjaśnienie zależności

| Pakiet | Rola |
|--------|------|
| `fastapi` | Framework HTTP API |
| `uvicorn` | ASGI server |
| `pydantic` | Walidacja danych |
| `python-dotenv` | Wczytywanie .env |
| `langchain*` | Framework LLM |
| `langgraph` | Budowanie workflow |
| `qdrant-client` | Klient bazy wektorowej |
| `fastembed` | Lokalne embeddingi |

---

## requirements.txt

```
fastapi>=0.110.0
uvicorn>=0.27.0
pydantic>=2.6.0
python-dotenv>=1.0.0
langchain>=0.2.0
langchain-core>=0.2.0
langchain-community>=0.2.0
langchain-openai>=0.1.0
langchain-ollama>=0.1.0
langgraph>=0.0.30
qdrant-client>=1.7.0
fastembed>=0.2.0
```

---

## Uruchamianie projektu

### Krok po kroku

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    URUCHAMIANIE PROJEKTU                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  1. KONFIGURACJA
  ───────────────
  cp .env.example .env
  # Edytuj .env (wybierz provider, ustaw klucze)


  2. DOCKER (usługi zewnętrzne)
  ─────────────────────────────
  docker-compose up -d

  # Dla Ollama - pobierz model
  docker exec trainer_ollama ollama pull llama3.2


  3. VIRTUAL ENVIRONMENT
  ──────────────────────
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt


  4. SEEDOWANIE BAZY
  ──────────────────
  python seed_database.py


  5. URUCHOMIENIE API
  ───────────────────
  uvicorn app.main:app --reload


  6. TEST
  ───────
  curl http://localhost:8000/
  curl http://localhost:8000/debug/config
  curl -X POST http://localhost:8000/generate-training \
    -H "Content-Type: application/json" \
    -d '{"num_people": 5, "difficulty": "medium", "rest_time": 60, "mode": "circuit"}'
```

---

**Poprzedni:** [06_main_py.md](./06_main_py.md) - FastAPI endpoints

**Następny:** [08_flow_complete.md](./08_flow_complete.md) - Pełny przepływ
