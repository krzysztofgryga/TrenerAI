from pydantic import BaseModel, Field
from typing import List

# Struktura pojedynczego ćwiczenia
class Exercise(BaseModel):
    id: str = Field(description="Unikalne ID ćwiczenia")
    name: str = Field(description="Nazwa ćwiczenia")
    description: str = Field(description="Krótka instrukcja dla trenera")
    muscle_group: str = Field(description="Główna partia mięśniowa", default="ogólne")
    difficulty: str = Field(description="Poziom: easy, medium, hard")
    type: str = Field(description="warmup, main, cooldown")

# Struktura całego planu (Output z API)
class TrainingPlan(BaseModel):
    warmup: List[Exercise] = Field(description="Lista ćwiczeń na rozgrzewkę")
    main_part: List[Exercise] = Field(description="Główna część treningu")
    cooldown: List[Exercise] = Field(description="Wyciszenie i rozciąganie")
    mode: str = Field(description="Tryb treningu: circuit lub common")
    total_duration_minutes: int = Field(description="Szacowany czas treningu")