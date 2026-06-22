import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.redis import init_redis, close_redis
from app.api.v1 import api_router
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables automatically on startup
    from app.core.database import init_db
    await init_db()
    
    # Initialize Redis connection on startup
    await init_redis()
    
    # Ensure directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CLONE_DIR, exist_ok=True)
    
    yield
    
    # Close Redis connection on shutdown
    await close_redis()

app = FastAPI(
    title="AI Code Review Platform API",
    description="Production-grade API for automated codebase code reviews using Google Gemini.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173", # Vite local dev server default
    "http://localhost:3000",
    "http://localhost",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_limit=150) # 150 requests/min per IP

# Register API Router
app.include_router(api_router, prefix="/api/v1")

@app.get("/health", status_code=status.HTTP_200_OK, tags=["system"])
async def health_check():
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "gemini_configured": bool(settings.GEMINI_API_KEY)
    }

@app.get("/", status_code=status.HTTP_200_OK, tags=["system"])
async def root():
    return {
        "message": "Welcome to the AI Code Review Platform API.",
        "docs_url": "/docs"
    }
