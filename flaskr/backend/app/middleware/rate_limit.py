from flask import request, jsonify
from functools import wraps
import redis
import time
from datetime import datetime
import logging

class RateLimiter:
    def __init__(self, redis_url='redis://localhost:6379/0'):
        self.redis = redis.from_url(redis_url)
        self.logger = logging.getLogger('rate_limiter')

    def _get_identifier(self):
        """Get unique identifier for the current request."""
        return f"{request.remote_addr}:{request.endpoint}"

    def limit(self, requests=100, window=60):
        """Rate limiting decorator."""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Get unique identifier for this request
                identifier = self._get_identifier()
                
                # Get current timestamp
                now = time.time()
                
                # Create a pipeline for atomic operations
                pipe = self.redis.pipeline()
                
                # Remove old requests outside the window
                pipe.zremrangebyscore(identifier, 0, now - window)
                
                # Add current request
                pipe.zadd(identifier, {str(now): now})
                
                # Count requests in window
                pipe.zcard(identifier)
                
                # Set expiry on the key
                pipe.expire(identifier, window)
                
                # Execute pipeline
                _, _, request_count, _ = pipe.execute()
                
                # Log request details
                self.logger.info({
                    'event': 'rate_limit_check',
                    'identifier': identifier,
                    'request_count': request_count,
                    'limit': requests,
                    'window': window,
                    'timestamp': datetime.utcnow().isoformat()
                })

                # Check if limit exceeded
                if request_count > requests:
                    self.logger.warning({
                        'event': 'rate_limit_exceeded',
                        'identifier': identifier,
                        'request_count': request_count,
                        'limit': requests
                    })
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': window
                    }), 429

                return f(*args, **kwargs)
            return wrapped
        return decorator