# Kompletny Poradnik TrenerAI

## Dla osob ktore nigdy nie pracowaly z frontendem

---

# CZESC 1: PODSTAWOWE POJECIA

## 1.1 Co to jest Frontend i Backend?

Wyobraz sobie restauracje:

```
┌─────────────────────────────────────────────────────────────────┐
│                         RESTAURACJA                              │
│                                                                  │
│   ┌─────────────────┐              ┌─────────────────┐          │
│   │    SALA         │              │     KUCHNIA     │          │
│   │   (Frontend)    │              │    (Backend)    │          │
│   │                 │              │                 │          │
│   │ - Menu          │   Kelner     │ - Gotowanie     │          │
│   │ - Stoliki       │ ──────────── │ - Skladniki     │          │
│   │ - Dekoracje     │   (HTTP)     │ - Przepisy      │          │
│   │                 │              │ - Lodowka       │          │
│   │ Klient widzi    │              │ Klient NIE      │          │
│   │ i uzywa         │              │ widzi           │          │
│   └─────────────────┘              └─────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

**Frontend (Sala):**
- To co uzytkownik WIDZI w przegladarce
- Przyciski, formularze, teksty, kolory
- W naszym przypadku: React + TypeScript

**Backend (Kuchnia):**
- To co dziala "za kulisami" na serwerze
- Baza danych, logika biznesowa, AI
- W naszym przypadku: Python + FastAPI

**HTTP (Kelner):**
- Sposob komunikacji miedzy frontendem a backendem
- Frontend wysyla "zamowienie" (request)
- Backend zwraca "danie" (response)

---

## 1.2 Co to jest React?

React to biblioteka JavaScript do budowania interfejsow uzytkownika.

### Kluczowa koncepcja: KOMPONENTY

Komponent to "klocek LEGO" z ktorego budujesz strone:

```
┌─────────────────────────────────────────────────────────────────┐
│                         APLIKACJA                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                        App.tsx                             │  │
│  │  ┌─────────┐  ┌────────────────────────────────────────┐  │  │
│  │  │ Sidebar │  │              MAIN CONTENT              │  │  │
│  │  │         │  │  ┌──────────────────────────────────┐  │  │  │
│  │  │ [Chat]  │  │  │         ChatInterface            │  │  │  │
│  │  │ [Plany] │  │  │  ┌────────────────────────────┐  │  │  │  │
│  │  │ [Ludzie]│  │  │  │      Message (user)        │  │  │  │  │
│  │  │         │  │  │  └────────────────────────────┘  │  │  │  │
│  │  │         │  │  │  ┌────────────────────────────┐  │  │  │  │
│  │  │         │  │  │  │      Message (AI)          │  │  │  │  │
│  │  │         │  │  │  └────────────────────────────┘  │  │  │  │
│  │  │         │  │  │  ┌────────────────────────────┐  │  │  │  │
│  │  │         │  │  │  │      Input + Button        │  │  │  │  │
│  │  │         │  │  │  └────────────────────────────┘  │  │  │  │
│  │  │         │  │  └──────────────────────────────────┘  │  │  │
│  │  └─────────┘  └────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

Kazdy prostokat to KOMPONENT. Komponenty mozna:
- Uzywac wielokrotnie (np. Message pojawia sie wiele razy)
- Zagniezdac (ChatInterface zawiera Message)
- Przekazywac dane miedzy nimi (props)

---

## 1.3 Co to jest TypeScript?

TypeScript = JavaScript + TYPY

```typescript
// JavaScript (bez typow) - moze byc wszystkim
let wiek = 25;
wiek = "dwadziescia piec";  // OK w JS, ale blad logiczny!

// TypeScript (z typami) - okreslamy co moze byc
let wiek: number = 25;
wiek = "dwadziescia piec";  // BLAD! TypeScript nie pozwoli
```

### Dlaczego to wazne?

Typy pomagaja uniknac bledow ZANIM uruchomisz kod:

```typescript
// Definiujemy "szablon" klienta
interface Client {
  id: string;
  name: string;
  age: number;      // MUSI byc liczba
  weight: number;   // MUSI byc liczba
}

// Teraz TypeScript pilnuje
const klient: Client = {
  id: "123",
  name: "Jan",
  age: "trzydziesci",  // BLAD! Oczekiwano number, dostano string
  weight: 80
};
```

