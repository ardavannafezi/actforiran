import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from data.countries import COUNTRIES
from data.roles import DEFAULT_RECIPIENT_ROLES


def _normalize_db_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL = _normalize_db_url(os.getenv("DATABASE_URL", "sqlite:///./local.db"))

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_defaults(db):
    from models import Country, RecipientRole

    if db.query(Country).count() == 0:
        db.bulk_insert_mappings(
            Country,
            [{"code": code, "name": name, "is_active": True} for code, name in COUNTRIES],
        )

    if db.query(RecipientRole).count() == 0:
        db.bulk_insert_mappings(
            RecipientRole,
            [
                {"name": role, "is_active": True, "is_system_default": True}
                for role in DEFAULT_RECIPIENT_ROLES
            ],
        )

    db.commit()


def init_db():
    from models import Base as ModelBase

    ModelBase.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()
