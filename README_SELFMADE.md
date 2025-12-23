# TrenerAI - Poradnik Rozwoju Projektu

Ten dokument opisuje jak samodzielnie rozwijać projekt TrenerAI.

---

## Spis treści

1. [Struktura projektu](#struktura-projektu)
2. [Uruchomienie środowiska](#uruchomienie-środowiska)
3. [Testowanie bez frontendu](#testowanie-bez-frontendu)
4. [Dodawanie nowej komendy czatu](#dodawanie-nowej-komendy-czatu)
5. [Dodawanie nowego endpointu API](#dodawanie-nowego-endpointu-api)
6. [Praca z bazą danych](#praca-z-bazą-danych)
7. [Praca z LLM (Ollama/OpenAI)](#praca-z-llm)
8. [Debugowanie](#debugowanie)
9. [Częste problemy](#częste-problemy)

---

## Struktura projektu

```
app/
├── main.py              # Główna aplikacja FastAPI (punkt wejścia)
├── agent.py             # LangGraph agent (generowanie planów treningowych)
│
├── api/                 # Endpointy REST API
│   ├── __init__.py      # Agreguje wszystkie routery
│   ├── chat.py          # POST /chat - główny czat
│   ├── clients.py       # CRUD /clients - zarządzanie klientami
│   ├── workouts.py      # CRUD /workouts - zapisane treningi
│   ├── trainings.py     # /generate-training - generowanie planów
│   ├── users.py         # /api/users - użytkownicy w bazie
│   └── feedback.py      # /api/feedback - oceny treningów
│
├── commands/            # System komend czatu (regex, bez LLM)
│   ├── types.py         # CommandType enum + dataclasses
│   ├── parser.py        # Regex patterns - rozpoznawanie komend
│   ├── executor.py      # Wykonywanie komend
│   └── session.py       # Stan sesji (pending confirmations)
│
├── services/            # Logika biznesowa
│   └── chat_service.py  # Obsługa czatu
│
├── schemas/             # Modele Pydantic (walidacja danych)
│   └── __init__.py      # Wszystkie schematy request/response
│
├── storage/             # Przechowywanie danych (JSON)
│   └── __init__.py      # load_clients, save_clients, etc.
│
├── core/                # Konfiguracja
│   └── __init__.py      # Settings, logging
│
└── database/            # SQLAlchemy (Postgres)
    ├── __init__.py
    └── models.py        # User, GeneratedTraining, Feedback
```

---

## Uruchomienie środowiska

### Wymagania
```bash
# Python 3.10+
python --version

# Zainstaluj zależności
pip install -r requirements.txt
```

### Uruchom usługi (Docker)
```bash
# Qdrant (baza wektorowa) + Postgres
docker-compose up -d

# Sprawdź czy działają
docker ps
```

### Uruchom backend
```bash
# Development mode (auto-reload przy zmianach)
uvicorn app.main:app --reload

# Backend dostępny na:
# http://localhost:8000        - API
# http://localhost:8000/docs   - Swagger UI (testowanie w przeglądarce)
```

### Zmienne środowiskowe (.env)
```bash
# LLM Provider
LLM_PROVIDER=ollama          # lub "openai"
LLM_MODEL=llama3.2           # lub "gpt-4o"
OLLAMA_BASE_URL=http://localhost:11434

# Bazy danych
QDRANT_URL=http://localhost:6333
DATABASE_URL=postgresql://trainer:trainer123@localhost:5432/trenerai
```

---

## Testowanie bez frontendu

### Opcja 1: Swagger UI (najprostsza)
1. Otwórz `http://localhost:8000/docs`
2. Kliknij na endpoint
3. Kliknij "Try it out"
4. Wpisz dane i kliknij "Execute"

### Opcja 2: Skrypt testowy
```bash
# Testy automatyczne
python scripts/test_api.py

# Tryb interaktywny (rozmowa z AI)
python scripts/test_api.py -i
```

### Opcja 3: curl
```bash
# Test czatu
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "lista klientów", "session_id": "test1"}'

# Test generowania treningu
curl -X POST http://localhost:8000/generate-training \
  -H "Content-Type: application/json" \
  -d '{
    "num_people": 3,
    "difficulty": "medium",
    "rest_time": 60,
    "mode": "circuit"
  }'
```

### Opcja 4: HTTPie (czytelniejszy curl)
```bash
pip install httpie

http POST localhost:8000/chat message="dodaj Jana 30 lat"
```

### Opcja 5: Python requests
```python
import requests

r = requests.post("http://localhost:8000/chat", json={
    "message": "lista klientów"
})
print(r.json())
```

---

## Dodawanie nowej komendy czatu

Przykład: dodajemy komendę **"statystyki"** która pokazuje podsumowanie.

### Krok 1: Dodaj typ komendy

Plik: `app/commands/types.py`
```python
class CommandType(str, Enum):
    # ... istniejące typy
    STATS = "STATS"  # <- DODAJ TO
```

### Krok 2: Dodaj regex pattern

Plik: `app/commands/parser.py`
```python
COMMAND_PATTERNS: List[Tuple[str, CommandType, Callable]] = [
    # ... istniejące patterny

    # DODAJ TO:
    (r'^(?:statystyki|stats|podsumowanie)$', CommandType.STATS, lambda m: {}),
]
```

**Wyjaśnienie regex:**
- `^` - początek tekstu
- `(?:...|...|...)` - jedna z opcji (statystyki LUB stats LUB podsumowanie)
- `$` - koniec tekstu

### Krok 3: Dodaj handler

Plik: `app/commands/executor.py`
```python
class CommandExecutor:
    def execute(self, command: ParsedCommand, session_id: str) -> CommandResult:
        handlers = {
            # ... istniejące handlery
            CommandType.STATS: self._stats,  # <- DODAJ TO
        }
        # ...

    # DODAJ TĘ METODĘ:
    def _stats(self, data: dict, session_id: str) -> CommandResult:
        """Pokaż statystyki klientów."""
        from app.storage import load_clients

        clients = load_clients()
        total = len(clients)

        if total == 0:
            return CommandResult(
                success=True,
                message="Brak klientów w bazie."
            )

        avg_age = sum(c['age'] for c in clients) / total
        avg_weight = sum(c['weight'] for c in clients) / total

        message = f"""## 📊 Statystyki

| Metryka | Wartość |
|---------|---------|
| Liczba klientów | {total} |
| Średni wiek | {avg_age:.1f} lat |
| Średnia waga | {avg_weight:.1f} kg |
"""

        return CommandResult(
            success=True,
            message=message,
            data={"total": total, "avg_age": avg_age, "avg_weight": avg_weight}
        )
```

### Krok 4: Testuj
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "statystyki"}'
```

---

## Dodawanie nowego endpointu API

Przykład: endpoint **GET /api/stats** zwracający statystyki.

### Krok 1: Utwórz router (lub dodaj do istniejącego)

Plik: `app/api/stats.py` (nowy plik)
```python
from fastapi import APIRouter
from app.storage import load_clients

router = APIRouter(prefix="/api", tags=["Statistics"])


@router.get("/stats")
def get_stats():
    """Zwróć statystyki systemu."""
    clients = load_clients()

    return {
        "total_clients": len(clients),
        "avg_age": sum(c['age'] for c in clients) / len(clients) if clients else 0,
    }
```

### Krok 2: Zarejestruj router

Plik: `app/api/__init__.py`
```python
from app.api.stats import router as stats_router  # <- DODAJ IMPORT

api_router = APIRouter()
# ... inne routery
api_router.include_router(stats_router)  # <- DODAJ TO
```

### Krok 3: Testuj
```bash
curl http://localhost:8000/api/stats
```

---

## Praca z bazą danych

### Modele SQLAlchemy

Plik: `app/database/models.py`
```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String)
    # ...
```

### Migracje (Alembic)
```bash
# Wygeneruj migrację po zmianie modelu
alembic revision --autogenerate -m "Add new field"

# Zastosuj migracje
alembic upgrade head
```

### Używanie w endpointach
```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db, User

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

---

## Praca z LLM

### Gdzie używany jest LLM

1. **Generowanie planów treningowych** - `app/agent.py` (LangGraph)
2. **Odpowiedzi na pytania ogólne** - `app/api/chat.py` (RAG)

### Konfiguracja

```bash
# Ollama (lokalne, darmowe)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI (płatne, lepsze)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
```

### Testowanie odpowiedzi LLM
```bash
# Pytanie które idzie do RAG/LLM (nie jest komendą)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "jakie ćwiczenia na plecy polecasz?"}'
```

### Ważna zasada: Komendy vs LLM

| Typ | Obsługa | Przykład |
|-----|---------|----------|
| Komenda | Regex (deterministyczne) | "dodaj Jana 30 lat" |
| Pytanie | LLM + RAG | "jakie ćwiczenia na plecy?" |

**Komendy NIE używają LLM** - są szybkie i przewidywalne.

---

## Debugowanie

### Logi
```bash
# Logi backendu widoczne w terminalu gdzie działa uvicorn
uvicorn app.main:app --reload

# Szukaj linii zaczynających się od:
# INFO:app.api.chat - informacje o requestach
# ERROR:... - błędy
```

### Sprawdź konfigurację
```bash
curl http://localhost:8000/debug/config
```

### Sprawdź czy Qdrant działa
```bash
curl http://localhost:6333/collections
```

### Sprawdź czy Ollama działa
```bash
curl http://localhost:11434/api/tags
```

---

## Częste problemy

### "Connection refused" na localhost:8000
```bash
# Backend nie jest uruchomiony
uvicorn app.main:app --reload
```

### "Collection not found" w Qdrant
```bash
# Załaduj ćwiczenia do bazy wektorowej
python scripts/load_exercises.py
```

### "Model not found" w Ollama
```bash
# Pobierz model
ollama pull llama3.2
```

### Zmiany w kodzie nie działają
```bash
# Upewnij się że używasz --reload
uvicorn app.main:app --reload

# Lub zrestartuj ręcznie (Ctrl+C i uruchom ponownie)
```

### Błędy importu
```bash
# Upewnij się że jesteś w głównym katalogu projektu
cd /path/to/TrenerAI
python -c "from app.main import app; print('OK')"
```

---

## Checklisty

### Przed commitem
- [ ] Backend się uruchamia (`uvicorn app.main:app`)
- [ ] Endpoint działa (curl / Swagger)
- [ ] Brak błędów w logach

### Nowa komenda czatu
- [ ] Typ w `commands/types.py`
- [ ] Pattern w `commands/parser.py`
- [ ] Handler w `commands/executor.py`
- [ ] Test curl

### Nowy endpoint API
- [ ] Router w `app/api/`
- [ ] Zarejestrowany w `app/api/__init__.py`
- [ ] Schema w `app/schemas/` (jeśli potrzebna)
- [ ] Test curl

---

## Przydatne linki

- FastAPI docs: https://fastapi.tiangolo.com/
- Pydantic docs: https://docs.pydantic.dev/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- LangGraph docs: https://python.langchain.com/docs/langgraph