---

## 1.4 Co to jest State (Stan)?

Stan to "pamiec" komponentu. Gdy stan sie zmienia, React automatycznie odswieza widok.

```typescript
// Przyklad: licznik klikniec
import { useState } from 'react';

function Licznik() {
  // useState tworzy "zmienna z pamiecia"
  // count = aktualna wartosc (zaczyna od 0)
  // setCount = funkcja do zmiany wartosci
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Kliknieto: {count} razy</p>
      <button onClick={() => setCount(count + 1)}>
        Kliknij mnie
      </button>
    </div>
  );
}
```

```
PRZED KLIKNIECIEM:          PO KLIKNIECIU:
┌─────────────────┐         ┌─────────────────┐
│ Kliknieto: 0    │  ─────> │ Kliknieto: 1    │
│ [Kliknij mnie]  │         │ [Kliknij mnie]  │
└─────────────────┘         └─────────────────┘

setCount(1) automatycznie odswieza widok!
```

---

## 1.5 Co to jest Props?

Props (properties) to sposob przekazywania danych miedzy komponentami.

```typescript
// Komponent-rodzic
function App() {
  return (
    <Powitanie imie="Jan" wiek={25} />
  );
}

// Komponent-dziecko (otrzymuje props)
function Powitanie(props: { imie: string; wiek: number }) {
  return (
    <div>
      <h1>Czesc, {props.imie}!</h1>
      <p>Masz {props.wiek} lat.</p>
    </div>
  );
}
```

```
┌─────────────────────────────────────────┐
│                 App                      │
│                                          │
│   imie="Jan", wiek=25                    │
│         │                                │
│         ▼ (przekazuje przez props)       │
│   ┌─────────────────────────────────┐   │
│   │          Powitanie              │   │
│   │                                 │   │
│   │   Czesc, Jan!                   │   │
│   │   Masz 25 lat.                  │   │
│   │                                 │   │
│   └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

# CZESC 2: STRUKTURA PROJEKTU

## 2.1 Drzewo plikow z objasnieniami

```
frontend/
│
├── index.html          # Punkt wejscia HTML (minimalna strona)
├── index.tsx           # Punkt wejscia React (uruchamia aplikacje)
├── App.tsx             # GLOWNY KOMPONENT (zarzadza wszystkim)
│
├── types.ts            # Definicje typow TypeScript
├── backendService.ts   # KOMUNIKACJA Z BACKENDEM (fetch)
│
├── components/         # Folder z komponentami UI
│   ├── ChatInterface.tsx    # Interfejs czatu z AI
│   ├── ClientsManager.tsx   # Zarzadzanie klientami
│   ├── SavedWorkouts.tsx    # Lista zapisanych treningow
│   └── Sidebar.tsx          # Menu boczne
│
├── utils/
│   └── pdfExport.ts    # Eksport do PDF
│
├── package.json        # Lista zaleznosci (bibliotek)
├── tsconfig.json       # Konfiguracja TypeScript
├── vite.config.ts      # Konfiguracja bundlera Vite
│
└── INSTRUKCJA.md       # Ten poradnik
```

---

## 2.2 Jak pliki sa ze soba powiazane

```
                    index.html
                        │
                        │ laduje
                        ▼
                    index.tsx
                        │
                        │ renderuje
                        ▼
┌───────────────────────────────────────────────────────────────┐
│                         App.tsx                                │
│                    (GLOWNY KOMPONENT)                         │
│                                                                │
│   importuje typy z ──────────────────────► types.ts           │
│   importuje API z ───────────────────────► backendService.ts  │
│                                                                │
│   renderuje komponenty:                                        │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│   │  Sidebar    │  │ChatInterface│  │ClientsManager│          │
│   └─────────────┘  └─────────────┘  └─────────────┘           │
│                           │                                    │
│                           │ uzywa                              │
│                           ▼                                    │
│                    backendService.ts                           │
│                           │                                    │
│                           │ HTTP fetch                         │
│                           ▼                                    │
│                    Backend (localhost:8000)                    │
└───────────────────────────────────────────────────────────────┘
```

---

# CZESC 3: ANALIZA PLIK PO PLIKU

## 3.1 types.ts - Definicje typow

Ten plik definiuje "szablony" danych uzywanych w aplikacji.

```typescript
// ========================================
// PLIK: frontend/types.ts
// CEL: Definiuje ksztalt danych
// ========================================

