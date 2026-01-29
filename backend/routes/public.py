import os
from typing import Optional
from urllib.parse import quote
import httpx

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from limiter import limiter
from models import AdvocacyTopic, Country, PoliticalRecipient, RecipientRole, EmailGenerationLog, Campaign
from schemas import (
    CountriesResponse,
    GenerateEmailRequest,
    GenerateEmailResponse,
    RecipientsResponse,
    TopicsResponse,
)
from services.ai_service import AIServiceError, generate_email
from data.top_countries import get_country_flag, TOP_COUNTRIES

router = APIRouter(prefix="/api/v1", tags=["public"])


@router.get("/suggest-country")
async def suggest_country(request: Request):
    """Get suggested country based on user's IP address"""
    client_ip = request.client.host if request.client else None
    
    if not client_ip or client_ip in ["127.0.0.1", "localhost"]:
        return {"suggested_country": None, "message": "Local IP detected"}
    
    try:
        # Use ipapi.co free service for IP geolocation
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"https://ipapi.co/{client_ip}/json/")
            data = response.json()
            
            if "country_code" in data and data["country_code"]:
                country_code = data["country_code"]
                # Check if this country is in our list
                matching_country = next((c for c in TOP_COUNTRIES if c["code"] == country_code), None)
                
                if matching_country:
                    return {
                        "suggested_country": {
                            "code": matching_country["code"],
                            "name": matching_country["name"],
                            "flag": matching_country["flag"]
                        }
                    }
    except Exception as e:
        # Silent fail - just return no suggestion
        pass
    
    return {"suggested_country": None, "message": "Could not determine location"}


@router.get("/countries", response_model=CountriesResponse)
async def list_countries(db: Session = Depends(get_db)):
    """Get list of top influential countries with flags"""
    # Get only countries from TOP_COUNTRIES list
    top_codes = [c["code"] for c in TOP_COUNTRIES]
    countries = db.query(Country).filter(
        Country.is_active.is_(True),
        Country.code.in_(top_codes)
    ).order_by(Country.name).all()
    
    return {
        "countries": [
            {
                "code": c.code,
                "name": c.name,
                "name_persian": c.name_persian or c.name,
                "flag": get_country_flag(c.code)
            } for c in countries
        ]
    }


@router.get("/recipients", response_model=RecipientsResponse)
async def list_recipients(
    country_code: Optional[str] = None,
    country_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(PoliticalRecipient, Country.name.label("country_name"), RecipientRole.name.label("role_name"))
        .join(Country, PoliticalRecipient.country_code == Country.code)
        .join(RecipientRole, PoliticalRecipient.role_id == RecipientRole.id)
        .filter(PoliticalRecipient.is_active.is_(True))
        .filter(PoliticalRecipient.approval_status == "approved")
    )

    if country_code:
        query = query.filter(PoliticalRecipient.country_code == country_code.upper())
    if country_name:
        query = query.filter(Country.name.ilike(f"%{country_name}%"))

    results = query.order_by(PoliticalRecipient.full_name).all()

    recipients = []
    for recipient, resolved_country_name, role_name in results:
        display_title = recipient.custom_title or role_name
        recipients.append(
            {
                "id": recipient.id,
                "full_name": recipient.full_name,
                "email_address": recipient.email_address,
                "display_title": display_title,
                "country_code": recipient.country_code,
                "country_name": resolved_country_name,
            }
        )

    return {"recipients": recipients}


@router.get("/topics", response_model=TopicsResponse)
async def list_topics(db: Session = Depends(get_db)):
    topics = (
        db.query(AdvocacyTopic)
        .filter(AdvocacyTopic.is_active.is_(True))
        .filter(AdvocacyTopic.approval_status == "approved")
        .order_by(AdvocacyTopic.display_title)
        .all()
    )

    return {
        "topics": [
            {
                "id": t.id,
                "slug": t.slug,
                "display_title": t.display_title,
                "description": t.description,
            }
            for t in topics
        ]
    }


@router.get("/campaigns")
async def list_campaigns(db: Session = Depends(get_db)):
    """Get list of hot campaigns (predefined by admins)"""
    campaigns = db.query(Campaign).filter(
        Campaign.is_active.is_(True),
        Campaign.is_hot.is_(True),
        Campaign.approval_status == "approved"
    ).order_by(Campaign.display_order, Campaign.created_at.desc()).all()
    
    result = []
    for campaign in campaigns:
        country = db.query(Country).filter(Country.code == campaign.country_code).first()
        result.append({
            "id": campaign.id,
            "title": campaign.title,
            "description": campaign.description,
            "slug": campaign.slug,
            "icon": campaign.icon or "🔥",
            "country": {
                "code": campaign.country_code,
                "name": country.name if country else "",
                "name_persian": country.name_persian if country else "",
                "flag": get_country_flag(campaign.country_code)
            },
            "recipient_ids": campaign.recipient_ids,
            "topic_ids": campaign.topic_ids
        })
    
    return {"campaigns": result}


