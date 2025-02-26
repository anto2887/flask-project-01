#!/bin/bash
set -e

# Configure max retries and delay
MAX_RETRIES=30
RETRY_DELAY=5

# Wait for database with retries
echo "Waiting for database..."
RETRIES=0
while [ $RETRIES -lt $MAX_RETRIES ]; do
    echo "Attempt $((RETRIES+1))/$MAX_RETRIES: Checking database connection..."
    if pg_isready -h ${DB_HOST} -p ${DB_PORT} -d ${DB_NAME} -U ${DB_USER}; then
        echo "Successfully connected to database!"
        break
    fi
    
    RETRIES=$((RETRIES+1))
    if [ $RETRIES -eq $MAX_RETRIES ]; then
        echo "Error: Maximum retries reached. Could not connect to database."
        exit 1
    fi
    
    echo "Database not yet available. Waiting ${RETRY_DELAY} seconds..."
    sleep $RETRY_DELAY
done

echo "Checking Redis connection..."
if ! redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} ping; then
    echo "Warning: Could not connect to Redis. Some functionality may be limited."
fi

# Initialize database if needed
if [ "$CREATE_TABLES_ON_STARTUP" = "True" ]; then
    echo "Initializing database..."
    python -c "from app import create_app; from app.db import db; app = create_app(); app.app_context().push(); db.create_all()"
    echo "Database tables created successfully"
fi

# Print debugging info
echo "Starting Flask application with following configuration:"
echo "- Database host: ${DB_HOST}"
echo "- Flask environment: ${FLASK_ENV}"
echo "- Create tables: ${CREATE_TABLES_ON_STARTUP}"

# Start Gunicorn in the foreground
echo "Starting Gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --worker-class=gthread \
    --workers=3 \
    --threads=2 \
    --timeout=120 \
    --access-logfile - \
    --error-logfile - \
    "app:create_app()"