// Wiadomosc w czacie
export interface Message {
  id: string;           // Unikalny identyfikator
  role: 'user' | 'model';  // Kto napisal: uzytkownik czy AI
  content: string;      // Tresc wiadomosci
  timestamp: number;    // Kiedy wyslano (ms od 1970)
}

// Zapisany trening
export interface SavedWorkout {
  id: string;
  title: string;        // Nazwa treningu
  content: string;      // Tresc (markdown)
  date: string;         // Data utworzenia
  color?: string;       // Opcjonalny kolor (? = opcjonalne)
}

// Wpis pomiaru (progress klienta)
export interface ProgressEntry {
  id: string;
  date: string;
  weight: number;       // Waga w kg
  bodyFat?: number;     // % tkanki tluszczowej (opcjonalne)
  waist?: number;       // Obwod pasa w cm (opcjonalne)
  notes?: string;       // Notatki (opcjonalne)
}

// Klient/Podopieczny
export interface Client {
  id: string;
  name: string;
  age: number;
  weight: number;
  goal: string;         // Cel treningowy
  notes: string;
  createdAt: string;    // Data dodania
  progress: ProgressEntry[];  // Lista pomiarow
}

// Enum = zbior stalych wartosci
export enum AppView {
  CHAT = 'chat',        // Widok czatu
  SAVED = 'saved',      // Widok zapisanych
  CLIENTS = 'clients',  // Widok klientow
  SETTINGS = 'settings' // Widok ustawien
}
```

### Jak to dziala w praktyce?

```typescript
// DOBRZE - zgodne z interfejsem Client
const klient: Client = {
  id: "1",
  name: "Jan Kowalski",
  age: 30,
  weight: 80,
  goal: "Schudnac",
  notes: "",
  createdAt: "19.12.2024",
  progress: []
};

// ZLE - TypeScript wyrzuci blad
const zlyKlient: Client = {
  id: "1",
  name: "Jan",
  // BRAK: age, weight, goal, notes, createdAt, progress
  // TypeScript: "Property 'age' is missing..."
};
```

---

## 3.2 backendService.ts - Komunikacja z API

Ten plik jest MOSTEM miedzy frontendem a backendem.

```typescript
// ========================================
// PLIK: frontend/backendService.ts
// CEL: Wysylanie requestow HTTP do backendu
// ========================================

import { Client, SavedWorkout } from './types';

// Adres backendu (mozna zmienic przez zmienna srodowiskowa)
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ---------------------------------------------
// CZAT - Wyslanie wiadomosci do AI
// ---------------------------------------------
export const getChatResponse = async (
  message: string,
  history: ChatMessage[] = []
): Promise<string> => {

  // 1. Wysylamy request POST do /chat
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',                              // Metoda HTTP
    headers: { 'Content-Type': 'application/json' },  // Format danych
    body: JSON.stringify({                       // Dane w formacie JSON
      message,      // Wiadomosc od uzytkownika
      history       // Historia rozmowy
    })
  });

  // 2. Odbieramy odpowiedz
  const data = await response.json();

  // 3. Zwracamy tekst odpowiedzi
  return data.response;
};
```

### Jak dziala fetch krok po kroku?

```
FRONTEND                                    BACKEND
────────                                    ───────

1. Uzytkownik wpisuje "lista klientow"
   │
   ▼
2. getChatResponse("lista klientow", [])
   │
   ▼
3. fetch('http://localhost:8000/chat', {
     method: 'POST',
     body: '{"message": "lista klientow", "history": []}'
   })
   │
   │ ──────────── HTTP REQUEST ────────────────────────>
   │
   │                                        4. Backend odbiera request
   │                                           │
   │                                           ▼
   │                                        5. parse_chat_command()
   │                                           │
   │                                           ▼
   │                                        6. execute_chat_command()
   │                                           │
   │                                           ▼
   │                                        7. Zwraca liste klientow
   │
   │ <─────────── HTTP RESPONSE ───────────────────────
   │
   ▼
8. response.json() parsuje odpowiedz
   │
   ▼
9. return data.response
   │
   ▼
