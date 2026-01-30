"""
Iranian Advocacy Email Campaign Platform - Backend API
FastAPI application for generating advocacy emails to politicians
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

# Import routes
from routes.public import router as public_router
from routes.admin import router as admin_router
from routes.test import router as test_router
from database import init_db
from limiter import limiter

# Initialize FastAPI app
app = FastAPI(
    title="ActForIran API",
    description="API for generating personalized advocacy emails regarding human rights violations in Iran",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
default_origins = [
    "https://actforiran.org",
    "https://www.actforiran.org",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
env_origins = os.getenv("FRONTEND_URLS") or os.getenv("FRONTEND_URL") or ""
extra_origins = [o.strip() for o in env_origins.split(",") if o.strip()]
allow_origins = list(dict.fromkeys(default_origins + extra_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=r"^https://(www\.)?actforiran\.org$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; "
        "base-uri 'none'; "
        "frame-ancestors 'none'; "
        "img-src 'self' data:; "
        "connect-src 'self' https://back.actforiran.org https://actforiran.org; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' https://cdn.jsdelivr.net; "
    )
    return response

# Rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "ActForIran API is running",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ActForIran API",
        "version": "1.0.0",
        "message": "Iranian Advocacy Email Campaign Platform - Backend is running successfully!",
        "endpoints": {
            "health": "/health",
            "docs": "/api/docs",
            "public": "/api/v1/",
            "admin": "/api/v1/admin/",
            "testing": "/api/test/"
        }
    }

# Include routers
app.include_router(public_router)
app.include_router(admin_router)
app.include_router(test_router, prefix="/api/test", tags=["testing"])

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 Starting ActForIran API...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🌐 Frontend URL: {os.getenv('FRONTEND_URL', 'Not set')}")
    print(f"💾 Database: {'Configured' if os.getenv('DATABASE_URL') else 'SQLite (local)'}")
    init_db()  # Initialize database and seed data
    print("✅ Application started successfully!")

@app.on_event("shutdown") 
async def shutdown_event():
    """Run on application shutdown"""
    print("📴 Shutting down ActForIran API...")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=os.getenv("ENVIRONMENT") != "production"
    )
