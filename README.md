# TrenerAI

AI-powered training plan generator for fitness trainers. Creates personalized workout routines using LangGraph workflow and Qdrant vector database.

## Features

- Generate customized training plans based on:
  - Number of participants (1-50)
  - Difficulty level (easy, medium, hard)
  - Rest time between exercises
  - Training mode (circuit or common)
- Semantic exercise search using vector embeddings
- LLM-powered plan generation with GPT-4o
- RESTful API with FastAPI
- Structured output with Pydantic models

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI       │────▶│   LangGraph     │────▶│   GPT-4o        │
│   REST API      │     │   Workflow      │     │   LLM           │
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

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- OpenAI API key

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
# Edit .env and add your OPENAI_API_KEY
```

### Running

1. Start Qdrant database:
```bash
docker-compose up -d
```

2. Seed the database with exercises:
```bash
python seed_database.py
```

3. Start the API server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Status check |
| GET | `/health` | Health check for orchestration |
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
├── docker-compose.yml   # Qdrant service
├── seed_database.py     # Database seeding script
├── requirements.txt     # Dependencies
├── pyproject.toml       # Project configuration
└── README.md
```

## Configuration

Environment variables (`.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | (required) |
| `OPENAI_MODEL` | LLM model to use | `gpt-4o` |
| `OPENAI_TEMPERATURE` | LLM temperature | `0.2` |
| `QDRANT_URL` | Qdrant server URL | `http://localhost:6333` |
| `QDRANT_COLLECTION_NAME` | Vector collection name | `gym_exercises` |

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