10. Wyswietlenie w ChatInterface
```

### Reszta funkcji API:

```typescript
// ---------------------------------------------
// KLIENCI - CRUD (Create, Read, Update, Delete)
// ---------------------------------------------

// Pobierz wszystkich klientow
export const getClients = async (): Promise<Client[]> => {
  const response = await fetch(`${API_URL}/clients`);  // GET request
  return await response.json();
};

// Dodaj nowego klienta
export const addClient = async (client: Client): Promise<boolean> => {
  const response = await fetch(`${API_URL}/clients`, {
    method: 'POST',                    // POST = tworzenie
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(client)
  });
  return response.ok;  // true jesli sukces (status 200-299)
};

// Zaktualizuj istniejacego klienta
export const updateClient = async (client: Client): Promise<boolean> => {
  const response = await fetch(`${API_URL}/clients/${client.id}`, {
    method: 'PUT',                     // PUT = aktualizacja
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(client)
  });
  return response.ok;
};

// Usun klienta
export const deleteClient = async (clientId: string): Promise<boolean> => {
  const response = await fetch(`${API_URL}/clients/${clientId}`, {
    method: 'DELETE'                   // DELETE = usuwanie
  });
  return response.ok;
};

// ---------------------------------------------
// TRENINGI - podobnie jak klienci
// ---------------------------------------------
export const getWorkouts = async (): Promise<SavedWorkout[]> => { ... };
export const addWorkout = async (workout: SavedWorkout): Promise<boolean> => { ... };
export const deleteWorkout = async (workoutId: string): Promise<boolean> => { ... };
```

---

## 3.3 App.tsx - Glowny komponent

To jest "centrala" calej aplikacji.

```typescript
// ========================================
// PLIK: frontend/App.tsx
// CEL: Zarzadza calym UI i stanami aplikacji
// ========================================

import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import SavedWorkouts from './components/SavedWorkouts';
import ClientsManager from './components/ClientsManager';
import { AppView, SavedWorkout, Client } from './types';
import * as api from './backendService';  // Importuje wszystko jako 'api'

const App: React.FC = () => {
  // ==========================================
  // STANY (useState) - "pamiec" aplikacji
  // ==========================================

  // Ktory widok jest aktywny (chat, saved, clients, settings)
  const [activeView, setActiveView] = useState<AppView>(AppView.CHAT);

  // Lista zapisanych treningow
  const [savedItems, setSavedItems] = useState<SavedWorkout[]>([]);

  // Lista klientow
  const [clients, setClients] = useState<Client[]>([]);

  // Czy sidebar jest zwiniety
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);

  // Toast notification (komunikat)
  const [toast, setToast] = useState<{ message: string; visible: boolean }>({
    message: '',
    visible: false
  });

  // ==========================================
  // EFEKTY (useEffect) - akcje przy starcie
  // ==========================================

  // Ladowanie danych przy pierwszym renderze
  useEffect(() => {
    const loadData = async () => {
      // Pobierz dane z backendu ROWNOLEGLE
      const [workouts, clientsData] = await Promise.all([
        api.getWorkouts(),   // GET /workouts
        api.getClients()     // GET /clients
      ]);

      // Zapisz w stanach
      setSavedItems(workouts);
      setClients(clientsData);
    };

    loadData();
  }, []);  // [] = wykonaj tylko raz przy pierwszym renderze

  // ==========================================
  // HANDLERY - funkcje obslugi zdarzen
  // ==========================================

  // Pokaz powiadomienie toast
  const showToast = (message: string) => {
    setToast({ message, visible: true });
    setTimeout(() => {
      setToast(prev => ({ ...prev, visible: false }));
    }, 3000);  // Ukryj po 3 sekundach
  };

  // Zapisz nowy trening
  const handleSaveWorkout = async (title: string, content: string) => {
    const newItem: SavedWorkout = {
      id: Date.now().toString(),  // ID = aktualny czas w ms
      title,
      content,
      date: new Date().toLocaleDateString('pl-PL'),
      color: '#3b82f6'
    };

    await api.addWorkout(newItem);           // Wyslij do backendu
    setSavedItems(prev => [newItem, ...prev]); // Dodaj do stanu
    showToast("Plan zostal zapisany!");
  };

  // Dodaj klienta
  const handleAddClient = async (client: Client) => {
    await api.addClient(client);             // Wyslij do backendu
    setClients(prev => [client, ...prev]);   // Dodaj do stanu
    showToast("Dodano podopiecznego.");
  };

  // Usun klienta
  const handleDeleteClient = async (id: string) => {
    await api.deleteClient(id);              // Wyslij do backendu
    setClients(prev => prev.filter(c => c.id !== id));  // Usun ze stanu
    showToast("Usunieto z bazy.");
  };

  // ==========================================
  // RENDER - co wyswietlamy
  // ==========================================

  return (
    <div className="flex h-screen">
      {/* Menu boczne */}
      <Sidebar
        activeView={activeView}
        onViewChange={setActiveView}  // Przekazujemy funkcje zmiany widoku
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />

      {/* Glowna tresc - zalezna od activeView */}
      <main className="flex-1">
        {activeView === AppView.CHAT && (
          <ChatInterface onSaveWorkout={handleSaveWorkout} />
        )}

        {activeView === AppView.SAVED && (
          <SavedWorkouts items={savedItems} onDelete={handleDeleteSaved} />
        )}

        {activeView === AppView.CLIENTS && (
          <ClientsManager
            clients={clients}
            onAdd={handleAddClient}
            onUpdate={handleUpdateClient}
            onDelete={handleDeleteClient}
          />
        )}
      </main>
    </div>
  );
};

