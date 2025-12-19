# Co to jest Embedding?

## Spis treści
1. [Analogia ze świata rzeczywistego](#analogia-ze-świata-rzeczywistego)
2. [Definicja techniczna](#definicja-techniczna)
3. [Jak to działa - wizualizacja](#jak-to-działa---wizualizacja)
4. [Przykład kodu](#przykład-kodu)
5. [Jak to jest używane w TrenerAI](#jak-to-jest-używane-w-trenerai)
6. [Częste błędy i pułapki](#częste-błędy-i-pułapki)
7. [Dalsze materiały](#dalsze-materiały)

---

## Analogia ze świata rzeczywistego

### Biblioteka i katalog

Wyobraź sobie, że jesteś bibliotekarzem w ogromnej bibliotece z milionami książek. Ktoś przychodzi i mówi:

> "Szukam czegoś o psach, ale nie wiem dokładnie czego"

Jak znajdziesz odpowiednie książki?

**Metoda tradycyjna (słowa kluczowe):**
- Szukasz książek z słowem "pies" w tytule
- Problem: "Czworonożny przyjaciel człowieka" nie zostanie znaleziona!

**Metoda z embeddingami (znaczenie):**
- Każda książka ma "kod znaczeniowy" - liczbę która opisuje O CZYM jest książka
- Książki o podobnych tematach mają podobne kody
- "Psy: przewodnik" i "Czworonożny przyjaciel człowieka" mają prawie identyczne kody!

```
TRADYCYJNE WYSZUKIWANIE          WYSZUKIWANIE Z EMBEDDINGAMI
─────────────────────────        ────────────────────────────

  Szukaj: "pies"                   Szukaj: "pies"
        │                                │
        ▼                                ▼
  ┌───────────────┐                ┌───────────────┐
  │ Porównaj      │                │ Zamień na     │
  │ litery        │                │ wektor [0.8,  │
  │               │                │ 0.2, -0.5...] │
  └───────┬───────┘                └───────┬───────┘
          │                                │
          ▼                                ▼
  Tylko: "Psy: przewodnik"         Wszystkie książki o psach:
                                   • "Psy: przewodnik"
                                   • "Czworonożny przyjaciel"
                                   • "Tresura szczeniąt"
                                   • "Rasy psów"
```

---

## Definicja techniczna

### Co to jest wektor?

Wektor to po prostu **lista liczb**. Na przykład:
- `[1.0, 2.5, -0.3]` - wektor 3-wymiarowy
- `[0.23, -0.87, 0.12, ..., 0.45]` - wektor 384-wymiarowy

### Co to jest embedding?

**Embedding** to proces zamiany tekstu (słowa, zdania, dokumentu) na wektor liczb w taki sposób, że:

1. **Podobne znaczeniowo teksty** → **bliskie wektory**
2. **Różne znaczeniowo teksty** → **odległe wektory**

```
TEKST                           WEKTOR (uproszczony do 3D)
─────                           ──────────────────────────

"pies"          ───────────▶    [0.9, 0.8, 0.1]
"szczeniak"     ───────────▶    [0.85, 0.75, 0.15]   ← blisko "pies"!
"kot"           ───────────▶    [0.7, 0.6, 0.2]      ← dość blisko
"samochód"      ───────────▶    [-0.5, 0.1, 0.9]     ← daleko!
"rower"         ───────────▶    [-0.4, 0.2, 0.85]    ← blisko "samochód"
```

### Jak mierzyć "bliskość"?

Używamy **podobieństwa kosinusowego** (cosine similarity):
- `1.0` = identyczne znaczenie
- `0.0` = brak związku
- `-1.0` = przeciwne znaczenie

```
            podobieństwo("pies", "szczeniak") = 0.95  ✓ bardzo podobne
            podobieństwo("pies", "samochód")  = 0.12  ✗ niepodobne
```

---

## Jak to działa - wizualizacja

### Przestrzeń 2D (uproszczona)

W rzeczywistości embeddingi mają 384+ wymiarów, ale zobaczmy to na prostszym przykładzie 2D:

```
                    ▲ wymiar 2 (np. "żywe vs nieżywe")
                    │
               1.0  │    •pies  •kot
                    │      •szczeniak
                    │
               0.5  │              •ryba
                    │
                    │
               0.0  ├─────────────────────────────────▶ wymiar 1
                    │                                    (np. "małe vs duże")
                    │
              -0.5  │
                    │         •samochód
                    │              •ciężarówka
              -1.0  │    •rower
                    │
                   -1.0  -0.5   0.0   0.5   1.0
```

**Obserwacje:**
- Zwierzęta są w górnej części (żywe)
- Pojazdy są w dolnej części (nieżywe)
- Pies i szczeniak są bardzo blisko siebie
- Samochód i ciężarówka są blisko siebie

### Przestrzeń 384D (rzeczywista)

W TrenerAI używamy modelu **FastEmbed** który generuje wektory 384-wymiarowe:

```
"Burpees: wyskok z pompką, maksymalne tempo"
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │           FastEmbed                  │
    │    (model all-MiniLM-L6-v2)         │
    └─────────────────────────────────────┘
                    │
                    ▼
    [0.023, -0.087, 0.145, 0.032, -0.198, 0.067, ..., 0.089]
     ▲                                                    ▲
     │                                                    │
     └────────────── 384 liczb ───────────────────────────┘
```

---

## Przykład kodu

### Instalacja

```bash
pip install fastembed
```

### Podstawowy przykład

```python
from fastembed import TextEmbedding

# 1. Utwórz model embeddingów
model = TextEmbedding()

# 2. Teksty do zakodowania
texts = [
    "Burpees: wyskok z pompką",
    "Pompki klasyczne",
    "Rozciąganie pleców",
]

# 3. Wygeneruj embeddingi
embeddings = list(model.embed(texts))

# 4. Sprawdź wynik
print(f"Liczba tekstów: {len(embeddings)}")
print(f"Wymiary wektora: {len(embeddings[0])}")
print(f"Pierwsze 5 wartości: {embeddings[0][:5]}")
```

**Wynik:**
```
Liczba tekstów: 3
Wymiary wektora: 384
Pierwsze 5 wartości: [0.023, -0.087, 0.145, 0.032, -0.198]
```

### Porównywanie podobieństwa

```python
import numpy as np
from fastembed import TextEmbedding

def cosine_similarity(vec1, vec2):
    """Oblicz podobieństwo kosinusowe między dwoma wektorami."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)

# Wygeneruj embeddingi
model = TextEmbedding()
texts = ["Burpees", "Pompki", "Medytacja"]
embeddings = list(model.embed(texts))

# Porównaj podobieństwo
sim_burpees_pompki = cosine_similarity(embeddings[0], embeddings[1])
sim_burpees_medytacja = cosine_similarity(embeddings[0], embeddings[2])

print(f"Burpees vs Pompki: {sim_burpees_pompki:.3f}")     # ~0.75
print(f"Burpees vs Medytacja: {sim_burpees_medytacja:.3f}") # ~0.25
```

---

## Jak to jest używane w TrenerAI

### Podczas seedowania bazy (seed_database.py)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROCES SEEDOWANIA                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  exercises.json                    FastEmbed                      Qdrant
  ──────────────                    ─────────                      ──────

  ┌────────────────┐          ┌─────────────────┐          ┌─────────────────┐
  │ {              │          │                 │          │ Kolekcja:       │
  │  "name":       │──────────│  embed()        │──────────│ "gym_exercises" │
  │  "Burpees",    │  tekst   │                 │  wektor  │                 │
  │  "desc": "..." │          │ "Burpees: ..."  │          │ [0.02, -0.08,   │
  │ }              │          │      │          │          │  0.14, ...]     │
  │                │          │      ▼          │          │ + metadata      │
  │ 100 ćwiczeń    │          │ [384 liczb]     │          │                 │
  └────────────────┘          └─────────────────┘          └─────────────────┘
```

**Kod w seed_database.py:**
```python
# Tworzymy model embeddingów
embeddings = FastEmbedEmbeddings()

# Dla każdego ćwiczenia, tekst = "nazwa: opis"
content = f"{ex['name']}: {ex['desc']}"
# np. "Burpees: wyskok z pompką, maksymalne tempo"

# Qdrant.from_documents() automatycznie:
# 1. Wywołuje embeddings.embed() na każdym tekście
# 2. Zapisuje wektor + metadata do bazy
```

### Podczas wyszukiwania (agent.py)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROCES WYSZUKIWANIA                                │
└─────────────────────────────────────────────────────────────────────────────┘

  Zapytanie użytkownika         FastEmbed              Qdrant
  ─────────────────────         ─────────              ──────

  difficulty="hard"             embed()            similarity_search()
        │                          │                      │
        ▼                          ▼                      ▼
  "hard workout              [0.15, -0.23,         Znajdź 20 najbliższych
   exercises"                 0.87, ...]           wektorów
        │                          │                      │
        └──────────────────────────┴──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────┐
                    │ Wyniki (posortowane po          │
                    │ podobieństwie):                 │
                    │                                 │
                    │ 1. Burpees (0.89)              │
                    │ 2. Pistol Squats (0.85)        │
                    │ 3. Diamond Push-ups (0.82)     │
                    │ ...                            │
                    └─────────────────────────────────┘
```

**Kod w agent.py:**
```python
def retrieve_exercises(state: TrainerState) -> dict:
    # Budujemy zapytanie tekstowe
    query = f"{state['difficulty']} workout exercises"

    # similarity_search robi:
    # 1. embed(query) → wektor zapytania
    # 2. Szuka najbliższych wektorów w Qdrant
    # 3. Zwraca dokumenty
    docs = vector_store.similarity_search(query, k=20)

    return {"exercises": docs}
```

---

## Częste błędy i pułapki

### 1. Różne modele = różne embeddingi

```
⚠️ BŁĄD: Użycie innego modelu do wyszukiwania niż do seedowania

  Seedowanie:    model_A.embed("Burpees") → [0.1, 0.2, ...]
  Wyszukiwanie:  model_B.embed("Burpees") → [0.8, -0.3, ...]  ← INNY WEKTOR!

  Wynik: Wyszukiwanie nie znajdzie nic sensownego!
```

**Rozwiązanie:** Zawsze używaj tego samego modelu do seedowania i wyszukiwania.

### 2. Wymiary muszą się zgadzać

```
⚠️ BŁĄD: Model 384D vs baza skonfigurowana na 768D

  Seedowanie:    embed() → [384 liczb]
  Baza Qdrant:   oczekuje [768 liczb]

  Wynik: Error!
```

### 3. Jakość tekstu wpływa na jakość embeddingu

```
SŁABY TEKST                         DOBRY TEKST
───────────                         ───────────
"w1"                                "Jumping Jacks: skoki z
                                     unoszeniem rąk, rozgrzewka"

Embedding nie ma kontekstu!         Embedding ma pełny kontekst
```

**W TrenerAI:** Dlatego używamy `f"{name}: {desc}"` zamiast samej nazwy.

### 4. Język ma znaczenie

```
⚠️ Model all-MiniLM-L6-v2 jest trenowany głównie na angielskim

  "Pompki" vs "Push-ups"

  Embedding "Push-ups" będzie lepszy bo model lepiej rozumie angielski.
```

---

## Dalsze materiały

### Dokumentacja
- [FastEmbed Documentation](https://qdrant.github.io/fastembed/)
- [Sentence Transformers](https://www.sbert.net/)

### Artykuły
- [What are Embeddings?](https://vickiboykis.com/what_are_embeddings/) - świetne wprowadzenie
- [Illustrated Word2Vec](https://jalammar.github.io/illustrated-word2vec/) - wizualne wyjaśnienie

### Modele embeddingów
| Model | Wymiary | Rozmiar | Jakość |
|-------|---------|---------|--------|
| all-MiniLM-L6-v2 | 384 | 80MB | Dobra |
| all-mpnet-base-v2 | 768 | 420MB | Lepsza |
| text-embedding-ada-002 (OpenAI) | 1536 | API | Najlepsza |

---

## Podsumowanie

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EMBEDDING                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TEKST ──────▶ MODEL ──────▶ WEKTOR [384 liczb] ──────▶ BAZA WEKTOROWA     │
│                                                                             │
│  • Podobne teksty → Bliskie wektory                                        │
│  • Umożliwia wyszukiwanie "po znaczeniu" zamiast "po słowach"              │
│  • W TrenerAI: szukamy ćwiczeń pasujących do poziomu trudności             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Następny dokument:** [02_what_is_vector_db.md](./02_what_is_vector_db.md) - Czym jest baza wektorowa?
