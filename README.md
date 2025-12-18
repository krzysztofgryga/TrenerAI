# TrenerAI

AI-powered training plan generator for fitness trainers. Creates personalized workout routines using LangGraph workflow and Qdrant vector database.

## Features

- Generate customized training plans based on:
  - Number of participants (1-50)
  - Difficulty level (easy, medium, hard)
  - Rest time between exercises
  - Training mode (circuit or common)
- Semantic exercise search using vector embeddings
- **Flexible LLM support**: OpenAI or local Ollama
- RESTful API with FastAPI
- Structured output with Pydantic models

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI       │────▶│   LangGraph     │────▶│  OpenAI/Ollama  │
│   REST API      │     │   Workflow      │     │      LLM        │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Qdrant        │
                        │   Vector DB     │
                        └─────────────────┘
```

### Workflow

1. **Retrieve** - Search Qdrant for exercise candidates matching criteria
2. **Plan** - Generate structured training plan using LLM

## Tech Stack

- **FastAPI** - Modern async web framework
- **LangGraph** - Graph-based LLM workflow orchestration
- **LangChain** - LLM integration framework
- **Qdrant** - Vector database for semantic search
- **FastEmbed** - Lightweight embedding generation
- **Pydantic** - Data validation and serialization
- **Ollama** - Local LLM runtime (optional)

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- **Either**: OpenAI API key **OR** Ollama installed locally

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/TrenerAI.git
cd TrenerAI
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
# or with uv
uv sync
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env - see configuration options below
```

### Running with Local LLM (Ollama)

1. Start Qdrant and Ollama:
```bash
docker-compose up -d
```

2. Pull a model (first time only):
```bash
docker exec trainer_ollama ollama pull llama3.2
# Or for better results:
docker exec trainer_ollama ollama pull qwen2.5:7b
```

3. Configure `.env` for Ollama:
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

4. Seed the database and start API:
```bash
python seed_database.py
uvicorn app.main:app --reload
```

### Running with OpenAI

1. Start Qdrant only:
```bash
docker-compose up -d qdrant
```

2. Configure `.env` for OpenAI:
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-your-api-key
```

3. Seed the database and start API:
```bash
python seed_database.py
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Status check |
| GET | `/health` | Health check for orchestration |
| GET | `/debug/config` | Show current configuration |
| POST | `/generate-training` | Generate training plan |

### Generate Training Plan

**POST** `/generate-training`

Request body:
```json
{
  "num_people": 5,
  "difficulty": "medium",
  "rest_time": 60,
  "mode": "circuit"
}
```

Parameters:
- `num_people` (int, 1-50): Number of participants
- `difficulty` (string): `easy`, `medium`, or `hard`
- `rest_time` (int, 10-300): Rest time between exercises in seconds
- `mode` (string): `circuit` (different exercises per person) or `common` (same for all)

Response:
```json
{
  "warmup": [...],
  "main_part": [...],
  "cooldown": [...],
  "mode": "circuit",
  "total_duration_minutes": 45
}
```

### API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
TrenerAI/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── agent.py         # LangGraph workflow
│   └── models/
│       ├── __init__.py
│       └── exercise.py  # Pydantic models
├── docker-compose.yml   # Qdrant + Ollama services
├── seed_database.py     # Database seeding script
├── requirements.txt     # Dependencies
├── pyproject.toml       # Project configuration
└── README.md
```

## Configuration

Environment variables (`.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider: `openai` or `ollama` | `openai` |
| `LLM_MODEL` | Model name | `gpt-4o` |
| `LLM_TEMPERATURE` | LLM temperature (0.0-1.0) | `0.2` |
| `OPENAI_API_KEY` | OpenAI API key (if using OpenAI) | - |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `QDRANT_URL` | Qdrant server URL | `http://localhost:6333` |
| `QDRANT_COLLECTION_NAME` | Vector collection name | `gym_exercises` |

### Recommended Ollama Models

| Model | Size | Quality | Speed |
|-------|------|---------|-------|
| `llama3.2` | 3B | Good | Fast |
| `llama3.2:7b` | 7B | Better | Medium |
| `qwen2.5:7b` | 7B | Better | Medium |
| `mistral` | 7B | Good | Medium |

## Exercise Library

The system includes 18 pre-defined exercises:

- **Warmup (5)**: Jumping Jacks, Boxing Run, Hip Circles, Arm Swings, Bodyweight Squats
- **Main - Easy (3)**: Classic Squat, Knee Push-ups, Plank
- **Main - Medium (4)**: Classic Push-ups, Walking Lunges, Kettlebell Swing, Australian Pull-ups
- **Main - Hard (4)**: Burpees, Diamond Push-ups, Pistol Squats, Man Maker
- **Cooldown (3)**: Child's Pose, Couch Stretch, Bar Hang

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Code Style

The project follows PEP 8 guidelines.

## License

MIT License