export default App;
```

### Schemat przeplywu danych w App.tsx:

```
┌─────────────────────────────────────────────────────────────────┐
│                           App.tsx                                │
│                                                                  │
│  STANY:                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │ activeView     │  │ savedItems     │  │ clients        │     │
│  │ = 'chat'       │  │ = [...]        │  │ = [...]        │     │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘     │
│          │                   │                   │               │
│          ▼                   ▼                   ▼               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    KOMPONENTY                            │    │
│  │                                                          │    │
│  │  ┌──────────┐    ┌──────────────┐    ┌──────────────┐   │    │
│  │  │ Sidebar  │    │ChatInterface │    │ClientsManager│   │    │
│  │  │          │    │              │    │              │   │    │
│  │  │ props:   │    │ props:       │    │ props:       │   │    │
│  │  │ -active  │    │ -onSaveWork  │    │ -clients     │   │    │
│  │  │ -onView  │    │              │    │ -onAdd       │   │    │
│  │  │ Change   │    │              │    │ -onDelete    │   │    │
│  │  └────┬─────┘    └──────┬───────┘    └──────┬───────┘   │    │
│  │       │                 │                   │            │    │
│  └───────┼─────────────────┼───────────────────┼────────────┘    │
│          │                 │                   │                 │
│          ▼                 ▼                   ▼                 │
│    Klikniecie w      Klikniecie         Klikniecie              │
│    menu zmienia      "Zapisz"           "Dodaj klienta"         │
│    activeView        wywola             wywola                   │
│                      handleSaveWorkout  handleAddClient          │
│                            │                   │                 │
│                            ▼                   ▼                 │
│                      api.addWorkout()    api.addClient()        │
│                            │                   │                 │
│                            ▼                   ▼                 │
│                      BACKEND (FastAPI)   BACKEND (FastAPI)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3.4 ChatInterface.tsx - Interfejs czatu

