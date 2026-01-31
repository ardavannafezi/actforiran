from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import (
    AdminActivityLog,
    AdvocacyTopic,
    Administrator,
    Campaign,
    Country,
    PoliticalRecipient,
    RecipientRole,
    TickerMessage,
)
from schemas import (
    AdminLoginRequest,
    AdminMeResponse,
    AdminTokenResponse,
    AdvocacyTopicAdminOut,
    AdvocacyTopicCreate,
    AdvocacyTopicUpdate,
    ApprovalRequest,
    CampaignCreate,
    CampaignOut,
    CampaignUpdate,
    PoliticalRecipientAdminOut,
    PoliticalRecipientCreate,
    PoliticalRecipientUpdate,
    RecipientRoleCreate,
    RecipientRoleOut,
    TickerMessageCreate,
    TickerMessageUpdate,
)
from services.auth import (
    create_access_token,
    get_current_admin,
    get_password_hash,
    require_super_admin,
    verify_password,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def log_action(
    db: Session,
    admin: Administrator,
    action_type: str,
    target_entity_type: str,
    target_entity_id: Optional[int],
    details: Optional[dict],
    request: Optional[Request] = None,
):
    log_entry = AdminActivityLog(
        admin_id=admin.id,
        action_type=action_type,
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
        action_details=details or {},
        ip_address=request.client.host if request and request.client else None,
    )
    db.add(log_entry)


@router.post("/auth/login", response_model=AdminTokenResponse)
async def admin_login(payload: AdminLoginRequest, response: Response, db: Session = Depends(get_db)):
    admin = db.query(Administrator).filter(Administrator.email == payload.email).first()
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Check if admin is active (super_admin is always allowed)
    if admin.role != "super_admin" and hasattr(admin, 'is_active') and not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    admin.last_login = datetime.utcnow()
    db.add(admin)
    db.commit()

    token = create_access_token(subject=admin.email, role=admin.role)
    return {"access_token": token, "token_type": "bearer", "role": admin.role}


@router.post("/auth/refresh", response_model=AdminTokenResponse)
async def refresh_token(admin: Administrator = Depends(get_current_admin)):
    token = create_access_token(subject=admin.email, role=admin.role)
    return {"access_token": token, "token_type": "bearer", "role": admin.role}


@router.get("/auth/me", response_model=AdminMeResponse)
async def admin_me(admin: Administrator = Depends(get_current_admin)):
    return {"id": admin.id, "email": admin.email, "role": admin.role}


@router.get("/roles", response_model=list[RecipientRoleOut])
async def list_roles(db: Session = Depends(get_db), admin: Administrator = Depends(get_current_admin)):
    roles = db.query(RecipientRole).order_by(RecipientRole.name).all()
    return [{"id": r.id, "name": r.name, "is_active": r.is_active} for r in roles]


@router.post("/roles", response_model=RecipientRoleOut)
async def create_role(
    payload: RecipientRoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    existing = db.query(RecipientRole).filter(RecipientRole.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role already exists")

    role = RecipientRole(
        name=payload.name,
        is_active=True,
        is_system_default=False,
        created_by_admin_id=admin.id,
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    log_action(db, admin, "CREATE_ROLE", "recipient_role", role.id, {"name": role.name}, request)
    db.commit()

    return {"id": role.id, "name": role.name, "is_active": role.is_active}


@router.get("/admins")
async def list_admins(
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    admins = db.query(Administrator).order_by(Administrator.created_at.desc()).all()
    return {
        "admins": [
            {
                "id": a.id,
                "email": a.email,
                "role": a.role,
                "is_active": a.is_active,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "last_login": a.last_login.isoformat() if a.last_login else None,
            }
            for a in admins
        ]
    }


@router.post("/admins")
async def create_admin(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    if not payload.get("email") or not payload.get("password"):
        raise HTTPException(status_code=400, detail="Email and password are required")

    existing = db.query(Administrator).filter(Administrator.email == payload["email"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_admin = Administrator(
        email=payload["email"],
        password_hash=get_password_hash(payload["password"]),
        role=payload.get("role", "admin"),
        is_active=payload.get("is_active", True),
        created_by_admin_id=admin.id,
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    log_action(db, admin, "CREATE_ADMIN", "administrator", new_admin.id, {"email": new_admin.email}, request)
    db.commit()

    return {
        "id": new_admin.id,
        "email": new_admin.email,
        "role": new_admin.role,
        "is_active": new_admin.is_active,
    }


@router.put("/admins/{admin_id}")
async def update_admin(
    admin_id: int,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    target_admin = db.query(Administrator).filter(Administrator.id == admin_id).first()
    if not target_admin:
        raise HTTPException(status_code=404, detail="Administrator not found")

    if "email" in payload:
        existing = db.query(Administrator).filter(
            Administrator.email == payload["email"],
            Administrator.id != admin_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        target_admin.email = payload["email"]

    if "password" in payload and payload["password"]:
        target_admin.password_hash = get_password_hash(payload["password"])

    if "role" in payload:
        target_admin.role = payload["role"]

    if "is_active" in payload:
        target_admin.is_active = payload["is_active"]

    db.add(target_admin)
    db.commit()

    log_action(db, admin, "UPDATE_ADMIN", "administrator", admin_id, {"updated_fields": list(payload.keys())}, request)
    db.commit()

    return {
        "id": target_admin.id,
        "email": target_admin.email,
        "role": target_admin.role,
        "is_active": target_admin.is_active,
    }


@router.delete("/admins/{admin_id}")
async def delete_admin(
    admin_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    if admin_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    target_admin = db.query(Administrator).filter(Administrator.id == admin_id).first()
    if not target_admin:
        raise HTTPException(status_code=404, detail="Administrator not found")

    log_action(db, admin, "DELETE_ADMIN", "administrator", admin_id, {"email": target_admin.email}, request)
    db.delete(target_admin)
    db.commit()
    return {"message": "Administrator deleted successfully"}


@router.post("/countries")
async def add_country(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    existing = db.query(Country).filter(Country.code == payload["code"].upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Country code already exists")

    country = Country(
        code=payload["code"].upper(),
        name=payload["name"],
        name_persian=payload.get("name_persian", ""),
        flag=payload.get("flag", ""),
        is_active=payload.get("is_active", True),
    )
    db.add(country)
    db.commit()
    db.refresh(country)

    log_action(db, admin, "CREATE_COUNTRY", "country", None, {"code": country.code}, request)
    db.commit()

    return {
        "code": country.code,
        "name": country.name,
        "name_persian": country.name_persian,
        "flag": country.flag,
        "is_active": country.is_active,
    }


@router.put("/countries/{country_code}")
async def update_country(
    country_code: str,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    country = db.query(Country).filter(Country.code == country_code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    if "name" in payload:
        country.name = payload["name"]
    if "name_persian" in payload:
        country.name_persian = payload["name_persian"]
    if "flag" in payload:
        country.flag = payload["flag"]
    if "is_active" in payload:
        country.is_active = payload["is_active"]

    db.add(country)
    db.commit()

    log_action(db, admin, "UPDATE_COUNTRY", "country", None, {"code": country.code}, request)
    db.commit()

    return {
        "code": country.code,
        "name": country.name,
        "name_persian": country.name_persian,
        "flag": country.flag,
        "is_active": country.is_active,
    }


@router.delete("/countries/{country_code}")
async def delete_country(
    country_code: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    country = db.query(Country).filter(Country.code == country_code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    log_action(db, admin, "DELETE_COUNTRY", "country", None, {"code": country.code}, request)
    db.delete(country)
    db.commit()
    return {"message": "Country deleted successfully"}


@router.get("/recipients", response_model=list[PoliticalRecipientAdminOut])
async def list_recipients(
    approval_status: Optional[str] = None,
    country_code: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    query = (
        db.query(
            PoliticalRecipient,
            Country.name.label("country_name"),
            RecipientRole.name.label("role_name"),
        )
        .join(Country, PoliticalRecipient.country_code == Country.code)
        .join(RecipientRole, PoliticalRecipient.role_id == RecipientRole.id)
    )

    if approval_status:
        query = query.filter(PoliticalRecipient.approval_status == approval_status)
    if country_code:
        query = query.filter(PoliticalRecipient.country_code == country_code.upper())

    results = query.order_by(PoliticalRecipient.full_name).all()
    return [
        {
            "id": r.id,
            "full_name": r.full_name,
            "email_address": r.email_address,
            "role_id": r.role_id,
            "role_name": role_name,
            "custom_title": r.custom_title,
            "media_outlets": r.media_outlets,
            "country_code": r.country_code,
            "country_name": country_name,
            "approval_status": r.approval_status,
            "is_active": r.is_active,
        }
        for r, country_name, role_name in results
    ]


@router.post("/recipients", response_model=PoliticalRecipientAdminOut)
async def create_recipient(
    payload: PoliticalRecipientCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    role = db.query(RecipientRole).filter(RecipientRole.id == payload.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")

    country = db.query(Country).filter(Country.code == payload.country_code.upper()).first()
    if not country:
        raise HTTPException(status_code=400, detail="Invalid country")

    approval_status = "approved"

    recipient = PoliticalRecipient(
        full_name=payload.full_name,
        email_address=payload.email_address,
        role_id=payload.role_id,
        custom_title=payload.custom_title,
        media_outlets=payload.media_outlets,
        country_code=payload.country_code.upper(),
        approval_status=approval_status,
        created_by_admin_id=admin.id,
        approved_by_admin_id=admin.id if approval_status == "approved" else None,
    )
    db.add(recipient)
    db.commit()
    db.refresh(recipient)

    log_action(
        db,
        admin,
        "CREATE_RECIPIENT",
        "political_recipient",
        recipient.id,
        {"full_name": recipient.full_name},
        request,
    )
    db.commit()

    return {
        "id": recipient.id,
        "full_name": recipient.full_name,
        "email_address": recipient.email_address,
        "role_id": recipient.role_id,
        "role_name": role.name,
        "custom_title": recipient.custom_title,
        "media_outlets": recipient.media_outlets,
        "country_code": recipient.country_code,
        "country_name": country.name,
        "approval_status": recipient.approval_status,
        "is_active": recipient.is_active,
    }


@router.put("/recipients/{recipient_id}", response_model=PoliticalRecipientAdminOut)
async def update_recipient(
    recipient_id: int,
    payload: PoliticalRecipientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    recipient = db.query(PoliticalRecipient).filter(PoliticalRecipient.id == recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    if payload.role_id is not None:
        role = db.query(RecipientRole).filter(RecipientRole.id == payload.role_id).first()
        if not role:
            raise HTTPException(status_code=400, detail="Invalid role")
        recipient.role_id = payload.role_id

    if payload.country_code is not None:
        country = db.query(Country).filter(Country.code == payload.country_code.upper()).first()
        if not country:
            raise HTTPException(status_code=400, detail="Invalid country")
        recipient.country_code = payload.country_code.upper()

    if payload.full_name is not None:
        recipient.full_name = payload.full_name
    if payload.email_address is not None:
        recipient.email_address = payload.email_address
    if payload.custom_title is not None:
        recipient.custom_title = payload.custom_title
    if payload.media_outlets is not None:
        recipient.media_outlets = payload.media_outlets
    if payload.is_active is not None:
        recipient.is_active = payload.is_active

    if admin.role != "super_admin":
        recipient.approval_status = "approved"
        recipient.approved_by_admin_id = admin.id

    db.add(recipient)
    db.commit()
    db.refresh(recipient)

    role = db.query(RecipientRole).filter(RecipientRole.id == recipient.role_id).first()
    country = db.query(Country).filter(Country.code == recipient.country_code).first()

    log_action(
        db,
        admin,
        "UPDATE_RECIPIENT",
        "political_recipient",
        recipient.id,
        {"full_name": recipient.full_name},
        request,
    )
    db.commit()

    return {
        "id": recipient.id,
        "full_name": recipient.full_name,
        "email_address": recipient.email_address,
        "role_id": recipient.role_id,
        "role_name": role.name if role else "",
        "custom_title": recipient.custom_title,
        "media_outlets": recipient.media_outlets,
        "country_code": recipient.country_code,
        "country_name": country.name if country else "",
        "approval_status": recipient.approval_status,
        "is_active": recipient.is_active,
    }


@router.delete("/recipients/{recipient_id}")
async def delete_recipient(
    recipient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    recipient = db.query(PoliticalRecipient).filter(PoliticalRecipient.id == recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    db.delete(recipient)
    log_action(
        db,
        admin,
        "DELETE_RECIPIENT",
        "political_recipient",
        recipient_id,
        {"full_name": recipient.full_name},
        request,
    )
    db.commit()
    return {"status": "deleted"}


@router.post("/recipients/{recipient_id}/approve")
async def approve_recipient(
    recipient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    recipient = db.query(PoliticalRecipient).filter(PoliticalRecipient.id == recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    recipient.approval_status = "approved"
    recipient.approved_by_admin_id = admin.id
    db.add(recipient)
    log_action(
        db,
        admin,
        "APPROVE_RECIPIENT",
        "political_recipient",
        recipient_id,
        None,
        request,
    )
    db.commit()
    return {"status": "approved"}


@router.post("/recipients/{recipient_id}/reject")
async def reject_recipient(
    recipient_id: int,
    payload: ApprovalRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    recipient = db.query(PoliticalRecipient).filter(PoliticalRecipient.id == recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    recipient.approval_status = "rejected"
    recipient.approved_by_admin_id = admin.id
    db.add(recipient)
    log_action(
        db,
        admin,
        "REJECT_RECIPIENT",
        "political_recipient",
        recipient_id,
        {"reason": payload.reason},
        request,
    )
    db.commit()
    return {"status": "rejected"}


@router.get("/topics", response_model=list[AdvocacyTopicAdminOut])
async def list_topics(
    approval_status: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    query = db.query(AdvocacyTopic)
    if approval_status:
        query = query.filter(AdvocacyTopic.approval_status == approval_status)
    topics = query.order_by(AdvocacyTopic.display_title).all()
    
    # Get all countries for name lookup
    countries = {c.code: c.name for c in db.query(Country).all()}
    
    return [
        {
            "id": t.id,
            "slug": t.slug,
            "display_title": t.display_title,
            "description": t.description,
            "country_codes": t.country_codes or [],
            "country_names": [countries.get(code, code) for code in (t.country_codes or [])],
            "recipient_ids": t.recipient_ids or [],
            "approval_status": t.approval_status,
            "is_active": t.is_active,
        }
        for t in topics
    ]


@router.post("/topics", response_model=AdvocacyTopicAdminOut)
async def create_topic(
    payload: AdvocacyTopicCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    try:
        existing = db.query(AdvocacyTopic).filter(AdvocacyTopic.slug == payload.slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="Slug already exists")

        approval_status = "approved"

        topic = AdvocacyTopic(
            slug=payload.slug,
            display_title=payload.display_title,
            description=payload.description,
            country_codes=payload.country_codes,  # Array of country codes
            recipient_ids=payload.recipient_ids if hasattr(payload, 'recipient_ids') else [],
            approval_status=approval_status,
            created_by_admin_id=admin.id,
            approved_by_admin_id=admin.id if approval_status == "approved" else None,
        )
        db.add(topic)
        db.commit()
        db.refresh(topic)

        log_action(
            db,
            admin,
            "CREATE_TOPIC",
            "advocacy_topic",
            topic.id,
            {"slug": topic.slug},
            request,
        )
        db.commit()

        # Get country names
        countries = {c.code: c.name for c in db.query(Country).all()}

        return {
            "id": topic.id,
            "slug": topic.slug,
            "display_title": topic.display_title,
            "description": topic.description,
            "country_codes": topic.country_codes or [],
            "country_names": [countries.get(code, code) for code in (topic.country_codes or [])],
            "recipient_ids": topic.recipient_ids or [],
            "approval_status": topic.approval_status,
            "is_active": topic.is_active,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating topic: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create topic: {str(e)}")


@router.put("/topics/{topic_id}", response_model=AdvocacyTopicAdminOut)
async def update_topic(
    topic_id: int,
    payload: AdvocacyTopicUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    topic = db.query(AdvocacyTopic).filter(AdvocacyTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if payload.slug is not None:
        existing_slug = db.query(AdvocacyTopic).filter(
            AdvocacyTopic.slug == payload.slug,
            AdvocacyTopic.id != topic.id
        ).first()
        if existing_slug:
            raise HTTPException(status_code=400, detail="Slug already exists")
        topic.slug = payload.slug
    if payload.display_title is not None:
        topic.display_title = payload.display_title
    if payload.description is not None:
        topic.description = payload.description
    if payload.country_codes is not None:
        topic.country_codes = payload.country_codes
    if payload.is_active is not None:
        topic.is_active = payload.is_active
    if hasattr(payload, 'recipient_ids') and payload.recipient_ids is not None:
        topic.recipient_ids = payload.recipient_ids

    # Topics are always auto-approved (no approval workflow)
    topic.approval_status = "approved"
    topic.approved_by_admin_id = admin.id

    db.add(topic)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Slug already exists")
    db.refresh(topic)

    log_action(
        db,
        admin,
        "UPDATE_TOPIC",
        "advocacy_topic",
        topic.id,
        {"slug": topic.slug},
        request,
    )
    db.commit()

    # Get country names
    countries = {c.code: c.name for c in db.query(Country).all()}

    return {
        "id": topic.id,
        "slug": topic.slug,
        "display_title": topic.display_title,
        "description": topic.description,
        "country_codes": topic.country_codes or [],
        "country_names": [countries.get(code, code) for code in (topic.country_codes or [])],
        "recipient_ids": topic.recipient_ids or [],
        "approval_status": topic.approval_status,
        "is_active": topic.is_active,
    }


@router.delete("/topics/{topic_id}")
async def delete_topic(
    topic_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    topic = db.query(AdvocacyTopic).filter(AdvocacyTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    db.delete(topic)
    log_action(
        db,
        admin,
        "DELETE_TOPIC",
        "advocacy_topic",
        topic_id,
        {"slug": topic.slug},
        request,
    )
    db.commit()
    return {"status": "deleted"}


@router.post("/topics/{topic_id}/approve")
async def approve_topic(
    topic_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    topic = db.query(AdvocacyTopic).filter(AdvocacyTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    topic.approval_status = "approved"
    topic.approved_by_admin_id = admin.id
    db.add(topic)
    log_action(
        db,
        admin,
        "APPROVE_TOPIC",
        "advocacy_topic",
        topic_id,
        None,
        request,
    )
    db.commit()
    return {"status": "approved"}


@router.post("/topics/{topic_id}/reject")
async def reject_topic(
    topic_id: int,
    payload: ApprovalRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    topic = db.query(AdvocacyTopic).filter(AdvocacyTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    topic.approval_status = "rejected"
    topic.approved_by_admin_id = admin.id
    db.add(topic)
    log_action(
        db,
        admin,
        "REJECT_TOPIC",
        "advocacy_topic",
        topic_id,
        {"reason": payload.reason},
        request,
    )
    db.commit()
    return {"status": "rejected"}


@router.get("/campaigns", response_model=list[CampaignOut])
async def list_campaigns(
    approval_status: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    query = db.query(Campaign)
    if approval_status:
        query = query.filter(Campaign.approval_status == approval_status)
    campaigns = query.order_by(Campaign.display_order).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "slug": c.slug,
            "description": c.description,
            "icon": c.icon,
            "recipient_ids": c.recipient_ids,
            "is_hot": c.is_hot,
            "is_active": c.is_active,
            "display_order": c.display_order,
            "approval_status": c.approval_status,
        }
        for c in campaigns
    ]


@router.get("/campaigns/pending", response_model=list[CampaignOut])
async def list_pending_campaigns(
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    campaigns = db.query(Campaign).filter(Campaign.approval_status == "pending").all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "slug": c.slug,
            "description": c.description,
            "icon": c.icon,
            "recipient_ids": c.recipient_ids,
            "is_hot": c.is_hot,
            "is_active": c.is_active,
            "display_order": c.display_order,
            "approval_status": c.approval_status,
        }
        for c in campaigns
    ]


@router.post("/campaigns", response_model=CampaignOut)
async def create_campaign(
    payload: CampaignCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    existing = db.query(Campaign).filter(Campaign.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")

    if not payload.recipient_ids or len(payload.recipient_ids) == 0:
        raise HTTPException(status_code=400, detail="At least one recipient is required")

    approval_status = "approved" if admin.role == "super_admin" else "pending"

    campaign = Campaign(
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        icon=payload.icon or "🔥",
        recipient_ids=payload.recipient_ids,
        is_hot=payload.is_hot,
        is_active=payload.is_active,
        display_order=payload.display_order,
        approval_status=approval_status,
        created_by_admin_id=admin.id,
        approved_by_admin_id=admin.id if approval_status == "approved" else None,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    log_action(db, admin, "CREATE_CAMPAIGN", "campaign", campaign.id, {"title": campaign.title}, request)
    db.commit()

    return {
        "id": campaign.id,
        "title": campaign.title,
        "slug": campaign.slug,
        "description": campaign.description,
        "icon": campaign.icon,
        "recipient_ids": campaign.recipient_ids,
        "is_hot": campaign.is_hot,
        "is_active": campaign.is_active,
        "display_order": campaign.display_order,
        "approval_status": campaign.approval_status,
    }


@router.put("/campaigns/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if payload.title is not None:
        campaign.title = payload.title
    if payload.slug is not None:
        campaign.slug = payload.slug
    if payload.description is not None:
        campaign.description = payload.description
    if payload.icon is not None:
        campaign.icon = payload.icon
    if payload.recipient_ids is not None:
        campaign.recipient_ids = payload.recipient_ids
    if payload.is_hot is not None:
        campaign.is_hot = payload.is_hot
    if payload.is_active is not None:
        campaign.is_active = payload.is_active
    if payload.display_order is not None:
        campaign.display_order = payload.display_order

    if admin.role != "super_admin":
        campaign.approval_status = "pending"
        campaign.approved_by_admin_id = None

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    log_action(db, admin, "UPDATE_CAMPAIGN", "campaign", campaign.id, {"title": campaign.title}, request)
    db.commit()

    return {
        "id": campaign.id,
        "title": campaign.title,
        "slug": campaign.slug,
        "description": campaign.description,
        "icon": campaign.icon,
        "recipient_ids": campaign.recipient_ids,
        "is_hot": campaign.is_hot,
        "is_active": campaign.is_active,
        "display_order": campaign.display_order,
        "approval_status": campaign.approval_status,
    }


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    db.delete(campaign)
    log_action(db, admin, "DELETE_CAMPAIGN", "campaign", campaign_id, {"title": campaign.title}, request)
    db.commit()
    return {"status": "deleted"}


@router.post("/campaigns/{campaign_id}/approve")
async def approve_campaign(
    campaign_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.approval_status = "approved"
    campaign.approved_by_admin_id = admin.id
    db.add(campaign)
    log_action(db, admin, "APPROVE_CAMPAIGN", "campaign", campaign_id, None, request)
    db.commit()
    return {"status": "approved"}


@router.post("/campaigns/{campaign_id}/reject")
async def reject_campaign(
    campaign_id: int,
    payload: ApprovalRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.approval_status = "rejected"
    campaign.approved_by_admin_id = admin.id
    db.add(campaign)
    log_action(db, admin, "REJECT_CAMPAIGN", "campaign", campaign_id, {"reason": payload.reason}, request)
    db.commit()
    return {"status": "rejected"}


# ============================================
# ANALYTICS ENDPOINTS
# ============================================

@router.get("/analytics/overview")
async def get_analytics_overview(
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin)
):
    """Get overall platform analytics"""
    from models import EmailGenerationLog
    from sqlalchemy import func, distinct
    
    email_units = func.coalesce(func.array_length(EmailGenerationLog.recipient_ids, 1), 0)
    total_emails = db.query(func.coalesce(func.sum(email_units), 0)).scalar() or 0
    successful_emails = db.query(func.coalesce(func.sum(email_units), 0)).filter(
        EmailGenerationLog.generation_successful == True
    ).scalar() or 0
    total_requests = db.query(func.count(EmailGenerationLog.id)).scalar() or 0
    
    # Count unique users by IP address
    unique_users = db.query(func.count(distinct(EmailGenerationLog.sender_ip_address))).filter(
        EmailGenerationLog.sender_ip_address.isnot(None)
    ).scalar() or 0
    
    # Count active campaigns (campaigns with at least one email sent)
    active_campaigns = db.query(func.count(distinct(EmailGenerationLog.campaign_id))).filter(
        EmailGenerationLog.campaign_id.isnot(None)
    ).scalar() or 0
    
    total_recipients = db.query(func.count(PoliticalRecipient.id)).filter(
        PoliticalRecipient.approval_status == "approved"
    ).scalar() or 0
    
    total_topics = db.query(func.count(AdvocacyTopic.id)).filter(
        AdvocacyTopic.approval_status == "approved"
    ).scalar() or 0
    
    total_countries = db.query(func.count(Country.code)).filter(
        Country.is_active == True
    ).scalar() or 0
    
    return {
        "total_emails_generated": total_emails,
        "total_emails": total_emails,
        "total_requests": total_requests,
        "successful_emails": successful_emails,
        "failed_emails": total_emails - successful_emails,
        "total_recipients": total_recipients,
        "total_topics": total_topics,
        "total_countries": total_countries,
        "unique_users": unique_users,
        "active_campaigns": active_campaigns,
        "success_rate": f"{round((successful_emails / total_emails * 100) if total_emails > 0 else 0, 1)}%"
    }


@router.get("/analytics/top-countries")
async def get_top_countries(
    limit: int = 10,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin)
):
    """Get most popular countries by email generation"""
    from models import EmailGenerationLog
    from sqlalchemy import func, desc
    
    results = db.query(
        EmailGenerationLog.selected_recipient_country,
        func.coalesce(func.sum(func.array_length(EmailGenerationLog.recipient_ids, 1)), 0).label('count')
    ).group_by(
        EmailGenerationLog.selected_recipient_country
    ).order_by(desc('count')).limit(limit).all()
    
    return {
        "top_countries": [
            {"country": r[0], "email_count": r[1]}
            for r in results
        ]
    }


@router.get("/analytics/top-topics")
async def get_top_topics(
    limit: int = 10,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin)
):
    """Get most used topics"""
    from models import EmailGenerationLog
    from sqlalchemy import func, desc
    
    # Get all topic IDs from logs
    logs = db.query(
        EmailGenerationLog.topic_ids,
        func.coalesce(func.array_length(EmailGenerationLog.recipient_ids, 1), 0).label("recipient_count")
    ).filter(
        EmailGenerationLog.topic_ids.isnot(None)
    ).all()
    
    topic_counts = {}
    for log in logs:
        topic_ids = log.topic_ids or []
        recipient_count = log.recipient_count or 0
        for topic_id in topic_ids:
            topic_counts[topic_id] = topic_counts.get(topic_id, 0) + recipient_count
    
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    results = []
    for topic_id, count in sorted_topics:
        topic = db.query(AdvocacyTopic).filter(AdvocacyTopic.id == topic_id).first()
        if topic:
            results.append({
                "topic_id": topic_id,
                "topic_title": topic.display_title,
                "usage_count": count
            })
    
    return {"top_topics": results}


@router.get("/analytics/top-recipients")
async def get_top_recipients(
    limit: int = 10,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin)
):
    """Get top recipients by email count (per-recipient counting)"""
    from models import EmailGenerationLog
    from sqlalchemy import func, desc

    recipient_id = func.unnest(EmailGenerationLog.recipient_ids).label("recipient_id")
    recipient_subq = db.query(recipient_id).select_from(EmailGenerationLog).subquery()

    results = db.query(
        PoliticalRecipient.id,
        PoliticalRecipient.full_name,
        PoliticalRecipient.email_address,
        Country.name.label("country_name"),
        func.count().label("email_count")
    ).join(
        recipient_subq, PoliticalRecipient.id == recipient_subq.c.recipient_id
    ).join(
        Country, PoliticalRecipient.country_code == Country.code
    ).group_by(
        PoliticalRecipient.id,
        PoliticalRecipient.full_name,
        PoliticalRecipient.email_address,
        Country.name
    ).order_by(desc("email_count")).limit(limit).all()

    return {
        "top_recipients": [
            {
                "recipient_id": r[0],
                "full_name": r[1],
                "email_address": r[2],
                "country_name": r[3],
                "email_count": r[4]
            }
            for r in results
        ]
    }


@router.get("/analytics/top-recipient-countries")
async def get_top_recipient_countries(
    limit: int = 10,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin)
):
    """Top recipient countries (per-recipient counting)"""
    from models import EmailGenerationLog
    from sqlalchemy import func, desc

    recipient_id = func.unnest(EmailGenerationLog.recipient_ids).label("recipient_id")
    recipient_subq = db.query(recipient_id).select_from(EmailGenerationLog).subquery()

    results = db.query(
        Country.name.label("country_name"),
        func.count().label("email_count")
    ).join(
        PoliticalRecipient, PoliticalRecipient.country_code == Country.code
    ).join(
        recipient_subq, PoliticalRecipient.id == recipient_subq.c.recipient_id
    ).group_by(
        Country.name
    ).order_by(desc("email_count")).limit(limit).all()

    return {
        "top_recipient_countries": [
            {"country": r[0], "email_count": r[1]}
            for r in results
        ]
    }


@router.get("/analytics/emails-over-time")
async def get_emails_over_time(
    granularity: str = "day",
    limit: int = 60,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin)
):
    """Emails over time (per-recipient counting). granularity=day|week|month"""
    from models import EmailGenerationLog
    from sqlalchemy import func, text, desc

    if granularity not in ["day", "week", "month"]:
        raise HTTPException(status_code=400, detail="Invalid granularity")

    time_bucket = func.date_trunc(granularity, EmailGenerationLog.created_at).label("bucket")
    email_units = func.coalesce(func.array_length(EmailGenerationLog.recipient_ids, 1), 0)

    results = db.query(
        time_bucket,
        func.coalesce(func.sum(email_units), 0).label("email_count")
    ).group_by(
        time_bucket
    ).order_by(desc(time_bucket)).limit(limit).all()

    # Return in chronological order
    results = list(reversed(results))
    return {
        "granularity": granularity,
        "series": [{"date": r[0].date().isoformat() if r[0] else None, "email_count": r[1]} for r in results]
    }


@router.get("/analytics/recent-activity")
async def get_recent_activity(
    limit: int = 20,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin)
):
    """Get recent email generation activity"""
    from models import EmailGenerationLog
    
    logs = db.query(EmailGenerationLog).order_by(
        EmailGenerationLog.created_at.desc()
    ).limit(limit).all()
    
    return {
        "recent_activity": [
            {
                "id": log.id,
                "country": log.selected_recipient_country,
                "is_resident": log.is_country_resident,
                "citizenship_status": log.sender_citizenship_status,
                "success": log.generation_successful,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "error": log.error_message
            }
            for log in logs
        ]
    }

# ==================== CAMPAIGN MANAGEMENT ====================

@router.get("/campaigns")
async def list_campaigns(
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin)
):
    """Get all campaigns for admin management"""
    from models import Campaign, EmailGenerationLog
    from sqlalchemy import func
    
    campaigns = db.query(Campaign).order_by(
        Campaign.display_order, Campaign.created_at.desc()
    ).all()
    
    result = []
    for campaign in campaigns:
        # Count emails sent for this campaign
        email_count = db.query(func.count(EmailGenerationLog.id)).filter(
            EmailGenerationLog.campaign_id == campaign.id
        ).scalar() or 0
        
        country = db.query(Country).filter(Country.code == campaign.country_code).first()
        from data.top_countries import get_country_flag
        
        result.append({
            "id": campaign.id,
            "title": campaign.title,
            "description": campaign.description,
            "slug": campaign.slug,
            "icon": campaign.icon or "🔥",
            "country": {
                "code": campaign.country_code,
                "name": country.name if country else "",
                "flag": get_country_flag(campaign.country_code)
            },
            "recipient_ids": campaign.recipient_ids,
            "topic_ids": campaign.topic_ids,
            "is_hot": campaign.is_hot,
            "is_active": campaign.is_active,
            "display_order": campaign.display_order,
            "email_count": email_count,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None
        })
    
    return {"campaigns": result}


@router.post("/campaigns")
async def create_campaign(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    """Create a new campaign"""
    from models import Campaign
    
    # Verify country exists
    country = db.query(Country).filter(Country.code == payload["country_code"].upper()).first()
    if not country:
        raise HTTPException(status_code=400, detail="Invalid country code")
    
    # Verify recipients exist
    from models import PoliticalRecipient
    recipients = db.query(PoliticalRecipient).filter(
        PoliticalRecipient.id.in_(payload["recipient_ids"])
    ).all()
    if len(recipients) != len(payload["recipient_ids"]):
        raise HTTPException(status_code=400, detail="One or more recipients are invalid")
    
    # Verify topics exist
    topics = db.query(AdvocacyTopic).filter(
        AdvocacyTopic.id.in_(payload["topic_ids"])
    ).all()
    if len(topics) != len(payload["topic_ids"]):
        raise HTTPException(status_code=400, detail="One or more topics are invalid")
    
    campaign = Campaign(
        title=payload["title"],
        description=payload.get("description", ""),
        slug=payload["slug"],
        icon=payload.get("icon", "🔥"),
        country_code=payload["country_code"].upper(),
        recipient_ids=payload["recipient_ids"],
        topic_ids=payload["topic_ids"],
        is_hot=payload.get("is_hot", False),
        is_active=payload.get("is_active", True),
        display_order=payload.get("display_order", 0),
        created_by_admin_id=admin.id
    )
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    log_action(db, admin, "create", "campaign", campaign.id, {
        "title": campaign.title,
        "country": campaign.country_code
    }, request)
    db.commit()
    
    from data.top_countries import get_country_flag
    return {
        "id": campaign.id,
        "title": campaign.title,
        "description": campaign.description,
        "slug": campaign.slug,
        "icon": campaign.icon,
        "country": {
            "code": campaign.country_code,
            "name": country.name,
            "flag": get_country_flag(campaign.country_code)
        },
        "recipient_ids": campaign.recipient_ids,
        "topic_ids": campaign.topic_ids,
        "is_hot": campaign.is_hot,
        "is_active": campaign.is_active,
        "display_order": campaign.display_order
    }


@router.put("/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: int,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    """Update an existing campaign"""
    from models import Campaign
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Update fields
    if "title" in payload:
        campaign.title = payload["title"]
    if "description" in payload:
        campaign.description = payload["description"]
    if "slug" in payload:
        campaign.slug = payload["slug"]
    if "icon" in payload:
        campaign.icon = payload["icon"]
    if "country_code" in payload:
        country = db.query(Country).filter(Country.code == payload["country_code"].upper()).first()
        if not country:
            raise HTTPException(status_code=400, detail="Invalid country code")
        campaign.country_code = payload["country_code"].upper()
    if "recipient_ids" in payload:
        from models import PoliticalRecipient
        recipients = db.query(PoliticalRecipient).filter(
            PoliticalRecipient.id.in_(payload["recipient_ids"])
        ).all()
        if len(recipients) != len(payload["recipient_ids"]):
            raise HTTPException(status_code=400, detail="One or more recipients are invalid")
        campaign.recipient_ids = payload["recipient_ids"]
    if "topic_ids" in payload:
        topics = db.query(AdvocacyTopic).filter(
            AdvocacyTopic.id.in_(payload["topic_ids"])
        ).all()
        if len(topics) != len(payload["topic_ids"]):
            raise HTTPException(status_code=400, detail="One or more topics are invalid")
        campaign.topic_ids = payload["topic_ids"]
    if "is_hot" in payload:
        campaign.is_hot = payload["is_hot"]
    if "is_active" in payload:
        campaign.is_active = payload["is_active"]
    if "display_order" in payload:
        campaign.display_order = payload["display_order"]
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    log_action(db, admin, "update", "campaign", campaign.id, {
        "updated_fields": list(payload.keys())
    }, request)
    db.commit()
    
    country = db.query(Country).filter(Country.code == campaign.country_code).first()
    from data.top_countries import get_country_flag
    
    return {
        "id": campaign.id,
        "title": campaign.title,
        "description": campaign.description,
        "slug": campaign.slug,
        "icon": campaign.icon,
        "country": {
            "code": campaign.country_code,
            "name": country.name if country else "",
            "flag": get_country_flag(campaign.country_code)
        },
        "recipient_ids": campaign.recipient_ids,
        "topic_ids": campaign.topic_ids,
        "is_hot": campaign.is_hot,
        "is_active": campaign.is_active,
        "display_order": campaign.display_order
    }


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    """Delete a campaign"""
    from models import Campaign
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    log_action(db, admin, "delete", "campaign", campaign.id, {
        "title": campaign.title
    }, request)
    
    db.delete(campaign)
    db.commit()
    
    return {"message": "Campaign deleted successfully"}


@router.get("/analytics/campaigns")
async def get_campaign_analytics(
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin)
):
    """Get analytics for all campaigns"""
    from models import Campaign, EmailGenerationLog
    from sqlalchemy import func
    
    campaigns = db.query(Campaign).all()
    
    results = []
    for campaign in campaigns:
        # Count total emails sent
        email_count = db.query(func.coalesce(func.sum(func.array_length(EmailGenerationLog.recipient_ids, 1)), 0)).filter(
            EmailGenerationLog.campaign_id == campaign.id
        ).scalar() or 0
        
        # Get country distribution for this campaign
        country_distribution = db.query(
            EmailGenerationLog.selected_recipient_country,
            func.coalesce(func.sum(func.array_length(EmailGenerationLog.recipient_ids, 1)), 0).label('count')
        ).filter(
            EmailGenerationLog.campaign_id == campaign.id
        ).group_by(EmailGenerationLog.selected_recipient_country).all()
        
        results.append({
            "campaign_id": campaign.id,
            "campaign_title": campaign.title,
            "email_count": email_count,
            "country_distribution": [
                {"country": country, "count": count}
                for country, count in country_distribution
            ]
        })
    
    return {"campaign_analytics": results}


@router.get("/analytics/user-countries")
async def get_user_countries(
    limit: int = 20,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin)
):
    """Get unique users by sender country (based on IP)"""
    from models import EmailGenerationLog
    from sqlalchemy import func, desc

    results = db.query(
        EmailGenerationLog.sender_country_name,
        EmailGenerationLog.sender_country_code,
        func.count(func.distinct(EmailGenerationLog.sender_ip_address)).label("user_count"),
    ).filter(
        EmailGenerationLog.sender_country_name.isnot(None)
    ).group_by(
        EmailGenerationLog.sender_country_name,
        EmailGenerationLog.sender_country_code,
    ).order_by(desc("user_count")).limit(limit).all()

    return {
        "user_countries": [
            {
                "country": r[0] or r[1] or "Unknown",
                "country_code": r[1],
                "user_count": r[2]
            }
            for r in results
        ]
    }


# ===============================
# TICKER MESSAGES ROUTES
# ===============================

@router.get("/ticker-messages")
async def list_ticker_messages(
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    """Get all ticker messages"""
    messages = db.query(TickerMessage).order_by(TickerMessage.display_order, TickerMessage.id).all()
    return {
        "ticker_messages": [
            {
                "id": m.id,
                "message_text": m.message_text,
                "is_active": m.is_active,
                "display_order": m.display_order,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            }
            for m in messages
        ]
    }


@router.post("/ticker-messages")
async def create_ticker_message(
    payload: TickerMessageCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    """Create a new ticker message"""
    new_message = TickerMessage(
        message_text=payload.message_text,
        is_active=payload.is_active if payload.is_active is not None else True,
        display_order=payload.display_order or 0,
        created_by_admin_id=admin.id,
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    log_action(db, admin, "CREATE_TICKER_MESSAGE", "ticker_message", new_message.id, {"message_text": new_message.message_text}, request)
    db.commit()

    return {
        "id": new_message.id,
        "message_text": new_message.message_text,
        "is_active": new_message.is_active,
        "display_order": new_message.display_order,
        "created_at": new_message.created_at.isoformat() if new_message.created_at else None,
    }


@router.put("/ticker-messages/{message_id}")
async def update_ticker_message(
    message_id: int,
    payload: TickerMessageUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    """Update a ticker message"""
    message = db.query(TickerMessage).filter(TickerMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Ticker message not found")

    if payload.message_text is not None:
        message.message_text = payload.message_text
    if payload.is_active is not None:
        message.is_active = payload.is_active
    if payload.display_order is not None:
        message.display_order = payload.display_order

    db.commit()
    db.refresh(message)

    log_action(db, admin, "UPDATE_TICKER_MESSAGE", "ticker_message", message.id, {"message_text": message.message_text}, request)
    db.commit()

    return {
        "id": message.id,
        "message_text": message.message_text,
        "is_active": message.is_active,
        "display_order": message.display_order,
        "updated_at": message.updated_at.isoformat() if message.updated_at else None,
    }


@router.delete("/ticker-messages/{message_id}")
async def delete_ticker_message(
    message_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin),
):
    """Delete a ticker message"""
    message = db.query(TickerMessage).filter(TickerMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Ticker message not found")

    log_action(db, admin, "DELETE_TICKER_MESSAGE", "ticker_message", message.id, {"message_text": message.message_text}, request)
    
    db.delete(message)
    db.commit()

    return {"success": True, "message": "Ticker message deleted"}


# ===============================
# BULK IMPORT RECIPIENTS ROUTE
# ===============================

@router.post("/recipients/bulk-import")
async def bulk_import_recipients(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin),
):
    """
    Bulk import political recipients.
    Payload format:
    {
        "recipients": [
            {
                "full_name": "Name",
                "email_address": "email@example.com",
                "role": "MP",
                "country_code": "GB",
                "custom_title": "Optional title",
                "is_active": true,
                "approval_status": "approved"
            },
            ...
        ],
        "skip_duplicates": true  // Optional, default true
    }
    """
    recipients_data = payload.get("recipients", [])
    skip_duplicates = payload.get("skip_duplicates", True)
    
    if not recipients_data:
        raise HTTPException(status_code=400, detail="No recipients provided")
    
    # Get or create roles
    role_cache = {}
    for role in db.query(RecipientRole).all():
        role_cache[role.name.lower()] = role.id
    
    created_count = 0
    skipped_count = 0
    errors = []
    
    for idx, rec in enumerate(recipients_data):
        try:
            email = rec.get("email_address", "").strip()
            full_name = rec.get("full_name", "").strip()
            role_name = rec.get("role", "").strip()
            country_code = rec.get("country_code", "GB").strip().upper()
            custom_title = rec.get("custom_title", "").strip() or None
            is_active = rec.get("is_active", True)
            approval_status = rec.get("approval_status", "approved")
            
            # Skip if no valid email
            if not email or email == "0" or "@" not in email:
                skipped_count += 1
                continue
            
            # Skip if no name
            if not full_name:
                skipped_count += 1
                continue
            
            # Check for duplicate by email
            if skip_duplicates:
                existing = db.query(PoliticalRecipient).filter(
                    PoliticalRecipient.email_address == email
                ).first()
                if existing:
                    skipped_count += 1
                    continue
            
            # Get or create role
            role_id = None
            if role_name:
                role_key = role_name.lower()
                if role_key in role_cache:
                    role_id = role_cache[role_key]
                else:
                    # Create new role
                    new_role = RecipientRole(name=role_name, is_active=True)
                    db.add(new_role)
                    db.flush()
                    role_cache[role_key] = new_role.id
                    role_id = new_role.id
            
            # Create recipient
            new_recipient = PoliticalRecipient(
                full_name=full_name,
                email_address=email,
                role_id=role_id,
                custom_title=custom_title,
                country_code=country_code,
                is_active=is_active,
                approval_status=approval_status,
            )
            db.add(new_recipient)
            created_count += 1
            
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
    
    db.commit()
    
    log_action(db, admin, "BULK_IMPORT_RECIPIENTS", "political_recipient", None, 
               {"created": created_count, "skipped": skipped_count, "errors": len(errors)}, request)
    db.commit()
    
    return {
        "success": True,
        "created": created_count,
        "skipped": skipped_count,
        "errors": errors[:20] if errors else [],  # Return first 20 errors
        "total_errors": len(errors)
    }


@router.get("/analytics")
async def get_analytics_bundle(
    db: Session = Depends(get_db),
    admin: Administrator = Depends(get_current_admin)
):
    """Bundle analytics for charts"""
    from models import EmailGenerationLog, Campaign
    from sqlalchemy import func, desc

    top_countries = db.query(
        EmailGenerationLog.selected_recipient_country,
        func.coalesce(func.sum(func.array_length(EmailGenerationLog.recipient_ids, 1)), 0).label('count')
    ).group_by(
        EmailGenerationLog.selected_recipient_country
    ).order_by(desc('count')).limit(10).all()

    campaigns = db.query(Campaign).all()
    campaign_analytics = []
    for campaign in campaigns:
        email_count = db.query(func.coalesce(func.sum(func.array_length(EmailGenerationLog.recipient_ids, 1)), 0)).filter(
            EmailGenerationLog.campaign_id == campaign.id
        ).scalar() or 0
        campaign_analytics.append({
            "campaign_id": campaign.id,
            "campaign_title": campaign.title,
            "email_count": email_count
        })

    user_countries = db.query(
        EmailGenerationLog.sender_country_name,
        EmailGenerationLog.sender_country_code,
        func.count(func.distinct(EmailGenerationLog.sender_ip_address)).label("user_count"),
    ).filter(
        EmailGenerationLog.sender_country_name.isnot(None)
    ).group_by(
        EmailGenerationLog.sender_country_name,
        EmailGenerationLog.sender_country_code,
    ).order_by(desc("user_count")).limit(10).all()

    # Top topics (per-recipient counting)
    logs = db.query(
        EmailGenerationLog.topic_ids,
        func.coalesce(func.array_length(EmailGenerationLog.recipient_ids, 1), 0).label("recipient_count")
    ).filter(EmailGenerationLog.topic_ids.isnot(None)).all()
    topic_counts = {}
    for log in logs:
        for topic_id in (log.topic_ids or []):
            topic_counts[topic_id] = topic_counts.get(topic_id, 0) + (log.recipient_count or 0)
    top_topic_ids = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_topics = []
    for topic_id, count in top_topic_ids:
        topic = db.query(AdvocacyTopic).filter(AdvocacyTopic.id == topic_id).first()
        if topic:
            top_topics.append({"topic_id": topic_id, "topic_title": topic.display_title, "usage_count": count})

    # Top recipients (per-recipient counting)
    recipient_id = func.unnest(EmailGenerationLog.recipient_ids).label("recipient_id")
    recipient_subq = db.query(recipient_id).select_from(EmailGenerationLog).subquery()

    top_recipients = db.query(
        PoliticalRecipient.id,
        PoliticalRecipient.full_name,
        PoliticalRecipient.email_address,
        Country.name.label("country_name"),
        func.count().label("email_count")
    ).join(
        recipient_subq, PoliticalRecipient.id == recipient_subq.c.recipient_id
    ).join(
        Country, PoliticalRecipient.country_code == Country.code
    ).group_by(
        PoliticalRecipient.id,
        PoliticalRecipient.full_name,
        PoliticalRecipient.email_address,
        Country.name
    ).order_by(desc("email_count")).limit(10).all()

    top_recipient_countries = db.query(
        Country.name.label("country_name"),
        func.count().label("email_count")
    ).join(
        PoliticalRecipient, PoliticalRecipient.country_code == Country.code
    ).join(
        recipient_subq, PoliticalRecipient.id == recipient_subq.c.recipient_id
    ).group_by(
        Country.name
    ).order_by(desc("email_count")).limit(10).all()

    return {
        "top_countries": [{"country": r[0], "email_count": r[1]} for r in top_countries],
        "campaign_analytics": campaign_analytics,
        "user_countries": [
            {"country": r[0] or r[1] or "Unknown", "country_code": r[1], "user_count": r[2]}
            for r in user_countries
        ],
        "top_topics": top_topics,
        "top_recipients": [
            {"recipient_id": r[0], "full_name": r[1], "email_address": r[2], "country_name": r[3], "email_count": r[4]}
            for r in top_recipients
        ],
        "top_recipient_countries": [
            {"country": r[0], "email_count": r[1]}
            for r in top_recipient_countries
        ],
    }
