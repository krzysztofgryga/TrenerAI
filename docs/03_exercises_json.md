# Dokumentacja: data/exercises.json

## Spis treści
1. [Cel pliku](#cel-pliku)
2. [Struktura JSON](#struktura-json)
3. [Kategorie ćwiczeń](#kategorie-ćwiczeń)
4. [Konwencja nazewnictwa ID](#konwencja-nazewnictwa-id)
5. [Jak dodać nowe ćwiczenie](#jak-dodać-nowe-ćwiczenie)
6. [Walidacja pliku](#walidacja-pliku)

---

## Cel pliku

Plik `data/exercises.json` to **źródło danych** dla bazy wektorowej:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRZEPŁYW DANYCH                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  data/exercises.json          seed_database.py              Qdrant
  ─────────────────            ────────────────              ──────

  ┌─────────────────┐         ┌─────────────────┐        ┌─────────────────┐
  │ 100 ćwiczeń     │────────▶│ load_exercises()│───────▶│ 100 wektorów    │
  │ w formacie JSON │         │ + embeddings    │        │ + metadata      │
  └─────────────────┘         └─────────────────┘        └─────────────────┘

  EDYTUJESZ TEN PLIK          URUCHAMIASZ SKRYPT         BAZA GOTOWA
  (dodajesz ćwiczenia)        python seed_database.py     DO WYSZUKIWANIA
```

---

## Struktura JSON

### Format pliku

```json
{
  "exercises": [
    {
      "id": "w1",
      "name": "Jumping Jacks",
      "type": "warmup",
      "level": "easy",
      "desc": "Jump with arm swings. Great cardio warmup."
    },
    ...
  ]
}
```

### Diagram struktury

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STRUKTURA exercises.json                             │
└─────────────────────────────────────────────────────────────────────────────┘

  {
    "exercises": [                    ◀── Klucz główny (wymagany)
      ┌─────────────────────────────────────────────────────────────────────┐
      │ {                                                                    │
      │   "id": "w1",              ◀── Unikalny identyfikator               │
      │   "name": "Jumping Jacks", ◀── Nazwa wyświetlana                    │
      │   "type": "warmup",        ◀── Kategoria: warmup/main/cooldown      │
      │   "level": "easy",         ◀── Poziom: easy/medium/hard             │
      │   "desc": "Jump with..."   ◀── Opis dla trenera                     │
      │ },                                                                   │
      └─────────────────────────────────────────────────────────────────────┘
      { ... },
      { ... },
      ...
    ]
  }
```

### Opis pól

| Pole | Typ | Wymagane | Opis |
|------|-----|----------|------|
| `id` | string | ✓ | Unikalny identyfikator ćwiczenia |
| `name` | string | ✓ | Nazwa ćwiczenia (wyświetlana w UI) |
| `type` | string | ✓ | Kategoria: `warmup`, `main`, `cooldown` |
| `level` | string | ✓ | Poziom trudności: `easy`, `medium`, `hard` |
| `desc` | string | ✓ | Krótki opis/instrukcja dla trenera |

---

## Kategorie ćwiczeń

### Podział na kategorie

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    100 ĆWICZEŃ W PLIKU                                       │
└─────────────────────────────────────────────────────────────────────────────┘

                        exercises.json
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ warmup  │          │  main   │          │cooldown │
   │  (20)   │          │  (60)   │          │  (20)   │
   │         │          │         │          │         │
   │ type:   │          │ type:   │          │ type:   │
   │ "warmup"│          │ "main"  │          │"cooldown"│
   └─────────┘          └────┬────┘          └─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         ┌────────┐    ┌────────┐    ┌────────┐
         │  easy  │    │ medium │    │  hard  │
         │  (20)  │    │  (20)  │    │  (20)  │
         │        │    │        │    │        │
         │ level: │    │ level: │    │ level: │
         │ "easy" │    │"medium"│    │ "hard" │
         └────────┘    └────────┘    └────────┘
```

### Warmup (20 ćwiczeń)

```
type: "warmup", level: "easy"

Przykłady:
• Jumping Jacks - skoki z unoszeniem rąk
• High Knees - bieg z wysokim unoszeniem kolan
• Arm Circles - kręcenie ramionami
• Hip Circles - kręcenie biodrami
```

### Main - Easy (20 ćwiczeń)

```
type: "main", level: "easy"

Przykłady:
• Classic Squat - przysiady
• Knee Push-ups - pompki na kolanach
• Plank - deska
• Wall Sit - krzesełko przy ścianie
```

### Main - Medium (20 ćwiczeń)

```
type: "main", level: "medium"

Przykłady:
• Classic Push-ups - pompki klasyczne
• Walking Lunges - wykroki w marszu
• Kettlebell Swing - wahadło z kettlebelem
• Australian Pull-ups - podciąganie australijskie
```

### Main - Hard (20 ćwiczeń)

```
type: "main", level: "hard"

Przykłady:
• Burpees - burpees z wyskokiem
• Diamond Push-ups - pompki diamentowe
• Pistol Squats - przysiady na jednej nodze
• Muscle-ups - wyjścia siłowe
```

### Cooldown (20 ćwiczeń)

```
type: "cooldown", level: "easy"

Przykłady:
• Child's Pose - pozycja dziecka
• Cat-Cow Stretch - kot-krowa
• Pigeon Pose - pozycja gołębia
• Standing Forward Fold - skłon w przód
```

---

## Konwencja nazewnictwa ID

### Wzorzec

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WZORZEC ID                                           │
└─────────────────────────────────────────────────────────────────────────────┘

  WARMUP:     w[numer]           w1, w2, w3, ..., w20
  MAIN EASY:  m_e[numer]         m_e1, m_e2, ..., m_e20
  MAIN MED:   m_m[numer]         m_m1, m_m2, ..., m_m20
  MAIN HARD:  m_h[numer]         m_h1, m_h2, ..., m_h20
  COOLDOWN:   c[numer]           c1, c2, c3, ..., c20
```

### Przykłady

| ID | Typ | Level | Nazwa |
|----|-----|-------|-------|
| `w1` | warmup | easy | Jumping Jacks |
| `w15` | warmup | easy | Shoulder Shrugs |
| `m_e1` | main | easy | Classic Squat |
| `m_m5` | main | medium | Kettlebell Swing |
| `m_h10` | main | hard | Handstand Push-ups |
| `c1` | cooldown | easy | Child's Pose |

---

## Jak dodać nowe ćwiczenie

### Krok 1: Edytuj plik JSON

```json
{
  "exercises": [
    ... istniejące ćwiczenia ...,

    {
      "id": "m_h21",
      "name": "Planche Push-ups",
      "type": "main",
      "level": "hard",
      "desc": "Push-ups with body leaning forward, feet elevated."
    }
  ]
}
```

### Krok 2: Uruchom seed_database.py

```bash
python seed_database.py
```

### Krok 3: Zweryfikuj

```bash
# Sprawdź liczbę ćwiczeń
curl http://localhost:6333/collections/gym_exercises
```

### Diagram procesu

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DODAWANIE NOWEGO ĆWICZENIA                                │
└─────────────────────────────────────────────────────────────────────────────┘

  1. EDYCJA                 2. SEEDOWANIE              3. WERYFIKACJA
  ────────                  ─────────────              ─────────────

  exercises.json            python seed_database.py    curl /collections/
       │                           │                        │
       ▼                           ▼                        ▼
  + nowy rekord            FastEmbed + Qdrant          101 ćwiczeń ✓
```

---

## Walidacja pliku

### Wymagana struktura

```python
# seed_database.py sprawdza:

1. Czy plik istnieje?
   → FileNotFoundError jeśli nie

2. Czy jest poprawny JSON?
   → json.JSONDecodeError jeśli nie

3. Czy ma klucz "exercises"?
   → ValueError jeśli nie

4. Czy każde ćwiczenie ma wymagane pola?
   → KeyError podczas przetwarzania
```

### Sprawdzenie ręczne

```bash
# Walidacja składni JSON
python -c "import json; json.load(open('data/exercises.json'))"

# Sprawdzenie liczby ćwiczeń
python -c "
import json
data = json.load(open('data/exercises.json'))
print(f'Liczba ćwiczeń: {len(data[\"exercises\"])}')
"
```

### Typowe błędy

```
❌ Brak przecinka po elemencie:
   { "id": "w1", ... }     ← brak przecinka!
   { "id": "w2", ... }

❌ Duplikat ID:
   { "id": "w1", "name": "Jumping Jacks", ... },
   { "id": "w1", "name": "High Knees", ... }  ← duplikat!

❌ Błędny type:
   { "type": "warm-up", ... }  ← powinno być "warmup"

❌ Błędny level:
   { "level": "intermediate", ... }  ← powinno być "medium"
```

---

## Powiązania z innymi plikami

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POWIĄZANIA                                           │
└─────────────────────────────────────────────────────────────────────────────┘

  data/exercises.json
         │
         ├──────────▶ seed_database.py
         │            • load_exercises() wczytuje plik
         │            • Tworzy embeddingi
         │            • Zapisuje do Qdrant
         │
         └──────────▶ Qdrant (gym_exercises)
                      • Przechowuje wektory
                      • Umożliwia similarity_search()
```

---

**Poprzedni:** [02_models_exercise_py.md](./02_models_exercise_py.md) - Modele Pydantic

**Następny:** [04_seed_database_py.md](./04_seed_database_py.md) - Seedowanie bazy
