# TrenerAI Flutter Frontend

Mobile/web app for the TrenerAI training plan generator.

## Setup

1. Install Flutter SDK: https://flutter.dev/docs/get-started/install

2. **Initialize platform files** (required first time):
```bash
cd frontend
flutter create . --project-name trener_ai
```
This generates platform-specific folders (web/, android/, ios/, etc.)

3. Get dependencies:
```bash
flutter pub get
```

4. Run the app:
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

## Troubleshooting

### "This application is not configured to build on the web"
Run `flutter create . --project-name trener_ai` to generate platform files.

### Shader compilation errors
This is a known Flutter issue. Try:
```bash
flutter clean
flutter pub get
flutter run -d chrome
```

### CORS errors in browser
Make sure the backend has CORS enabled (it does by default).
