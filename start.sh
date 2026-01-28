#!/bin/bash
echo "🚀 Starting ActForIran Platform..."
echo "📂 Current directory: $(pwd)"

# Check if we're in the correct directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the root directory of the actforiran project"
    echo "   Expected structure: ./backend and ./frontend directories"
    exit 1
fi

# Setup environment
export ENVIRONMENT=development
export FRONTEND_URL=http://localhost:3000
export DATABASE_URL=sqlite:///./actforiran.db
export JWT_SECRET=your-super-secret-jwt-key-here-change-in-production
export OPENAI_API_KEY=your-openai-key-here
export OPENAI_MODEL=gpt-4o-mini

echo "🛠️  Environment configured:"
echo "   Environment: $ENVIRONMENT"
echo "   Frontend URL: $FRONTEND_URL"
echo "   Database: SQLite (local)"
echo "   JWT Secret: [CONFIGURED]"
echo "   OpenAI Key: ${OPENAI_API_KEY:0:10}..."

# Navigate to backend directory
cd backend

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🗄️  Initializing database and seeding data..."
python -c "from database import init_db; init_db()"

echo "🌐 Starting backend server on http://localhost:8000..."
echo "📋 API Documentation: http://localhost:8000/api/docs"
echo "🔐 Admin Login: admin@actforiran.org / admin123"
echo ""
echo "🎯 Test endpoints:"
echo "   Health: http://localhost:8000/health"
echo "   Countries: http://localhost:8000/api/v1/countries"
echo "   Test Suite: http://localhost:8000/api/test/connectivity"
echo ""
echo "🎨 Frontend files are in ../frontend/"
echo "   Open index.html in your browser or serve with a local server"
echo ""
echo "Press Ctrl+C to stop the server"
echo "==========================================="

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000