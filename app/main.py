"""Main FastAPI application"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.rate_limiting import RateLimitingMiddleware
from app.routes import reviews
from app.database.base import init_db


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    # Setup logging first
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file
    )
    
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="Backend API for Flex Living Reviews Dashboard"
    )
    
    # Add request logging middleware (before rate limiting to log all requests)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add rate limiting middleware (if enabled)
    if settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitingMiddleware,
            requests_per_minute=settings.rate_limit_per_minute,
            requests_per_hour=settings.rate_limit_per_hour,
            exempt_paths=["/health", "/docs", "/redoc", "/openapi.json"]  # Exempt health and docs
        )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(reviews.router, prefix=settings.api_prefix)
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize database on startup"""
        try:
            await init_db()
            from app.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.info("Database initialized successfully")
        except Exception as e:
            from app.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
    
    return app


# Create app instance
app = create_app()


@app.get("/health", tags=["health"])
async def health_check(request: Request):
    """Health check endpoint"""
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    request_id = getattr(request.state, "request_id", "unknown")
    logger.debug(f"[{request_id}] Health check requested")
    
    return {
        "status": "healthy",
        "service": settings.api_title,
        "version": settings.api_version
    }

