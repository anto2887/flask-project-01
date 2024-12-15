#!/bin/sh
set -e

# Enable debug mode to see what's happening
set -x

# Wait for database
echo "Waiting for database..."
/usr/local/bin/wait-for-it.sh ${DB_HOST}:${DB_PORT} -t 60

# Initialize database if needed
if [ "$CREATE_TABLES_ON_STARTUP" = "True" ]; then
    echo "Initializing database..."
    # Use python directly instead of flask CLI
    python3 -c "
from app import create_app
from app.db import db
app = create_app()
with app.app_context():
    db.create_all()
"
fi

echo "Starting Gunicorn..."
# Start gunicorn with specific worker class and configuration
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --worker-class=gthread \
    --workers=3 \
    --threads=2 \
    --timeout=120 \
    --max-requests=1000 \
    --max-requests-jitter=50 \
    --log-level=debug \
    --access-logfile=- \
    --error-logfile=- \
    --capture-output \
    --enable-stdio-inheritance \
    "app:create_app()"