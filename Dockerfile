FROM python:3.11-slim

# Tworzymy grupę i użytkownika systemowego 'appuser'
# To kluczowe dla bezpieczeństwa - atakujący trudniej przejmie system
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Instalacja zależności systemowych
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Kopiowanie i instalacja zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu
COPY ./app ./app
COPY ./data ./data
COPY ./alembic ./alembic
COPY ./alembic.ini .

# Nadanie uprawnień użytkownikowi
RUN chown -R appuser:appuser /app

# Przełączenie na bezpiecznego użytkownika
USER appuser

# Port
EXPOSE 8000

# Healthcheck wbudowany w obraz
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Produkcja: bez --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
