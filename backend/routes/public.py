import os
import asyncio
from typing import Optional
from urllib.parse import quote
import httpx

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from limiter import limiter
from models import AdvocacyTopic, Country, PoliticalRecipient, RecipientRole, EmailGenerationLog, Campaign, TickerMessage
from schemas import (
    CountriesResponse,
    GenerateEmailRequest,
    GenerateEmailGroupsResponse,
    LogEmailSendRequest,
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
async def list_topics(
    country_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AdvocacyTopic).filter(
        AdvocacyTopic.is_active.is_(True),
        AdvocacyTopic.approval_status == "approved"
    )
    
    topics = query.order_by(AdvocacyTopic.display_title).all()
    
    # Filter by country if provided - topic matches if country_code is in its country_codes array
    if country_code:
        country_upper = country_code.upper()
        topics = [t for t in topics if country_upper in (t.country_codes or [])]

    return {
        "topics": [
            {
                "id": t.id,
                "slug": t.slug,
                "display_title": t.display_title,
                "description": t.description,
                "country_codes": t.country_codes or [],
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

    if not campaigns:
        campaigns = db.query(Campaign).filter(
            Campaign.is_active.is_(True),
            Campaign.approval_status == "approved"
        ).order_by(Campaign.display_order, Campaign.created_at.desc()).all()
    
    result = []
    for campaign in campaigns:
        result.append({
            "id": campaign.id,
            "title": campaign.title,
            "description": campaign.description,
            "slug": campaign.slug,
            "icon": campaign.icon or "🔥",
            "is_hot": campaign.is_hot,
            "is_active": campaign.is_active,
            "recipient_ids": campaign.recipient_ids or []
        })
    
    return {"campaigns": result}


@router.get("/ticker-messages")
async def get_ticker_messages(db: Session = Depends(get_db)):
    """Get active ticker messages for homepage slider"""
    messages = db.query(TickerMessage).filter(
        TickerMessage.is_active.is_(True)
    ).order_by(TickerMessage.display_order, TickerMessage.created_at.desc()).all()
    
    return {
        "messages": [msg.message_text for msg in messages]
    }


@router.post("/generate-email", response_model=GenerateEmailGroupsResponse)
@limiter.limit("5/hour")
async def generate_email_endpoint(
    request: Request,
    payload: GenerateEmailRequest,
    db: Session = Depends(get_db),
):
    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=503, detail="AI service is not configured")
        
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

        token_usage = 0
        sender_citizenship_status = payload.sender_citizenship_status
        if not sender_citizenship_status and payload.is_resident is not None:
            sender_citizenship_status = "selected_country_citizen" if payload.is_resident else "international_supporter"

        if sender_citizenship_status not in ["international_supporter", "iranian_citizen", "selected_country_citizen"]:
            raise HTTPException(status_code=400, detail="Invalid sender citizenship status")

        recipients_by_id = {r[0].id: r for r in recipients}
        ordered_recipient_ids = payload.recipient_ids

        def chunk_list(items, size):
            return [items[i:i + size] for i in range(0, len(items), size)]

        groups = []
        for group_ids in chunk_list(ordered_recipient_ids, 15):
            group_recipients = [recipients_by_id[rid] for rid in group_ids if rid in recipients_by_id]
            group_payload = [
                {
                    "id": r[0].id,
                    "full_name": r[0].full_name,
                    "email_address": r[0].email_address,
                    "display_title": r[0].custom_title or r[1],
                }
                for r in group_recipients
            ]

            try:
                subject, body, used_tokens = await asyncio.wait_for(
                    generate_email(
                        country_name=country.name,
                        recipients=group_payload,
                        topics=topics_payload,
                        sender_citizenship_status=sender_citizenship_status,
                        user_name=payload.user_name,
                    ),
                    timeout=12.0,
                )
                token_usage += used_tokens
            except asyncio.TimeoutError as exc:
                print("❌ AI Service Timeout")
                raise HTTPException(status_code=504, detail="AI service timed out. Please try again.") from exc
            except AIServiceError as exc:
                print(f"❌ AI Service Error: {str(exc)}")
                raise HTTPException(status_code=500, detail=f"AI service error: {str(exc)}") from exc
            except Exception as exc:
                print(f"❌ Unexpected error during email generation: {str(exc)}")
                raise HTTPException(status_code=500, detail=f"Failed to generate email: {str(exc)}") from exc

            recipient_emails = [r[0].email_address for r in group_recipients]
            mailto_recipients = ",".join(recipient_emails)
            mailto_link = (
                f"mailto:{mailto_recipients}?subject={quote(subject)}&body={quote(body)}"
                if subject and body
                else ""
            )

            groups.append({
                "subject": subject,
                "body": body,
                "recipients": [{"name": r[0].full_name, "email": r[0].email_address} for r in group_recipients],
                "recipient_ids": group_ids,
                "mailto_link": mailto_link,
            })

        return {"groups": groups}
    
    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ Unexpected error in generate_email_endpoint: {str(exc)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}") from exc


@router.post("/log-email-send")
@limiter.limit("30/hour")
async def log_email_send(
    request: Request,
    payload: LogEmailSendRequest,
    db: Session = Depends(get_db),
):
    country = db.query(Country).filter(Country.code == payload.country_code.upper()).first()
    if not country:
        raise HTTPException(status_code=400, detail="Invalid country code")

    sender_citizenship_status = payload.sender_citizenship_status
    if sender_citizenship_status not in ["international_supporter", "iranian_citizen", "selected_country_citizen"]:
        raise HTTPException(status_code=400, detail="Invalid sender citizenship status")

    sender_country_code = None
    sender_country_name = None
    client_ip = request.client.host if request.client else None
    if client_ip and client_ip not in ["127.0.0.1", "localhost"]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"https://ipapi.co/{client_ip}/json/")
                data = response.json()
                sender_country_code = data.get("country_code")
                sender_country_name = data.get("country_name")
        except Exception:
            pass

    log_entry = EmailGenerationLog(
        campaign_id=payload.campaign_id,
        sender_ip_address=request.client.host if request.client else None,
        sender_country_code=sender_country_code,
        sender_country_name=sender_country_name,
        sender_user_name=payload.user_name,
        sender_citizenship_status=sender_citizenship_status,
        is_country_resident=sender_citizenship_status == "selected_country_citizen",
        selected_recipient_country=country.name,
        recipient_ids=payload.recipient_ids,
        topic_ids=payload.topic_ids,
        generated_subject=payload.subject,
        generated_body=(payload.body[:500] + "...") if payload.body and len(payload.body) > 500 else payload.body,
        generation_successful=True,
        error_message=None,
        ai_model_used=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        ai_tokens_used=0,
    )
    db.add(log_entry)
    db.commit()

    return {"status": "logged"}
