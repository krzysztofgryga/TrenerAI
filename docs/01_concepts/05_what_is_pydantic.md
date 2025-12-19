# Co to jest Pydantic?

## Spis treści
1. [Analogia ze świata rzeczywistego](#analogia-ze-świata-rzeczywistego)
2. [Definicja techniczna](#definicja-techniczna)
3. [Podstawowe użycie](#podstawowe-użycie)
4. [Walidacja danych](#walidacja-danych)
5. [Serializacja JSON](#serializacja-json)
6. [Jak to jest używane w TrenerAI](#jak-to-jest-używane-w-trenerai)
7. [Częste błędy](#częste-błędy)

---

## Analogia ze świata rzeczywistego

### Formularz urzędowy

Wyobraź sobie formularz w urzędzie:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FORMULARZ WNIOSKU                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Imię: ______________ (wymagane, tylko litery)                             │
│                                                                             │
│  Wiek: ______________ (wymagane, liczba 18-120)                            │
│                                                                             │
│  Email: _____________ (wymagane, format: x@y.z)                            │
│                                                                             │
│  Telefon: ___________ (opcjonalne, 9 cyfr)                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Urzędnik sprawdza:**
- Czy wszystkie wymagane pola są wypełnione?
- Czy wiek to liczba między 18 a 120?
- Czy email ma poprawny format?

**Pydantic robi to samo dla danych w Pythonie!**

---

## Definicja techniczna

**Pydantic** to biblioteka Python do:
1. **Definiowania struktury danych** (jakie pola, jakie typy)
2. **Walidacji danych** (czy dane są poprawne)
3. **Serializacji/deserializacji** (Python ↔ JSON)

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str                           # wymagane, tekst
    age: int = Field(ge=18, le=120)     # wymagane, 18-120
    email: str                          # wymagane
    phone: str | None = None            # opcjonalne
```

---

## Podstawowe użycie

### Tworzenie modelu

```python
from pydantic import BaseModel

class Exercise(BaseModel):
    id: str
    name: str
    difficulty: str
    type: str

# Tworzenie instancji
ex = Exercise(
    id="w1",
    name="Jumping Jacks",
    difficulty="easy",
    type="warmup"
)

print(ex.name)  # "Jumping Jacks"
```

### Walidacja typów

```python
# ✓ Poprawne - wszystkie typy zgadzają się
ex = Exercise(id="w1", name="Jumping Jacks", difficulty="easy", type="warmup")

# ✗ Błąd - brakuje wymaganych pól
ex = Exercise(id="w1", name="Jumping Jacks")
# ValidationError: difficulty, type are required

# ✗ Błąd - zły typ
ex = Exercise(id=123, name="Jumping Jacks", difficulty="easy", type="warmup")
# ValidationError: id should be str, not int
```

---

## Walidacja danych

### Field z ograniczeniami

```python
from pydantic import BaseModel, Field
from typing import Annotated

class TrainingRequest(BaseModel):
    # Liczba 1-50
    num_people: Annotated[int, Field(ge=1, le=50)]

    # Tekst z dozwolonymi wartościami (przez Enum)
    difficulty: str

    # Liczba 10-300, domyślnie 60
    rest_time: Annotated[int, Field(ge=10, le=300)] = 60
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WALIDATORY FIELD                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ge = greater or equal (>=)     Field(ge=1)      → wartość >= 1            │
│  le = less or equal (<=)        Field(le=50)     → wartość <= 50           │
│  gt = greater than (>)          Field(gt=0)      → wartość > 0             │
│  lt = less than (<)             Field(lt=100)    → wartość < 100           │
│  min_length                     Field(min_length=1) → min 1 znak           │
│  max_length                     Field(max_length=100) → max 100 znaków     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Enum dla dozwolonych wartości

```python
from enum import Enum

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class TrainingRequest(BaseModel):
    difficulty: Difficulty  # tylko easy/medium/hard

# ✓ Poprawne
req = TrainingRequest(difficulty="medium")

# ✗ Błąd
req = TrainingRequest(difficulty="extreme")
# ValidationError: difficulty must be easy, medium, or hard
```

---

## Serializacja JSON

### Python → JSON

```python
ex = Exercise(id="w1", name="Jumping Jacks", difficulty="easy", type="warmup")

# Do słownika
data = ex.model_dump()
# {"id": "w1", "name": "Jumping Jacks", "difficulty": "easy", "type": "warmup"}

# Do JSON string
json_str = ex.model_dump_json()
# '{"id":"w1","name":"Jumping Jacks",...}'
```

### JSON → Python

```python
# Ze słownika
data = {"id": "w1", "name": "Jumping Jacks", "difficulty": "easy", "type": "warmup"}
ex = Exercise.model_validate(data)

# Z JSON string
json_str = '{"id":"w1","name":"Jumping Jacks","difficulty":"easy","type":"warmup"}'
ex = Exercise.model_validate_json(json_str)
```

---

## Jak to jest używane w TrenerAI

### 1. Request validation (main.py)

```python
class TrainingRequest(BaseModel):
    num_people: Annotated[int, Field(ge=1, le=50)]
    difficulty: Difficulty
    rest_time: Annotated[int, Field(ge=10, le=300)] = 60
    mode: TrainingMode
    warmup_count: Annotated[int, Field(ge=1, le=10)] = 3

@app.post("/generate-training")
def generate(request: TrainingRequest):  # ← Pydantic waliduje!
    # Jeśli dane są złe → automatyczny błąd 422
    # Jeśli dane są OK → request jest typowany
    pass
```

### 2. Response models (models/exercise.py)

```python
class Exercise(BaseModel):
    id: str
    name: str
    description: str

class TrainingPlan(BaseModel):
    warmup: List[Exercise]
    main_part: List[Exercise]
    cooldown: List[Exercise]
    mode: str
    total_duration_minutes: int
```

### 3. LLM structured output (agent.py)

```python
# OpenAI może generować bezpośrednio do Pydantic
llm_with_structure = llm.with_structured_output(TrainingPlan)
plan = llm_with_structure.invoke(prompt)
# plan jest typu TrainingPlan, nie dict!
```

---

## Częste błędy

### 1. dict() vs model_dump()

```python
# Pydantic v1 (stare)
data = model.dict()

# Pydantic v2 (nowe) ← TrenerAI używa tego
data = model.model_dump()
```

### 2. Brak walidacji przy tworzeniu

```python
# ✗ Pomija walidację!
ex = Exercise.model_construct(id=123, name=None)

# ✓ Zawsze waliduje
ex = Exercise(id="w1", name="Jumping Jacks", ...)
```

---

## Podsumowanie

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PYDANTIC                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEFINIUJE:     class Model(BaseModel): ...                                │
│  WALIDUJE:      Model(data) → ValidationError jeśli błędne                 │
│  SERIALIZUJE:   model.model_dump() → dict / JSON                           │
│                                                                             │
│  W TRENERAI:                                                                │
│  • TrainingRequest - walidacja inputu API                                  │
│  • TrainingPlan - struktura odpowiedzi                                     │
│  • Exercise - struktura ćwiczenia                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Poprzedni:** [04_what_is_rag.md](./04_what_is_rag.md)

**Następny:** [../02_models_exercise_py.md](../02_models_exercise_py.md) - Modele w TrenerAI
