#!/bin/sh
set -e

# Wait for database
echo "Waiting for database..."
/usr/local/bin/wait-for-it.sh ${DB_HOST}:${DB_PORT} -t 60

# Initialize database if needed
if [ "$CREATE_TABLES_ON_STARTUP" = "True" ]; then
    echo "Initializing database..."
    # Create a proper Python script instead of inline command
    cat > /tmp/init_db.py << EOF
from app import create_app
from app.db import db

def init_db():
    app = create_app()
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
EOF
    python3 /tmp/init_db.py
fi

echo "Starting Gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --worker-class=gthread \
    --workers=3 \
    --threads=2 \
    --timeout=120 \
    "app:create_app()"