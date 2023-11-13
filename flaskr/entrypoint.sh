#!/bin/sh

# Start Flask app
flask run --host 0.0.0.0 &

# Wait for Flask app to be up
sleep 5  # Adjust this value if needed

# Initialize scheduler
flask init-scheduler

# Keep the container running
tail -f /dev/null