@router.post("/generate-email", response_model=GenerateEmailResponse)
@limiter.limit("5/hour")
async def generate_email_endpoint(
    request: Request,
    payload: GenerateEmailRequest,
    db: Session = Depends(get_db),
):
    country = db.query(Country).filter(Country.code == payload.country_code.upper()).first()
    if not country:
        raise HTTPException(status_code=400, detail="Invalid country code")

    recipients = (
        db.query(PoliticalRecipient, RecipientRole.name.label("role_name"))
        .join(RecipientRole, PoliticalRecipient.role_id == RecipientRole.id)
        .filter(PoliticalRecipient.id.in_(payload.recipient_ids))
        .filter(PoliticalRecipient.approval_status == "approved")
        .filter(PoliticalRecipient.is_active.is_(True))
        .all()
    )
    if len(recipients) != len(payload.recipient_ids):
        raise HTTPException(status_code=400, detail="One or more recipients are invalid")

    topics = (
        db.query(AdvocacyTopic)
        .filter(AdvocacyTopic.id.in_(payload.topic_ids))
        .filter(AdvocacyTopic.approval_status == "approved")
        .filter(AdvocacyTopic.is_active.is_(True))
        .all()
    )
    if len(topics) != len(payload.topic_ids):
        raise HTTPException(status_code=400, detail="One or more topics are invalid")

    recipients_payload = []
    for recipient, role_name in recipients:
        recipients_payload.append(
            {
                "id": recipient.id,
                "full_name": recipient.full_name,
                "email_address": recipient.email_address,
                "display_title": recipient.custom_title or role_name,
            }
        )

    topics_payload = [
        {
            "id": t.id,
            "display_title": t.display_title,
            "description": t.description or "",
            "requested_action": "",
            "sources": [],
        }
        for t in topics
    ]

    subject = ""
    body = ""
    token_usage = 0
    error_message = None
    success = True
    sender_citizenship_status = payload.sender_citizenship_status
    if not sender_citizenship_status and payload.is_resident is not None:
        sender_citizenship_status = "selected_country_citizen" if payload.is_resident else "international_supporter"

    if sender_citizenship_status not in ["international_supporter", "iranian_citizen", "selected_country_citizen"]:
        raise HTTPException(status_code=400, detail="Invalid sender citizenship status")

    try:
        subject, body, token_usage = await generate_email(
            country_name=country.name,
            recipients=recipients_payload,
            topics=topics_payload,
            sender_citizenship_status=sender_citizenship_status,
            user_name=payload.user_name,
        )
    except AIServiceError as exc:
        success = False
        error_message = str(exc)
        raise HTTPException(status_code=502, detail="AI service failed to generate email") from exc
    finally:
        is_country_resident = sender_citizenship_status == "selected_country_citizen"
        log_entry = EmailGenerationLog(
            campaign_id=payload.campaign_id,
            sender_ip_address=request.client.host if request.client else None,
            sender_country_code=None,
            sender_country_name=None,
            sender_user_name=payload.user_name,
            sender_citizenship_status=sender_citizenship_status,
            is_country_resident=is_country_resident,
            selected_recipient_country=country.name,
            recipient_ids=payload.recipient_ids,
            topic_ids=payload.topic_ids,
            generated_subject=subject or None,
            generated_body=(body[:500] + "...") if body and len(body) > 500 else body,
            generation_successful=success,
            error_message=error_message,
            ai_model_used=os.getenv("OPENAI_MODEL", "o4-mini"),
            ai_tokens_used=token_usage,
        )
        db.add(log_entry)
        db.commit()

    recipient_emails = [r[0].email_address for r in recipients]
    mailto_recipients = ",".join(recipient_emails)

    mailto_link = (
        f"mailto:{mailto_recipients}?subject={quote(subject)}&body={quote(body)}"
        if subject and body
        else ""
    )

    return {
        "subject": subject,
        "body": body,
        "recipients": [
            {"name": r[0].full_name, "email": r[0].email_address} for r in recipients
        ],
        "mailto_link": mailto_link,
    }
