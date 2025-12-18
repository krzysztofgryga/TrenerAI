"""
TrenerAI Database Seeding Script

This script populates the Qdrant vector database with the exercise library.
It must be run before starting the API server to ensure exercises are
available for retrieval.

The script:
1. Connects to Qdrant (must be running)
2. Creates/recreates the exercise collection
3. Generates embeddings using FastEmbed
4. Stores all exercises with their metadata

Usage:
    python seed_database.py

Requirements:
    - Qdrant must be running (docker-compose up -d qdrant)
    - Environment variables configured in .env
"""

import os
import logging

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

# =============================================================================
# Exercise Library
# =============================================================================

EXERCISES = [
    # -------------------------------------------------------------------------
    # Warmup Exercises (5)
    # Used to prepare the body for the main workout
    # -------------------------------------------------------------------------
    {
        "id": "w1",
        "name": "Jumping Jacks",
        "type": "warmup",
        "level": "easy",
        "desc": "Jump with arm swings. Great cardio warmup."
    },
    {
        "id": "w2",
        "name": "Boxing Run",
        "type": "warmup",
        "level": "easy",
        "desc": "Run in place with straight punches."
    },
    {
        "id": "w3",
        "name": "Hip Circles",
        "type": "warmup",
        "level": "easy",
        "desc": "Wide hip rotation circles for mobility."
    },
    {
        "id": "w4",
        "name": "Arm Swings",
        "type": "warmup",
        "level": "easy",
        "desc": "Dynamic horizontal arm swings."
    },
    {
        "id": "w5",
        "name": "Bodyweight Squats",
        "type": "warmup",
        "level": "easy",
        "desc": "Quick warmup squats to activate legs."
    },

    # -------------------------------------------------------------------------
    # Main Exercises - Easy (3)
    # Beginner-friendly exercises
    # -------------------------------------------------------------------------
    {
        "id": "m_e1",
        "name": "Classic Squat",
        "type": "main",
        "level": "easy",
        "desc": "Bodyweight squat with proper form."
    },
    {
        "id": "m_e2",
        "name": "Knee Push-ups",
        "type": "main",
        "level": "easy",
        "desc": "Modified push-up on knees for beginners."
    },
    {
        "id": "m_e3",
        "name": "Plank",
        "type": "main",
        "level": "easy",
        "desc": "Hold plank position for 30 seconds."
    },

    # -------------------------------------------------------------------------
    # Main Exercises - Medium (4)
    # Intermediate exercises requiring some fitness
    # -------------------------------------------------------------------------
    {
        "id": "m_m1",
        "name": "Classic Push-ups",
        "type": "main",
        "level": "medium",
        "desc": "Chest to ground, body straight throughout."
    },
    {
        "id": "m_m2",
        "name": "Walking Lunges",
        "type": "main",
        "level": "medium",
        "desc": "Walk forward with deep lunges."
    },
    {
        "id": "m_m3",
        "name": "Kettlebell Swing",
        "type": "main",
        "level": "medium",
        "desc": "Hip-driven kettlebell swing."
    },
    {
        "id": "m_m4",
        "name": "Australian Pull-ups",
        "type": "main",
        "level": "medium",
        "desc": "Horizontal pull-ups on low bar or TRX."
    },

    # -------------------------------------------------------------------------
    # Main Exercises - Hard (4)
    # Advanced exercises for experienced athletes
    # -------------------------------------------------------------------------
    {
        "id": "m_h1",
        "name": "Burpees",
        "type": "main",
        "level": "hard",
        "desc": "Down, up, jump. Maximum tempo."
    },
    {
        "id": "m_h2",
        "name": "Diamond Push-ups",
        "type": "main",
        "level": "hard",
        "desc": "Push-ups with hands in diamond position."
    },
    {
        "id": "m_h3",
        "name": "Pistol Squats",
        "type": "main",
        "level": "hard",
        "desc": "Single-leg squat requiring balance and strength."
    },
    {
        "id": "m_h4",
        "name": "Man Maker",
        "type": "main",
        "level": "hard",
        "desc": "Push-up, dumbbell row, and overhead press combo."
    },

    # -------------------------------------------------------------------------
    # Cooldown Exercises (3)
    # Used to relax and stretch after the main workout
    # -------------------------------------------------------------------------
    {
        "id": "c1",
        "name": "Child's Pose",
        "type": "cooldown",
        "level": "easy",
        "desc": "Back relaxation stretch on mat."
    },
    {
        "id": "c2",
        "name": "Couch Stretch",
        "type": "cooldown",
        "level": "easy",
        "desc": "Quad stretch against wall."
    },
    {
        "id": "c3",
        "name": "Bar Hang",
        "type": "cooldown",
        "level": "easy",
        "desc": "Dead hang for spinal decompression."
    },
]


# =============================================================================
# Main Function
# =============================================================================

def main() -> None:
    """
    Seed the Qdrant vector database with the exercise library.

    This function:
    1. Converts exercises to LangChain Document format
    2. Generates embeddings using FastEmbed
    3. Creates/recreates the Qdrant collection
    4. Stores all documents with embeddings

    Raises:
        ConnectionError: If Qdrant is not accessible.
        Exception: If embedding or storage fails.
    """
    logger.info("Starting database seeding...")
    logger.info(f"Qdrant URL: {QDRANT_URL}")
    logger.info(f"Collection: {COLLECTION_NAME}")

    # Convert exercises to Document format
    documents = []
    for ex in EXERCISES:
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
        logger.info("Database seeding completed successfully!")
        logger.info(f"Total exercises indexed: {len(documents)}")
        logger.info("  - Warmup: 5")
        logger.info("  - Main (easy): 3")
        logger.info("  - Main (medium): 4")
        logger.info("  - Main (hard): 4")
        logger.info("  - Cooldown: 3")

    except Exception as e:
        logger.error(f"Failed to seed database: {e}")
        logger.error("Make sure Qdrant is running: docker-compose up -d qdrant")
        raise


if __name__ == "__main__":
    main()
