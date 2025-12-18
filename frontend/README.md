# TrenerAI Flutter Frontend

Mobile/web app for the TrenerAI training plan generator.

## Setup

1. Install Flutter SDK: https://flutter.dev/docs/get-started/install

2. Get dependencies:
```bash
cd frontend
flutter pub get
```

3. Run the app:
```bash
# Web
flutter run -d chrome

# Android (with emulator running)
flutter run -d android

# iOS (macOS only)
flutter run -d ios
```

## Backend Connection

The app automatically detects the correct backend URL:
- **Web**: `http://localhost:8000`
- **Android Emulator**: `http://10.0.2.2:8000`
- **iOS/Desktop**: `http://localhost:8000`

Make sure the backend is running before using the app.

## Building

```bash
# Web
flutter build web

# Android APK
flutter build apk

# iOS
flutter build ios
```
