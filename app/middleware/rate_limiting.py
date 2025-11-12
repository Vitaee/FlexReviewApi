from collections import defaultdict
from time import time
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.logging_config import get_logger


logger = get_logger(__name__)


class RateLimiter:
    """
    In-memory rate limiter using token bucket algorithm.
    Thread-safe for async operations.
    """
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute per IP
            requests_per_hour: Maximum requests per hour per IP
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Store request timestamps per IP
        # Format: {ip: [timestamps]}
        self._request_history: dict[str, list[float]] = defaultdict(list)
        self._cleanup_interval = 3600  # Clean up old entries every hour
        self._last_cleanup = time()
    
    def _cleanup_old_entries(self) -> None:
        """Remove request timestamps older than 1 hour"""
        current_time = time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # 1 hour ago
        
        # Clean up old entries
        ips_to_remove = []
        for ip, timestamps in self._request_history.items():
            # Keep only timestamps from the last hour
            filtered_timestamps = [ts for ts in timestamps if ts > cutoff_time]
            if filtered_timestamps:
                self._request_history[ip] = filtered_timestamps
            else:
                ips_to_remove.append(ip)
        
        # Remove IPs with no recent requests
        for ip in ips_to_remove:
            del self._request_history[ip]
        
        self._last_cleanup = current_time
    
    def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """
        Check if request is allowed based on rate limits.
        
        Args:
            identifier: Unique identifier (typically IP address)
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
            rate_limit_info contains: remaining, reset_after, limit
        """
        current_time = time()
        
        # Cleanup old entries periodically
        self._cleanup_old_entries()
        
        # Get request history for this identifier
        timestamps = self._request_history[identifier]
        
        # Filter timestamps within the time windows
        one_minute_ago = current_time - 60
        one_hour_ago = current_time - 3600
        
        recent_minute = [ts for ts in timestamps if ts > one_minute_ago]
        recent_hour = [ts for ts in timestamps if ts > one_hour_ago]
        
        # Check limits
        minute_limit_exceeded = len(recent_minute) >= self.requests_per_minute
        hour_limit_exceeded = len(recent_hour) >= self.requests_per_hour
        
        if minute_limit_exceeded or hour_limit_exceeded:
            # Calculate reset time
            if minute_limit_exceeded:
                reset_after = 60 - (current_time - recent_minute[0])
                limit = self.requests_per_minute
                window = "minute"
            else:
                reset_after = 3600 - (current_time - recent_hour[0])
                limit = self.requests_per_hour
                window = "hour"
            
            return False, {
                "limit": limit,
                "remaining": 0,
                "reset_after": int(reset_after),
                "window": window
            }
        
        # Add current request timestamp
        timestamps.append(current_time)
        
        # Calculate remaining requests
        remaining_minute = max(0, self.requests_per_minute - len(recent_minute) - 1)
        remaining_hour = max(0, self.requests_per_hour - len(recent_hour) - 1)
        remaining = min(remaining_minute, remaining_hour)
        
        return True, {
            "limit": self.requests_per_minute if remaining_minute < remaining_hour else self.requests_per_hour,
            "remaining": remaining,
            "reset_after": 60 if remaining_minute < remaining_hour else 3600,
            "window": "minute" if remaining_minute < remaining_hour else "hour"
        }


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware - applies rate limits to all requests.
    Reusable and configurable.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        exempt_paths: list[str] | None = None
    ):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: ASGI application
            requests_per_minute: Maximum requests per minute per IP
            requests_per_hour: Maximum requests per hour per IP
            exempt_paths: List of path prefixes to exempt from rate limiting (e.g., ["/health"])
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour
        )
        self.exempt_paths = exempt_paths or []
    
    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting"""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""
        # Skip rate limiting for exempt paths
        if self._is_exempt(request.url.path):
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        is_allowed, rate_info = self.rate_limiter.is_allowed(client_ip)
        
        if not is_allowed:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning(
                f"[{request_id}] Rate limit exceeded | "
                f"IP: {client_ip} | "
                f"Path: {request.url.path} | "
                f"Limit: {rate_info['limit']}/{rate_info['window']}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {rate_info['limit']} requests per {rate_info['window']}",
                    "retry_after": rate_info["reset_after"]
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": str(rate_info["remaining"]),
                    "X-RateLimit-Reset-After": str(rate_info["reset_after"]),
                    "Retry-After": str(rate_info["reset_after"])
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset-After"] = str(rate_info["reset_after"])
        
        return response
    
    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """
        Extract client IP address from request.
        Reuses logic from RequestLoggingMiddleware (DRY principle).
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address
        """
        # Check for forwarded IP (from proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"

