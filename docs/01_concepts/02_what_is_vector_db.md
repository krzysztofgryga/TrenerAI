# Co to jest Baza Wektorowa (Vector Database)?

## Spis treści
1. [Analogia ze świata rzeczywistego](#analogia-ze-świata-rzeczywistego)
2. [Definicja techniczna](#definicja-techniczna)
3. [Porównanie z tradycyjnymi bazami danych](#porównanie-z-tradycyjnymi-bazami-danych)
4. [Jak działa wyszukiwanie](#jak-działa-wyszukiwanie)
5. [Qdrant - baza używana w TrenerAI](#qdrant---baza-używana-w-trenerai)
6. [Przykład kodu](#przykład-kodu)
7. [Jak to jest używane w TrenerAI](#jak-to-jest-używane-w-trenerai)
8. [Częste błędy i pułapki](#częste-błędy-i-pułapki)
9. [Dalsze materiały](#dalsze-materiały)

---

## Analogia ze świata rzeczywistego

### Galeria sztuki

Wyobraź sobie galerię sztuki z tysiącami obrazów. Chcesz znaleźć obrazy "podobne" do tego, który ci się podoba.

**Tradycyjna baza danych (SQL):**
```
Kurator pyta: "Jaki tytuł? Jaki artysta? Jaki rok?"

Ty: "Nie wiem... Chcę coś z podobnym klimatem, kolorami, stylem..."

Kurator: "Nie mogę pomóc. Mam tylko katalog z tytułami i datami."
```

**Baza wektorowa:**
```
Kurator pyta: "Pokaż mi obraz który ci się podoba"

Ty: *pokazujesz obraz zachodu słońca w stylu impresjonistycznym*

Kurator: "Rozumiem! Oto 10 najbardziej podobnych obrazów
         w naszej kolekcji, posortowanych od najbardziej
         do najmniej podobnych"
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GALERIA SZTUKI                                        │
└─────────────────────────────────────────────────────────────────────────────┘

  TRADYCYJNA BAZA                      BAZA WEKTOROWA
  ───────────────                      ───────────────

  "Szukaj: tytuł = 'Zachód'"           "Szukaj: podobne do tego obrazu"
           │                                    │
           ▼                                    ▼
  ┌─────────────────┐                  ┌─────────────────┐
  │ SELECT * FROM   │                  │ Zamień obraz    │
  │ obrazy WHERE    │                  │ na wektor       │
  │ tytuł LIKE      │                  │ [0.2, 0.8, ...] │
  │ '%Zachód%'      │                  │                 │
  └────────┬────────┘                  └────────┬────────┘
           │                                    │
           ▼                                    ▼
  Tylko: "Zachód słońca                Wszystkie podobne:
         w Gdańsku"                    • Zachód nad morzem
                                       • Wschód słońca (też ciepłe kolory!)
                                       • Impresja - światło
                                       • Pejzaż wieczorny
```

---

## Definicja techniczna

### Co to jest baza wektorowa?

**Baza wektorowa** to wyspecjalizowana baza danych, która:

1. **Przechowuje wektory** (listy liczb) zamiast tekstu/liczb
2. **Wyszukuje po podobieństwie** zamiast dokładnego dopasowania
3. **Jest zoptymalizowana** dla operacji na wektorach wielowymiarowych

### Struktura danych

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PUNKT W BAZIE WEKTOROWEJ                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ID: "w1"                                                             │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ WEKTOR: [0.023, -0.087, 0.145, 0.032, -0.198, ..., 0.089]           │   │
│  │         └──────────────── 384 liczb ────────────────────┘           │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ METADATA (payload):                                                  │   │
│  │   • name: "Jumping Jacks"                                           │   │
│  │   • type: "warmup"                                                  │   │
│  │   • level: "easy"                                                   │   │
│  │   • desc: "Jump with arm swings"                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

Każdy punkt (point) w bazie zawiera:
- **ID** - unikalny identyfikator
- **Wektor** - embedding (lista liczb)
- **Metadata** - dodatkowe informacje (filtrowanie, wyświetlanie)

---

## Porównanie z tradycyjnymi bazami danych

### SQL (np. PostgreSQL)

```sql
-- Struktura tabeli
CREATE TABLE exercises (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100),
    type VARCHAR(20),
    level VARCHAR(20),
    description TEXT
);

-- Wyszukiwanie
SELECT * FROM exercises
WHERE type = 'warmup'
  AND level = 'easy';
```

**Ograniczenia:**
- Szuka tylko po DOKŁADNYM dopasowaniu
- "easy" ≠ "łatwe" ≠ "beginner"
- Nie rozumie znaczenia, tylko tekst

### Baza wektorowa (np. Qdrant)

```python
# Wyszukiwanie
results = collection.search(
    query_vector=[0.1, 0.2, ...],  # wektor zapytania
    limit=10,                       # ile wyników
    query_filter={                  # opcjonalne filtry
        "type": "warmup"
    }
)
```

**Zalety:**
- Szuka po PODOBIEŃSTWIE znaczeniowym
- "easy workout" znajdzie też "beginner exercises"
- Rozumie kontekst i znaczenie

### Porównanie wizualne

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SQL vs BAZA WEKTOROWA                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  ZAPYTANIE: "Szukam ćwiczeń cardio dla początkujących"

  SQL (tradycyjna)                    BAZA WEKTOROWA
  ────────────────                    ───────────────

  SELECT * FROM exercises             query = embed("cardio dla początkujących")
  WHERE description LIKE              search(query_vector=query, limit=10)
    '%cardio%'
  AND description LIKE
    '%początkujących%';

        │                                    │
        ▼                                    ▼

  WYNIK: 0 rekordów                   WYNIK: 10 ćwiczeń
  (bo w bazie jest "easy"             • Jumping Jacks (warmup, easy)
   a nie "początkujących")            • High Knees (warmup, easy)
                                      • Boxing Run (warmup, easy)
                                      • ...
```

---

## Jak działa wyszukiwanie

### Algorytm wyszukiwania najbliższych sąsiadów

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WYSZUKIWANIE K-NEAREST NEIGHBORS (KNN)                    │
└─────────────────────────────────────────────────────────────────────────────┘

  1. ZAPYTANIE: "hard exercises"

  2. EMBEDDING ZAPYTANIA:
     embed("hard exercises") → [0.8, 0.3, -0.2, ...]

  3. PORÓWNANIE Z WSZYSTKIMI WEKTORAMI W BAZIE:

     Baza:                                    Odległość od zapytania:
     ─────                                    ───────────────────────
     Burpees      [0.75, 0.35, -0.15, ...]   → 0.12 (bardzo blisko!)
     Pompki       [0.60, 0.40, -0.10, ...]   → 0.28
     Stretching   [-0.30, 0.10, 0.80, ...]   → 0.95 (daleko)
     Plank        [0.50, 0.25, -0.20, ...]   → 0.35
     Medytacja    [-0.50, -0.20, 0.60, ...]  → 1.20 (bardzo daleko)

  4. SORTOWANIE PO ODLEGŁOŚCI (rosnąco):
     1. Burpees     (0.12)
     2. Pompki      (0.28)
     3. Plank       (0.35)
     ...

  5. ZWRÓĆ TOP K (np. k=3):
     → Burpees, Pompki, Plank
```

### Metryki odległości

| Metryka | Opis | Użycie |
|---------|------|--------|
| **Cosine** | Kąt między wektorami | Najczęstsze dla tekstu |
| **Euclidean** | Odległość geometryczna | Dla obrazów |
| **Dot Product** | Iloczyn skalarny | Gdy wektory są znormalizowane |

```
COSINE SIMILARITY (używane w TrenerAI)
──────────────────────────────────────

                    ▲
                   /│
                  / │  wektor A: "Burpees"
                 /  │
                /   │
               / θ  │  θ = kąt między wektorami
              /─────┼────────────────▶
                    │                 wektor B: "hard exercises"
                    │

  cos(θ) = podobieństwo

  θ = 0°   → cos(0°) = 1.0   (identyczne)
  θ = 90°  → cos(90°) = 0.0  (niepowiązane)
  θ = 180° → cos(180°) = -1.0 (przeciwne)
```

---

## Qdrant - baza używana w TrenerAI

### Co to jest Qdrant?

**Qdrant** to open-source'owa baza wektorowa napisana w Rust:
- Szybka i wydajna
- Łatwa w użyciu (Docker, REST API)
- Darmowa dla małych projektów
- Obsługuje filtrowanie po metadanych

### Architektura Qdrant

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              QDRANT                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Kolekcja: "gym_exercises"                     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  Konfiguracja:                                                       │   │
│  │  • vector_size: 384                                                  │   │
│  │  • distance: Cosine                                                  │   │
│  │                                                                      │   │
│  │  Punkty:                                                             │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │ ID: "w1"  │ Vector: [0.02, -0.08, ...]  │ type: "warmup"     │   │   │
│  │  ├──────────────────────────────────────────────────────────────┤   │   │
│  │  │ ID: "w2"  │ Vector: [0.05, -0.12, ...]  │ type: "warmup"     │   │   │
│  │  ├──────────────────────────────────────────────────────────────┤   │   │
│  │  │ ID: "m1"  │ Vector: [0.18, 0.23, ...]   │ type: "main"       │   │   │
│  │  ├──────────────────────────────────────────────────────────────┤   │   │
│  │  │ ...       │ ...                         │ ...                │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  │  100 punktów (ćwiczeń)                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Uruchamianie Qdrant

```bash
# Docker (najprostsze)
docker run -p 6333:6333 qdrant/qdrant

# Lub przez docker-compose (jak w TrenerAI)
docker-compose up -d qdrant
```

### REST API

Qdrant udostępnia REST API na porcie 6333:

```bash
# Sprawdź status
curl http://localhost:6333/

# Lista kolekcji
curl http://localhost:6333/collections

# Szczegóły kolekcji
curl http://localhost:6333/collections/gym_exercises
```

---

## Przykład kodu

### Bezpośrednie użycie Qdrant

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 1. Połącz z Qdrant
client = QdrantClient(host="localhost", port=6333)

# 2. Utwórz kolekcję
client.create_collection(
    collection_name="my_collection",
    vectors_config=VectorParams(
        size=384,           # wymiar wektorów
        distance=Distance.COSINE
    )
)

# 3. Dodaj punkty
client.upsert(
    collection_name="my_collection",
    points=[
        PointStruct(
            id=1,
            vector=[0.1, 0.2, 0.3, ...],  # 384 liczb
            payload={"name": "Burpees", "type": "main"}
        ),
        PointStruct(
            id=2,
            vector=[0.15, 0.25, 0.35, ...],
            payload={"name": "Pompki", "type": "main"}
        )
    ]
)

# 4. Wyszukaj podobne
results = client.search(
    collection_name="my_collection",
    query_vector=[0.12, 0.22, 0.32, ...],
    limit=5
)

for result in results:
    print(f"{result.payload['name']}: {result.score}")
```

### Użycie przez LangChain (jak w TrenerAI)

```python
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.documents import Document

# 1. Model embeddingów
embeddings = FastEmbedEmbeddings()

# 2. Dokumenty do zapisania
documents = [
    Document(
        page_content="Burpees: wyskok z pompką",
        metadata={"id": "m1", "type": "main", "level": "hard"}
    ),
    Document(
        page_content="Jumping Jacks: skoki z rękoma",
        metadata={"id": "w1", "type": "warmup", "level": "easy"}
    )
]

# 3. Zapisz do Qdrant (automatycznie tworzy embeddingi)
vector_store = Qdrant.from_documents(
    documents,
    embeddings,
    url="http://localhost:6333",
    collection_name="gym_exercises",
    force_recreate=True  # usuń starą kolekcję
)

# 4. Wyszukaj
results = vector_store.similarity_search(
    query="hard workout exercises",
    k=5
)

for doc in results:
    print(f"{doc.metadata['id']}: {doc.page_content}")
```

---

## Jak to jest używane w TrenerAI

### Seedowanie (seed_database.py)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SEEDOWANIE BAZY                                      │
└─────────────────────────────────────────────────────────────────────────────┘

  exercises.json                                              Qdrant
  ──────────────                                              ──────

  ┌─────────────────┐                                  ┌─────────────────┐
  │ {               │                                  │ Collection:     │
  │  "id": "w1",    │    ┌─────────────────────┐      │ gym_exercises   │
  │  "name": "...", │───▶│ Document(           │      │                 │
  │  "type": "...", │    │   page_content=     │      │ ┌─────────────┐ │
  │  "desc": "..."  │    │     "name: desc",   │─────▶│ │ ID: "w1"    │ │
  │ }               │    │   metadata={...}    │      │ │ Vec: [...]  │ │
  └─────────────────┘    │ )                   │      │ │ Meta: {...} │ │
                         └─────────────────────┘      │ └─────────────┘ │
  x 100 ćwiczeń                                       │ x 100 punktów   │
                                                      └─────────────────┘
```

**Kod:**
```python
# seed_database.py

# 1. Wczytaj ćwiczenia z JSON
exercises = load_exercises()

# 2. Zamień na dokumenty LangChain
documents = []
for ex in exercises:
    doc = Document(
        page_content=f"{ex['name']}: {ex['desc']}",
        metadata={
            "id": ex["id"],
            "name": ex["name"],
            "type": ex["type"],
            "level": ex["level"]
        }
    )
    documents.append(doc)

# 3. Zapisz do Qdrant
Qdrant.from_documents(
    documents,
    embeddings,
    url=QDRANT_URL,
    collection_name=COLLECTION_NAME,
    force_recreate=True
)
```

### Wyszukiwanie (agent.py)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WYSZUKIWANIE ĆWICZEŃ                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  Zapytanie                 Vector Store               Wyniki
  ─────────                 ────────────               ──────

  difficulty = "hard"       similarity_search()        Lista Document
        │                          │                        │
        ▼                          ▼                        ▼
  query = "hard             ┌─────────────┐            [Doc1, Doc2, Doc3...]
  workout exercises"        │   Qdrant    │                 │
        │                   │             │                 │
        └──────────────────▶│  search()   │─────────────────┘
                            │             │
                            └─────────────┘
```

**Kod:**
```python
# agent.py

def retrieve_exercises(state: TrainerState) -> dict:
    # 1. Połącz z Qdrant
    vector_store = get_vector_store()

    # 2. Zbuduj zapytanie
    query = f"{state['difficulty']} workout exercises"

    # 3. Wyszukaj podobne
    docs = vector_store.similarity_search(query, k=20)

    # 4. Zwróć do następnego węzła
    return {"exercises": docs}
```

---

## Częste błędy i pułapki

### 1. Baza nie jest uruchomiona

```
⚠️ BŁĄD: Connection refused

  Qdrant.from_documents(..., url="http://localhost:6333")

  Error: Connection refused at localhost:6333
```

**Rozwiązanie:**
```bash
# Sprawdź czy Qdrant działa
docker ps | grep qdrant

# Jeśli nie, uruchom
docker-compose up -d qdrant
```

### 2. Kolekcja nie istnieje

```
⚠️ BŁĄD: Collection not found

  vector_store.similarity_search(...)

  Error: Collection 'gym_exercises' not found
```

**Rozwiązanie:**
```bash
# Uruchom seedowanie
python seed_database.py
```

### 3. Niezgodność wymiarów

```
⚠️ BŁĄD: Dimension mismatch

  Kolekcja skonfigurowana na 384 wymiarów
  Ale nowy model embeddingów generuje 768 wymiarów

  Error: Vector dimension mismatch
```

**Rozwiązanie:**
- Usuń kolekcję i seeduj ponownie
- Lub użyj `force_recreate=True`

### 4. Zbyt mało wyników

```
⚠️ PROBLEM: k=5, ale zwraca tylko 2 wyniki

  Możliwe przyczyny:
  1. W bazie jest mało rekordów
  2. Filtry są zbyt restrykcyjne
  3. Threshold podobieństwa odrzuca wyniki
```

---

## Dalsze materiały

### Dokumentacja
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [LangChain Qdrant Integration](https://python.langchain.com/docs/integrations/vectorstores/qdrant)

### Porównanie baz wektorowych
| Baza | Język | Licencja | Wyróżniki |
|------|-------|----------|-----------|
| **Qdrant** | Rust | Apache 2.0 | Szybka, łatwa |
| Pinecone | - | SaaS | Managed, skalowalna |
| Weaviate | Go | BSD-3 | GraphQL API |
| Milvus | C++/Go | Apache 2.0 | Enterprise-grade |
| ChromaDB | Python | Apache 2.0 | Prosta, lokalna |

### Kiedy używać bazy wektorowej?
- ✅ Wyszukiwanie semantyczne (po znaczeniu)
- ✅ Systemy rekomendacji
- ✅ RAG (Retrieval Augmented Generation)
- ✅ Wykrywanie duplikatów
- ❌ Transakcje finansowe
- ❌ Relacje między danymi (użyj SQL)

---

## Podsumowanie

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BAZA WEKTOROWA                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRZECHOWUJE: Wektory (embeddingi) + Metadata                              │
│  WYSZUKUJE: Po podobieństwie znaczeniowym                                  │
│  UŻYCIE W TRENERAI: Znajdowanie ćwiczeń pasujących do poziomu trudności    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Zapytanie: "hard exercises"                                         │   │
│  │       ↓                                                              │   │
│  │  embed() → [0.8, 0.3, -0.2, ...]                                     │   │
│  │       ↓                                                              │   │
│  │  similarity_search() → [Burpees, Pistol Squats, Diamond Push-ups]   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Poprzedni dokument:** [01_what_is_embedding.md](./01_what_is_embedding.md) - Czym są embeddingi?

**Następny dokument:** [03_what_is_langgraph.md](./03_what_is_langgraph.md) - Czym jest LangGraph?
