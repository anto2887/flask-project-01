# Stage 1: Build environment
FROM python:3.9-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-warn-script-location -r requirements.txt

# Stage 2: Runtime environment
FROM python:3.9-slim

# Set timezone
RUN ln -snf /usr/share/zoneinfo/America/Chicago /etc/localtime && echo America/Chicago > /etc/timezone

# Install runtime dependencies and AWS CLI
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    unzip \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws \
    && apt-get remove -y unzip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /flaskr

# Copy installed dependencies from builder stage
COPY --from=builder /root/.local /root/.local

# Ensure scripts directory is in PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application files
COPY . .

# Copy and set permissions for scripts
COPY wait-for-it.sh /usr/local/bin/wait-for-it.sh
COPY entrypoint.sh /flaskr/entrypoint.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh /flaskr/entrypoint.sh

# Create logs directory
RUN mkdir -p /flaskr/logs && chmod 777 /flaskr/logs

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app
ENV FLASK_ENV=production
ENV PYTHONPATH=/flaskr
ENV CREATE_TABLES_ON_STARTUP=True
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0:5000 --workers=3 --timeout=120 --access-logfile=- --error-logfile=- --capture-output --enable-stdio-inheritance"

# Command to run the application
ENTRYPOINT ["/flaskr/entrypoint.sh"]