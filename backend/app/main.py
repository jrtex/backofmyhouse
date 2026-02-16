import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import SessionLocal
from app.logging_config import setup_logging
from app.middleware.rate_limit import limiter
from app.middleware.request_logging import RequestLoggingMiddleware
from app.routers import auth, recipes, categories, tags, users
from app.routers import settings as settings_router
from app.routers import import_router
from app.routers import backup_router
from app.routers import ai_usage
from app.services.ai_usage_service import AIUsageService

app_settings = get_settings()
setup_logging(log_level=app_settings.log_level, log_format=app_settings.log_format)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Recipe Management API",
    description="API for managing recipes, categories, and tags",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["Recipes"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
app.include_router(tags.router, prefix="/api/tags", tags=["Tags"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Settings"])
app.include_router(import_router.router, prefix="/api/import", tags=["Import"])
app.include_router(backup_router.router, prefix="/api/backup", tags=["Backup"])
app.include_router(ai_usage.router, prefix="/api/ai-usage", tags=["AI Usage"])


@app.on_event("startup")
async def startup_cleanup():
    db = SessionLocal()
    try:
        deleted = AIUsageService.cleanup_old_logs(db, app_settings.ai_usage_retention_days)
        if deleted > 0:
            logger.info("Startup AI usage log cleanup", extra={"deleted_count": deleted})
    except Exception:
        logger.exception("Failed to clean up old AI usage logs on startup")
    finally:
        db.close()


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
