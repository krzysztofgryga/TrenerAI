# Instrukcja Obslugi TrenerAI

## Spis tresci

1. [Architektura systemu](#architektura-systemu)
2. [Jak frontend komunikuje sie z backendem](#jak-frontend-komunikuje-sie-z-backendem)
3. [Endpointy API](#endpointy-api)
4. [Przeplyw danych](#przeplyw-danych)
5. [Uruchomienie aplikacji](#uruchomienie-aplikacji)
6. [Komendy czatu](#komendy-czatu)

---

## Architektura systemu

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│                         (React + TypeScript)                             │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ ChatInterface│  │SavedWorkouts │  │ClientsManager│  │   Sidebar   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────────────┘  │
│         │                 │                 │                            │
│         └─────────────────┼─────────────────┘                            │
│                           │                                              │
│                    ┌──────┴──────┐                                       │
│                    │backendService│  <-- Warstwa komunikacji z API       │
│                    └──────┬──────┘                                       │
└───────────────────────────┼──────────────────────────────────────────────┘
                            │
                            │ HTTP (fetch)
                            │ http://localhost:8000
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                     │
│                      (FastAPI + Python)                                  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                         main.py                                  │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐             │    │
│  │  │  /chat  │  │/clients │  │/workouts│  │/generate│             │    │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘             │    │
│  └───────┼────────────┼───────────┼────────────┼───────────────────┘    │
│          │            │           │            │                         │
│          ▼            ▼           ▼            ▼                         │
│  ┌───────────┐  ┌──────────────────────┐  ┌─────────────┐               │
│  │  agent.py │  │ data/clients.json    │  │  agent.py   │               │
│  │  (LLM)    │  │ data/workouts.json   │  │ (LangGraph) │               │
│  └─────┬─────┘  └──────────────────────┘  └──────┬──────┘               │
│        │                                         │                       │
│        ▼                                         ▼                       │
│  ┌───────────┐                            ┌───────────┐                  │
│  │  Ollama   │                            │  Qdrant   │                  │
│  │ (LLM)     │                            │ (Vector DB)│                 │
│  └───────────┘                            └───────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Jak frontend komunikuje sie z backendem

### 1. Warstwa komunikacji: `backendService.ts`

Frontend NIE komunikuje sie bezposrednio z backendem. Wszystkie wywolania przechodza przez plik `backendService.ts`:

```typescript
// frontend/backendService.ts

const API_URL = 'http://localhost:8000';  // Adres backendu

// Przyklad: Wyslanie wiadomosci do czatu
export const getChatResponse = async (message: string, history: []) => {
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history })
  });
  const data = await response.json();
  return data.response;
};
```

### 2. Schemat komunikacji

```
┌────────────────┐         ┌─────────────────┐         ┌────────────┐
│  Uzytkownik    │         │    Frontend     │         │   Backend  │
│  (przegladarka)│         │    (React)      │         │  (FastAPI) │
└───────┬────────┘         └────────┬────────┘         └─────┬──────┘
        │                           │                        │
        │ 1. Wpisuje wiadomosc      │                        │
        │ ─────────────────────────>│                        │
        │                           │                        │
        │                           │ 2. POST /chat          │
        │                           │ {message, history}     │
        │                           │ ──────────────────────>│
        │                           │                        │
        │                           │                        │ 3. Sprawdza komendy
        │                           │                        │    lub wywoluje LLM
        │                           │                        │
        │                           │ 4. {response: "..."}   │
        │                           │ <──────────────────────│
        │                           │                        │
        │ 5. Wyswietla odpowiedz    │                        │
        │ <─────────────────────────│                        │
        │                           │                        │
```

### 3. Jak komponenty uzywaja API

**ChatInterface.tsx:**
```typescript
import { getChatResponse } from '../backendService';

// Gdy uzytkownik wysyla wiadomosc:
const responseText = await getChatResponse(input, history);
setMessages([...messages, { role: 'model', content: responseText }]);
```

**App.tsx (zarzadzanie klientami):**
```typescript
import * as api from './backendService';

// Ladowanie danych przy starcie:
useEffect(() => {
  const loadData = async () => {
    const clients = await api.getClients();      // GET /clients
    const workouts = await api.getWorkouts();    // GET /workouts
    setClients(clients);
    setSavedItems(workouts);
  };
  loadData();
}, []);

// Dodawanie klienta:
const handleAddClient = async (client) => {
  await api.addClient(client);                   // POST /clients
  setClients([client, ...clients]);
};
```

---

## Endpointy API

### Tabela wszystkich endpointow

| Metoda | Endpoint | Opis | Request Body | Response |
|--------|----------|------|--------------|----------|
| GET | `/` | Status API | - | `{status, version}` |
| GET | `/health` | Health check | - | `{status: "healthy"}` |
| POST | `/chat` | Czat z AI + komendy | `{message, history}` | `{response}` |
| GET | `/clients` | Lista klientow | - | `[{id, name, ...}]` |
| POST | `/clients` | Dodaj klienta | `{id, name, age, ...}` | `{status, client}` |
| PUT | `/clients/{id}` | Aktualizuj klienta | `{id, name, age, ...}` | `{status, client}` |
| DELETE | `/clients/{id}` | Usun klienta | - | `{status: "ok"}` |
| GET | `/workouts` | Lista treningow | - | `[{id, title, ...}]` |
| POST | `/workouts` | Dodaj trening | `{id, title, content}` | `{status, workout}` |
| DELETE | `/workouts/{id}` | Usun trening | - | `{status: "ok"}` |
| POST | `/generate-training` | Generuj plan (RAG) | `{num_people, difficulty, ...}` | `{warmup, main_part, cooldown}` |

### Przyklady wywolan

**1. Czat z AI:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "lista klientów", "history": []}'
```

**2. Dodanie klienta:**
```bash
curl -X POST http://localhost:8000/clients \
  -H "Content-Type: application/json" \
  -d '{
    "id": "123",
    "name": "Jan Kowalski",
    "age": 30,
    "weight": 80,
    "goal": "Schudnac 5kg",
    "notes": "",
    "createdAt": "19.12.2024",
    "progress": []
  }'
```

---

## Przeplyw danych

### 1. Czat z AI (bez komendy)

```
Uzytkownik: "Stworz plan treningowy na mase"
                    │
                    ▼
┌─────────────────────────────────────┐
│        ChatInterface.tsx            │
│  getChatResponse(message, history)  │
└─────────────────┬───────────────────┘
                  │ POST /chat
                  ▼
┌─────────────────────────────────────┐
│            main.py                  │
│  1. parse_chat_command() → None     │  (brak komendy)
│  2. get_vector_store()              │  (polacz z Qdrant)
│  3. similarity_search()             │  (znajdz cwiczenia)
│  4. get_llm().invoke()              │  (wyslij do Ollama)
└─────────────────┬───────────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│    Qdrant     │   │    Ollama     │
│ (cwiczenia)   │   │  (generuje    │
│               │   │   odpowiedz)  │
└───────────────┘   └───────────────┘
```

### 2. Komenda czatu (np. "dodaj klienta")

```
Uzytkownik: "dodaj klienta: Jan, 30 lat, 80kg, cel: masa"
                    │
                    ▼
┌─────────────────────────────────────┐
│            main.py                  │
│  1. parse_chat_command()            │
│     → {action: "add_client",        │
│        data: "Jan, 30 lat..."}      │
│                                     │
│  2. execute_chat_command()          │
│     → Parsuje dane                  │
│     → save_clients()                │
│     → Zwraca potwierdzenie          │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│       data/clients.json             │
│  [{"id": "...", "name": "Jan"...}]  │
└─────────────────────────────────────┘
```

### 3. Zapis treningu z czatu do panelu

```
┌──────────────────────────────────────────────────────────────────┐
│                      ChatInterface                                │
│                                                                   │
│  AI: "# PLAN TRENINGOWY..."                                      │
│                                                                   │
│  [Zapisz] ← Uzytkownik klika                                     │
│     │                                                             │
│     │ onSaveWorkout(title, content)                              │
│     ▼                                                             │
└─────┬────────────────────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────────────────────────┐
│                         App.tsx                                   │
│                                                                   │
│  handleSaveWorkout = async (title, content) => {                 │
│    const newItem = { id, title, content, date };                 │
│    await api.addWorkout(newItem);     ──────────────┐            │
│    setSavedItems([newItem, ...prev]);               │            │
│  }                                                  │            │
└─────────────────────────────────────────────────────┼────────────┘
                                                      │
                                                      │ POST /workouts
                                                      ▼
                                        ┌─────────────────────────┐
                                        │   data/workouts.json    │
                                        └─────────────────────────┘
```

---

## Uruchomienie aplikacji

### Wymagania

- Python 3.10+
- Node.js 18+
- Docker (dla Qdrant i Ollama)

### Krok 1: Uruchom uslugi Docker

```bash
cd /home/user/TrenerAI
docker-compose up -d
```

To uruchamia:
- **Qdrant** na porcie `6333` (baza wektorowa)
- **Ollama** na porcie `11434` (LLM)

### Krok 2: Skonfiguruj backend

```bash
# Utworz plik .env
cat > .env << EOF
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=gym_exercises
EOF

# Zainstaluj zaleznosci
pip install -r requirements.txt

# Zaladuj cwiczenia do bazy
python seed_database.py
```

### Krok 3: Uruchom backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend dostepny pod: `http://localhost:8000`
Dokumentacja API: `http://localhost:8000/docs`

### Krok 4: Uruchom frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend dostepny pod: `http://localhost:5173`

### Schemat portow

```
┌─────────────────────────────────────────────────────┐
│                    LOCALHOST                         │
│                                                      │
│  :5173  ─── Frontend (React/Vite)                   │
│  :8000  ─── Backend (FastAPI)                       │
│  :6333  ─── Qdrant (Vector DB)                      │
│  :11434 ─── Ollama (LLM)                            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Komendy czatu

### Zarzadzanie klientami

| Komenda | Przyklad | Opis |
|---------|----------|------|
| Lista klientow | `lista klientów` | Wyswietla wszystkich podopiecznych |
| Dodaj klienta | `dodaj klienta: Jan Kowalski, 30 lat, 80kg, cel: schudnac` | Dodaje nowego podopiecznego |
| Dane klienta | `dane klienta: Jan` | Pokazuje szczegoly podopiecznego |
| Usun klienta | `usuń klienta: Jan` | Usuwa podopiecznego z bazy |
| Treningi klienta | `treningi dla: Jan` | Pokazuje zapisane treningi klienta |

### Przyklady uzycia

```
Ty: lista klientów

AI: # BAZA PODOPIECZNYCH

    | Imię | Wiek | Waga | Cel |
    |---|---|---|---|
    | Jan Kowalski | 30 | 80kg | Schudnac 5kg |
    | Anna Nowak | 25 | 60kg | Budowa masy |
```

```
Ty: dodaj klienta: Piotr Wisniewski, 35 lat, 90kg, cel: redukcja

AI: # DODANO PODOPIECZNEGO

    ✓ **Piotr Wisniewski** zostal dodany do bazy.

    | Parametr | Wartosc |
    |---|---|
    | Wiek | 35 lat |
    | Waga | 90 kg |
    | Cel | redukcja |
```

---

## Struktura plikow

```
TrenerAI/
├── app/
│   ├── main.py          # Glowny plik API (endpointy)
│   ├── agent.py         # LangGraph workflow (RAG)
│   └── models/
│       └── exercise.py  # Modele Pydantic
├── data/
│   ├── exercises.json   # 100 cwiczen (seed)
│   ├── clients.json     # Dane klientow (runtime)
│   └── workouts.json    # Zapisane treningi (runtime)
├── frontend/
│   ├── App.tsx          # Glowny komponent React
│   ├── backendService.ts # <-- KOMUNIKACJA Z API
│   ├── types.ts         # TypeScript interfaces
│   └── components/
│       ├── ChatInterface.tsx
│       ├── ClientsManager.tsx
│       ├── SavedWorkouts.tsx
│       └── Sidebar.tsx
├── docker-compose.yml   # Qdrant + Ollama
├── .env                 # Konfiguracja
└── requirements.txt     # Zaleznosci Python
```

---

## Debugowanie

### 1. Sprawdz czy backend dziala

```bash
curl http://localhost:8000/
# Oczekiwana odpowiedz: {"status":"TrenerAI API Online","version":"0.2.0"}
```

### 2. Sprawdz konfiguracje

```bash
curl http://localhost:8000/debug/config
```

### 3. Sprawdz logi backendu

Backend loguje wszystkie requesty:
```
2024-12-19 10:00:00 - app.main - INFO - Chat request: lista klientów...
```

### 4. Sprawdz Network tab w przegladarce

1. Otworz DevTools (F12)
2. Przejdz do zakladki "Network"
3. Filtruj po "Fetch/XHR"
4. Sprawdz requesty do `localhost:8000`

---

## FAQ

**Q: Frontend nie laczy sie z backendem?**
A: Sprawdz czy backend dziala na porcie 8000. Sprawdz CORS w `main.py`.

**Q: Czat nie odpowiada?**
A: Sprawdz czy Ollama dziala: `curl http://localhost:11434/api/tags`

**Q: Brak cwiczen w odpowiedziach?**
A: Uruchom `python seed_database.py` aby zaladowac cwiczenia do Qdrant.

**Q: Klienci nie zapisuja sie?**
A: Sprawdz czy katalog `data/` istnieje i ma odpowiednie uprawnienia.
