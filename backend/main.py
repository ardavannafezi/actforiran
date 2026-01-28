"""
Iranian Advocacy Email Campaign Platform - Backend
FastAPI application for generating advocacy emails to politicians
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from dotenv import load_dotenv

from database import init_db
from limiter import limiter
from routes.public import router as public_router

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Iranian Advocacy Platform API",
    description="API for generating personalized advocacy emails regarding human rights violations in Iran",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, limiter._rate_limit_exceeded_handler)

# Routes
app.include_router(public_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Iranian Advocacy Platform API",
        "version": "1.0.0",
        "message": "Backend is running successfully!",
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database_configured": bool(os.getenv("DATABASE_URL")),
        "ai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "ai_model": os.getenv("OPENAI_MODEL", "o4-mini"),
        "jwt_configured": bool(os.getenv("JWT_SECRET")),
    }


@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {
        "message": "API is working correctly!",
        "endpoints": {
            "health": "/api/health",
            "docs": "/api/docs",
            "public": "/api/v1/",
            "admin": "/api/v1/admin/",
        },
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 Iranian Advocacy Platform API starting...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🌐 Frontend URL: {os.getenv('FRONTEND_URL', 'Not set')}")
    print(f"💾 Database: {'Configured' if os.getenv('DATABASE_URL') else 'Not configured'}")
    print(f"🤖 AI Service: {'Configured' if os.getenv('OPENAI_API_KEY') else 'Not configured'}")
    init_db()
    print("✅ Application started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("🛑 Iranian Advocacy Platform API shutting down...")
