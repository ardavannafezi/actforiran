from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Administrator
from schemas import AdminLoginRequest, AdminMeResponse, AdminTokenResponse
from services.auth import (
    create_access_token,
    get_current_admin,
    verify_password,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


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
