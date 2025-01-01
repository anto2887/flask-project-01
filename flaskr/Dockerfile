# Stage 1: Build environment
FROM python:3.9-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies - combining RUN commands and cleaning up in same layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy and install requirements - separate layer for better caching
COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# Stage 2: Runtime environment
FROM python:3.9-slim

# Set timezone and install runtime dependencies in a single layer
RUN ln -snf /usr/share/zoneinfo/America/Chicago /etc/localtime && \
    echo America/Chicago > /etc/timezone && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        unzip \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws \
    && apt-get remove -y unzip \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /flaskr

# Copy installed dependencies from builder stage
COPY --from=builder /root/.local /root/.local

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH \
    FLASK_APP=app \
    FLASK_ENV=production \
    PYTHONPATH=/flaskr \
    CREATE_TABLES_ON_STARTUP=True \
    GUNICORN_CMD_ARGS="--bind=0.0.0.0:5000 --workers=3 --timeout=120 --access-logfile=- --error-logfile=- --capture-output --enable-stdio-inheritance"

# Copy scripts first (smaller, change less often)
COPY wait-for-it.sh /usr/local/bin/
COPY entrypoint.sh ./
RUN chmod +x /usr/local/bin/wait-for-it.sh ./entrypoint.sh && \
    mkdir -p /flaskr/logs && \
    chmod 777 /flaskr/logs

# Copy application files last (changes most often)
COPY . .

EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]