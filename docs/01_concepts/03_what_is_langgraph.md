# Co to jest LangGraph?

## Spis treści
1. [Analogia ze świata rzeczywistego](#analogia-ze-świata-rzeczywistego)
2. [Definicja techniczna](#definicja-techniczna)
3. [Porównanie z tradycyjnym kodem](#porównanie-z-tradycyjnym-kodem)
4. [Podstawowe koncepty](#podstawowe-koncepty)
5. [Przykład kodu](#przykład-kodu)
6. [Jak to jest używane w TrenerAI](#jak-to-jest-używane-w-trenerai)
7. [Częste błędy i pułapki](#częste-błędy-i-pułapki)
8. [Dalsze materiały](#dalsze-materiały)

---

## Analogia ze świata rzeczywistego

### Linia produkcyjna w fabryce

Wyobraź sobie fabrykę produkującą samochody:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LINIA PRODUKCYJNA SAMOCHODU                          │
└─────────────────────────────────────────────────────────────────────────────┘

  SUROWCE            STACJA 1          STACJA 2          STACJA 3          GOTOWY
  (input)            (rama)            (silnik)          (lakier)          PRODUKT

  ┌────────┐        ┌────────┐        ┌────────┐        ┌────────┐        ┌────────┐
  │ Stal,  │───────▶│ Spawaj │───────▶│ Montuj │───────▶│ Maluj  │───────▶│  🚗   │
  │ Części │        │ ramę   │        │ silnik │        │        │        │ Gotowe │
  └────────┘        └────────┘        └────────┘        └────────┘        └────────┘
      │                  │                 │                 │
      │                  ▼                 ▼                 ▼
      │            Stan: rama        Stan: rama +      Stan: rama +
      │                              silnik            silnik + lakier
      │
      └── STAN POCZĄTKOWY: surowce
```

**Każda stacja:**
- Otrzymuje stan (co zostało zrobione wcześniej)
- Wykonuje swoją operację
- Przekazuje zaktualizowany stan dalej

**LangGraph działa tak samo**, ale zamiast stacji fabrycznych mamy "węzły" (nodes), a zamiast surowców mamy dane (stan).

---

## Definicja techniczna

### Co to jest LangGraph?

**LangGraph** to biblioteka do budowania aplikacji AI jako grafów, gdzie:

- **Węzły (Nodes)** = funkcje wykonujące operacje (np. szukaj, generuj)
- **Krawędzie (Edges)** = połączenia między węzłami (co po czym)
- **Stan (State)** = dane przepływające przez graf

### Dlaczego graf?

```
TRADYCYJNY KOD (liniowy)           LANGGRAPH (graf)
────────────────────────           ─────────────────

def process(data):                 ┌─────────┐
    step1_result = step1(data)     │  START  │
    step2_result = step2(step1)    └────┬────┘
    step3_result = step3(step2)         │
    return step3_result                 ▼
                                   ┌─────────┐     ┌─────────┐
Problemy:                          │  step1  │────▶│  step2  │
• Trudno dodać warunki             └─────────┘     └────┬────┘
• Trudno równoległe kroki                               │
• Trudno debugować                      ┌───────────────┤
                                        ▼               ▼
                                   ┌─────────┐     ┌─────────┐
                                   │ step3a  │     │ step3b  │
                                   └────┬────┘     └────┬────┘
                                        │               │
                                        └───────┬───────┘
                                                ▼
                                           ┌─────────┐
                                           │   END   │
                                           └─────────┘
```

**Zalety grafu:**
1. **Wizualizacja** - widać przepływ danych
2. **Elastyczność** - łatwo dodać/usunąć kroki
3. **Warunki** - różne ścieżki w zależności od danych
4. **Debugowanie** - wiadomo gdzie błąd

---

## Porównanie z tradycyjnym kodem

### Tradycyjne podejście (bez LangGraph)

```python
def generate_training(num_people, difficulty, mode):
    # Krok 1: Znajdź ćwiczenia w bazie
    exercises = search_exercises(difficulty)

    # Krok 2: Wygeneruj plan przez LLM
    plan = call_llm(exercises, num_people, mode)

    # Krok 3: Waliduj odpowiedź
    if not is_valid(plan):
        raise Error("Invalid plan")

    return plan
```

**Problemy:**
- Wszystko w jednej funkcji
- Trudno testować pojedyncze kroki
- Trudno obsłużyć błędy
- Trudno dodać logowanie

### Podejście LangGraph

```python
from langgraph.graph import StateGraph

# Definicja stanu
class State(TypedDict):
    num_people: int
    difficulty: str
    exercises: list
    plan: dict

# Krok 1: Węzeł wyszukiwania
def search_node(state: State) -> dict:
    exercises = search_exercises(state["difficulty"])
    return {"exercises": exercises}

# Krok 2: Węzeł generowania
def generate_node(state: State) -> dict:
    plan = call_llm(state["exercises"], state["num_people"])
    return {"plan": plan}

# Budowanie grafu
workflow = StateGraph(State)
workflow.add_node("search", search_node)
workflow.add_node("generate", generate_node)
workflow.add_edge("search", "generate")
workflow.set_entry_point("search")
workflow.set_finish_point("generate")

# Kompilacja i uruchomienie
app = workflow.compile()
result = app.invoke({"num_people": 5, "difficulty": "hard"})
```

**Zalety:**
- Każdy krok jest osobną funkcją
- Łatwo testować pojedyncze węzły
- Graf jest czytelny
- Łatwo dodać nowe kroki

---

## Podstawowe koncepty

### 1. Stan (State)

Stan to słownik z danymi przepływającymi przez graf:

```python
from typing import TypedDict, List

class TrainerState(TypedDict):
    # Wejście od użytkownika
    num_people: int
    difficulty: str
    mode: str

    # Wypełniane przez węzły
    exercises: List[Document]    # ← wypełnia "retrieve"
    plan: TrainingPlan           # ← wypełnia "generate"
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STAN (State)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  POCZĄTKOWO:                        PO "retrieve":                          │
│  ┌─────────────────────────┐        ┌─────────────────────────┐            │
│  │ num_people: 5           │        │ num_people: 5           │            │
│  │ difficulty: "hard"      │        │ difficulty: "hard"      │            │
│  │ mode: "circuit"         │   ──▶  │ mode: "circuit"         │            │
│  │ exercises: []           │        │ exercises: [Doc1, Doc2] │ ◀── NOWE   │
│  │ plan: None              │        │ plan: None              │            │
│  └─────────────────────────┘        └─────────────────────────┘            │
│                                                                             │
│  PO "generate":                                                             │
│  ┌─────────────────────────┐                                               │
│  │ num_people: 5           │                                               │
│  │ difficulty: "hard"      │                                               │
│  │ mode: "circuit"         │                                               │
│  │ exercises: [Doc1, Doc2] │                                               │
│  │ plan: TrainingPlan(...) │ ◀── NOWE                                      │
│  └─────────────────────────┘                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Węzły (Nodes)

Węzeł to funkcja która:
- Otrzymuje aktualny stan
- Wykonuje operację
- Zwraca aktualizację stanu

```python
def retrieve_exercises(state: TrainerState) -> dict:
    """
    Węzeł wyszukujący ćwiczenia w bazie wektorowej.

    Args:
        state: Aktualny stan (zawiera difficulty)

    Returns:
        dict: Aktualizacja stanu {"exercises": [...]}
    """
    # Odczytaj z stanu
    difficulty = state["difficulty"]

    # Wykonaj operację
    docs = vector_store.similarity_search(f"{difficulty} exercises", k=20)

    # Zwróć TYLKO zmiany (nie cały stan!)
    return {"exercises": docs}
```

**Ważne:** Węzeł zwraca tylko te pola które się zmieniły. LangGraph automatycznie merguje z resztą stanu.

### 3. Krawędzie (Edges)

Krawędzie definiują kolejność wykonania węzłów:

```python
# Prosta krawędź: po "retrieve" idź do "generate"
workflow.add_edge("retrieve", "generate")

# Krawędź warunkowa: w zależności od wyniku
def should_retry(state):
    if state["plan"] is None:
        return "retry"    # idź do węzła "retry"
    return "end"          # zakończ

workflow.add_conditional_edges("generate", should_retry)
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TYPY KRAWĘDZI                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  PROSTA KRAWĘDŹ                      KRAWĘDŹ WARUNKOWA
  ──────────────                      ──────────────────

  ┌──────────┐                        ┌──────────┐
  │ retrieve │                        │ generate │
  └────┬─────┘                        └────┬─────┘
       │                                   │
       │ add_edge()                        │ add_conditional_edges()
       │                                   │
       ▼                                   ▼
  ┌──────────┐                   ┌────────────────────┐
  │ generate │                   │ should_retry(state)│
  └──────────┘                   └─────────┬──────────┘
                                           │
                            ┌──────────────┼──────────────┐
                            │              │              │
                            ▼              ▼              ▼
                       "retry"          "end"         "error"
                            │              │              │
                            ▼              ▼              ▼
                       ┌────────┐    ┌─────────┐    ┌─────────┐
                       │ retry  │    │   END   │    │  error  │
                       └────────┘    └─────────┘    └─────────┘
```

### 4. Kompilacja i wywołanie

```python
# 1. Utwórz graf
workflow = StateGraph(TrainerState)

# 2. Dodaj węzły
workflow.add_node("retrieve", retrieve_exercises)
workflow.add_node("generate", generate_plan)

# 3. Dodaj krawędzie
workflow.add_edge("retrieve", "generate")
workflow.set_entry_point("retrieve")
workflow.set_finish_point("generate")

# 4. Skompiluj (sprawdza poprawność grafu)
app = workflow.compile()

# 5. Uruchom
result = app.invoke({
    "num_people": 5,
    "difficulty": "hard",
    "mode": "circuit"
})

print(result["plan"])  # TrainingPlan
```

---

## Przykład kodu

### Minimalny przykład

```python
from typing import TypedDict
from langgraph.graph import StateGraph

# 1. Definicja stanu
class SimpleState(TypedDict):
    input: str
    uppercase: str
    reversed: str

# 2. Węzeł 1: zamień na wielkie litery
def to_uppercase(state: SimpleState) -> dict:
    return {"uppercase": state["input"].upper()}

# 3. Węzeł 2: odwróć tekst
def reverse_text(state: SimpleState) -> dict:
    return {"reversed": state["uppercase"][::-1]}

# 4. Budowanie grafu
workflow = StateGraph(SimpleState)
workflow.add_node("uppercase", to_uppercase)
workflow.add_node("reverse", reverse_text)

workflow.add_edge("uppercase", "reverse")
workflow.set_entry_point("uppercase")
workflow.set_finish_point("reverse")

# 5. Kompilacja
app = workflow.compile()

# 6. Uruchomienie
result = app.invoke({"input": "hello"})
print(result)
# {"input": "hello", "uppercase": "HELLO", "reversed": "OLLEH"}
```

### Wizualizacja grafu

```python
# LangGraph pozwala wygenerować diagram
from IPython.display import Image, display
display(Image(app.get_graph().draw_png()))
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WIZUALIZACJA POWYŻSZEGO GRAFU                            │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   START     │
                              └──────┬──────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │  uppercase  │
                              │             │
                              │ "hello" ──▶ │
                              │ "HELLO"     │
                              └──────┬──────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │   reverse   │
                              │             │
                              │ "HELLO" ──▶ │
                              │ "OLLEH"     │
                              └──────┬──────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │    END      │
                              └─────────────┘
```

---

## Jak to jest używane w TrenerAI

### Graf w TrenerAI

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRENERAI WORKFLOW                                    │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   START     │
                              └──────┬──────┘
                                     │
                    TrainerState:    │
                    {                │
                      num_people: 5, │
                      difficulty: "hard",
                      mode: "circuit",
                      exercises: [],
                      plan: None
                    }
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │      retrieve         │
                         │                       │
                         │ 1. Buduje query       │
                         │ 2. Szuka w Qdrant     │
                         │ 3. Filtruje wyniki    │
                         │                       │
                         │ return {              │
                         │   "exercises": [...]  │
                         │ }                     │
                         └───────────┬───────────┘
                                     │
                    TrainerState:    │
                    {                │
                      ...            │
                      exercises: [Doc1, Doc2, ...],  ◀── ZAKTUALIZOWANE
                      plan: None
                    }
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │        plan           │
                         │                       │
                         │ 1. Buduje prompt      │
                         │ 2. Wywołuje LLM       │
                         │ 3. Parsuje JSON       │
                         │                       │
                         │ return {              │
                         │   "plan": TrainingPlan│
                         │ }                     │
                         └───────────┬───────────┘
                                     │
                    TrainerState:    │
                    {                │
                      ...            │
                      exercises: [...],
                      plan: TrainingPlan(...)  ◀── ZAKTUALIZOWANE
                    }
                                     │
                                     ▼
                              ┌─────────────┐
                              │    END      │
                              └─────────────┘
```

### Kod w agent.py

```python
# agent.py

from typing import TypedDict, List
from langgraph.graph import StateGraph
from langchain_core.documents import Document


class TrainerState(TypedDict):
    """Stan przepływający przez workflow."""
    num_people: int
    difficulty: str
    rest_time: int
    mode: str
    warmup_count: int
    main_count: int
    cooldown_count: int
    exercises: List[Document]
    plan: TrainingPlan


def retrieve_exercises(state: TrainerState) -> dict:
    """
    Węzeł 1: Wyszukuje ćwiczenia w bazie wektorowej.
    """
    vector_store = get_vector_store()
    query = f"{state['difficulty']} workout exercises"
    docs = vector_store.similarity_search(query, k=20)
    return {"exercises": docs}


def generate_plan(state: TrainerState) -> dict:
    """
    Węzeł 2: Generuje plan treningowy przez LLM.
    """
    llm = get_llm()
    prompt = build_prompt(state)
    response = llm.invoke(prompt)
    plan = parse_response(response)
    return {"plan": plan}


def create_workflow() -> StateGraph:
    """
    Tworzy i konfiguruje graf workflow.
    """
    workflow = StateGraph(TrainerState)

    # Dodaj węzły
    workflow.add_node("retrieve", retrieve_exercises)
    workflow.add_node("plan", generate_plan)

    # Dodaj krawędzie
    workflow.add_edge("retrieve", "plan")

    # Punkty startowy i końcowy
    workflow.set_entry_point("retrieve")
    workflow.set_finish_point("plan")

    return workflow.compile()
```

---

## Częste błędy i pułapki

### 1. Zapomnienie o set_entry_point

```python
⚠️ BŁĄD: Brak punktu startowego

workflow.add_node("retrieve", retrieve_exercises)
workflow.add_node("plan", generate_plan)
workflow.add_edge("retrieve", "plan")
# workflow.set_entry_point("retrieve")  ← BRAKUJE!

app = workflow.compile()
# Error: No entry point defined
```

### 2. Zwracanie całego stanu zamiast zmian

```python
⚠️ BŁĄD: Nadpisanie całego stanu

def bad_node(state: TrainerState) -> dict:
    exercises = search(...)
    # Zwraca CAŁY stan - nadpisuje wszystko!
    return {
        "num_people": state["num_people"],
        "difficulty": state["difficulty"],
        "exercises": exercises,
        "plan": None
    }

✓ POPRAWNIE: Zwróć tylko zmiany

def good_node(state: TrainerState) -> dict:
    exercises = search(...)
    # Zwraca TYLKO zmiany
    return {"exercises": exercises}
```

### 3. Niepołączone węzły

```python
⚠️ BŁĄD: Węzeł bez krawędzi

workflow.add_node("retrieve", retrieve_exercises)
workflow.add_node("plan", generate_plan)
workflow.add_node("validate", validate_plan)  # ← nie jest połączony!

workflow.add_edge("retrieve", "plan")
workflow.set_finish_point("plan")

# "validate" nigdy się nie wykona!
```

### 4. Cykl bez warunku wyjścia

```python
⚠️ BŁĄD: Nieskończona pętla

workflow.add_edge("generate", "validate")
workflow.add_edge("validate", "generate")  # ← pętla bez warunku!

# Rozwiązanie: użyj conditional_edges
def check_valid(state):
    if state["is_valid"]:
        return "end"
    return "generate"  # spróbuj ponownie

workflow.add_conditional_edges("validate", check_valid)
```

---

## Dalsze materiały

### Dokumentacja
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Tutorials](https://langchain-ai.github.io/langgraph/tutorials/)

### Przykłady
- [ReAct Agent](https://langchain-ai.github.io/langgraph/tutorials/introduction/) - agent z reasoning
- [Multi-Agent](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/) - wiele agentów

### Porównanie z alternatywami
| Biblioteka | Opis | Kiedy używać |
|------------|------|--------------|
| **LangGraph** | Grafy stanowe | Złożone workflow, warunki |
| LangChain | Łańcuchy | Proste pipeline'y |
| Prefect | Workflow engine | ETL, data pipelines |
| Airflow | DAG scheduler | Batch processing |

---

## Podsumowanie

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LANGGRAPH                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KONCEPTY:                                                                  │
│  • State   - dane przepływające przez graf                                 │
│  • Nodes   - funkcje wykonujące operacje                                   │
│  • Edges   - połączenia między węzłami                                     │
│                                                                             │
│  WORKFLOW W TRENERAI:                                                       │
│                                                                             │
│    ┌──────────────┐         ┌──────────────┐                               │
│    │   retrieve   │────────▶│     plan     │                               │
│    │              │         │              │                               │
│    │ Szuka w      │         │ Generuje     │                               │
│    │ Qdrant       │         │ przez LLM    │                               │
│    └──────────────┘         └──────────────┘                               │
│                                                                             │
│  ZALETY:                                                                    │
│  ✓ Czytelna struktura                                                      │
│  ✓ Łatwe testowanie                                                        │
│  ✓ Wsparcie dla warunków                                                   │
│  ✓ Debugowanie                                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Poprzedni dokument:** [02_what_is_vector_db.md](./02_what_is_vector_db.md) - Czym jest baza wektorowa?

**Następny dokument:** [04_what_is_rag.md](./04_what_is_rag.md) - Czym jest RAG?
