# Dokumentacja: seed_database.py

## Spis treści
1. [Cel skryptu](#cel-skryptu)
2. [Wymagana wiedza](#wymagana-wiedza)
3. [Importy](#importy)
4. [Konfiguracja](#konfiguracja)
5. [Funkcja load_exercises](#funkcja-load_exercises)
6. [Funkcja count_exercises_by_category](#funkcja-count_exercises_by_category)
7. [Funkcja main](#funkcja-main)
8. [Uruchamianie skryptu](#uruchamianie-skryptu)
9. [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## Cel skryptu

Skrypt `seed_database.py` **wypełnia bazę wektorową** ćwiczeniami:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CEL SEEDOWANIA                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  BEZ SEEDOWANIA:                     PO SEEDOWANIU:
  ───────────────                     ──────────────

  ┌─────────────────┐                 ┌─────────────────┐
  │     Qdrant      │                 │     Qdrant      │
  │                 │                 │                 │
  │   (pusta baza)  │   ─────────▶    │  100 ćwiczeń    │
  │                 │   seed_db.py    │  + embeddingi   │
  │   0 punktów     │                 │  + metadata     │
  └─────────────────┘                 └─────────────────┘

  API zwraca błąd:                    API działa:
  "Collection not found"              similarity_search() ✓
```

---

## Wymagana wiedza

Przed przeczytaniem tego dokumentu:
- [01_what_is_embedding.md](./01_concepts/01_what_is_embedding.md)
- [02_what_is_vector_db.md](./01_concepts/02_what_is_vector_db.md)
- [03_exercises_json.md](./03_exercises_json.md)

---

## Importy

```python
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
```

### Wyjaśnienie importów

| Import | Źródło | Opis |
|--------|--------|------|
| `json` | stdlib | Parsowanie pliku exercises.json |
| `os` | stdlib | Dostęp do zmiennych środowiskowych |
| `logging` | stdlib | Logowanie postępu |
| `Path` | pathlib | Obsługa ścieżek plików |
| `load_dotenv` | python-dotenv | Wczytanie .env |
| `Document` | langchain_core | Format dokumentu dla LangChain |
| `Qdrant` | langchain_community | Klient bazy wektorowej |
| `FastEmbedEmbeddings` | langchain_community | Model embeddingów |

---

## Konfiguracja

```python
load_dotenv()  # Wczytaj .env

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises")
DEFAULT_EXERCISES_PATH = Path(__file__).parent / "data" / "exercises.json"
```

### Diagram konfiguracji

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KONFIGURACJA                                         │
└─────────────────────────────────────────────────────────────────────────────┘

  .env                               seed_database.py
  ────                               ────────────────

  QDRANT_URL=http://localhost:6333   QDRANT_URL = os.getenv(...)
  QDRANT_COLLECTION_NAME=gym_ex...   COLLECTION_NAME = os.getenv(...)
                                     DEFAULT_EXERCISES_PATH = Path(...)
         │                                      │
         │                                      │
         └──────────────────┬───────────────────┘
                            │
                            ▼
                    ┌───────────────────┐
                    │ Połączenie z      │
                    │ Qdrant na         │
                    │ localhost:6333    │
                    └───────────────────┘
```

---

## Funkcja load_exercises

### Kod

```python
def load_exercises(file_path: Path = None) -> List[Dict[str, Any]]:
    if file_path is None:
        file_path = DEFAULT_EXERCISES_PATH

    logger.info(f"Loading exercises from: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(...)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "exercises" not in data:
        raise ValueError(...)

    exercises = data["exercises"]
    logger.info(f"Loaded {len(exercises)} exercises from file")

    return exercises
```

### Diagram przepływu

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      load_exercises()                                        │
└─────────────────────────────────────────────────────────────────────────────┘

  INPUT: file_path (opcjonalny)
         │
         ▼
  ┌─────────────────────────┐
  │ Czy file_path podany?   │
  │                         │
  │ NIE → użyj DEFAULT_PATH │
  │ TAK → użyj file_path    │
  └───────────┬─────────────┘
              │
              ▼
  ┌─────────────────────────┐
  │ Czy plik istnieje?      │──── NIE ───▶ FileNotFoundError
  └───────────┬─────────────┘
              │ TAK
              ▼
  ┌─────────────────────────┐
  │ json.load(file)         │──── BŁĄD ──▶ JSONDecodeError
  └───────────┬─────────────┘
              │ OK
              ▼
  ┌─────────────────────────┐
  │ Czy jest klucz          │──── NIE ───▶ ValueError
  │ "exercises"?            │
  └───────────┬─────────────┘
              │ TAK
              ▼
  OUTPUT: List[Dict] (100 ćwiczeń)
```

---

## Funkcja count_exercises_by_category

### Kod

```python
def count_exercises_by_category(exercises: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {
        "warmup": 0,
        "main_easy": 0,
        "main_medium": 0,
        "main_hard": 0,
        "cooldown": 0
    }

    for ex in exercises:
        ex_type = ex.get("type", "")
        ex_level = ex.get("level", "")

        if ex_type == "warmup":
            counts["warmup"] += 1
        elif ex_type == "cooldown":
            counts["cooldown"] += 1
        elif ex_type == "main":
            if ex_level == "easy":
                counts["main_easy"] += 1
            # ... medium, hard
    return counts
```

### Cel

Funkcja pomocnicza do wyświetlania statystyk po seedowaniu:

```
Database seeding completed successfully!
Total exercises indexed: 100
  - Warmup: 20
  - Main (easy): 20
  - Main (medium): 20
  - Main (hard): 20
  - Cooldown: 20
```

---

## Funkcja main

### Kod (uproszczony)

```python
def main(exercises_file: Path = None) -> None:
    # 1. Wczytaj ćwiczenia
    exercises = load_exercises(exercises_file)

    # 2. Zamień na Documents
    documents = []
    for ex in exercises:
        metadata = {"id": ex["id"], "name": ex["name"], ...}
        content = f"{ex['name']}: {ex['desc']}"
        documents.append(Document(page_content=content, metadata=metadata))

    # 3. Inicjalizuj embeddingi
    embeddings = FastEmbedEmbeddings()

    # 4. Zapisz do Qdrant
    Qdrant.from_documents(
        documents,
        embeddings,
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
        force_recreate=True
    )
```

### Diagram procesu main()

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              main()                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  KROK 1: Wczytaj ćwiczenia
  ─────────────────────────

  exercises.json ──▶ load_exercises() ──▶ List[Dict]
                                          (100 ćwiczeń)


  KROK 2: Zamień na Documents
  ───────────────────────────

  {"id": "w1", "name": "Jumping Jacks", "desc": "..."}
                     │
                     ▼
  Document(
      page_content = "Jumping Jacks: Jump with arm swings",  ◀── TO BĘDZIE
      metadata = {                                               EMBEDDOWANE
          "id": "w1",
          "name": "Jumping Jacks",
          "type": "warmup",
          "level": "easy"
      }
  )


  KROK 3: Generuj embeddingi
  ──────────────────────────

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                          FastEmbedEmbeddings                             │
  │                                                                          │
  │  "Jumping Jacks: Jump..."  ──────▶  [0.023, -0.087, ..., 0.045]        │
  │                                      └────── 384 liczb ──────┘          │
  └─────────────────────────────────────────────────────────────────────────┘


  KROK 4: Zapisz do Qdrant
  ────────────────────────

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                     Qdrant.from_documents()                              │
  │                                                                          │
  │  Dla każdego Document:                                                   │
  │  1. Wygeneruj embedding (jeśli jeszcze nie ma)                          │
  │  2. Utwórz punkt w kolekcji:                                            │
  │     • id: "w1"                                                          │
  │     • vector: [0.023, -0.087, ...]                                      │
  │     • payload: {"name": "Jumping Jacks", "type": "warmup", ...}        │
  │                                                                          │
  │  force_recreate=True → usuń starą kolekcję i stwórz nową               │
  └─────────────────────────────────────────────────────────────────────────┘
```

### Co robi Document?

```python
Document(
    page_content="Jumping Jacks: Jump with arm swings",  # → będzie embeddowane
    metadata={"id": "w1", "name": "...", "type": "warmup"}  # → payload w Qdrant
)
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DOCUMENT                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  page_content: str                        metadata: dict                    │
│  ──────────────────                       ──────────────                    │
│  "Jumping Jacks: Jump with..."            {"id": "w1", ...}                 │
│           │                                        │                        │
│           │    FastEmbed                           │                        │
│           ▼                                        ▼                        │
│  ┌─────────────────┐                     ┌─────────────────┐               │
│  │ WEKTOR          │                     │ PAYLOAD         │               │
│  │ [0.02, -0.08,   │                     │ w Qdrant        │               │
│  │  ..., 0.04]     │                     │ (do filtrów)    │               │
│  └─────────────────┘                     └─────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Uruchamianie skryptu

### Podstawowe użycie

```bash
# Upewnij się że Qdrant działa
docker-compose up -d qdrant

# Uruchom seedowanie
python seed_database.py
```

### Własny plik ćwiczeń

```bash
python seed_database.py --file /path/to/my-exercises.json
# lub
python seed_database.py -f /path/to/my-exercises.json
```

### Oczekiwany output

```
2025-01-15 10:30:00 - __main__ - INFO - Starting database seeding...
2025-01-15 10:30:00 - __main__ - INFO - Qdrant URL: http://localhost:6333
2025-01-15 10:30:00 - __main__ - INFO - Collection: gym_exercises
2025-01-15 10:30:00 - __main__ - INFO - Loading exercises from: data/exercises.json
2025-01-15 10:30:00 - __main__ - INFO - Loaded 100 exercises from file
2025-01-15 10:30:00 - __main__ - INFO - Prepared 100 exercises for indexing
2025-01-15 10:30:00 - __main__ - INFO - Initializing FastEmbed embeddings...
2025-01-15 10:30:05 - __main__ - INFO - Sending vectors to Qdrant...
2025-01-15 10:30:10 - __main__ - INFO - Database seeding completed successfully!
2025-01-15 10:30:10 - __main__ - INFO - Total exercises indexed: 100
2025-01-15 10:30:10 - __main__ - INFO -   - Warmup: 20
2025-01-15 10:30:10 - __main__ - INFO -   - Main (easy): 20
2025-01-15 10:30:10 - __main__ - INFO -   - Main (medium): 20
2025-01-15 10:30:10 - __main__ - INFO -   - Main (hard): 20
2025-01-15 10:30:10 - __main__ - INFO -   - Cooldown: 20
```

---

## Rozwiązywanie problemów

### Błąd: Connection refused

```
Error: Connection refused at localhost:6333
```

**Przyczyna:** Qdrant nie jest uruchomiony

**Rozwiązanie:**
```bash
docker-compose up -d qdrant
# Poczekaj kilka sekund
docker ps  # sprawdź czy działa
python seed_database.py
```

### Błąd: File not found

```
FileNotFoundError: Exercises file not found: data/exercises.json
```

**Przyczyna:** Brak pliku z ćwiczeniami

**Rozwiązanie:**
- Upewnij się że plik `data/exercises.json` istnieje
- Lub użyj `--file` aby wskazać inną lokalizację

### Błąd: Invalid JSON

```
json.JSONDecodeError: Expecting property name...
```

**Przyczyna:** Błąd składni w pliku JSON

**Rozwiązanie:**
```bash
# Sprawdź składnię
python -c "import json; json.load(open('data/exercises.json'))"
```

---

## Powiązania z innymi plikami

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POWIĄZANIA                                           │
└─────────────────────────────────────────────────────────────────────────────┘

  seed_database.py
         │
         ├──── CZYTA ────▶ data/exercises.json
         │                 (100 ćwiczeń w JSON)
         │
         ├──── CZYTA ────▶ .env
         │                 (QDRANT_URL, COLLECTION_NAME)
         │
         └──── ZAPISUJE ──▶ Qdrant
                            (kolekcja gym_exercises)
                                   │
                                   │
                                   ▼
                            agent.py
                            (similarity_search)
```

---

**Poprzedni:** [03_exercises_json.md](./03_exercises_json.md) - Plik ćwiczeń

**Następny:** [05_agent_py.md](./05_agent_py.md) - LangGraph workflow
