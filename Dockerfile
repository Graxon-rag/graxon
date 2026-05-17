# --- Stage 1: Build Stage ---
FROM python:3.11-slim AS builder

# Setting the specific working directory
WORKDIR /graxon/graxon

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies needed for building some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Generate wheels (compiled binaries)
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /graxon/graxon/wheels -r requirements.txt


# --- Stage 2: Runtime Stage ---
FROM python:3.11-slim

WORKDIR /graxon/graxon

# Create a dedicated user for security
RUN groupadd -r graxon-user && useradd -r -g graxon-user graxon-user

# Copy and install the wheels from the builder stage
COPY --from=builder /graxon/graxon/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy app code
COPY ./app ./app

# Copy migrations
COPY ./migrations ./migrations
COPY ./alembic.ini ./

# Copy entrypoint
COPY ./entrypoint.sh ./

RUN chmod +x ./entrypoint.sh

# Set ownership to the non-root user
RUN chown -R graxon-user:graxon-user /graxon/graxon
USER graxon-user

EXPOSE 8888

ENTRYPOINT [ "./entrypoint.sh" ]
