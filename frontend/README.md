# TrenerAI - Frontend

Aplikacja mobilna AI Trainer zbudowana w React + Vite + Capacitor.

## Technologie

- **React 19** - UI framework
- **Vite 7** - Build tool
- **Capacitor 8** - Native mobile wrapper (iOS/Android)
- **React Router 7** - Nawigacja
- **Lucide React** - Ikony
- **liquid-glass-react** - Efekty glass morphism

## Struktura

```
frontend/
├── src/
│   ├── components/     # Komponenty UI
│   │   ├── ChatMessage.jsx
│   │   ├── GlassCard.jsx
│   │   ├── NavBar.jsx
│   │   ├── ProgressRing.jsx
│   │   └── WorkoutCard.jsx
│   ├── pages/          # Strony aplikacji
│   │   ├── Home.jsx
│   │   ├── Workouts.jsx
│   │   ├── AICoach.jsx
│   │   └── Profile.jsx
│   ├── services/       # API
│   │   └── backendService.js
│   ├── App.jsx
│   └── main.jsx
├── ios/                # Projekt iOS (Xcode)
├── android/            # Projekt Android (Android Studio)
└── capacitor.config.json
```

## Uruchomienie

### Development (przeglądarka)

```bash
cd frontend
npm install
npm run dev
```

Otwórz http://localhost:5173

### Build produkcyjny

```bash
npm run build
```

## Budowanie aplikacji mobilnych

### Wymagania

- **iOS**: macOS + Xcode 15+ + Apple Developer Account ($99/rok)
- **Android**: Android Studio + JDK 17+

### iOS

```bash
# Build i otwórz w Xcode
npm run cap:ios

# Tylko build (bez otwierania)
npm run build:ios
```

W Xcode:
1. Wybierz Team (Apple Developer Account)
2. Wybierz urządzenie/symulator
3. Cmd+R (Run)

### Android

```bash
# Build i otwórz w Android Studio
npm run cap:android

# Tylko build (bez otwierania)
npm run build:android
```

W Android Studio:
1. Poczekaj na Gradle sync
2. Wybierz emulator lub podłącz telefon
3. Shift+F10 (Run)

## Konfiguracja API

Utwórz plik `.env`:

```bash
cp .env.example .env
```

Edytuj `VITE_API_URL`:

```env
# Lokalne dev
VITE_API_URL=http://localhost:8000

# Produkcja
VITE_API_URL=https://api.trenerai.com
```

**Uwaga dla mobile**: Na urządzeniu mobilnym `localhost` nie działa.
Użyj IP komputera w sieci lokalnej:

```env
VITE_API_URL=http://192.168.1.100:8000
```

## Motywy

Aplikacja obsługuje 2 motywy:
- **Fioletowy** (domyślny) - neonowy fiolet/różowy/cyan
- **Złoto-Czarny** - elegancki złoty gradient

Zmiana motywu: NavBar → Ustawienia → Wybierz motyw

## Generowanie APK/IPA

### Android (APK)

```bash
npm run build:android
cd android
./gradlew assembleRelease
```

APK: `android/app/build/outputs/apk/release/app-release.apk`

### iOS (IPA)

W Xcode:
1. Product → Archive
2. Distribute App → Ad Hoc / App Store

## Troubleshooting

### "Cannot connect to backend"

1. Sprawdź czy backend działa: `curl http://localhost:8000/health`
2. Na mobile użyj IP zamiast localhost
3. Sprawdź CORS w backendzie

### iOS build fails

```bash
cd ios/App
pod install --repo-update
```

### Android Gradle error

```bash
cd android
./gradlew clean
```
