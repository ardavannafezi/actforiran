#!/usr/bin/env python3
"""
Quick start script for ActForIran backend
Run this to start the server with proper CORS configuration
"""

import os
import sys

# Set environment variables
os.environ['ENVIRONMENT'] = 'development'
os.environ['DATABASE_URL'] = 'sqlite:///./actforiran.db'
os.environ['JWT_SECRET'] = 'dev-secret-key-change-in-production'

# Change to backend directory
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

print("=" * 60)
print("🚀 Starting ActForIran Backend Server")
print("=" * 60)
print(f"📂 Working directory: {os.getcwd()}")
print(f"🌐 Server will run on: http://localhost:8000")
print(f"📚 API Docs: http://localhost:8000/api/docs")
print(f"🧪 Test Page: Open frontend/test.html in browser")
print("=" * 60)
print()
print("✅ CORS is configured to allow ALL origins (development mode)")
print("✅ Database will be initialized automatically")
print("✅ Sample data will be seeded")
print()
print("Press Ctrl+C to stop the server")
print("=" * 60)
print()

# Initialize database
from database import init_db
init_db()
print("✓ Database initialized and seeded\n")

# Start server
import uvicorn
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    log_level="info"
)