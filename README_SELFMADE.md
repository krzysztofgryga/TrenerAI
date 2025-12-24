# TrenerAI - Kompletny Poradnik Rozwoju Projektu

Ten dokument opisuje jak samodzielnie rozwijać projekt TrenerAI - od podstaw po zaawansowane funkcjonalności.

---

## Spis treści

1. [Struktura projektu](#struktura-projektu)
2. [Architektura i przepływ danych](#architektura-i-przepływ-danych)
3. [Uruchomienie środowiska](#uruchomienie-środowiska)
4. [Docker i docker-compose](#docker-i-docker-compose)
5. [Testowanie bez frontendu](#testowanie-bez-frontendu)
6. [System komend czatu](#system-komend-czatu)
7. [Dodawanie nowej komendy czatu](#dodawanie-nowej-komendy-czatu)
8. [Regex - jak pisać wzorce](#regex---jak-pisać-wzorce)
9. [Flow potwierdzania akcji](#flow-potwierdzania-akcji)
10. [Dodawanie nowego endpointu API](#dodawanie-nowego-endpointu-api)
11. [Schematy Pydantic](#schematy-pydantic)
12. [Praca z bazą danych Postgres](#praca-z-bazą-danych-postgres)
13. [Praca z JSON storage](#praca-z-json-storage)
14. [LangGraph Agent](#langgraph-agent)
15. [Qdrant i RAG](#qdrant-i-rag)
16. [Praca z LLM](#praca-z-llm)
17. [Obsługa błędów](#obsługa-błędów)
18. [Debugowanie](#debugowanie)
19. [Bezpieczeństwo](#bezpieczeństwo)
20. [Git workflow](#git-workflow)
21. [Częste problemy i rozwiązania](#częste-problemy-i-rozwiązania)
22. [Checklisty](#checklisty)
23. [Przydatne linki](#przydatne-linki)

---

## Struktura projektu

```
TrenerAI/
├── app/                     # Główny kod aplikacji
│   ├── main.py              # Punkt wejścia FastAPI (~150 linii)
│   ├── agent.py             # LangGraph agent (generowanie planów)
│   │
│   ├── api/                 # Endpointy REST API (routery FastAPI)
│   │   ├── __init__.py      # Agreguje wszystkie routery → api_router
│   │   ├── chat.py          # POST /chat - główny czat z AI
│   │   ├── clients.py       # CRUD /clients - zarządzanie klientami (JSON)
│   │   ├── workouts.py      # CRUD /workouts - zapisane treningi (JSON)
│   │   ├── trainings.py     # /generate-training + /api/trainings (Postgres)
│   │   ├── users.py         # /api/users - użytkownicy w DB
│   │   └── feedback.py      # /api/feedback - oceny treningów
│   │
│   ├── commands/            # System komend czatu (deterministyczny, regex)
│   │   ├── __init__.py      # Eksportuje publiczne API modułu
│   │   ├── types.py         # CommandType enum, ParsedCommand, CommandResult
│   │   ├── parser.py        # COMMAND_PATTERNS - regex do rozpoznawania
│   │   ├── executor.py      # CommandExecutor - wykonuje komendy
│   │   └── session.py       # PendingAction, PENDING_ACTIONS - stan sesji
│   │
│   ├── services/            # Logika biznesowa (warstwa pośrednia)
│   │   ├── __init__.py
│   │   └── chat_service.py  # ChatService - obsługa czatu
│   │
│   ├── schemas/             # Modele Pydantic (walidacja request/response)
│   │   └── __init__.py      # Wszystkie schematy w jednym miejscu
│   │
│   ├── storage/             # Przechowywanie danych w plikach JSON
│   │   └── __init__.py      # load_clients, save_clients, load_workouts...
│   │
│   ├── core/                # Konfiguracja aplikacji
│   │   └── __init__.py      # Settings dataclass, setup_logging()
│   │
│   └── database/            # SQLAlchemy ORM (Postgres)
│       ├── __init__.py      # get_db, init_db, SessionLocal
│       └── models.py        # User, GeneratedTraining, Feedback
│
├── data/                    # Dane JSON (clients.json, workouts.json)
├── scripts/                 # Skrypty pomocnicze
│   ├── test_api.py          # Testowanie API bez frontendu
│   └── load_exercises.py    # Ładowanie ćwiczeń do Qdrant
├── alembic/                 # Migracje bazy danych
├── docker-compose.yml       # Definicja kontenerów Docker
├── requirements.txt         # Zależności Python
└── .env                     # Zmienne środowiskowe (nie commitować!)
```

---

## Architektura i przepływ danych

### Warstwy aplikacji

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│                   (React / przeglądarka)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP Request
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER (app/api/)                    │
│  Routery FastAPI - walidacja, routing, response             │
│  chat.py, clients.py, trainings.py, users.py, feedback.py   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  SERVICES LAYER (app/services/)              │
│  Logika biznesowa - ChatService                              │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    COMMANDS     │  │   LANGGRAPH     │  │      RAG        │
│  (app/commands/)│  │  (app/agent.py) │  │   (Qdrant)      │
│  Regex parser   │  │  Plan generator │  │  Vector search  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
              │               │               │
              ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ JSON Storage │  │   Postgres   │  │    Qdrant    │       │
│  │ (clients,    │  │ (users,      │  │ (exercises   │       │
│  │  workouts)   │  │  trainings)  │  │  embeddings) │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Flow wiadomości czatu

```
Użytkownik: "dodaj Jana 30 lat"
                │
                ▼
┌───────────────────────────────────────┐
│ 1. Czy to potwierdzenie? (tak/nie)   │ ← session.py: is_confirmation()
│    NIE → idź dalej                    │
└───────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ 2. Czy pasuje do regex komendy?      │ ← parser.py: parse_command()
│    TAK → CommandType.CREATE_USER      │
└───────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ 3. Wykonaj komendę                   │ ← executor.py: execute()
│    → Zapisz PendingAction             │
│    → Zwróć "Czy potwierdzasz?"        │
└───────────────────────────────────────┘
                │
                ▼
Użytkownik: "tak"
                │
                ▼
┌───────────────────────────────────────┐
│ 1. Czy to potwierdzenie?             │
│    TAK → execute_pending()            │
│    → Zapisz do JSON/DB                │
│    → Zwróć "Dodano Jana"              │
└───────────────────────────────────────┘
```

### Flow pytania ogólnego (RAG)

```
Użytkownik: "jakie ćwiczenia na plecy?"
                │
                ▼
┌───────────────────────────────────────┐
│ 1. Czy to potwierdzenie? NIE         │
│ 2. Czy pasuje do regex? NIE          │
└───────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ 3. RAG: Szukaj w Qdrant              │
│    → similarity_search("plecy", k=10) │
│    → Znajdź podobne ćwiczenia         │
└───────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ 4. LLM: Wygeneruj odpowiedź          │
│    → Prompt + kontekst z Qdrant       │
│    → Ollama/OpenAI generuje tekst     │
└───────────────────────────────────────┘
```

---

## Uruchomienie środowiska

### Wymagania systemowe

```bash
# Python 3.10 lub nowszy
python --version  # Python 3.10+

# Docker i Docker Compose
docker --version
docker-compose --version

# Ollama (opcjonalne, jeśli używasz lokalnego LLM)
ollama --version
```

### Instalacja krok po kroku

```bash
# 1. Sklonuj repozytorium
git clone <url-repo>
cd TrenerAI

# 2. Utwórz virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub: venv\Scripts\activate  # Windows

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Skopiuj plik konfiguracyjny
cp .env.example .env
# Edytuj .env według potrzeb

# 5. Uruchom kontenery Docker
docker-compose up -d

# 6. Załaduj ćwiczenia do Qdrant (jednorazowo)
python scripts/load_exercises.py

# 7. Uruchom backend
uvicorn app.main:app --reload
```

### Zmienne środowiskowe (.env)

```bash
# ==========================
# LLM Configuration
# ==========================

# Provider: "ollama" (lokalne, darmowe) lub "openai" (płatne)
LLM_PROVIDER=ollama

# Model do użycia
LLM_MODEL=llama3.2           # dla Ollama
# LLM_MODEL=gpt-4o           # dla OpenAI

# Ollama URL (jeśli używasz Ollama)
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI API Key (jeśli używasz OpenAI)
# OPENAI_API_KEY=sk-...

# ==========================
# Database Configuration
# ==========================

# Qdrant (baza wektorowa)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=gym_exercises

# PostgreSQL
DATABASE_URL=postgresql://trainer:trainer123@localhost:5432/trenerai

# ==========================
# App Configuration
# ==========================

# Środowisko: development, production
ENVIRONMENT=development

# Poziom logowania: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

---

## Docker i docker-compose

### docker-compose.yml - wyjaśnienie

```yaml
version: '3.8'

services:
  # Qdrant - baza wektorowa do RAG
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"    # REST API
      - "6334:6334"    # gRPC
    volumes:
      - qdrant_data:/qdrant/storage
    # Dane przechowywane w Docker volume

  # PostgreSQL - relacyjna baza danych
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: trainer
      POSTGRES_PASSWORD: trainer123
      POSTGRES_DB: trenerai
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  qdrant_data:     # Persystentne dane Qdrant
  postgres_data:   # Persystentne dane Postgres
```

### Przydatne komendy Docker

```bash
# Uruchom wszystkie kontenery
docker-compose up -d

# Zobacz logi kontenerów
docker-compose logs -f

# Logi konkretnego kontenera
docker-compose logs -f qdrant
docker-compose logs -f postgres

# Zatrzymaj kontenery
docker-compose down

# Zatrzymaj i usuń dane (UWAGA: kasuje dane!)
docker-compose down -v

# Restart konkretnego kontenera
docker-compose restart qdrant

# Sprawdź status kontenerów
docker-compose ps

# Wejdź do kontenera Postgres
docker-compose exec postgres psql -U trainer -d trenerai
```

### Sprawdzanie czy usługi działają

```bash
# Qdrant
curl http://localhost:6333/collections
# Oczekiwana odpowiedź: {"result":{"collections":[...]}}

# Postgres
docker-compose exec postgres pg_isready -U trainer
# Oczekiwana odpowiedź: accepting connections

# Ollama (jeśli używasz)
curl http://localhost:11434/api/tags
# Oczekiwana odpowiedź: {"models":[...]}
```

---

## Testowanie bez frontendu

### Swagger UI (najłatwiejsze)

1. Uruchom backend: `uvicorn app.main:app --reload`
2. Otwórz w przeglądarce: `http://localhost:8000/docs`
3. Kliknij na endpoint → "Try it out" → wpisz dane → "Execute"

**Zalety:** wizualne, pokazuje schematy, waliduje dane

### Skrypt testowy (scripts/test_api.py)

```bash
# Testy automatyczne - sprawdza podstawowe endpointy
python scripts/test_api.py

# Tryb interaktywny - rozmowa z AI jak w chacie
python scripts/test_api.py -i
```

### curl - wszystkie endpointy

```bash
# ================================
# HEALTH & DEBUG
# ================================

# Status API
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# Konfiguracja (debug)
curl http://localhost:8000/debug/config

# ================================
# CHAT
# ================================

# Podstawowa wiadomość
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "cześć", "session_id": "test1"}'

# Komenda - lista klientów
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "lista klientów"}'

# Komenda - dodaj klienta (wymaga potwierdzenia)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "dodaj Jana 30 lat", "session_id": "sess1"}'

# Potwierdź (ta sama sesja!)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "tak", "session_id": "sess1"}'

# Pytanie do LLM (RAG)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "jakie ćwiczenia na plecy polecasz?"}'

# ================================
# CLIENTS (JSON storage)
# ================================

# Lista wszystkich klientów
curl http://localhost:8000/clients

# Dodaj klienta
curl -X POST http://localhost:8000/clients \
  -H "Content-Type: application/json" \
  -d '{
    "id": "1",
    "name": "Jan Kowalski",
    "age": 30,
    "weight": 80,
    "goal": "Budowa masy",
    "notes": "",
    "createdAt": "2024-01-15",
    "progress": []
  }'

# Aktualizuj klienta
curl -X PUT http://localhost:8000/clients/1 \
  -H "Content-Type: application/json" \
  -d '{
    "id": "1",
    "name": "Jan Kowalski",
    "age": 31,
    "weight": 82,
    "goal": "Budowa masy",
    "notes": "Zwiększona waga",
    "createdAt": "2024-01-15",
    "progress": []
  }'

# Usuń klienta
curl -X DELETE http://localhost:8000/clients/1

# ================================
# WORKOUTS (JSON storage)
# ================================

# Lista treningów
curl http://localhost:8000/workouts

# Dodaj trening
curl -X POST http://localhost:8000/workouts \
  -H "Content-Type: application/json" \
  -d '{
    "id": "w1",
    "clientId": "1",
    "title": "Trening pleców",
    "content": "1. Martwy ciąg...",
    "date": "2024-01-20"
  }'

# Usuń trening
curl -X DELETE http://localhost:8000/workouts/w1

# ================================
# GENERATE TRAINING (LangGraph)
# ================================

# Wygeneruj plan (bez zapisu do DB)
curl -X POST http://localhost:8000/generate-training \
  -H "Content-Type: application/json" \
  -d '{
    "num_people": 3,
    "difficulty": "medium",
    "rest_time": 60,
    "mode": "circuit",
    "warmup_count": 3,
    "main_count": 5,
    "cooldown_count": 3
  }'

# ================================
# DATABASE ENDPOINTS (Postgres)
# ================================

# Utwórz użytkownika
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jan@example.com",
    "name": "Jan Kowalski",
    "age": 30,
    "weight": 80,
    "height": 180,
    "goals": "Budowa masy mięśniowej",
    "preferred_difficulty": "medium"
  }'

# Lista użytkowników
curl http://localhost:8000/api/users

# Pobierz użytkownika po ID
curl http://localhost:8000/api/users/1

# Wygeneruj i zapisz trening
curl -X POST "http://localhost:8000/api/trainings?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "num_people": 1,
    "difficulty": "medium",
    "rest_time": 60,
    "mode": "common"
  }'

# Pobierz trening po ID
curl http://localhost:8000/api/trainings/1

# Treningi użytkownika
curl http://localhost:8000/api/users/1/trainings

# Dodaj feedback
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "training_id": 1,
    "rating": 4,
    "comment": "Dobry trening, ale za krótka rozgrzewka",
    "was_too_hard": false,
    "was_too_easy": false
  }'

# Pobierz feedback
curl http://localhost:8000/api/feedback/1
```

### HTTPie (czytelniejsza alternatywa dla curl)

```bash
pip install httpie

# Proste wywołania
http localhost:8000/health
http POST localhost:8000/chat message="lista klientów"
http localhost:8000/clients
```

### Python requests

```python
import requests
import json

BASE = "http://localhost:8000"

# Chat
r = requests.post(f"{BASE}/chat", json={"message": "lista klientów"})
print(json.dumps(r.json(), indent=2, ensure_ascii=False))

# Generate training
r = requests.post(f"{BASE}/generate-training", json={
    "num_people": 3,
    "difficulty": "medium",
    "rest_time": 60,
    "mode": "circuit"
})
print(json.dumps(r.json(), indent=2, ensure_ascii=False))
```

---

## System komend czatu

### Filozofia

**Komendy są deterministyczne** - używają regex, NIE LLM:
- Szybkie (brak opóźnienia LLM)
- Przewidywalne (zawsze ten sam wynik)
- Niezawodne (nie "halucynują")

**LLM tylko do pytań otwartych** - gdy regex nie pasuje:
- "Jakie ćwiczenia na plecy?"
- "Opisz technikę martwego ciągu"

### Istniejące typy komend

```python
class CommandType(str, Enum):
    HELP = "HELP"              # pomoc, help, ?
    CREATE_USER = "CREATE_USER"    # dodaj Jana 30 lat
    LIST_USERS = "LIST_USERS"      # lista klientów
    SHOW_USER = "SHOW_USER"        # pokaż Jana
    DELETE_USER = "DELETE_USER"    # usuń Jana
    CREATE_TRAINING = "CREATE_TRAINING"  # stwórz trening...
    NONE = "NONE"              # brak komendy → idź do LLM
```

### Jak działa parser

```python
# app/commands/parser.py

COMMAND_PATTERNS = [
    # (regex, typ_komendy, funkcja_ekstrakcji_danych)
    (r'^(?:pomoc|help|\?)$', CommandType.HELP, lambda m: {}),
    (r'(?:dodaj|utwórz).*?([A-Z][a-z]+).*?(\d+)\s*lat', CommandType.CREATE_USER, extract_user),
    # ...
]

def parse_command(message: str) -> ParsedCommand:
    for pattern, cmd_type, extractor in COMMAND_PATTERNS:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return ParsedCommand(
                command=cmd_type,
                data=extractor(match),
                original_message=message
            )
    return ParsedCommand(command=CommandType.NONE, data={}, original_message=message)
```

---

## Dodawanie nowej komendy czatu

### Przykład: komenda "statystyki"

#### Krok 1: Typ komendy

Plik: `app/commands/types.py`
```python
class CommandType(str, Enum):
    # ... istniejące
    STATS = "STATS"  # NOWE
```

#### Krok 2: Regex pattern

Plik: `app/commands/parser.py`
```python
COMMAND_PATTERNS = [
    # ... istniejące

    # NOWE - akceptuje: statystyki, stats, podsumowanie
    (r'^(?:statystyki|stats|podsumowanie)$', CommandType.STATS, lambda m: {}),
]
```

#### Krok 3: Handler

Plik: `app/commands/executor.py`
```python
class CommandExecutor:
    def execute(self, command: ParsedCommand, session_id: str) -> CommandResult:
        handlers = {
            # ... istniejące
            CommandType.STATS: self._stats,  # NOWE
        }
        handler = handlers.get(command.command)
        if handler:
            return handler(command.data, session_id)
        return CommandResult(success=False, message="Nieznana komenda")

    # NOWA METODA
    def _stats(self, data: dict, session_id: str) -> CommandResult:
        from app.storage import load_clients

        clients = load_clients()
        total = len(clients)

        if total == 0:
            return CommandResult(success=True, message="Brak klientów w bazie.")

        avg_age = sum(c['age'] for c in clients) / total
        avg_weight = sum(c['weight'] for c in clients) / total

        message = f"""## 📊 Statystyki

| Metryka | Wartość |
|---------|---------|
| Liczba klientów | {total} |
| Średni wiek | {avg_age:.1f} lat |
| Średnia waga | {avg_weight:.1f} kg |"""

        return CommandResult(
            success=True,
            message=message,
            data={"total": total, "avg_age": avg_age, "avg_weight": avg_weight}
        )
```

#### Krok 4: Test

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "statystyki"}'
```

---

## Regex - jak pisać wzorce

### Podstawy

```python
# Dopasowania
^           # początek tekstu
$           # koniec tekstu
.           # dowolny znak (oprócz newline)
\s          # biały znak (spacja, tab)
\d          # cyfra [0-9]
\w          # litera, cyfra lub _

# Kwantyfikatory
*           # 0 lub więcej
+           # 1 lub więcej
?           # 0 lub 1
{n}         # dokładnie n
{n,m}       # od n do m

# Grupy
(abc)       # grupa przechwytująca - match.group(1)
(?:abc)     # grupa nieprzechwytująca
(?:a|b|c)   # alternatywa: a LUB b LUB c

# Klasy znaków
[abc]       # a lub b lub c
[a-z]       # mała litera
[A-Z]       # wielka litera
[A-ZĄĆĘŁŃÓŚŹŻ]  # wielka litera + polskie znaki
```

### Przykłady z projektu

```python
# Pomoc - dokładne dopasowanie
r'^(?:pomoc|help|\?)$'
# Pasuje: "pomoc", "help", "?"
# Nie pasuje: "pomoc mi", "help me"

# Dodaj użytkownika
r'(?:dodaj|utwórz|nowy)\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)'
# Pasuje: "dodaj Jana", "utwórz Kowalski", "nowy Tomek"
# Grupa 1: imię (Jan, Kowalski, Tomek)

# Wiek
r'(\d+)\s*(?:lat|lata|roku|lat)'
# Pasuje: "30 lat", "25lat", "45 lata"
# Grupa 1: wiek (30, 25, 45)

# Lista
r'^(?:lista|pokaż|wyświetl)\s+(?:klientów|podopiecznych|użytkowników)$'
# Pasuje: "lista klientów", "pokaż podopiecznych"
```

### Testowanie regex online

- https://regex101.com/ - najlepsze narzędzie
- Wybierz "Python" jako flavor
- Wklej pattern i testowe teksty

### Funkcja ekstrakcji danych

```python
def extract_user_data(match) -> dict:
    """Ekstrakcja danych z regex match."""
    text = match.group(1)  # Cały dopasowany tekst po "dodaj"

    # Domyślne wartości
    data = {"name": "Nieznany", "age": 25, "weight": 70.0}

    # Szukaj imienia (wielka litera na początku)
    name_match = re.search(r'([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)', text)
    if name_match:
        data["name"] = name_match.group(1)

    # Szukaj wieku
    age_match = re.search(r'(\d+)\s*lat', text)
    if age_match:
        data["age"] = int(age_match.group(1))

    # Szukaj wagi
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*kg', text)
    if weight_match:
        data["weight"] = float(weight_match.group(1))

    return data
```

---

## Flow potwierdzania akcji

### Dlaczego potwierdzenia?

Operacje destrukcyjne (usuwanie) lub tworzące dane wymagają potwierdzenia, żeby uniknąć przypadkowych akcji.

### Jak to działa

```python
# app/commands/session.py

@dataclass
class PendingAction:
    command: str              # np. "CREATE_USER"
    data: dict                # dane do wykonania
    message: str              # co pokazać użytkownikowi
    created_at: datetime
    expires_at: datetime      # wygasa po 5 minutach

# Globalne store (w pamięci)
PENDING_ACTIONS: Dict[str, PendingAction] = {}

def set_pending_action(session_id: str, action: PendingAction):
    PENDING_ACTIONS[session_id] = action

def get_pending_action(session_id: str) -> Optional[PendingAction]:
    action = PENDING_ACTIONS.get(session_id)
    if action and datetime.now() < action.expires_at:
        return action
    return None

def clear_pending_action(session_id: str):
    PENDING_ACTIONS.pop(session_id, None)

def is_confirmation(message: str) -> Optional[bool]:
    """Sprawdź czy wiadomość to potwierdzenie."""
    msg = message.lower().strip()
    if msg in ['tak', 'yes', 'ok', 'potwierdź', 't', 'y']:
        return True
    if msg in ['nie', 'no', 'anuluj', 'cancel', 'n']:
        return False
    return None  # Nie jest potwierdzeniem
```

### Flow w executor

```python
def _create_user(self, data: dict, session_id: str) -> CommandResult:
    # Nie wykonuj od razu - zapisz jako pending
    action = PendingAction(
        command="CREATE_USER",
        data=data,
        message=f"Dodać {data['name']}, {data['age']} lat?",
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(minutes=5)
    )
    set_pending_action(session_id, action)

    return CommandResult(
        success=True,
        message=f"Czy potwierdzasz dodanie:\n- Imię: {data['name']}\n- Wiek: {data['age']}",
        needs_confirmation=True
    )

def execute_pending(self, session_id: str) -> CommandResult:
    """Wykonaj oczekującą akcję po potwierdzeniu."""
    action = get_pending_action(session_id)
    if not action:
        return CommandResult(success=False, message="Brak akcji do potwierdzenia")

    clear_pending_action(session_id)

    if action.command == "CREATE_USER":
        # Teraz naprawdę zapisz
        from app.storage import add_client
        client = add_client(action.data)
        return CommandResult(
            success=True,
            message=f"✓ Dodano: {client['name']}",
            data=client
        )
```

### Ważne: session_id

```bash
# Ta sama sesja - potwierdzenie działa
curl -X POST localhost:8000/chat -d '{"message": "dodaj Jana", "session_id": "abc123"}'
curl -X POST localhost:8000/chat -d '{"message": "tak", "session_id": "abc123"}'  # ✓

# Inna sesja - nie zadziała
curl -X POST localhost:8000/chat -d '{"message": "dodaj Jana", "session_id": "abc123"}'
curl -X POST localhost:8000/chat -d '{"message": "tak", "session_id": "xyz789"}'  # ✗
```

---

## Dodawanie nowego endpointu API

### Przykład: GET /api/stats

#### Krok 1: Utwórz router

Plik: `app/api/stats.py` (nowy)
```python
from fastapi import APIRouter
from app.storage import load_clients, load_workouts

router = APIRouter(prefix="/api", tags=["Statistics"])


@router.get("/stats")
def get_stats():
    """Zwróć statystyki systemu."""
    clients = load_clients()
    workouts = load_workouts()

    return {
        "clients": {
            "total": len(clients),
            "avg_age": sum(c['age'] for c in clients) / len(clients) if clients else 0,
        },
        "workouts": {
            "total": len(workouts),
        }
    }


@router.get("/stats/clients/{client_id}")
def get_client_stats(client_id: str):
    """Statystyki konkretnego klienta."""
    clients = load_clients()
    client = next((c for c in clients if c['id'] == client_id), None)

    if not client:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Klient nie znaleziony")

    workouts = load_workouts()
    client_workouts = [w for w in workouts if w.get('clientId') == client_id]

    return {
        "client": client,
        "workouts_count": len(client_workouts),
        "progress_entries": len(client.get('progress', []))
    }
```

#### Krok 2: Zarejestruj router

Plik: `app/api/__init__.py`
```python
from app.api.stats import router as stats_router  # DODAJ

api_router = APIRouter()
# ... inne
api_router.include_router(stats_router)  # DODAJ
```

#### Krok 3: Test

```bash
curl http://localhost:8000/api/stats
curl http://localhost:8000/api/stats/clients/1
```

---

## Schematy Pydantic

### Po co schematy?

- **Walidacja** - automatyczne sprawdzanie typów i ograniczeń
- **Dokumentacja** - Swagger pokazuje strukturę
- **Serializacja** - konwersja Python ↔ JSON

### Lokalizacja

Wszystkie schematy w: `app/schemas/__init__.py`

### Tworzenie schematu

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

# Request schema
class ClientCreate(BaseModel):
    """Schema do tworzenia klienta."""
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=1, le=120)  # ge=greater or equal
    weight: float = Field(..., ge=20, le=300)
    goal: str = Field(default="Poprawa kondycji")
    notes: Optional[str] = None

# Response schema (z bazy danych)
class ClientResponse(BaseModel):
    """Schema odpowiedzi - klient z bazy."""
    model_config = ConfigDict(from_attributes=True)  # Pozwala na ORM

    id: str
    name: str
    age: int
    weight: float
    goal: str
    notes: Optional[str]
    created_at: datetime

# Nested schema
class ProgressEntry(BaseModel):
    date: str
    weight: float
    body_fat: Optional[float] = None

class ClientWithProgress(ClientResponse):
    progress: List[ProgressEntry] = []
```

### Użycie w endpoincie

```python
from app.schemas import ClientCreate, ClientResponse

@router.post("/clients", response_model=ClientResponse)
def create_client(client: ClientCreate):  # Walidacja wejścia
    # client jest już zwalidowany
    # Pydantic automatycznie zwróci błąd 422 jeśli dane niepoprawne
    ...
    return saved_client  # Automatyczna serializacja
```

### Częste walidatory

```python
from pydantic import Field, field_validator

class UserCreate(BaseModel):
    email: str
    age: int = Field(ge=1, le=120)
    weight: float = Field(ge=20, le=500)
    difficulty: str = Field(pattern=r'^(easy|medium|hard)$')

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Niepoprawny email')
        return v.lower()
```

---

## Praca z bazą danych Postgres

### Modele SQLAlchemy

Plik: `app/database/models.py`
```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    age = Column(Integer)
    weight = Column(Float)
    height = Column(Float)
    goals = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacja do treningów
    trainings = relationship("GeneratedTraining", back_populates="user")


class GeneratedTraining(Base):
    __tablename__ = "generated_trainings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    input_params = Column(JSON)  # Parametry wejściowe
    plan = Column(JSON)          # Wygenerowany plan
    model_name = Column(String)  # Który model LLM
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="trainings")
    feedback = relationship("Feedback", back_populates="training", uselist=False)
```

### CRUD operacje

```python
from sqlalchemy.orm import Session
from app.database import User

# CREATE
def create_user(db: Session, email: str, name: str):
    user = User(email=email, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)  # Odśwież żeby dostać ID
    return user

# READ
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# UPDATE
def update_user(db: Session, user_id: int, **kwargs):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for key, value in kwargs.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user

# DELETE
def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
```

### Dependency Injection w FastAPI

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db

@router.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    # db jest automatycznie przekazywane przez FastAPI
    # i zamykane po zakończeniu requestu
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Migracje Alembic

```bash
# Struktura katalogów
alembic/
├── versions/          # Pliki migracji
├── env.py            # Konfiguracja
└── script.py.mako    # Template

# Inicjalizacja (jednorazowo)
alembic init alembic

# Po zmianie modelu - wygeneruj migrację
alembic revision --autogenerate -m "Add phone field to users"

# Zastosuj migracje
alembic upgrade head

# Cofnij ostatnią migrację
alembic downgrade -1

# Zobacz historię
alembic history

# Zobacz aktualną wersję
alembic current
```

### Dodawanie nowej tabeli

1. Dodaj model w `app/database/models.py`:
```python
class Diet(Base):
    __tablename__ = "diets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    calories = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. Wygeneruj migrację:
```bash
alembic revision --autogenerate -m "Add diets table"
```

3. Zastosuj:
```bash
alembic upgrade head
```

---

## Praca z JSON storage

### Lokalizacja

Plik: `app/storage/__init__.py`

Dane zapisywane w: `data/clients.json`, `data/workouts.json`

### Dostępne funkcje

```python
from app.storage import (
    # Klienci
    load_clients,      # -> List[dict]
    save_clients,      # (clients: List[dict]) -> None
    add_client,        # (data: dict) -> dict (z wygenerowanym ID)
    get_client_by_id,  # (client_id: str) -> Optional[dict]
    get_client_by_name,# (name: str) -> Optional[dict]
    update_client,     # (client_id: str, data: dict) -> Optional[dict]
    delete_client,     # (client_id: str) -> bool

    # Treningi
    load_workouts,
    save_workouts,
    add_workout,
    delete_workout,
)
```

### Przykład użycia

```python
from app.storage import load_clients, add_client, delete_client

# Pobierz wszystkich
clients = load_clients()
print(f"Mam {len(clients)} klientów")

# Dodaj nowego
new_client = add_client({
    "name": "Anna Nowak",
    "age": 28,
    "weight": 65.0,
    "goal": "Redukcja"
})
print(f"Dodano: {new_client['id']}")

# Usuń
deleted = delete_client(new_client['id'])
print(f"Usunięto: {deleted}")
```

### Struktura danych

```json
// data/clients.json
[
  {
    "id": "1703001234567",
    "name": "Jan Kowalski",
    "age": 30,
    "weight": 80.0,
    "goal": "Budowa masy",
    "notes": "",
    "createdAt": "15.01.2024",
    "progress": [
      {
        "id": "p1",
        "date": "2024-01-20",
        "weight": 81.5,
        "bodyFat": 18.5,
        "waist": 85
      }
    ]
  }
]
```

---

## LangGraph Agent

### Co to jest?

LangGraph to framework do budowania agentów AI jako grafów stanów. W TrenerAI używany do generowania planów treningowych.

### Lokalizacja

Plik: `app/agent.py`

### Jak działa

```python
# Uproszczony schemat

# 1. Stan agenta
class TrainingState(TypedDict):
    num_people: int
    difficulty: str
    mode: str
    retrieved_exercises: List[str]  # Z Qdrant
    final_plan: dict                # Wygenerowany plan

# 2. Węzły grafu (funkcje)
def retrieve_exercises(state: TrainingState) -> TrainingState:
    """Pobierz ćwiczenia z Qdrant."""
    exercises = vector_store.similarity_search(...)
    return {**state, "retrieved_exercises": exercises}

def generate_plan(state: TrainingState) -> TrainingState:
    """Wygeneruj plan używając LLM."""
    prompt = build_prompt(state)
    response = llm.invoke(prompt)
    plan = parse_response(response)
    return {**state, "final_plan": plan}

# 3. Graf
graph = StateGraph(TrainingState)
graph.add_node("retrieve", retrieve_exercises)
graph.add_node("generate", generate_plan)
graph.add_edge("retrieve", "generate")
graph.set_entry_point("retrieve")
graph.set_finish_point("generate")

app_graph = graph.compile()

# 4. Użycie
result = app_graph.invoke({
    "num_people": 3,
    "difficulty": "medium",
    "mode": "circuit"
})
plan = result["final_plan"]
```

### Modyfikowanie agenta

```python
# Dodanie nowego węzła

def validate_plan(state: TrainingState) -> TrainingState:
    """Waliduj wygenerowany plan."""
    plan = state["final_plan"]
    # ... walidacja
    return state

# Dodaj do grafu
graph.add_node("validate", validate_plan)
graph.add_edge("generate", "validate")
graph.set_finish_point("validate")
```

---

## Qdrant i RAG

### Co to jest?

- **Qdrant** - baza wektorowa (przechowuje embeddingi)
- **RAG** (Retrieval Augmented Generation) - pobierz kontekst z bazy, przekaż do LLM

### Jak to działa

```
1. Ładowanie ćwiczeń (jednorazowo):
   "Martwy ciąg" → [0.23, -0.45, 0.12, ...] (embedding)
   Zapisz w Qdrant

2. Pytanie użytkownika:
   "ćwiczenia na plecy" → [0.25, -0.43, 0.15, ...] (embedding)

3. Similarity search:
   Znajdź 10 najbliższych wektorów w Qdrant
   → Martwy ciąg, Wiosłowanie, Podciąganie...

4. Przekaż do LLM:
   "Mając te ćwiczenia: [lista], odpowiedz na: ćwiczenia na plecy?"
```

### Ładowanie danych do Qdrant

```bash
python scripts/load_exercises.py
```

```python
# scripts/load_exercises.py
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings

# Ćwiczenia do załadowania
exercises = [
    {"name": "Martwy ciąg", "muscles": "plecy, pośladki", "difficulty": "hard"},
    {"name": "Wiosłowanie sztangą", "muscles": "plecy", "difficulty": "medium"},
    # ...
]

# Utwórz dokumenty
docs = [Document(page_content=format_exercise(e)) for e in exercises]

# Załaduj do Qdrant
vectorstore = Qdrant.from_documents(
    docs,
    embedding=OpenAIEmbeddings(),  # lub OllamaEmbeddings
    url="http://localhost:6333",
    collection_name="gym_exercises"
)
```

### Wyszukiwanie

```python
from app.agent import get_vector_store

vector_store = get_vector_store()

# Semantic search
docs = vector_store.similarity_search("ćwiczenia na barki", k=5)
for doc in docs:
    print(doc.page_content)
```

### Sprawdzanie Qdrant

```bash
# Lista kolekcji
curl http://localhost:6333/collections

# Szczegóły kolekcji
curl http://localhost:6333/collections/gym_exercises

# Liczba dokumentów
curl http://localhost:6333/collections/gym_exercises/points/count
```

---

## Praca z LLM

### Konfiguracja

```python
# app/agent.py

def get_llm():
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-4o"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("LLM_MODEL", "llama3.2"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
```

### Ollama - lokalne modele

```bash
# Zainstaluj Ollama
# https://ollama.ai

# Pobierz model
ollama pull llama3.2

# Lista modeli
ollama list

# Uruchom interaktywnie (test)
ollama run llama3.2
```

### Wywoływanie LLM

```python
from app.agent import get_llm

llm = get_llm()

# Prosty prompt
response = llm.invoke("Opisz technikę martwego ciągu")
print(response.content)

# Z historią (chat)
from langchain_core.messages import HumanMessage, AIMessage

messages = [
    HumanMessage(content="Jestem początkujący na siłowni"),
    AIMessage(content="Świetnie! Chętnie pomogę..."),
    HumanMessage(content="Jakie ćwiczenia na start?")
]
response = llm.invoke(messages)
```

### Prompt engineering

```python
# Dobry prompt dla trenera
SYSTEM_PROMPT = """Jesteś doświadczonym trenerem personalnym.

ZASADY:
- Odpowiadaj po polsku
- Bądź konkretny i zwięzły
- Podawaj ilości (serie, powtórzenia)
- Ostrzegaj o błędach technicznych
- Dopasuj do poziomu użytkownika

DOSTĘPNE ĆWICZENIA Z BAZY:
{exercises}
"""

# Użycie
prompt = SYSTEM_PROMPT.format(exercises="\n".join(retrieved_docs))
response = llm.invoke(prompt + "\n\nPytanie: " + user_question)
```

---

## Obsługa błędów

### HTTPException

```python
from fastapi import HTTPException

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Użytkownik nie znaleziony"
        )
    return user

# Błędy walidacji (automatyczne przez Pydantic) → 422
# Błędy serwera → 500
```

### Kody statusu HTTP

```python
# 200 OK - sukces
# 201 Created - utworzono zasób
# 204 No Content - sukces bez treści (np. DELETE)
# 400 Bad Request - błąd w żądaniu
# 401 Unauthorized - brak autoryzacji
# 403 Forbidden - brak uprawnień
# 404 Not Found - nie znaleziono
# 422 Unprocessable Entity - błąd walidacji
# 500 Internal Server Error - błąd serwera
# 503 Service Unavailable - usługa niedostępna
```

### Try/except w endpointach

```python
@router.post("/generate")
async def generate(request: TrainingRequest):
    try:
        result = app_graph.invoke(request.dict())
        return result["final_plan"]

    except ValueError as e:
        # Znany błąd (np. brak kolekcji)
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Nieznany błąd - loguj
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Wystąpił błąd podczas generowania"
        )
```

### CommandResult z success flag

```python
@dataclass
class CommandResult:
    success: bool
    message: str
    data: Optional[dict] = None
    needs_confirmation: bool = False

# Użycie
if not client:
    return CommandResult(
        success=False,
        message="Nie znaleziono klienta"
    )
```

---

## Debugowanie

### Logi

```python
import logging
logger = logging.getLogger(__name__)

# Poziomy logowania
logger.debug("Szczegóły do debugowania")
logger.info("Informacja o działaniu")
logger.warning("Ostrzeżenie")
logger.error("Błąd")
logger.exception("Błąd z traceback")  # W bloku except

# W terminalu uvicorn zobaczysz:
# INFO:app.api.chat:Processing message: lista klientów
```

### Debug endpoint

```bash
curl http://localhost:8000/debug/config
```

### Sprawdzanie usług

```bash
# Backend
curl http://localhost:8000/health

# Qdrant
curl http://localhost:6333/collections

# Postgres
docker-compose exec postgres pg_isready -U trainer

# Ollama
curl http://localhost:11434/api/tags
```

### Print debugging

```python
# W kodzie (tymczasowo)
print(f"DEBUG: {variable=}")

# Albo z loggerem
logger.debug(f"Parsed command: {parsed}")
```

### Swagger UI

Otwórz `http://localhost:8000/docs` - zobaczysz wszystkie endpointy, schematy, możesz testować.

---

## Bezpieczeństwo

### Co NIE commitować

```gitignore
# .gitignore
.env                  # Klucze API, hasła
*.pem                 # Certyfikaty
*.key                 # Klucze prywatne
__pycache__/
.vscode/
.idea/
```

### Walidacja danych

```python
# Pydantic waliduje automatycznie
class UserCreate(BaseModel):
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(..., ge=1, le=120)

# Nigdy nie ufaj danym z zewnątrz
user_input = request.message
# NIE: os.system(user_input)
# NIE: eval(user_input)
# NIE: db.execute(f"SELECT * WHERE name = '{user_input}'")
```

### SQL Injection

```python
# ŹLE - podatne na SQL injection
db.execute(f"SELECT * FROM users WHERE name = '{name}'")

# DOBRZE - parametryzowane zapytania
db.query(User).filter(User.name == name).first()
```

### Zmienne środowiskowe

```python
# NIE hardcoduj sekretów
api_key = "sk-1234..."  # ŹLE

# Używaj zmiennych środowiskowych
api_key = os.getenv("OPENAI_API_KEY")  # DOBRZE
```

### CORS w produkcji

```python
# Development (OK)
allow_origins=["*"]

# Production (zmień na konkretne domeny)
allow_origins=["https://myapp.com", "https://www.myapp.com"]
```

---

## Git workflow

### Branches

```bash
# Nowa funkcjonalność
git checkout -b feature/add-statistics

# Bugfix
git checkout -b fix/chat-confirmation

# Po zakończeniu
git checkout main
git merge feature/add-statistics
```

### Commits

```bash
# Dobre commity
git commit -m "Add statistics command to chat"
git commit -m "Fix confirmation flow for delete command"
git commit -m "Refactor executor to use handlers dict"

# Złe commity
git commit -m "changes"
git commit -m "fix"
git commit -m "wip"
```

### Przed pushem

```bash
# Sprawdź czy działa
uvicorn app.main:app --reload
curl http://localhost:8000/health

# Sprawdź syntax
python -m py_compile app/main.py

# Sprawdź git status
git status
git diff
```

---

## Częste problemy i rozwiązania

### "Connection refused" localhost:8000

```bash
# Backend nie uruchomiony
uvicorn app.main:app --reload
```

### "Connection refused" localhost:6333

```bash
# Qdrant nie uruchomiony
docker-compose up -d qdrant
```

### "Collection not found"

```bash
# Brak ćwiczeń w Qdrant
python scripts/load_exercises.py
```

### "Model not found" (Ollama)

```bash
ollama pull llama3.2
```

### Import error

```bash
# Upewnij się że jesteś w głównym katalogu
cd /path/to/TrenerAI
python -c "from app.main import app"
```

### Zmiany nie działają

```bash
# Używaj --reload
uvicorn app.main:app --reload

# Lub zrestartuj
# Ctrl+C, potem uruchom ponownie
```

### Pydantic validation error (422)

```bash
# Sprawdź co Swagger pokazuje jako wymagane pola
# Otwórz http://localhost:8000/docs
# Kliknij na endpoint → Schema
```

### Database connection error

```bash
# Sprawdź czy Postgres działa
docker-compose ps
docker-compose logs postgres

# Sprawdź DATABASE_URL w .env
```

---

## Checklisty

### Przed commitem

- [ ] Backend się uruchamia
- [ ] Endpoint działa (test curl)
- [ ] Brak błędów w logach
- [ ] Brak hardcodowanych sekretów

### Nowa komenda czatu

- [ ] Typ w `commands/types.py`
- [ ] Pattern w `commands/parser.py`
- [ ] Handler w `commands/executor.py`
- [ ] Test: `curl -X POST localhost:8000/chat -d '{"message": "..."}'`

### Nowy endpoint API

- [ ] Router w `app/api/`
- [ ] Zarejestrowany w `app/api/__init__.py`
- [ ] Schema w `app/schemas/` (jeśli potrzebna)
- [ ] Test curl
- [ ] Widoczny w Swagger

### Nowa tabela w bazie

- [ ] Model w `app/database/models.py`
- [ ] `alembic revision --autogenerate -m "..."`
- [ ] `alembic upgrade head`
- [ ] CRUD w routerze

---

## Przydatne linki

### Dokumentacja

- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- SQLAlchemy: https://docs.sqlalchemy.org/
- LangChain: https://python.langchain.com/
- LangGraph: https://python.langchain.com/docs/langgraph
- Qdrant: https://qdrant.tech/documentation/
- Alembic: https://alembic.sqlalchemy.org/

### Narzędzia

- Regex tester: https://regex101.com/
- JSON formatter: https://jsonformatter.org/
- HTTP client: https://httpie.io/

### Python

- Type hints: https://docs.python.org/3/library/typing.html
- Dataclasses: https://docs.python.org/3/library/dataclasses.html
- Async: https://docs.python.org/3/library/asyncio.html
