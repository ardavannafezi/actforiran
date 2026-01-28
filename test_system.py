#!/usr/bin/env python3
"""
ActForIran Platform - Database Testing and Validation Script
Tests all database connections, seeding, and API endpoints
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from database import SessionLocal, init_db, seed_defaults
from models import Administrator, Country, RecipientRole, PoliticalRecipient, AdvocacyTopic
from services.auth import verify_password

def test_database_connection():
    """Test database connection and basic operations"""
    print("🔗 Testing database connection...")
    
    try:
        db = SessionLocal()
        # Test a simple query
        count = db.query(Administrator).count()
        print(f"✅ Database connected successfully! Found {count} administrators.")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_database_seeding():
    """Test database seeding with sample data"""
    print("🌱 Testing database seeding...")
    
    try:
        db = SessionLocal()
        
        # Check if seeding created the expected data
        admin_count = db.query(Administrator).count()
        country_count = db.query(Country).count()
        role_count = db.query(RecipientRole).count()
        recipient_count = db.query(PoliticalRecipient).count()
        topic_count = db.query(AdvocacyTopic).count()
        
        print(f"📊 Database contents:")
        print(f"   Administrators: {admin_count}")
        print(f"   Countries: {country_count}")
        print(f"   Recipient Roles: {role_count}")
        print(f"   Political Recipients: {recipient_count}")
        print(f"   Advocacy Topics: {topic_count}")
        
        # Test admin user
        admin = db.query(Administrator).filter(Administrator.email == "admin@actforiran.org").first()
        if admin:
            password_valid = verify_password("admin123", admin.password_hash)
            print(f"🔐 Admin user test: {'✅ Password correct' if password_valid else '❌ Password incorrect'}")
        else:
            print("❌ Admin user not found!")
        
        # Test some sample data
        iran_country = db.query(Country).filter(Country.code == "IRN").first()
        if iran_country:
            print(f"🇮🇷 Iran country: {iran_country.name}")
        
        sample_recipients = db.query(PoliticalRecipient).limit(3).all()
        print(f"👥 Sample recipients:")
        for recipient in sample_recipients:
            print(f"   - {recipient.full_name} ({recipient.email_address})")
        
        sample_topics = db.query(AdvocacyTopic).limit(3).all()
        print(f"📝 Sample topics:")
        for topic in sample_topics:
            print(f"   - {topic.display_title}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database seeding test failed: {e}")
        return False

async def test_api_endpoints():
    """Test API endpoints"""
    print("🌐 Testing API endpoints...")
    
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
        
        # Test countries endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/countries")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Countries endpoint working ({len(data.get('countries', []))} countries)")
            else:
                print(f"❌ Countries endpoint failed: {response.status_code}")
        
        # Test recipients endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/recipients")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Recipients endpoint working ({len(data.get('recipients', []))} recipients)")
            else:
                print(f"❌ Recipients endpoint failed: {response.status_code}")
        
        # Test topics endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/topics")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Topics endpoint working ({len(data.get('topics', []))} topics)")
            else:
                print(f"❌ Topics endpoint failed: {response.status_code}")
        
        return True
        
    except ImportError:
        print("⚠️  httpx not installed, skipping API tests")
        print("   Install with: pip install httpx")
        return False
    except Exception as e:
        print(f"❌ API testing failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 ActForIran Platform - Database & API Tests")
    print("=" * 50)
    
    # Set environment for testing
    os.environ["DATABASE_URL"] = "sqlite:///./actforiran.db"
    os.environ["ENVIRONMENT"] = "development"
    
    # Initialize database
    print("🗄️  Initializing database...")
    init_db()
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_database_connection():
        tests_passed += 1
    
    if test_database_seeding():
        tests_passed += 1
    
    # Note: API tests require the server to be running
    print("\nℹ️  API endpoint tests require the server to be running")
    print("   Start the server with: ./start.sh")
    print("   Then run: python test_system.py --api-only")
    
    print("\n" + "=" * 50)
    print(f"📋 Test Results: {tests_passed}/{total_tests - 1} tests passed")
    
    if tests_passed == total_tests - 1:
        print("✅ All database tests passed!")
        print("\n🚀 Next steps:")
        print("   1. Run ./start.sh to start the backend server")
        print("   2. Open frontend/index.html in your browser")
        print("   3. Test the full application workflow")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    if "--api-only" in sys.argv:
        asyncio.run(test_api_endpoints())
    else:
        success = main()
        sys.exit(0 if success else 1)