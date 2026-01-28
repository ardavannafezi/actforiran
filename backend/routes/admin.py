from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db
from models import (
    AdminActivityLog,
    AdvocacyTopic,
    Administrator,
    Country,
    PoliticalRecipient,
    RecipientRole,
)
from schemas import (
    AdminLoginRequest,
    AdminMeResponse,
    AdminTokenResponse,
    AdvocacyTopicAdminOut,
    AdvocacyTopicCreate,
    AdvocacyTopicUpdate,
    ApprovalRequest,
    PoliticalRecipientAdminOut,
    PoliticalRecipientCreate,
    PoliticalRecipientUpdate,
    RecipientRoleCreate,
    RecipientRoleOut,
)
from services.auth import (
    create_access_token,
    get_current_admin,
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
async def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Administrator).filter(Administrator.email == payload.email).first()
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

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

    approval_status = "approved" if admin.role == "super_admin" else "pending"

    recipient = PoliticalRecipient(
        full_name=payload.full_name,
        email_address=payload.email_address,
        role_id=payload.role_id,
        custom_title=payload.custom_title,
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
    if payload.is_active is not None:
        recipient.is_active = payload.is_active

    if admin.role != "super_admin":
        recipient.approval_status = "pending"
        recipient.approved_by_admin_id = None

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
    return [
        {
            "id": t.id,
            "slug": t.slug,
            "display_title": t.display_title,
            "description": t.description,
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
    existing = db.query(AdvocacyTopic).filter(AdvocacyTopic.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")

    approval_status = "approved" if admin.role == "super_admin" else "pending"

    topic = AdvocacyTopic(
        slug=payload.slug,
        display_title=payload.display_title,
        description=payload.description,
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

    return {
        "id": topic.id,
        "slug": topic.slug,
        "display_title": topic.display_title,
        "description": topic.description,
        "approval_status": topic.approval_status,
        "is_active": topic.is_active,
    }


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
        topic.slug = payload.slug
    if payload.display_title is not None:
        topic.display_title = payload.display_title
    if payload.description is not None:
        topic.description = payload.description
    if payload.is_active is not None:
        topic.is_active = payload.is_active

    if admin.role != "super_admin":
        topic.approval_status = "pending"
        topic.approved_by_admin_id = None

    db.add(topic)
    db.commit()
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

    return {
        "id": topic.id,
        "slug": topic.slug,
        "display_title": topic.display_title,
        "description": topic.description,
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
