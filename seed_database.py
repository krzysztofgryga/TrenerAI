"""
TrenerAI Database Seeding Script

This script populates the Qdrant vector database with the exercise library.
It must be run before starting the API server to ensure exercises are
available for retrieval.

The script:
1. Connects to Qdrant (must be running)
2. Loads exercises from data/exercises.json
3. Creates/recreates the exercise collection
4. Generates embeddings using FastEmbed
5. Stores all exercises with their metadata

Usage:
    python seed_database.py

Requirements:
    - Qdrant must be running (docker-compose up -d qdrant)
    - Environment variables configured in .env
    - data/exercises.json file with exercise definitions
"""

import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

load_dotenv()

# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises")

# Default path to exercises file (relative to project root)
DEFAULT_EXERCISES_PATH = Path(__file__).parent / "data" / "exercises.json"


# =============================================================================
# Exercise Loading
# =============================================================================

def load_exercises(file_path: Path = None) -> List[Dict[str, Any]]:
    """
    Load exercises from a JSON file.

    Args:
        file_path: Path to the exercises JSON file.
                   Defaults to data/exercises.json in project root.

    Returns:
        List of exercise dictionaries with keys: id, name, type, level, desc

    Raises:
        FileNotFoundError: If the exercises file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        ValueError: If the file structure is invalid.

    Example file structure:
        {
            "exercises": [
                {"id": "w1", "name": "...", "type": "warmup", "level": "easy", "desc": "..."},
                ...
            ]
        }
    """
    if file_path is None:
        file_path = DEFAULT_EXERCISES_PATH

    logger.info(f"Loading exercises from: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(
            f"Exercises file not found: {file_path}\n"
            f"Please create the file with exercise definitions."
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "exercises" not in data:
        raise ValueError(
            "Invalid exercises file format. Expected JSON with 'exercises' key."
        )

    exercises = data["exercises"]
    logger.info(f"Loaded {len(exercises)} exercises from file")

    return exercises


def count_exercises_by_category(exercises: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count exercises by type and level.

    Args:
        exercises: List of exercise dictionaries.

    Returns:
        Dictionary with category counts.
    """
    counts = {
        "warmup": 0,
        "main_easy": 0,
        "main_medium": 0,
        "main_hard": 0,
        "cooldown": 0
    }

    for ex in exercises:
        ex_type = ex.get("type", "")
        ex_level = ex.get("level", "")

        if ex_type == "warmup":
            counts["warmup"] += 1
        elif ex_type == "cooldown":
            counts["cooldown"] += 1
        elif ex_type == "main":
            if ex_level == "easy":
                counts["main_easy"] += 1
            elif ex_level == "medium":
                counts["main_medium"] += 1
            elif ex_level == "hard":
                counts["main_hard"] += 1

    return counts


# =============================================================================
# Main Function
# =============================================================================

def main(exercises_file: Path = None) -> None:
    """
    Seed the Qdrant vector database with the exercise library.

    This function:
    1. Loads exercises from JSON file
    2. Converts exercises to LangChain Document format
    3. Generates embeddings using FastEmbed
    4. Creates/recreates the Qdrant collection
    5. Stores all documents with embeddings

    Args:
        exercises_file: Optional path to exercises JSON file.
                        Defaults to data/exercises.json

    Raises:
        ConnectionError: If Qdrant is not accessible.
        FileNotFoundError: If exercises file doesn't exist.
        Exception: If embedding or storage fails.
    """
    logger.info("Starting database seeding...")
    logger.info(f"Qdrant URL: {QDRANT_URL}")
    logger.info(f"Collection: {COLLECTION_NAME}")

    # Load exercises from file
    exercises = load_exercises(exercises_file)

    # Convert exercises to Document format
    documents = []
    for ex in exercises:
        # Metadata is stored alongside the vector for filtering
        metadata = {
            "id": ex["id"],
            "name": ex["name"],
            "type": ex["type"],
            "level": ex["level"]
        }
        # Page content is embedded as the vector
        content = f"{ex['name']}: {ex['desc']}"
        documents.append(Document(page_content=content, metadata=metadata))

    logger.info(f"Prepared {len(documents)} exercises for indexing")

    # Initialize embedding model
    logger.info("Initializing FastEmbed embeddings...")
    embeddings = FastEmbedEmbeddings()

    # Create collection and add documents
    logger.info("Sending vectors to Qdrant (this may take a moment)...")

    try:
        Qdrant.from_documents(
            documents,
            embeddings,
            url=QDRANT_URL,
            collection_name=COLLECTION_NAME,
            force_recreate=True  # Clears existing collection
        )

        # Count and display statistics
        counts = count_exercises_by_category(exercises)

        logger.info("Database seeding completed successfully!")
        logger.info(f"Total exercises indexed: {len(documents)}")
        logger.info(f"  - Warmup: {counts['warmup']}")
        logger.info(f"  - Main (easy): {counts['main_easy']}")
        logger.info(f"  - Main (medium): {counts['main_medium']}")
        logger.info(f"  - Main (hard): {counts['main_hard']}")
        logger.info(f"  - Cooldown: {counts['cooldown']}")

    except Exception as e:
        logger.error(f"Failed to seed database: {e}")
        logger.error("Make sure Qdrant is running: docker-compose up -d qdrant")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Seed TrenerAI database with exercises"
    )
    parser.add_argument(
        "--file", "-f",
        type=Path,
        default=None,
        help="Path to exercises JSON file (default: data/exercises.json)"
    )

    args = parser.parse_args()
    main(exercises_file=args.file)
