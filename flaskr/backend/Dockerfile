# Stage 1: Build environment
FROM python:3.9-slim AS builder

# Set build time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime environment
FROM python:3.9-slim

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    FLASK_APP=app \
    FLASK_ENV=production \
    PYTHONPATH=/flaskr \
    CREATE_TABLES_ON_STARTUP=True \
    TZ=America/Chicago

# Install runtime dependencies and tools for database connectivity
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    redis-tools \
    curl \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /flaskr

# Copy installed dependencies from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application files
COPY . .

# Make sure the entrypoint script is executable
RUN chmod +x ./entrypoint.sh && \
    mkdir -p /flaskr/logs && \
    chmod 777 /flaskr/logs

EXPOSE 5000

# Use the correct entrypoint script
ENTRYPOINT ["./entrypoint.sh"]