"""
Rate limiting configuration using slowapi with Redis backend.
"""
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from dotenv import load_dotenv

load_dotenv()

# Get Redis URL from environment (same as Celery)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create limiter with Redis backend
# Default limit: 10 requests per minute
limiter = Limiter(
    key_func=get_remote_address,  # Identify users by IP address
    storage_uri=redis_url,  # Use Redis for distributed rate limiting
    default_limits=["10/minute"],  # Default rate limit
    headers_enabled=True  # Include rate limit info in response headers
)


def setup_rate_limiter(app):
    """
    Setup rate limiter for FastAPI app.
    Call this in main.py after creating the app.
    
    This applies rate limiting globally to all endpoints.
    You can override limits on specific endpoints using @limiter.limit() decorator.
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

