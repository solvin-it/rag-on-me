#### Multi-stage Dockerfile
# Stage 1: builder - install build deps and compile wheels
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /tmp/build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
        curl \
        libmagic1 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first (leverage cache). This assumes the build context is the repo root.
COPY requirements.txt ./requirements.txt

# Build wheels into a local wheelhouse to reduce network calls during final install
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip wheel --wheel-dir /tmp/wheels -r requirements.txt


# Stage 2: runtime - smaller image, install from local wheelhouse
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps needed at runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy wheelhouse from builder
COPY --from=builder /tmp/wheels /wheels

# Copy requirements and try to install strictly from the wheelhouse first (--no-index).
# If some packages are missing from wheels, fall back to PyPI.
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir --disable-pip-version-check --no-index --find-links /wheels -r /app/requirements.txt || \
        python -m pip install --no-cache-dir --disable-pip-version-check -r /app/requirements.txt

# Copy application code (build context root -> /app)
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
