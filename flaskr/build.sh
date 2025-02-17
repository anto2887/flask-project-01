#!/bin/bash

# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build backend
echo "Building backend..."
docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --cache-from flaskr-backend:latest \
  -t flaskr-backend \
  ./backend

# Build frontend
echo "Building frontend..."
docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --cache-from flaskr-frontend:latest \
  -t flaskr-frontend \
  ./frontend

# Start services
echo "Starting services..."
docker-compose up -d

echo "Build complete!"