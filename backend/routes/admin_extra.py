# Additional admin endpoints to be added to admin.py

ADMIN_MANAGEMENT = """

# ==================== ADMIN MANAGEMENT ====================

@router.get("/admins")
async def list_admins(
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    \"\"\"List all administrators (super admin only)\"\"\"
    admins = db.query(Administrator).order_by(Administrator.created_at.desc()).all()
    
    return {
        "admins": [
            {
                "id": a.id,
                "email": a.email,
                "role": a.role,
                "is_active": a.is_active,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "last_login": a.last_login.isoformat() if a.last_login else None
            }
            for a in admins
        ]
    }


@router.post("/admins")
async def create_admin(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    \"\"\"Create a new administrator (super admin only)\"\"\"
    from services.auth import get_password_hash
    
    # Check if email already exists
    existing = db.query(Administrator).filter(Administrator.email == payload["email"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    new_admin = Administrator(
        email=payload["email"],
        password_hash=get_password_hash(payload["password"]),
        role=payload.get("role", "admin"),
        is_active=payload.get("is_active", True),
        created_by_admin_id=admin.id
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    log_action(db, admin, "create", "administrator", new_admin.id, {
        "email": new_admin.email,
        "role": new_admin.role
    }, request)
    db.commit()
    
    return {
        "id": new_admin.id,
        "email": new_admin.email,
        "role": new_admin.role,
        "is_active": new_admin.is_active
    }


@router.put("/admins/{admin_id}")
async def update_admin(
    admin_id: int,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    \"\"\"Update administrator (super admin only)\"\"\"
    from services.auth import get_password_hash
    
    target_admin = db.query(Administrator).filter(Administrator.id == admin_id).first()
    if not target_admin:
        raise HTTPException(status_code=404, detail="Administrator not found")
    
    if "email" in payload:
        # Check if new email is already taken
        existing = db.query(Administrator).filter(
            Administrator.email == payload["email"],
            Administrator.id != admin_id
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
    
    log_action(db, admin, "update", "administrator", admin_id, {
        "updated_fields": list(payload.keys())
    }, request)
    db.commit()
    
    return {
        "id": target_admin.id,
        "email": target_admin.email,
        "role": target_admin.role,
        "is_active": target_admin.is_active
    }


@router.delete("/admins/{admin_id}")
async def delete_admin(
    admin_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    \"\"\"Delete administrator (super admin only)\"\"\"
    if admin_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    target_admin = db.query(Administrator).filter(Administrator.id == admin_id).first()
    if not target_admin:
        raise HTTPException(status_code=404, detail="Administrator not found")
    
    log_action(db, admin, "delete", "administrator", admin_id, {
        "email": target_admin.email
    }, request)
    
    db.delete(target_admin)
    db.commit()
    
    return {"message": "Administrator deleted successfully"}


# ==================== COUNTRY MANAGEMENT ====================

@router.post("/countries")
async def add_country(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    \"\"\"Add a new country (super admin only)\"\"\"
    existing = db.query(Country).filter(Country.code == payload["code"].upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Country code already exists")
    
    country = Country(
        code=payload["code"].upper(),
        name=payload["name"],
        name_persian=payload.get("name_persian", ""),
        flag=payload.get("flag", ""),
        is_active=payload.get("is_active", True)
    )
    
    db.add(country)
    db.commit()
    db.refresh(country)
    
    log_action(db, admin, "create", "country", None, {
        "code": country.code,
        "name": country.name
    }, request)
    db.commit()
    
    return {
        "code": country.code,
        "name": country.name,
        "name_persian": country.name_persian,
        "flag": country.flag,
        "is_active": country.is_active
    }


@router.put("/countries/{country_code}")
async def update_country(
    country_code: str,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    \"\"\"Update country (super admin only)\"\"\"
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
    
    log_action(db, admin, "update", "country", None, {
        "code": country_code,
        "updated_fields": list(payload.keys())
    }, request)
    db.commit()
    
    return {
        "code": country.code,
        "name": country.name,
        "name_persian": country.name_persian,
        "flag": country.flag,
        "is_active": country.is_active
    }


@router.delete("/countries/{country_code}")
async def delete_country(
    country_code: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    \"\"\"Delete country (super admin only)\"\"\"
    country = db.query(Country).filter(Country.code == country_code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    # Check if country is used by recipients or campaigns
    recipient_count = db.query(PoliticalRecipient).filter(
        PoliticalRecipient.country_code == country_code.upper()
    ).count()
    
    if recipient_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete country with {recipient_count} recipients. Deactivate it instead."
        )
    
    log_action(db, admin, "delete", "country", None, {
        "code": country_code,
        "name": country.name
    }, request)
    
    db.delete(country)
    db.commit()
    
    return {"message": "Country deleted successfully"}


# ==================== CAMPAIGN APPROVAL ====================

@router.post("/campaigns/{campaign_id}/approve")
async def approve_campaign(
    campaign_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    \"\"\"Approve a campaign (super admin only)\"\"\"
    from models import Campaign
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign.approval_status = "approved"
    campaign.approved_by_admin_id = admin.id
    campaign.is_active = True
    
    db.add(campaign)
    db.commit()
    
    log_action(db, admin, "approve", "campaign", campaign_id, {
        "title": campaign.title
    }, request)
    db.commit()
    
    return {"message": "Campaign approved", "campaign_id": campaign_id}


@router.post("/campaigns/{campaign_id}/reject")
async def reject_campaign(
    campaign_id: int,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    \"\"\"Reject a campaign (super admin only)\"\"\"
    from models import Campaign
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign.approval_status = "rejected"
    campaign.is_active = False
    
    db.add(campaign)
    db.commit()
    
    log_action(db, admin, "reject", "campaign", campaign_id, {
        "title": campaign.title,
        "reason": payload.get("reason", "")
    }, request)
    db.commit()
    
    return {"message": "Campaign rejected", "campaign_id": campaign_id}


@router.get("/campaigns/pending")
async def list_pending_campaigns(
    db: Session = Depends(get_db),
    admin: Administrator = Depends(require_super_admin)
):
    \"\"\"List all pending campaigns for approval (super admin only)\"\"\"
    from models import Campaign
    
    campaigns = db.query(Campaign).filter(
        Campaign.approval_status == "pending"
    ).order_by(Campaign.created_at.desc()).all()
    
    result = []
    for campaign in campaigns:
        country = db.query(Country).filter(Country.code == campaign.country_code).first()
        from data.top_countries import get_country_flag
        
        result.append({
            "id": campaign.id,
            "title": campaign.title,
            "description": campaign.description,
            "slug": campaign.slug,
            "country": {
                "code": campaign.country_code,
                "name": country.name if country else "",
                "flag": get_country_flag(campaign.country_code)
            },
            "recipient_count": len(campaign.recipient_ids) if campaign.recipient_ids else 0,
            "topic_count": len(campaign.topic_ids) if campaign.topic_ids else 0,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None
        })
    
    return {"pending_campaigns": result}
"""
