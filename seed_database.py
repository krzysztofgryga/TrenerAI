"""
Database seeding script for TrenerAI.

Populates Qdrant vector database with exercise library.
Run this script before starting the API server.
"""

import os
import logging

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises")

# Exercise library
EXERCISES = [
    # Warmup exercises
    {"id": "w1", "name": "Jumping Jacks", "type": "warmup", "level": "easy",
     "desc": "Jump with arm swings."},
    {"id": "w2", "name": "Boxing Run", "type": "warmup", "level": "easy",
     "desc": "Run in place with straight punches."},
    {"id": "w3", "name": "Hip Circles", "type": "warmup", "level": "easy",
     "desc": "Wide hip rotation circles."},
    {"id": "w4", "name": "Arm Swings", "type": "warmup", "level": "easy",
     "desc": "Dynamic horizontal arm swings."},
    {"id": "w5", "name": "Bodyweight Squats", "type": "warmup", "level": "easy",
     "desc": "Quick warmup squats."},

    # Main exercises - Easy
    {"id": "m_e1", "name": "Classic Squat", "type": "main", "level": "easy",
     "desc": "Bodyweight squat."},
    {"id": "m_e2", "name": "Knee Push-ups", "type": "main", "level": "easy",
     "desc": "Modified push-up on knees."},
    {"id": "m_e3", "name": "Plank", "type": "main", "level": "easy",
     "desc": "Hold position for 30 seconds."},

    # Main exercises - Medium
    {"id": "m_m1", "name": "Classic Push-ups", "type": "main", "level": "medium",
     "desc": "Chest to ground, body straight."},
    {"id": "m_m2", "name": "Walking Lunges", "type": "main", "level": "medium",
     "desc": "Walk forward with deep lunges."},
    {"id": "m_m3", "name": "Kettlebell Swing", "type": "main", "level": "medium",
     "desc": "Hip-driven weight swing."},
    {"id": "m_m4", "name": "Australian Pull-ups", "type": "main", "level": "medium",
     "desc": "Pull-ups on TRX or low bar."},

    # Main exercises - Hard
    {"id": "m_h1", "name": "Burpees", "type": "main", "level": "hard",
     "desc": "Down, up, jump. Maximum tempo."},
    {"id": "m_h2", "name": "Diamond Push-ups", "type": "main", "level": "hard",
     "desc": "Hands in diamond position."},
    {"id": "m_h3", "name": "Pistol Squats", "type": "main", "level": "hard",
     "desc": "Single-leg squat."},
    {"id": "m_h4", "name": "Man Maker", "type": "main", "level": "hard",
     "desc": "Push-up, dumbbell row, and overhead press."},

    # Cooldown exercises
    {"id": "c1", "name": "Child's Pose", "type": "cooldown", "level": "easy",
     "desc": "Back relaxation on mat."},
    {"id": "c2", "name": "Couch Stretch", "type": "cooldown", "level": "easy",
     "desc": "Quad stretch against wall."},
    {"id": "c3", "name": "Bar Hang", "type": "cooldown", "level": "easy",
     "desc": "Dead hang for spinal decompression."},
]


def main():
    """Seed the vector database with exercise library."""
    logger.info("Starting database seeding with FastEmbed...")

    # Prepare documents
    documents = []
    for ex in EXERCISES:
        metadata = {
            "id": ex["id"],
            "name": ex["name"],
            "type": ex["type"],
            "level": ex["level"]
        }
        content = f"{ex['name']}: {ex['desc']}"
        documents.append(Document(page_content=content, metadata=metadata))

    # Initialize embeddings
    embeddings = FastEmbedEmbeddings()

    logger.info(f"Sending {len(documents)} vectors to Qdrant...")
    logger.info(f"URL: {QDRANT_URL}, Collection: {COLLECTION_NAME}")

    # Create collection and add documents
    Qdrant.from_documents(
        documents,
        embeddings,
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
        force_recreate=True
    )

    logger.info("Database seeding completed successfully!")


if __name__ == "__main__":
    main()
