#!/usr/bin/env python3
"""
Prosty skrypt do testowania API bez frontendu.

Użycie:
    python scripts/test_api.py

Wymaga uruchomionego backendu:
    uvicorn app.main:app --reload
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_chat(message: str, session_id: str = "test") -> dict:
    """Testuj endpoint /chat"""
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": message, "session_id": session_id}
    )
    return response.json()


def test_generate_training() -> dict:
    """Testuj generowanie planu treningowego"""
    response = requests.post(
        f"{BASE_URL}/generate-training",
        json={
            "num_people": 3,
            "difficulty": "medium",
            "rest_time": 60,
            "mode": "circuit",
            "warmup_count": 2,
            "main_count": 4,
            "cooldown_count": 2
        }
    )
    return response.json()


def print_result(name: str, result: dict):
    """Ładnie wyświetl wynik"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def run_interactive():
    """Tryb interaktywny - rozmawiaj z API"""
    session_id = "interactive"
    print("\n🏋️ TrenerAI - Tryb interaktywny")
    print("Wpisz 'exit' aby wyjść\n")

    while True:
        message = input("Ty: ").strip()
        if message.lower() in ['exit', 'quit', 'q']:
            break

        try:
            result = test_chat(message, session_id)
            print(f"\nAI: {result.get('response', result)}\n")

            if result.get('needs_confirmation'):
                print("(Czekam na potwierdzenie: tak/nie)\n")

        except requests.exceptions.ConnectionError:
            print("❌ Błąd: Backend nie jest uruchomiony!")
            print("   Uruchom: uvicorn app.main:app --reload")
            break


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "-i":
        # Tryb interaktywny
        run_interactive()
    else:
        # Testy automatyczne
        print("🧪 Testowanie API TrenerAI")

        try:
            # Test health
            r = requests.get(f"{BASE_URL}/health")
            print(f"✓ Backend online: {r.json()}")

            # Test komendy
            print_result("Lista klientów", test_chat("lista klientów"))
            print_result("Dodaj klienta", test_chat("dodaj Jana 30 lat"))
            print_result("Potwierdź", test_chat("tak"))
            print_result("Lista po dodaniu", test_chat("lista klientów"))

            # Test LLM (RAG)
            print_result("Pytanie do LLM", test_chat("jakie ćwiczenia na plecy?"))

        except requests.exceptions.ConnectionError:
            print("❌ Backend nie jest uruchomiony!")
            print("   Uruchom: uvicorn app.main:app --reload")
