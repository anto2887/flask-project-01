#!/bin/sh

# Wait for database
echo "Waiting for database..."
/usr/local/bin/wait-for-it.sh ${DB_HOST}:${DB_PORT} -t 60

# Initialize database if needed
if [ "$CREATE_TABLES_ON_STARTUP" = "True" ]; then
    echo "Initializing database..."
    flask init-db
fi

# Start Flask app
flask run --host 0.0.0.0 &

# Wait for Flask app to be up
echo "Waiting for Flask app to start..."
until curl -f http://localhost:5000/health >/dev/null 2>&1; do
    sleep 2
done

# Initialize scheduler
echo "Initializing scheduler..."
flask init-scheduler

# Keep the container running
tail -f /dev/null