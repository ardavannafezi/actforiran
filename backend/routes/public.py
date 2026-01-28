import os
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from limiter import limiter
from models import AdvocacyTopic, Country, PoliticalRecipient, RecipientRole, EmailGenerationLog
from schemas import (
    CountriesResponse,
    GenerateEmailRequest,
    GenerateEmailResponse,
    RecipientsResponse,
    TopicsResponse,
)
from services.ai_service import AIServiceError, generate_email

router = APIRouter(prefix="/api/v1", tags=["public"])


@router.get("/countries", response_model=CountriesResponse)
async def list_countries(db: Session = Depends(get_db)):
    countries = db.query(Country).filter(Country.is_active.is_(True)).order_by(Country.name).all()
    return {"countries": [{"code": c.code, "name": c.name} for c in countries]}


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
        {"id": t.id, "display_title": t.display_title, "description": t.description or ""} for t in topics
    ]

    subject = ""
    body = ""
    token_usage = 0
    error_message = None
    success = True

    try:
        subject, body, token_usage = await generate_email(
            country_name=country.name,
            recipients=recipients_payload,
            topics=topics_payload,
            is_resident=payload.is_resident,
        )
    except AIServiceError as exc:
        success = False
        error_message = str(exc)
        raise HTTPException(status_code=502, detail="AI service failed to generate email") from exc
    finally:
        log_entry = EmailGenerationLog(
            sender_ip_address=request.client.host if request.client else None,
            sender_country_code=None,
            sender_country_name=None,
            is_country_resident=payload.is_resident,
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
