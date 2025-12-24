#!/usr/bin/env python3
"""
Load all data collections into Qdrant vector database.

This is the single script for loading ALL Qdrant collections in TrenerAI.

Usage:
    python scripts/load_qdrant_collections.py

    # Load specific collection:
    python scripts/load_qdrant_collections.py -c exercises   # For LangGraph training generator
    python scripts/load_qdrant_collections.py -c techniques  # Exercise techniques for RAG
    python scripts/load_qdrant_collections.py -c nutrition   # Nutrition info for RAG
    python scripts/load_qdrant_collections.py -c programs    # Training programs for RAG

    # Load all collections:
    python scripts/load_qdrant_collections.py --all

Requires:
    - Qdrant running on localhost:6333
    - Environment vars set in .env
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from langchain_core.documents import Document
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# Collection names
COLLECTIONS_CONFIG = {
    # Original exercises collection (for LangGraph training generator)
    "exercises": {
        "collection_name": os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises"),
        "data_path": "data/exercises.json",
        "description": "Exercises for training plan generator (LangGraph)",
    },
    # New RAG collections
    "techniques": {
        "collection_name": "trainer_techniques",
        "data_path": "data/qdrant/techniques.json",
        "description": "Exercise techniques, form cues, common mistakes",
    },
    "nutrition": {
        "collection_name": "trainer_nutrition",
        "data_path": "data/qdrant/nutrition.json",
        "description": "Food items with macros and timing",
    },
    "programs": {
        "collection_name": "trainer_programs",
        "data_path": "data/qdrant/programs.json",
        "description": "Training programs (PPL, FBW, Upper/Lower, etc.)",
    },
}


# =============================================================================
# Formatters
# =============================================================================

def format_exercise(item: dict) -> str:
    """Format exercise from exercises.json for embedding."""
    return f"{item['name']}: {item['desc']}"


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


FORMATTERS = {
    "exercises": format_exercise,
    "techniques": format_technique,
    "nutrition": format_nutrition,
    "programs": format_program,
}


# =============================================================================
# Loading Functions
# =============================================================================

def load_json_data(file_path: Path, collection_type: str) -> list:
    """Load JSON data from file."""
    logger.info(f"Loading data from: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle exercises.json format (has "exercises" key)
    if collection_type == "exercises":
        if "exercises" not in data:
            raise ValueError("Invalid exercises.json format. Expected 'exercises' key.")
        return data["exercises"]

    # Other collections are direct arrays
    return data


def create_documents(data: list, formatter: callable, collection_type: str) -> list:
    """Create LangChain documents from data."""
    docs = []
    for item in data:
        content = formatter(item)
        metadata = {"source": collection_type}

        # Add item fields to metadata
        if collection_type == "exercises":
            metadata.update({
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "type": item.get("type", ""),
                "level": item.get("level", ""),
            })
        else:
            metadata.update(item)

        doc = Document(page_content=content, metadata=metadata)
        docs.append(doc)

    return docs


def load_collection(collection_type: str, qdrant_url: str) -> bool:
    """Load a single collection into Qdrant."""
    from langchain_community.vectorstores import Qdrant
    from qdrant_client import QdrantClient

    if collection_type not in COLLECTIONS_CONFIG:
        logger.error(f"Unknown collection type: {collection_type}")
        return False

    config = COLLECTIONS_CONFIG[collection_type]
    collection_name = config["collection_name"]
    data_path = Path(__file__).parent.parent / config["data_path"]

    logger.info("=" * 60)
    logger.info(f"Loading: {collection_type}")
    logger.info(f"Collection: {collection_name}")
    logger.info(f"Description: {config['description']}")
    logger.info("=" * 60)

    try:
        # Load data
        data = load_json_data(data_path, collection_type)
        logger.info(f"Loaded {len(data)} items")

        # Get formatter
        formatter = FORMATTERS[collection_type]

        # Create documents
        docs = create_documents(data, formatter, collection_type)
        logger.info(f"Created {len(docs)} documents")

        # Initialize embeddings (FastEmbed for consistency)
        logger.info("Initializing FastEmbed embeddings...")
        embeddings = FastEmbedEmbeddings()

        # Create collection
        logger.info(f"Sending to Qdrant...")
        Qdrant.from_documents(
            docs,
            embeddings,
            url=qdrant_url,
            collection_name=collection_name,
            force_recreate=True  # Clear existing
        )

        logger.info(f"SUCCESS: Created '{collection_name}' with {len(docs)} documents")

        # Print stats for exercises
        if collection_type == "exercises":
            counts = {"warmup": 0, "main": 0, "cooldown": 0}
            for item in data:
                ex_type = item.get("type", "")
                if ex_type in counts:
                    counts[ex_type] += 1
            logger.info(f"  - Warmup: {counts['warmup']}")
            logger.info(f"  - Main: {counts['main']}")
            logger.info(f"  - Cooldown: {counts['cooldown']}")

        return True

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to load {collection_type}: {e}")
        return False


def show_collections(qdrant_url: str):
    """Show all collections in Qdrant."""
    from qdrant_client import QdrantClient

    try:
        client = QdrantClient(url=qdrant_url)
        collections = client.get_collections().collections

        logger.info("\n" + "=" * 60)
        logger.info("Available collections in Qdrant:")
        logger.info("=" * 60)

        for col in collections:
            info = client.get_collection(col.name)
            logger.info(f"  - {col.name}: {info.points_count} documents")

    except Exception as e:
        logger.error(f"Failed to list collections: {e}")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Load data into Qdrant collections for TrenerAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Collections:
  exercises   - Gym exercises for LangGraph training generator
  techniques  - Exercise techniques, form cues (for RAG)
  nutrition   - Food items with macros (for RAG)
  programs    - Training programs like PPL, FBW (for RAG)

Examples:
  python scripts/load_qdrant_collections.py --all
  python scripts/load_qdrant_collections.py -c exercises
  python scripts/load_qdrant_collections.py -c techniques -c nutrition
        """
    )
    parser.add_argument(
        "--collection", "-c",
        action="append",
        choices=list(COLLECTIONS_CONFIG.keys()),
        help="Collection(s) to load (can be used multiple times)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Load all collections"
    )
    parser.add_argument(
        "--qdrant-url",
        default=QDRANT_URL,
        help=f"Qdrant URL (default: {QDRANT_URL})"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List existing collections and exit"
    )

    args = parser.parse_args()

    logger.info(f"Qdrant URL: {args.qdrant_url}")

    # Just list collections
    if args.list:
        show_collections(args.qdrant_url)
        return

    # Determine what to load
    if args.all:
        to_load = list(COLLECTIONS_CONFIG.keys())
    elif args.collection:
        to_load = args.collection
    else:
        # Default: load all
        to_load = list(COLLECTIONS_CONFIG.keys())

    logger.info(f"Collections to load: {to_load}")

    # Load collections
    success = 0
    failed = 0
    for collection_type in to_load:
        if load_collection(collection_type, args.qdrant_url):
            success += 1
        else:
            failed += 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Successful: {success}")
    logger.info(f"Failed: {failed}")

    # Show all collections
    show_collections(args.qdrant_url)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
