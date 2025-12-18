import os
from dotenv import load_dotenv
from langchain_core.documents import Document
# ✅ ZMIANA: Używamy stabilnego wrappera z community zamiast eksperymentalnego
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises")

# BAZA TRENINGOWA
raw_exercises = [
    # --- ROZGRZEWKA ---
    {"id": "w1", "name": "Pajacyki", "type": "warmup", "level": "easy", "desc": "Skoki z wymachami rąk."},
    {"id": "w2", "name": "Bieg bokserski", "type": "warmup", "level": "easy",
     "desc": "Bieg w miejscu z ciosami prostymi."},
    {"id": "w3", "name": "Krążenia bioder", "type": "warmup", "level": "easy", "desc": "Obszerne krążenia biodrami."},
    {"id": "w4", "name": "Wymachy ramion", "type": "warmup", "level": "easy",
     "desc": "Dynamiczne wymachy w płaszczyźnie poziomej."},
    {"id": "w5", "name": "Przysiady bez obciążenia", "type": "warmup", "level": "easy",
     "desc": "Szybkie przysiady rozgrzewkowe."},

    # --- CZĘŚĆ GŁÓWNA (EASY) ---
    {"id": "m_e1", "name": "Przysiad klasyczny", "type": "main", "level": "easy",
     "desc": "Przysiad z ciężarem własnego ciała."},
    {"id": "m_e2", "name": "Pompki na kolanach", "type": "main", "level": "easy", "desc": "Ułatwiona wersja pompki."},
    {"id": "m_e3", "name": "Plank (Deska)", "type": "main", "level": "easy", "desc": "Utrzymaj pozycję przez 30s."},

    # --- CZĘŚĆ GŁÓWNA (MEDIUM) ---
    {"id": "m_m1", "name": "Pompki klasyczne", "type": "main", "level": "medium",
     "desc": "Klatka do samej ziemi, ciało proste."},
    {"id": "m_m2", "name": "Wykroki chodzone", "type": "main", "level": "medium",
     "desc": "Idź przed siebie robiąc głębokie wykroki."},
    {"id": "m_m3", "name": "Kettlebell Swing", "type": "main", "level": "medium",
     "desc": "Wymach odważnikiem z biodra."},
    {"id": "m_m4", "name": "Podciąganie australijskie", "type": "main", "level": "medium",
     "desc": "Podciąganie na TRX lub niskim drążku."},

    # --- CZĘŚĆ GŁÓWNA (HARD) ---
    {"id": "m_h1", "name": "Burpees", "type": "main", "level": "hard",
     "desc": "Padnij, powstań, wyskocz. Maksymalne tempo."},
    {"id": "m_h2", "name": "Pompki diamentowe", "type": "main", "level": "hard",
     "desc": "Dłonie złączone w kształt diamentu."},
    {"id": "m_h3", "name": "Pistolety (Przysiad jednonóż)", "type": "main", "level": "hard",
     "desc": "Przysiad na jednej nodze."},
    {"id": "m_h4", "name": "Man Maker", "type": "main", "level": "hard",
     "desc": "Pompka, wiosłowanie hantlem i wyciśnięcie nad głowę."},

    # --- RELAKS ---
    {"id": "c1", "name": "Pozycja dziecka", "type": "cooldown", "level": "easy",
     "desc": "Rozluźnienie pleców na macie."},
    {"id": "c2", "name": "Rozciąganie kanapowe", "type": "cooldown", "level": "easy",
     "desc": "Rozciąganie mięśnia czworogłowego przy ścianie."},
    {"id": "c3", "name": "Zwis na drążku", "type": "cooldown", "level": "easy",
     "desc": "Luźny zwis dla dekompresji kręgosłupa."},
]


def main():
    print("🚀 Rozpoczynam indeksowanie bazy (FastEmbed)...")

    # 1. Przygotowanie dokumentów
    documents = []
    for ex in raw_exercises:
        metadata = {"id": ex["id"], "name": ex["name"], "type": ex["type"], "level": ex["level"]}
        content = f"{ex['name']}: {ex['desc']}"
        documents.append(Document(page_content=content, metadata=metadata))

    # 2. Inicjalizacja Embeddings
    embeddings = FastEmbedEmbeddings()

    print(f"📤 Wysyłanie {len(documents)} wektorów do Qdrant...")
    print(f"🔗 Adres: {QDRANT_URL}, Kolekcja: {COLLECTION_NAME}")

    # 3. Jedna prosta komenda, która robi wszystko (Tworzy kolekcję i dodaje dane)
    # Używamy importu z langchain_community - jest niezawodny
    Qdrant.from_documents(
        documents,
        embeddings,
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
        force_recreate=True  # To czyści starą kolekcję, więc nie musisz robić tego ręcznie
    )

    print("✅ Sukces! Baza danych została załadowana.")


if __name__ == "__main__":
    main()