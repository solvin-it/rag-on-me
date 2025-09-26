FROM python:3.12-slim

# Basic environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required by a few packages (psycopg, unstructured, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
        curl \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest first to leverage Docker layer caching
COPY ../requirements.txt /app/requirements.txt

# Install Python deps
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the application code
COPY .. /app

# Expose the port the app listens on
EXPOSE 8000

# Default command: run Uvicorn (production deployments may override this)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