```typescript
// ========================================
// PLIK: frontend/components/ChatInterface.tsx
// CEL: Interfejs rozmowy z AI
// ========================================

import React, { useState, useRef, useEffect } from 'react';
import { Message } from '../types';
import { getChatResponse } from '../backendService';

// Props = dane ktore komponent otrzymuje od rodzica
interface ChatInterfaceProps {
  onSaveWorkout: (title: string, content: string) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onSaveWorkout }) => {
  // STANY
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'model',
      content: '# SYSTEM GOTOWY\nWprowadz zapytanie...',
      timestamp: Date.now()
    }
  ]);
  const [input, setInput] = useState('');           // Tekst w polu input
  const [isLoading, setIsLoading] = useState(false); // Czy czekamy na AI

  // REF - referencja do elementu DOM (do scrollowania)
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll do dolu gdy pojawia sie nowa wiadomosc
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Obsluga wyslania wiadomosci
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();  // Zapobiegaj przeladowaniu strony
    if (!input.trim() || isLoading) return;

    // 1. Dodaj wiadomosc uzytkownika do listy
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: Date.now()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');        // Wyczysc pole
    setIsLoading(true);  // Pokaz ladowanie

    // 2. Przygotuj historie (ostatnie 6 wiadomosci)
    const history = messages.slice(-6).map(m => ({
      role: m.role,
      content: m.content
    }));

    // 3. Wyslij do backendu i czekaj na odpowiedz
    const responseText = await getChatResponse(input, history);

    // 4. Dodaj odpowiedz AI do listy
    setMessages(prev => [...prev, {
      id: (Date.now() + 1).toString(),
      role: 'model',
      content: responseText,
      timestamp: Date.now()
    }]);
    setIsLoading(false);
  };

  // RENDER
  return (
    <div className="flex flex-col h-full">
      {/* Lista wiadomosci */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            {msg.content}

            {/* Przycisk "Zapisz" tylko dla odpowiedzi AI */}
            {msg.role === 'model' && (
              <button onClick={() => onSaveWorkout(
                msg.content.split('\n')[0],  // Tytul = pierwsza linia
                msg.content                   // Tresc = calosc
              )}>
                Zapisz
              </button>
            )}
          </div>
        ))}

        {/* Indicator ladowania */}
        {isLoading && <div>Analiza...</div>}

        {/* Element do scrollowania */}
        <div ref={messagesEndRef} />
      </div>

      {/* Formularz wprowadzania */}
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Napisz..."
        />
        <button type="submit" disabled={isLoading}>
          Wyslij
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;
```

### Schemat dzialania ChatInterface:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ChatInterface                                │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    LISTA WIADOMOSCI                        │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ [AI] # SYSTEM GOTOWY                                │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ [Ty] lista klientow                                 │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ [AI] # BAZA PODOPIECZNYCH                           │  │  │
│  │  │      | Imie | Wiek | ...                            │  │  │
│  │  │                                      [Zapisz]       │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  [ Napisz wiadomosc...                        ] [Wyslij]  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

KROK PO KROKU:

1. Uzytkownik wpisuje "lista klientow"
2. Klika "Wyslij" lub Enter
3. handleSubmit() sie odpala:
   a) Dodaje wiadomosc uzytkownika do messages
   b) Wysyla getChatResponse() do backendu
   c) Czeka na odpowiedz
   d) Dodaje odpowiedz AI do messages
4. React automatycznie odswieza widok
5. useEffect scrolluje do dolu
```

---

# CZESC 4: JAK ZMODYFIKOWAC KOD

## 4.1 Dodanie nowej komendy czatu

Chcesz dodac komende "pomoc" ktora pokazuje dostepne komendy?

### Krok 1: Zmodyfikuj backend (main.py)

```python
# W funkcji parse_chat_command() dodaj:

def parse_chat_command(message: str) -> Optional[dict]:
    msg = message.lower().strip()

    # NOWA KOMENDA: pomoc
    if any(x in msg for x in ["pomoc", "help", "komendy", "?"]):
        return {"action": "help"}

    # ... reszta kodu ...
```

### Krok 2: Dodaj obsluge w execute_chat_command()

```python
def execute_chat_command(cmd: dict) -> str:
    action = cmd["action"]

    # NOWA OBSLUGA
    if action == "help":
        return """# DOSTEPNE KOMENDY

| Komenda | Opis |
|---------|------|
| `lista klientow` | Pokaz wszystkich podopiecznych |
| `dodaj klienta: Imie, wiek lat, wagakg, cel: opis` | Dodaj nowego |
| `dane klienta: Imie` | Pokaz szczegoly |
| `usun klienta: Imie` | Usun z bazy |
| `treningi dla: Imie` | Pokaz treningi klienta |
| `pomoc` | Ta lista |
"""

    # ... reszta kodu ...
```

### Krok 3: Przetestuj

```bash
# Uruchom backend
uvicorn app.main:app --reload

