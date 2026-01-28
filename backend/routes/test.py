"""
Testing endpoints for connectivity and functionality
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import *
from typing import Dict, Any

router = APIRouter()

@router.get("/connectivity")
async def test_connectivity():
    """Test basic API connectivity"""
    return {
        "status": "success",
        "message": "Backend API is working correctly",
        "timestamp": "2026-01-28T00:00:00Z"
    }

@router.get("/database")
async def test_database(db: Session = Depends(get_db)):
    """Test database connectivity and show sample data"""
    try:
        # Test each table
        admin_count = db.query(Administrator).count()
        country_count = db.query(Country).count()
        role_count = db.query(RecipientRole).count()
        recipient_count = db.query(PoliticalRecipient).count()
        topic_count = db.query(AdvocacyTopic).count()
        
        # Get sample data
        sample_admin = db.query(Administrator).first()
        sample_country = db.query(Country).first()
        sample_recipient = db.query(PoliticalRecipient).first()
        sample_topic = db.query(AdvocacyTopic).first()
        
        return {
            "status": "success",
            "message": "Database connection working",
            "data": {
                "counts": {
                    "administrators": admin_count,
                    "countries": country_count,
                    "roles": role_count,
                    "recipients": recipient_count,
                    "topics": topic_count
                },
                "samples": {
                    "admin": {
                        "email": sample_admin.email if sample_admin else None,
                        "role": sample_admin.role if sample_admin else None
                    },
                    "country": {
                        "code": sample_country.code if sample_country else None,
                        "name": sample_country.name if sample_country else None
                    },
                    "recipient": {
                        "name": sample_recipient.full_name if sample_recipient else None,
                        "country": sample_recipient.country_code if sample_recipient else None
                    },
                    "topic": {
                        "title": sample_topic.display_title if sample_topic else None,
                        "slug": sample_topic.slug if sample_topic else None
                    }
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/public-endpoints")
async def test_public_endpoints(db: Session = Depends(get_db)):
    """Test all public API endpoints"""
    try:
        # Test countries endpoint
        countries = db.query(Country).filter(Country.is_active == True).limit(5).all()
        
        # Test recipients endpoint  
        recipients = db.query(PoliticalRecipient).filter(
            PoliticalRecipient.approval_status == "approved"
        ).limit(5).all()
        
        # Test topics endpoint
        topics = db.query(AdvocacyTopic).filter(
            AdvocacyTopic.approval_status == "approved"
        ).limit(5).all()
        
        return {
            "status": "success",
            "message": "Public endpoints data available",
            "data": {
                "countries": [
                    {"code": c.code, "name": c.name} for c in countries
                ],
                "recipients": [
                    {
                        "name": r.full_name,
                        "country": r.country_code,
                        "email": r.email_address
                    } for r in recipients
                ],
                "topics": [
                    {
                        "title": t.display_title,
                        "slug": t.slug,
                        "description": t.description
                    } for t in topics
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Public endpoints test failed: {str(e)}")

@router.post("/email-generation")
async def test_email_generation():
    """Test email generation functionality (mock)"""
    # Mock AI response for testing
    mock_response = {
        "status": "success",
        "message": "Email generation test completed",
        "generated_email": {
            "subject": "Urgent: International Action Needed on Iran Human Rights Crisis",
            "body": "Dear Prime Minister,\\n\\nAs a concerned citizen, I write to urge immediate action regarding the ongoing human rights violations in Iran. The Iranian regime continues to suppress peaceful protesters and deny basic freedoms to its people.\\n\\nI respectfully request that your government:\\n1. Impose targeted sanctions on Iranian officials\\n2. Support international investigations\\n3. Provide humanitarian aid to affected communities\\n\\nThank you for your attention to this critical matter.\\n\\nSincerely,\\nA concerned citizen",
            "recipients": [
                {
                    "name": "Test Recipient",
                    "email": "test@example.com"
                }
            ]
        }
    }
    
    return mock_response

@router.get("/admin-login-test")
async def test_admin_credentials():
    """Show test admin credentials"""
    return {
        "status": "success",
        "message": "Test admin credentials",
        "credentials": {
            "email": "admin@actforiran.org",
            "password": "admin123",
            "note": "Use these credentials to test admin panel login"
        }
    }

@router.get("/sample-data")
async def test_sample_data(db: Session = Depends(get_db)):
    """Get sample data for testing"""
    try:
        sample_country = db.query(Country).first()
        sample_recipients = db.query(PoliticalRecipient).filter(
            PoliticalRecipient.approval_status == "approved"
        ).limit(3).all()
        sample_topics = db.query(AdvocacyTopic).filter(
            AdvocacyTopic.approval_status == "approved"
        ).limit(3).all()
        
        return {
            "status": "success",
            "message": "Sample data retrieved",
            "data": {
                "country": {
                    "code": sample_country.code if sample_country else None,
                    "name": sample_country.name if sample_country else None
                },
                "recipients": [
                    {
                        "id": r.id,
                        "name": r.full_name,
                        "email": r.email_address,
                        "country": r.country_code
                    } for r in sample_recipients
                ],
                "topics": [
                    {
                        "id": t.id,
                        "title": t.display_title,
                        "slug": t.slug
                    } for t in sample_topics
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sample data: {str(e)}")

@router.get("/admin-auth")
async def test_admin_auth(db: Session = Depends(get_db)):
    """Test admin authentication setup"""
    try:
        admin = db.query(Administrator).filter(
            Administrator.email == "admin@actforiran.org"
        ).first()
        
        if not admin:
            return {
                "status": "error",
                "message": "Admin user not found in database",
                "note": "Run database seeding to create admin user"
            }
        
        return {
            "status": "success",
            "message": "Admin user exists in database",
            "admin": {
                "email": admin.email,
                "role": admin.role,
                "is_active": admin.is_active,
                "note": "Password: admin123 (bcrypt hashed in DB)"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking admin: {str(e)}")