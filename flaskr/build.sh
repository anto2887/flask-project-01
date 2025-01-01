#!/bin/bash
# build.sh

# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build with optimizations
docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --cache-from flaskr-app:latest \
  -t flaskr-app \
  .