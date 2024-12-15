#!/bin/sh
set -e

# Wait for database
echo "Waiting for database..."
/usr/local/bin/wait-for-it.sh ${DB_HOST}:${DB_PORT} -t 60

# Initialize database if needed
if [ "$CREATE_TABLES_ON_STARTUP" = "True" ]; then
    echo "Initializing database..."
    FLASK_APP=app flask init-db
fi

echo "Starting Gunicorn..."
# Use app:create_app() as the WSGI callable
exec gunicorn --bind 0.0.0.0:5000 "app:create_app()" $GUNICORN_CMD_ARGS