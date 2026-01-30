from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.middleware.rate_limit import limiter
from app.routers import auth, recipes, categories, tags, users
from app.routers import settings as settings_router
from app.routers import import_router

app_settings = get_settings()

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

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["Recipes"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
app.include_router(tags.router, prefix="/api/tags", tags=["Tags"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Settings"])
app.include_router(import_router.router, prefix="/api/import", tags=["Import"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
