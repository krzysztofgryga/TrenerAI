#!/usr/bin/env python3
"""
Load all data collections into Qdrant vector database.

Usage:
    python scripts/load_qdrant_collections.py

    # Load specific collection:
    python scripts/load_qdrant_collections.py --collection techniques
    python scripts/load_qdrant_collections.py --collection nutrition
    python scripts/load_qdrant_collections.py --collection programs

    # Load all collections:
    python scripts/load_qdrant_collections.py --all

Requires:
    - Qdrant running on localhost:6333
    - LLM_PROVIDER and related env vars set
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from langchain_core.documents import Document

# Get embedding model based on provider
def get_embeddings():
    """Get embedding model based on LLM_PROVIDER."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings()
    else:
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )


def load_json(file_path: Path) -> list:
    """Load JSON data from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_technique(item: dict) -> str:
    """Format technique item for embedding."""
    parts = [
        f"Ćwiczenie: {item['exercise']}",
        f"Mięśnie: {', '.join(item['muscles'])}",
        f"Poziom trudności: {item['difficulty']}",
        f"Technika wykonania: {item['technique']}",
        f"Najczęstsze błędy: {', '.join(item['common_mistakes'])}",
        f"Wskazówki (cues): {', '.join(item['cues'])}",
        f"Warianty: {', '.join(item['variations'])}",
    ]
    if item.get('contraindications'):
        parts.append(f"Przeciwwskazania: {', '.join(item['contraindications'])}")
    return "\n".join(parts)


def format_nutrition(item: dict) -> str:
    """Format nutrition item for embedding."""
    parts = [
        f"Produkt: {item['food']}",
        f"Kalorie: {item['calories']} kcal na 100g",
        f"Białko: {item['protein']}g, Węglowodany: {item['carbs']}g, Tłuszcz: {item['fat']}g",
        f"Kategoria: {item['category']}",
        f"Kiedy jeść: {', '.join(item['when'])}",
        f"Korzyści: {', '.join(item['benefits'])}",
        f"Wskazówki: {item['tips']}",
    ]
    return "\n".join(parts)


def format_program(item: dict) -> str:
    """Format program item for embedding."""
    parts = [
        f"Program: {item['name']}",
        f"Cel: {item['goal']}",
        f"Dni w tygodniu: {item['days_per_week']}",
        f"Poziom zaawansowania: {item['level']}",
        f"Opis: {item['description']}",
        f"Harmonogram: {', '.join(item['schedule'])}",
        f"Progresja: {item['progression']}",
        f"Wskazówki: {', '.join(item['tips'])}",
    ]
    return "\n".join(parts)


def create_documents(data: list, formatter: callable, source: str) -> list:
    """Create LangChain documents from data."""
    docs = []
    for item in data:
        content = formatter(item)
        doc = Document(
            page_content=content,
            metadata={"source": source, **item}
        )
        docs.append(doc)
    return docs


def load_collection(name: str, data_path: Path, formatter: callable, qdrant_url: str):
    """Load a single collection into Qdrant."""
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient

    print(f"\n{'='*50}")
    print(f"Loading collection: {name}")
    print(f"{'='*50}")

    # Load data
    data = load_json(data_path)
    print(f"Loaded {len(data)} items from {data_path}")

    # Create documents
    docs = create_documents(data, formatter, name)
    print(f"Created {len(docs)} documents")

    # Get embeddings
    embeddings = get_embeddings()
    print(f"Using embeddings: {type(embeddings).__name__}")

    # Check if collection exists and delete it
    client = QdrantClient(url=qdrant_url)
    collection_name = f"trainer_{name}"

    try:
        client.delete_collection(collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except Exception:
        pass  # Collection doesn't exist

    # Create new collection with documents
    vectorstore = QdrantVectorStore.from_documents(
        docs,
        embeddings,
        url=qdrant_url,
        collection_name=collection_name,
    )

    print(f"Created collection '{collection_name}' with {len(docs)} documents")
    return vectorstore


def main():
    parser = argparse.ArgumentParser(description="Load data into Qdrant collections")
    parser.add_argument("--collection", "-c", choices=["techniques", "nutrition", "programs"],
                       help="Load specific collection")
    parser.add_argument("--all", "-a", action="store_true", help="Load all collections")
    parser.add_argument("--qdrant-url", default=os.getenv("QDRANT_URL", "http://localhost:6333"),
                       help="Qdrant URL")
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / "data" / "qdrant"

    collections = {
        "techniques": (data_dir / "techniques.json", format_technique),
        "nutrition": (data_dir / "nutrition.json", format_nutrition),
        "programs": (data_dir / "programs.json", format_program),
    }

    if args.all:
        to_load = list(collections.keys())
    elif args.collection:
        to_load = [args.collection]
    else:
        # Default: load all
        to_load = list(collections.keys())

    print(f"Qdrant URL: {args.qdrant_url}")
    print(f"Collections to load: {to_load}")

    for name in to_load:
        data_path, formatter = collections[name]
        if not data_path.exists():
            print(f"WARNING: Data file not found: {data_path}")
            continue
        load_collection(name, data_path, formatter, args.qdrant_url)

    print(f"\n{'='*50}")
    print("Done! All collections loaded.")
    print(f"{'='*50}")

    # Show available collections
    from qdrant_client import QdrantClient
    client = QdrantClient(url=args.qdrant_url)
    collections_list = client.get_collections()
    print("\nAvailable collections:")
    for col in collections_list.collections:
        info = client.get_collection(col.name)
        print(f"  - {col.name}: {info.points_count} documents")


if __name__ == "__main__":
    main()
