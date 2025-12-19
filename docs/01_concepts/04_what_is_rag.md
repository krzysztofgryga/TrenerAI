# Co to jest RAG (Retrieval Augmented Generation)?

## Spis treści
1. [Analogia ze świata rzeczywistego](#analogia-ze-świata-rzeczywistego)
2. [Definicja techniczna](#definicja-techniczna)
3. [Problem który RAG rozwiązuje](#problem-który-rag-rozwiązuje)
4. [Jak działa RAG](#jak-działa-rag)
5. [RAG w TrenerAI](#rag-w-trenerai)
6. [Porównanie podejść](#porównanie-podejść)
7. [Częste błędy i pułapki](#częste-błędy-i-pułapki)
8. [Dalsze materiały](#dalsze-materiały)

---

## Analogia ze świata rzeczywistego

### Student przed egzaminem

Wyobraź sobie dwa typy studentów:

**Student A (LLM bez RAG):**
```
Profesor: "Opisz procedurę sercowo-płucnej w waszym szpitalu"

Student A: "Hmm... pamiętam coś z wykładów...
            Chyba 30 uciśnięć klatki piersiowej,
            potem 2 oddechy... ale nie jestem pewien
            szczegółów procedury w naszym szpitalu."

Problem: Odpowiada z pamięci, może się mylić,
         nie zna specyficznych procedur szpitala
```

**Student B (LLM z RAG):**
```
Profesor: "Opisz procedurę sercowo-płucną w waszym szpitalu"

Student B: *otwiera notes z procedurami szpitala*
           *znajduje sekcję o resuscytacji*
           *czyta i formułuje odpowiedź*

           "Zgodnie z procedurą szpitala XYZ (strona 47):
            1. Zawołaj pomoc i zadzwoń 112
            2. 30 uciśnięć na głębokość 5cm
            3. 2 oddechy ratunkowe
            4. Kontynuuj do przyjazdu AED..."

Zaleta: Odpowiada na podstawie DOKUMENTÓW,
        nie zgaduje, może cytować źródło
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RAG = STUDENT Z NOTATKAMI                           │
└─────────────────────────────────────────────────────────────────────────────┘

  BEZ RAG (tylko pamięć)              Z RAG (pamięć + dokumenty)
  ──────────────────────              ─────────────────────────

  ┌─────────────────┐                 ┌─────────────────┐
  │    Pytanie      │                 │    Pytanie      │
  └────────┬────────┘                 └────────┬────────┘
           │                                   │
           ▼                                   ▼
  ┌─────────────────┐                 ┌─────────────────┐
  │      LLM        │                 │    Wyszukaj     │◀── NOWY KROK!
  │                 │                 │    dokumenty    │
  │ "Zgaduję na     │                 └────────┬────────┘
  │  podstawie      │                          │
  │  treningu"      │                          ▼
  └────────┬────────┘                 ┌─────────────────┐
           │                          │   Dokumenty     │
           │                          │   (kontekst)    │
           │                          └────────┬────────┘
           │                                   │
           │                                   ▼
           │                          ┌─────────────────┐
           │                          │      LLM        │
           │                          │                 │
           │                          │ "Na podstawie   │
           │                          │  dokumentów..." │
           │                          └────────┬────────┘
           │                                   │
           ▼                                   ▼
  ┌─────────────────┐                 ┌─────────────────┐
  │   Odpowiedź     │                 │   Odpowiedź     │
  │   (może błędna) │                 │   (oparta na    │
  └─────────────────┘                 │    źródłach)    │
                                      └─────────────────┘
```

---

## Definicja techniczna

### Co to jest RAG?

**RAG (Retrieval Augmented Generation)** to technika która:

1. **Retrieval** (Wyszukiwanie) - znajdź relevantne dokumenty
2. **Augmented** (Wzbogacenie) - dodaj dokumenty do promptu
3. **Generation** (Generowanie) - LLM generuje odpowiedź na podstawie dokumentów

### Wzór RAG

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WZÓR RAG                                        │
└─────────────────────────────────────────────────────────────────────────────┘

  ODPOWIEDŹ = LLM( PYTANIE + RELEVANTNE_DOKUMENTY )

  Gdzie:
  • PYTANIE = to co użytkownik chce wiedzieć
  • RELEVANTNE_DOKUMENTY = wyszukane z bazy wektorowej
  • LLM = model językowy generujący odpowiedź
```

### Składniki RAG

| Składnik | Rola | W TrenerAI |
|----------|------|------------|
| **Baza dokumentów** | Przechowuje wiedzę | Ćwiczenia w Qdrant |
| **Embedder** | Zamienia tekst na wektory | FastEmbed |
| **Vector Store** | Wyszukuje podobne dokumenty | Qdrant |
| **LLM** | Generuje odpowiedź | OpenAI / Ollama |

---

## Problem który RAG rozwiązuje

### Ograniczenia LLM

LLM (Large Language Model) jak GPT-4 ma ograniczenia:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OGRANICZENIA LLM                                      │
└─────────────────────────────────────────────────────────────────────────────┘

  1. HALUCYNACJE
  ──────────────
  LLM może wymyślać fakty które brzmią prawdziwie

  User: "Jakie ćwiczenia są w bazie TrenerAI?"
  LLM:  "W bazie są: Quantum Jumps, Teleportation Squats..."
        └── WYMYŚLONE! LLM nie zna naszej bazy


  2. NIEAKTUALNA WIEDZA
  ─────────────────────
  LLM wie tylko to, na czym był trenowany (data cutoff)

  User: "Jakie nowe ćwiczenia dodaliśmy wczoraj?"
  LLM:  "Nie mam informacji o waszych ostatnich zmianach"
        └── NIE WIE! Trenowany na danych do 2024


  3. BRAK WIEDZY DOMENOWEJ
  ────────────────────────
  LLM nie zna specyficznych danych twojej firmy/projektu

  User: "Ile ćwiczeń warmup mamy w bazie?"
  LLM:  "Nie mam dostępu do waszej bazy danych"
        └── NIE MA DOSTĘPU! To nasze prywatne dane
```

### Jak RAG to rozwiązuje

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RAG ROZWIĄZUJE PROBLEMY                               │
└─────────────────────────────────────────────────────────────────────────────┘

  1. HALUCYNACJE → CYTOWANIE ŹRÓDEŁ
  ─────────────────────────────────

  Prompt: "Na podstawie TYCH ćwiczeń stwórz plan: [Burpees, Pompki, Plank]"
  LLM:    "Plan: 1. Burpees, 2. Pompki, 3. Plank"
          └── OPARTE NA DOSTARCZONYCH DANYCH!


  2. NIEAKTUALNA WIEDZA → ŚWIEŻE DOKUMENTY
  ────────────────────────────────────────

  Baza wektorowa zawsze ma aktualne ćwiczenia
  (dodaliśmy wczoraj → dziś są w bazie → RAG je znajdzie)


  3. BRAK WIEDZY DOMENOWEJ → TWOJE DOKUMENTY
  ──────────────────────────────────────────

  Wyszukujemy z NASZEJ bazy, nie z internetu
  LLM dostaje NASZE ćwiczenia jako kontekst
```

---

## Jak działa RAG

### Dwie fazy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FAZY RAG                                             │
└─────────────────────────────────────────────────────────────────────────────┘

  FAZA 1: INDEXING (jednorazowo)         FAZA 2: QUERYING (każde zapytanie)
  ──────────────────────────────         ─────────────────────────────────

  ┌───────────────┐                      ┌───────────────┐
  │  Dokumenty    │                      │   Zapytanie   │
  │  (exercises)  │                      │   użytkownika │
  └───────┬───────┘                      └───────┬───────┘
          │                                      │
          ▼                                      ▼
  ┌───────────────┐                      ┌───────────────┐
  │   Chunking    │                      │   Embedding   │
  │ (dzielenie)   │                      │   zapytania   │
  └───────┬───────┘                      └───────┬───────┘
          │                                      │
          ▼                                      ▼
  ┌───────────────┐                      ┌───────────────┐
  │   Embedding   │                      │  Similarity   │
  │  dokumentów   │                      │    Search     │
  └───────┬───────┘                      └───────┬───────┘
          │                                      │
          ▼                                      ▼
  ┌───────────────┐                      ┌───────────────┐
  │  Vector Store │◀─────────────────────│  Top K docs   │
  │   (Qdrant)    │                      │  (najbliższe) │
  └───────────────┘                      └───────┬───────┘
                                                 │
                                                 ▼
                                         ┌───────────────┐
                                         │ Prompt + docs │
                                         │     ↓         │
                                         │     LLM       │
                                         │     ↓         │
                                         │  Odpowiedź    │
                                         └───────────────┘
```

### Krok po kroku

**Faza 1: Indexing (seed_database.py)**

```python
# 1. Wczytaj dokumenty
exercises = load_exercises()  # 100 ćwiczeń

# 2. Zamień na format Document
documents = [
    Document(
        page_content="Burpees: wyskok z pompką",
        metadata={"type": "main", "level": "hard"}
    ),
    ...
]

# 3. Wygeneruj embeddingi i zapisz do Qdrant
Qdrant.from_documents(documents, embeddings, ...)
```

**Faza 2: Querying (agent.py)**

```python
# 1. Użytkownik wysyła zapytanie
query = "hard workout exercises"

# 2. Wyszukaj podobne dokumenty
docs = vector_store.similarity_search(query, k=20)
# docs = [Burpees, Pistol Squats, Diamond Push-ups, ...]

# 3. Zbuduj prompt z dokumentami
prompt = f"""
Na podstawie tych ćwiczeń stwórz plan treningowy:

Dostępne ćwiczenia:
{format_exercises(docs)}

Parametry:
- Liczba osób: 5
- Tryb: circuit
"""

# 4. Wyślij do LLM
plan = llm.invoke(prompt)
```

---

## RAG w TrenerAI

### Architektura RAG

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAG W TRENERAI                                     │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │           UŻYTKOWNIK                │
                    │                                     │
                    │  POST /generate-training            │
                    │  {                                  │
                    │    "num_people": 5,                 │
                    │    "difficulty": "hard",            │
                    │    "mode": "circuit"                │
                    │  }                                  │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                              RETRIEVAL                                   │
  │  ┌─────────────────────────────────────────────────────────────────┐    │
  │  │                                                                  │    │
  │  │  query = "hard workout exercises"                               │    │
  │  │                    │                                            │    │
  │  │                    ▼                                            │    │
  │  │  ┌──────────────────────────────────┐                          │    │
  │  │  │         FastEmbed                 │                          │    │
  │  │  │  embed(query) → [0.8, 0.3, ...]  │                          │    │
  │  │  └──────────────────────────────────┘                          │    │
  │  │                    │                                            │    │
  │  │                    ▼                                            │    │
  │  │  ┌──────────────────────────────────┐                          │    │
  │  │  │           Qdrant                  │                          │    │
  │  │  │  similarity_search(vector, k=20) │                          │    │
  │  │  └──────────────────────────────────┘                          │    │
  │  │                    │                                            │    │
  │  │                    ▼                                            │    │
  │  │  Top 20 ćwiczeń: [Burpees, Pistol Squats, ...]                 │    │
  │  │                                                                  │    │
  │  └─────────────────────────────────────────────────────────────────┘    │
  └─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                             AUGMENTATION                                 │
  │  ┌─────────────────────────────────────────────────────────────────┐    │
  │  │                                                                  │    │
  │  │  prompt = f"""                                                  │    │
  │  │  Jesteś ekspertem fitness. Stwórz plan dla 5 osób.             │    │
  │  │                                                                  │    │
  │  │  DOSTĘPNE ĆWICZENIA (użyj TYLKO tych):                          │    │
  │  │  Warmup: Jumping Jacks, High Knees, Boxing Run                  │    │
  │  │  Main: Burpees, Pistol Squats, Diamond Push-ups                 │    │
  │  │  Cooldown: Child's Pose, Stretching                             │    │
  │  │                                                                  │    │
  │  │  Tryb: circuit (różne ćwiczenia dla każdej osoby)               │    │
  │  │  """                                                            │    │
  │  │                                                                  │    │
  │  └─────────────────────────────────────────────────────────────────┘    │
  └─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                              GENERATION                                  │
  │  ┌─────────────────────────────────────────────────────────────────┐    │
  │  │                                                                  │    │
  │  │  ┌────────────────────────────────┐                             │    │
  │  │  │        OpenAI / Ollama          │                             │    │
  │  │  │                                 │                             │    │
  │  │  │  Generuje TrainingPlan:         │                             │    │
  │  │  │  {                              │                             │    │
  │  │  │    "warmup": [Jumping Jacks],   │                             │    │
  │  │  │    "main_part": [Burpees, ...], │                             │    │
  │  │  │    "cooldown": [Child's Pose]   │                             │    │
  │  │  │  }                              │                             │    │
  │  │  └────────────────────────────────┘                             │    │
  │  │                                                                  │    │
  │  └─────────────────────────────────────────────────────────────────┘    │
  └─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │          ODPOWIEDŹ                  │
                    │                                     │
                    │  TrainingPlan z ćwiczeniami         │
                    │  TYLKO z naszej bazy!               │
                    └─────────────────────────────────────┘
```

### Dlaczego to ważne w TrenerAI

```
BEZ RAG:
─────────
User: "Stwórz plan z trudnymi ćwiczeniami"
LLM:  "Plan: 1. Quantum Burpees, 2. Teleportation Jumps..."
      └── WYMYŚLONE ĆWICZENIA! Nie ma ich w naszej bazie!


Z RAG:
──────
User: "Stwórz plan z trudnymi ćwiczeniami"

1. Retrieval: Szukamy w Qdrant "hard exercises"
   → Znajdujemy: Burpees, Pistol Squats, Diamond Push-ups

2. Augmentation: Prompt zawiera TYLKO te ćwiczenia
   "Użyj TYLKO tych ćwiczeń: Burpees, Pistol Squats, Diamond Push-ups"

3. Generation: LLM tworzy plan
   → Plan zawiera TYLKO prawdziwe ćwiczenia z bazy!
```

---

## Porównanie podejść

### LLM vs RAG vs Fine-tuning

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PORÓWNANIE PODEJŚĆ                                       │
└─────────────────────────────────────────────────────────────────────────────┘

  PODEJŚCIE        OPIS                      KIEDY UŻYWAĆ
  ─────────        ────                      ────────────

  Pure LLM         LLM odpowiada z pamięci   Ogólne pytania
  ────────                                   (nie potrzebujesz
                   User → LLM → Answer       specyficznych danych)


  RAG              LLM + wyszukane           Specyficzne dane
  ───              dokumenty                 które się zmieniają
                                             (ćwiczenia, produkty,
                   User → Search → LLM       dokumentacja)
                              ↓
                           Docs


  Fine-tuning      LLM wytrenowany na        Styl, format,
  ───────────      twoich danych             specjalistyczna
                                             terminologia
                   User → Custom LLM
```

### Kiedy RAG, kiedy Fine-tuning?

| Aspekt | RAG | Fine-tuning |
|--------|-----|-------------|
| **Koszt** | Niski (tylko baza wektorowa) | Wysoki (trening modelu) |
| **Aktualizacja** | Łatwa (dodaj do bazy) | Trudna (re-trening) |
| **Dokładność** | Cytuje źródła | Może halucynować |
| **Czas setup** | Minuty | Godziny/dni |
| **Wiedza** | Fakty, dane | Styl, format |

**TrenerAI używa RAG bo:**
- Ćwiczenia mogą się zmieniać (dodawanie nowych)
- Potrzebujemy DOKŁADNYCH nazw z bazy
- Nie chcemy żeby LLM wymyślał ćwiczenia

---

## Częste błędy i pułapki

### 1. Za mało kontekstu (k za małe)

```
⚠️ BŁĄD: k=3, ale potrzebujemy 10 ćwiczeń do planu

similarity_search(query, k=3)  # tylko 3 ćwiczenia

LLM: "Mam tylko 3 ćwiczenia, nie mogę stworzyć
      pełnego planu dla 5 osób w trybie circuit"
```

**Rozwiązanie:** Zwiększ `k` (w TrenerAI używamy k=20)

### 2. Za dużo kontekstu (k za duże)

```
⚠️ BŁĄD: k=1000, context window przepełniony

similarity_search(query, k=1000)

Prompt: "Oto 1000 ćwiczeń: [...]"  # 50,000 tokenów!

Error: Context length exceeded (max 4096)
```

**Rozwiązanie:** Ogranicz `k` do rozsądnej wartości

### 3. Słabe zapytanie

```
⚠️ BŁĄD: Niespecyficzne zapytanie

query = "exercises"  # za ogólne

Wyniki: losowe ćwiczenia, nie pasujące do poziomu

✓ LEPIEJ:

query = f"{difficulty} workout exercises for training"
# "hard workout exercises for training"
```

### 4. Brak instrukcji w prompcie

```
⚠️ BŁĄD: LLM nie wie że ma używać tylko podanych ćwiczeń

prompt = f"Stwórz plan. Ćwiczenia: {exercises}"

LLM: *używa ćwiczeń z promptu ALE DODAJE własne*

✓ LEPIEJ:

prompt = f"""
Stwórz plan używając WYŁĄCZNIE tych ćwiczeń:
{exercises}

NIE DODAWAJ żadnych innych ćwiczeń!
"""
```

---

## Dalsze materiały

### Dokumentacja
- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)
- [RAG From Scratch (YouTube)](https://www.youtube.com/playlist?list=PLfaIDFEXuae2LXbO1_PKyVJiQ23ZztA0x)

### Artykuły
- [What is RAG?](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [RAG vs Fine-tuning](https://www.anyscale.com/blog/fine-tuning-vs-rag)

### Wzorce RAG
| Wzorzec | Opis |
|---------|------|
| **Naive RAG** | Prosty: retrieve → generate |
| **Advanced RAG** | + re-ranking, query rewriting |
| **Modular RAG** | Komponenty wymienne |
| **Agentic RAG** | Agent decyduje czy szukać |

---

## Podsumowanie

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 RAG                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RAG = Retrieval + Augmented + Generation                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. RETRIEVAL: Znajdź relevantne dokumenty                          │   │
│  │       similarity_search("hard exercises") → [Burpees, ...]         │   │
│  │                                                                      │   │
│  │  2. AUGMENTATION: Dodaj dokumenty do promptu                        │   │
│  │       prompt = "Na podstawie TYCH ćwiczeń: [Burpees, ...]"         │   │
│  │                                                                      │   │
│  │  3. GENERATION: LLM generuje odpowiedź                              │   │
│  │       llm.invoke(prompt) → TrainingPlan                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ROZWIĄZUJE:                                                                │
│  ✓ Halucynacje (LLM używa tylko podanych danych)                           │
│  ✓ Nieaktualna wiedza (baza zawsze aktualna)                               │
│  ✓ Brak wiedzy domenowej (nasze dokumenty)                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Poprzedni dokument:** [03_what_is_langgraph.md](./03_what_is_langgraph.md) - Czym jest LangGraph?

**Następny dokument:** [05_what_is_pydantic.md](./05_what_is_pydantic.md) - Czym jest Pydantic?
