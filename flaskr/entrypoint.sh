#!/bin/sh
set -e

# Wait for database
echo "Waiting for database..."
/usr/local/bin/wait-for-it.sh ${DB_HOST}:${DB_PORT} -t 60

# Initialize database if needed
if [ "$CREATE_TABLES_ON_STARTUP" = "True" ]; then
    echo "Initializing database..."
    flask init-db
fi

echo "Starting Gunicorn..."
exec gunicorn "app:create_app()" $GUNICORN_CMD_ARGS