# W przegladarce wpisz w czacie:
# "pomoc"
```

---

## 4.2 Dodanie nowego pola do klienta

Chcesz dodac pole "email" do klienta?

### Krok 1: Zmodyfikuj types.ts (frontend)

```typescript
export interface Client {
  id: string;
  name: string;
  age: number;
  weight: number;
  goal: string;
  notes: string;
  email: string;        // NOWE POLE
  createdAt: string;
  progress: ProgressEntry[];
}
```

### Krok 2: Zmodyfikuj main.py (backend)

```python
class Client(BaseModel):
    id: str
    name: str
    age: int
    weight: float
    goal: str
    notes: str = ""
    email: str = ""     # NOWE POLE
    createdAt: str
    progress: List[ProgressEntry] = []
```

### Krok 3: Zmodyfikuj ClientsManager.tsx (formularz)

```tsx
// W formularzu dodaj pole input dla email:

<div className="space-y-2">
  <label>Email</label>
  <input
    type="email"
    value={formData.email}
    onChange={e => setFormData({...formData, email: e.target.value})}
    placeholder="jan@example.com"
  />
</div>
```

---

## 4.3 Dodanie nowego widoku

Chcesz dodac widok "Statystyki"?

### Krok 1: Dodaj nowy enum w types.ts

```typescript
export enum AppView {
  CHAT = 'chat',
  SAVED = 'saved',
  CLIENTS = 'clients',
  SETTINGS = 'settings',
  STATS = 'stats'       // NOWY WIDOK
}
```

### Krok 2: Stworz nowy komponent

```typescript
// frontend/components/Statistics.tsx

import React from 'react';
import { Client, SavedWorkout } from '../types';

interface StatisticsProps {
  clients: Client[];
  workouts: SavedWorkout[];
}

const Statistics: React.FC<StatisticsProps> = ({ clients, workouts }) => {
  return (
    <div className="p-8">
      <h1>Statystyki</h1>
      <p>Liczba klientow: {clients.length}</p>
      <p>Liczba treningow: {workouts.length}</p>
    </div>
  );
};

export default Statistics;
```

### Krok 3: Dodaj do App.tsx

```tsx
import Statistics from './components/Statistics';

// W renderze:
{activeView === AppView.STATS && (
  <Statistics clients={clients} workouts={savedItems} />
)}
```

### Krok 4: Dodaj do menu w Sidebar.tsx

```tsx
// Dodaj do tablicy nawigacji:
{ id: AppView.STATS, icon: 'fa-chart-bar', label: 'Statystyki' },
```

---

# CZESC 5: DEBUGOWANIE I ROZWIAZYWANIE PROBLEMOW

## 5.1 Jak debugowac frontend

### Uzyj console.log()

```typescript
const handleSubmit = async () => {
  console.log('1. Wyslano wiadomosc:', input);

  const response = await getChatResponse(input, history);
  console.log('2. Otrzymano odpowiedz:', response);

  // ...
};
```

### Sprawdz Network tab w DevTools

1. Otworz przegladarke (Chrome/Firefox)
2. Kliknij F12 (otwiera DevTools)
3. Przejdz do zakladki "Network"
4. Wyslij wiadomosc w czacie
5. Zobacz request do `/chat`

```
┌─────────────────────────────────────────────────────────────────┐
│ DevTools - Network                                               │
├─────────────────────────────────────────────────────────────────┤
│ Name         │ Status │ Type    │ Size   │ Time                 │
├─────────────────────────────────────────────────────────────────┤
│ chat         │ 200    │ fetch   │ 1.2 KB │ 2.5s                 │
│              │        │         │        │                       │
│ Kliknij "chat" aby zobaczyc szczegoly:                          │
│                                                                  │
│ Request:                                                         │
│ {"message": "lista klientow", "history": []}                    │
│                                                                  │
│ Response:                                                        │
│ {"response": "# BAZA PODOPIECZNYCH\n\n..."}                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5.2 Typowe bledy i rozwiazania

### Blad: "Failed to fetch"

