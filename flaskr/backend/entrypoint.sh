#!/bin/bash
# Wait for database if needed
wait-for-it.sh ${DATABASE_HOST:-db}:${DATABASE_PORT:-5432} -t 60

# Start the Flask application
exec gunicorn --bind 0.0.0.0:5000 app:app