# TrenerAI

AI-powered training plan generator for fitness trainers. Creates personalized workout routines using LangGraph workflow and Qdrant vector database.

## Features

- Generate customized training plans based on:
  - Number of participants (1-50)
  - Difficulty level (easy, medium, hard)
  - Rest time between exercises
  - Training mode (circuit or common)
  - Customizable exercise counts per phase (warmup, main, cooldown)
- **100 pre-defined exercises** loaded from external JSON file
- Semantic exercise search using vector embeddings
- **Flexible LLM support**: OpenAI or local Ollama
- RESTful API with FastAPI
- Structured output with Pydantic models

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Flutter       │────▶│   FastAPI       │────▶│   LangGraph     │────▶│  OpenAI/Ollama  │
│   Mobile/Web    │     │   REST API      │     │   Workflow      │     │      LLM        │
└─────────────────┘     └─────────────────┘     └────────┬────────┘     └─────────────────┘
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
- **Flutter** - Cross-platform mobile/web frontend

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
  "mode": "circuit",
  "warmup_count": 3,
  "main_count": 5,
  "cooldown_count": 3
}
```

Parameters:
- `num_people` (int, 1-50): Number of participants
- `difficulty` (string): `easy`, `medium`, or `hard`
- `rest_time` (int, 10-300): Rest time between exercises in seconds
- `mode` (string): `circuit` (different exercises per person) or `common` (same for all)
- `warmup_count` (int, 1-10, default 3): Number of warmup exercises
- `main_count` (int, 1-20, default 5): Number of main exercises
- `cooldown_count` (int, 1-10, default 3): Number of cooldown exercises

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
├── app/                       # Backend (Python/FastAPI)
│   ├── __init__.py
│   ├── main.py                # FastAPI application
│   ├── agent.py               # LangGraph workflow
│   └── models/
│       ├── __init__.py
│       └── exercise.py        # Pydantic models
├── frontend/                  # Frontend (Flutter)
│   ├── lib/
│   │   ├── main.dart          # App entry point
│   │   ├── models/            # Data models
│   │   ├── screens/           # UI screens
│   │   └── services/          # API service
│   └── pubspec.yaml           # Flutter dependencies
├── data/
│   └── exercises.json         # Exercise definitions (100 exercises)
├── docker-compose.yml         # Qdrant + Ollama services
├── seed_database.py           # Database seeding script
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project configuration
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

The system includes **100 pre-defined exercises** in `data/exercises.json`:

- **Warmup (20)**: Jumping Jacks, High Knees, Butt Kicks, Arm Circles, and more
- **Main - Easy (20)**: Classic Squat, Knee Push-ups, Plank, Wall Sit, and more
- **Main - Medium (20)**: Classic Push-ups, Walking Lunges, Kettlebell Swing, and more
- **Main - Hard (20)**: Burpees, Diamond Push-ups, Pistol Squats, Muscle-ups, and more
- **Cooldown (20)**: Child's Pose, Couch Stretch, Bar Hang, Cat-Cow Stretch, and more

### Custom Exercise File

You can modify `data/exercises.json` to add your own exercises or use a custom file:

```bash
# Use default file (data/exercises.json)
python seed_database.py

# Use custom file
python seed_database.py --file /path/to/my-exercises.json
```

Exercise file format:
```json
{
  "exercises": [
    {
      "id": "w1",
      "name": "Jumping Jacks",
      "type": "warmup",
      "level": "easy",
      "desc": "Jump with arm swings. Great cardio warmup."
    }
  ]
}
```

Fields:
- `id`: Unique identifier (e.g., "w1", "m_e1", "c5")
- `name`: Exercise name
- `type`: Category - `warmup`, `main`, or `cooldown`
- `level`: Difficulty - `easy`, `medium`, or `hard`
- `desc`: Brief description for trainers

## Flutter Frontend

The project includes a cross-platform mobile/web app built with Flutter.

### Prerequisites

- Flutter SDK 3.0+: https://flutter.dev/docs/get-started/install

### Running the Frontend

```bash
cd frontend

# Get dependencies
flutter pub get

# Run on web
flutter run -d chrome

# Run on Android emulator
flutter run -d android

# Run on iOS simulator (macOS only)
flutter run -d ios
```

### Backend Connection

The app automatically detects the backend URL:
- **Web**: `http://localhost:8000`
- **Android Emulator**: `http://10.0.2.2:8000` (host machine alias)
- **iOS/Desktop**: `http://localhost:8000`

### Building for Production

```bash
# Web (outputs to frontend/build/web)
flutter build web

# Android APK
flutter build apk

# iOS (macOS only)
flutter build ios
```

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