```
┌─────────────────────────────────────────────────────────────────┐
│ OBJAW: Blad polaczenia z backendem                               │
│                                                                  │
│ PRZYCZYNA:                                                       │
│ - Backend nie jest uruchomiony                                   │
│ - Zly adres API                                                  │
│ - CORS blokuje request                                           │
│                                                                  │
│ ROZWIAZANIE:                                                     │
│ 1. Sprawdz czy backend dziala:                                   │
│    curl http://localhost:8000/                                   │
│                                                                  │
│ 2. Sprawdz logi backendu:                                        │
│    Powinno byc "Uvicorn running on http://0.0.0.0:8000"         │
│                                                                  │
│ 3. Sprawdz CORS w main.py:                                       │
│    allow_origins=["*"]                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Blad: "TypeError: Cannot read properties of undefined"

```
┌─────────────────────────────────────────────────────────────────┐
│ OBJAW: Probujemy uzyc czegos co nie istnieje                     │
│                                                                  │
│ PRZYKLAD:                                                        │
│ const name = client.name;  // client jest undefined!             │
│                                                                  │
│ ROZWIAZANIE:                                                     │
│ 1. Uzyj optional chaining (?.)                                   │
│    const name = client?.name;  // Zwroci undefined zamiast bledu│
│                                                                  │
│ 2. Sprawdz czy dane zostaly zaladowane                           │
│    if (!client) return <div>Ladowanie...</div>;                  │
│                                                                  │
│ 3. Dodaj console.log() aby zobaczyc co jest w zmiennej           │
│    console.log('client:', client);                               │
└─────────────────────────────────────────────────────────────────┘
```

### Blad: "Objects are not valid as a React child"

```
┌─────────────────────────────────────────────────────────────────┐
│ OBJAW: Probujemy wyrenderowac obiekt bezposrednio                │
│                                                                  │
│ ZLE:                                                             │
│ return <div>{client}</div>;  // client to obiekt!                │
│                                                                  │
│ DOBRZE:                                                          │
│ return <div>{client.name}</div>;  // uzywamy konkretnego pola    │
│                                                                  │
│ LUB do debugowania:                                              │
│ return <div>{JSON.stringify(client)}</div>;                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5.3 Przydatne komendy

```bash
# FRONTEND
cd frontend

npm install          # Zainstaluj zaleznosci
npm run dev          # Uruchom serwer deweloperski
npm run build        # Zbuduj wersje produkcyjna

# BACKEND
cd ..

pip install -r requirements.txt   # Zainstaluj zaleznosci
uvicorn app.main:app --reload     # Uruchom z auto-reloadem
python seed_database.py           # Zaladuj cwiczenia do Qdrant

# DOCKER
docker-compose up -d              # Uruchom Qdrant + Ollama
docker-compose logs -f            # Pokaz logi
docker-compose down               # Zatrzymaj

# TESTY
curl http://localhost:8000/                    # Status API
curl http://localhost:8000/clients             # Lista klientow
curl http://localhost:11434/api/tags           # Lista modeli Ollama
```

---

# CZESC 6: SLOWNICZEK

| Termin | Znaczenie |
|--------|-----------|
| **Component** | Komponent - "klocek" UI w React |
| **State** | Stan - dane ktore moga sie zmieniac |
| **Props** | Wlasciwosci - dane przekazywane do komponentu |
| **Hook** | Funkcja specjalna React (useState, useEffect) |
| **Render** | Wyswietlenie komponentu na ekranie |
| **API** | Interfejs programistyczny (endpointy backendu) |
| **Endpoint** | Adres URL na backendzie (np. /clients) |
| **Fetch** | Funkcja do wysylania requestow HTTP |
| **Async/Await** | Sposob obslugi operacji asynchronicznych |
| **JSON** | Format danych (JavaScript Object Notation) |
| **TypeScript** | JavaScript z typami |
| **Interface** | Definicja struktury obiektu w TypeScript |
| **CORS** | Cross-Origin Resource Sharing - polityka bezpieczenstwa |
| **RAG** | Retrieval Augmented Generation - technika AI |

---

# CZESC 7: CO DALEJ?

1. **Przeczytaj oficjalna dokumentacje React:**
   https://react.dev/learn

2. **Naucz sie TypeScript:**
   https://www.typescriptlang.org/docs/handbook/intro.html

3. **Poznaj Tailwind CSS (stylowanie):**
   https://tailwindcss.com/docs

4. **Eksperymentuj z kodem:**
   - Zmien tekst przycisku
   - Dodaj nowe pole do formularza
   - Stworz nowy komponent

5. **Uzywaj DevTools:**
   - Console tab - logi i bledy
   - Network tab - requesty HTTP
   - Elements tab - struktura HTML

---

*Dokument wygenerowany dla projektu TrenerAI*
