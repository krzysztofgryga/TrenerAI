# Dokumentacja: app/models/exercise.py

## Spis treści
1. [Cel pliku](#cel-pliku)
2. [Wymagana wiedza](#wymagana-wiedza)
3. [Importy](#importy)
4. [Klasa Exercise](#klasa-exercise)
5. [Klasa TrainingPlan](#klasa-trainingplan)
6. [Użycie w projekcie](#użycie-w-projekcie)
7. [Przykłady](#przykłady)

---

## Cel pliku

Plik `app/models/exercise.py` definiuje **struktury danych** używane w całym projekcie:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CEL MODELI                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. WALIDACJA         - Czy dane mają poprawną strukturę?                  │
│  2. SERIALIZACJA      - Python → JSON (odpowiedź API)                      │
│  3. STRUCTURED OUTPUT - LLM generuje dokładnie tę strukturę                │
│  4. DOKUMENTACJA      - Field() opisuje co oznacza każde pole              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Wymagana wiedza

Przed przeczytaniem tego dokumentu, zapoznaj się z:
- [05_what_is_pydantic.md](./01_concepts/05_what_is_pydantic.md) - podstawy Pydantic

---

## Importy

```python
from pydantic import BaseModel, Field
from typing import List
```

### Wyjaśnienie importów

| Import | Źródło | Opis |
|--------|--------|------|
| `BaseModel` | pydantic | Klasa bazowa dla modeli danych |
| `Field` | pydantic | Funkcja do konfiguracji pól (opis, domyślna wartość) |
| `List` | typing | Typ generyczny dla listy |

---

## Klasa Exercise

### Kod źródłowy

```python
class Exercise(BaseModel):
    """Single exercise data model."""
    id: str = Field(description="Unique exercise identifier")
    name: str = Field(description="Exercise name")
    description: str = Field(description="Brief instruction for the trainer")
    muscle_group: str = Field(
        default="general",
        description="Primary muscle group targeted"
    )
    difficulty: str = Field(description="Level: easy, medium, hard")
    type: str = Field(description="Exercise type: warmup, main, cooldown")
```

### Diagram klasy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Exercise                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  POLA:                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ id: str              │ "w1", "m_e1", "c3"        │ WYMAGANE        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ name: str            │ "Burpees"                 │ WYMAGANE        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ description: str     │ "Wyskok z pompką"         │ WYMAGANE        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ muscle_group: str    │ "chest", "legs"           │ default="general"│  │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ difficulty: str      │ "easy", "medium", "hard"  │ WYMAGANE        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ type: str            │ "warmup", "main", "cooldown"│ WYMAGANE      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Opis pól

#### `id: str`
```python
id: str = Field(description="Unique exercise identifier")
```
- **Typ:** String (tekst)
- **Wymagane:** Tak
- **Konwencja nazewnictwa:**
  - `w1`, `w2`, ... - warmup exercises
  - `m_e1`, `m_e2`, ... - main easy
  - `m_m1`, `m_m2`, ... - main medium
  - `m_h1`, `m_h2`, ... - main hard
  - `c1`, `c2`, ... - cooldown

#### `name: str`
```python
name: str = Field(description="Exercise name")
```
- **Typ:** String
- **Wymagane:** Tak
- **Przykłady:** "Burpees", "Jumping Jacks", "Child's Pose"

#### `description: str`
```python
description: str = Field(description="Brief instruction for the trainer")
```
- **Typ:** String
- **Wymagane:** Tak
- **Cel:** Krótka instrukcja dla trenera jak wykonać ćwiczenie
- **Przykłady:** "Wyskok z pompką, maksymalne tempo", "Skoki z unoszeniem rąk"

#### `muscle_group: str`
```python
muscle_group: str = Field(
    default="general",
    description="Primary muscle group targeted"
)
```
- **Typ:** String
- **Wymagane:** Nie (domyślnie "general")
- **Przykłady:** "chest", "legs", "core", "back", "shoulders"

#### `difficulty: str`
```python
difficulty: str = Field(description="Level: easy, medium, hard")
```
- **Typ:** String
- **Wymagane:** Tak
- **Dozwolone wartości:** "easy", "medium", "hard"

#### `type: str`
```python
type: str = Field(description="Exercise type: warmup, main, cooldown")
```
- **Typ:** String
- **Wymagane:** Tak
- **Dozwolone wartości:** "warmup", "main", "cooldown"

---

## Klasa TrainingPlan

### Kod źródłowy

```python
class TrainingPlan(BaseModel):
    """Complete training plan output structure."""
    warmup: List[Exercise] = Field(
        description="List of warmup exercises"
    )
    main_part: List[Exercise] = Field(
        description="Main training exercises"
    )
    cooldown: List[Exercise] = Field(
        description="Cooldown and stretching exercises"
    )
    mode: str = Field(
        description="Training mode: circuit or common"
    )
    total_duration_minutes: int = Field(
        description="Estimated total training duration"
    )
```

### Diagram klasy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            TrainingPlan                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  POLA:                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ warmup: List[Exercise]           │ [Ex1, Ex2, Ex3]     │ WYMAGANE  │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ main_part: List[Exercise]        │ [Ex4, Ex5, ...]     │ WYMAGANE  │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ cooldown: List[Exercise]         │ [Ex10, Ex11]        │ WYMAGANE  │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ mode: str                        │ "circuit"/"common"  │ WYMAGANE  │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ total_duration_minutes: int      │ 45                  │ WYMAGANE  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RELACJA:                                                                   │
│  TrainingPlan ──────────contains──────────▶ Exercise                       │
│                  (warmup, main_part, cooldown)                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Opis pól

#### `warmup: List[Exercise]`
- **Typ:** Lista obiektów Exercise
- **Cel:** Ćwiczenia rozgrzewkowe (początek treningu)
- **Typowa ilość:** 3-5 ćwiczeń

#### `main_part: List[Exercise]`
- **Typ:** Lista obiektów Exercise
- **Cel:** Główna część treningu
- **Typowa ilość:** 5-20 ćwiczeń (zależy od trybu i liczby osób)

#### `cooldown: List[Exercise]`
- **Typ:** Lista obiektów Exercise
- **Cel:** Ćwiczenia wyciszające i rozciągające
- **Typowa ilość:** 3-5 ćwiczeń

#### `mode: str`
- **Typ:** String
- **Wartości:**
  - `"circuit"` - trening obwodowy (każda osoba na innej stacji)
  - `"common"` - wszyscy robią to samo

#### `total_duration_minutes: int`
- **Typ:** Liczba całkowita
- **Cel:** Szacowany czas trwania treningu w minutach

---

## Użycie w projekcie

### 1. LLM Structured Output (agent.py)

```python
# LLM generuje odpowiedź bezpośrednio jako TrainingPlan
llm_with_structure = llm.with_structured_output(TrainingPlan)
plan = llm_with_structure.invoke(prompt)
# plan jest typu TrainingPlan, nie dict!
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LLM STRUCTURED OUTPUT                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  LLM (GPT-4)                                    Python
  ──────────                                     ──────

  Generuje JSON:                                 Automatycznie parsuje:
  {                            ──────────────▶   TrainingPlan(
    "warmup": [...],                               warmup=[Exercise(...)],
    "main_part": [...],                            main_part=[...],
    "cooldown": [...],                             cooldown=[...],
    "mode": "circuit",                             mode="circuit",
    "total_duration_minutes": 45                   total_duration_minutes=45
  }                                              )
```

### 2. API Response (main.py)

```python
@app.post("/generate-training")
def generate_training(request: TrainingRequest) -> TrainingPlan:
    # ... generowanie planu ...
    return result["plan"]  # Pydantic automatycznie serializuje do JSON
```

### 3. Walidacja (automatyczna)

```python
# Jeśli LLM zwróci niepoprawne dane:
{
  "warmup": "to nie jest lista!",  # ✗ Błąd!
  "main_part": [...]
}

# Pydantic wyrzuci ValidationError
# → obsłużone w agent.py jako fallback
```

---

## Przykłady

### Tworzenie Exercise

```python
from app.models.exercise import Exercise

# Minimalny (wszystkie wymagane pola)
ex = Exercise(
    id="w1",
    name="Jumping Jacks",
    description="Skoki z unoszeniem rąk",
    difficulty="easy",
    type="warmup"
)

# Z opcjonalnym muscle_group
ex = Exercise(
    id="m_m1",
    name="Classic Push-ups",
    description="Pompki klasyczne",
    muscle_group="chest",
    difficulty="medium",
    type="main"
)
```

### Tworzenie TrainingPlan

```python
from app.models.exercise import Exercise, TrainingPlan

warmup = [
    Exercise(id="w1", name="Jumping Jacks", description="...",
             difficulty="easy", type="warmup"),
    Exercise(id="w2", name="High Knees", description="...",
             difficulty="easy", type="warmup"),
]

main = [
    Exercise(id="m_h1", name="Burpees", description="...",
             difficulty="hard", type="main"),
]

cooldown = [
    Exercise(id="c1", name="Child's Pose", description="...",
             difficulty="easy", type="cooldown"),
]

plan = TrainingPlan(
    warmup=warmup,
    main_part=main,
    cooldown=cooldown,
    mode="circuit",
    total_duration_minutes=45
)
```

### Serializacja do JSON

```python
# Do słownika Python
data = plan.model_dump()
# {
#   "warmup": [...],
#   "main_part": [...],
#   ...
# }

# Do stringa JSON
json_str = plan.model_dump_json()
# '{"warmup":[...],"main_part":[...],...}'
```

### Deserializacja z JSON

```python
# Ze słownika
data = {"warmup": [...], ...}
plan = TrainingPlan.model_validate(data)

# Z JSON stringa
json_str = '{"warmup":[...],...}'
plan = TrainingPlan.model_validate_json(json_str)
```

---

## Powiązania z innymi plikami

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POWIĄZANIA                                           │
└─────────────────────────────────────────────────────────────────────────────┘

  models/exercise.py
         │
         ├──────────▶ agent.py
         │            • TrainingPlan używany w generate_plan()
         │            • with_structured_output(TrainingPlan)
         │
         ├──────────▶ main.py
         │            • TrainingPlan jako typ zwracany z /generate-training
         │
         └──────────▶ Frontend (Flutter)
                      • models/training_plan.dart (odpowiednik w Dart)
```

---

**Poprzedni:** [01_concepts/](./01_concepts/) - Koncepty

**Następny:** [03_exercises_json.md](./03_exercises_json.md) - Struktura pliku ćwiczeń
