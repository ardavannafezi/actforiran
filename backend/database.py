import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext

from data.countries import COUNTRIES
from data.roles import DEFAULT_RECIPIENT_ROLES
from data.top_countries import TOP_COUNTRIES

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def _normalize_db_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

DATABASE_URL = _normalize_db_url(os.getenv("DATABASE_URL", "sqlite:///./actforiran.db"))

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
    from models import Administrator, Country, RecipientRole, PoliticalRecipient, AdvocacyTopic

    # Check if already seeded
    if db.query(Administrator).count() > 0:
        print("Database already seeded, skipping...")
        return

    print("🌱 Seeding initial data...")

    # Create super admin
    super_admin = Administrator(
        email="admin@actforiran.org",
        password_hash=get_password_hash("admin123"),
        role="super_admin"
    )
    db.add(super_admin)
    db.commit()
    db.refresh(super_admin)

    # Seed countries (top 60 influential countries)
    if db.query(Country).count() == 0:
        db.bulk_insert_mappings(
            Country,
            [{"code": c["code"], "name": c["name"], "is_active": True} for c in TOP_COUNTRIES],
        )

    # Seed roles
    if db.query(RecipientRole).count() == 0:
        db.bulk_insert_mappings(
            RecipientRole,
            [
                {"name": role, "is_active": True, "is_system_default": True, "created_by_admin_id": super_admin.id}
                for role in DEFAULT_RECIPIENT_ROLES
            ],
        )

    db.commit()
    
    # Get role IDs for recipients
    pm_role = db.query(RecipientRole).filter_by(name="Prime Minister").first()
    president_role = db.query(RecipientRole).filter_by(name="President").first()
    fm_role = db.query(RecipientRole).filter_by(name="Foreign Minister").first()
    sos_role = db.query(RecipientRole).filter_by(name="Secretary of State").first()
    chancellor_role = db.query(RecipientRole).filter_by(name="Chancellor").first()
    
    # Create sample recipients (all approved by super admin)
    recipients_data = [
        # United States
        {"full_name": "Joe Biden", "email_address": "president@whitehouse.gov", "role_id": president_role.id, "country_code": "USA"},
        {"full_name": "Antony Blinken", "email_address": "secretary@state.gov", "role_id": sos_role.id, "country_code": "USA"},
        
        # Canada  
        {"full_name": "Justin Trudeau", "email_address": "pm@pm.gc.ca", "role_id": pm_role.id, "country_code": "CAN"},
        {"full_name": "Mélanie Joly", "email_address": "melanie.joly@international.gc.ca", "role_id": fm_role.id, "country_code": "CAN"},
        
        # United Kingdom
        {"full_name": "Keir Starmer", "email_address": "keir.starmer@parliament.uk", "role_id": pm_role.id, "country_code": "GBR"},
        {"full_name": "David Lammy", "email_address": "david.lammy@fcdo.gov.uk", "role_id": fm_role.id, "country_code": "GBR"},
        
        # France
        {"full_name": "Emmanuel Macron", "email_address": "emmanuel.macron@elysee.fr", "role_id": president_role.id, "country_code": "FRA"},
        {"full_name": "Jean-Noël Barrot", "email_address": "jean-noel.barrot@diplomatie.gouv.fr", "role_id": fm_role.id, "country_code": "FRA"},
        
        # Germany
        {"full_name": "Olaf Scholz", "email_address": "olaf.scholz@bundeskanzler.de", "role_id": chancellor_role.id, "country_code": "DEU"},
        {"full_name": "Annalena Baerbock", "email_address": "annalena.baerbock@auswaertiges-amt.de", "role_id": fm_role.id, "country_code": "DEU"},
        
        # Australia
        {"full_name": "Anthony Albanese", "email_address": "anthony.albanese@pm.gov.au", "role_id": pm_role.id, "country_code": "AUS"},
        {"full_name": "Penny Wong", "email_address": "penny.wong@dfat.gov.au", "role_id": fm_role.id, "country_code": "AUS"}
    ]
    
    for recipient_data in recipients_data:
        recipient = PoliticalRecipient(
            **recipient_data,
            is_active=True,
            approval_status="approved",
            created_by_admin_id=super_admin.id,
            approved_by_admin_id=super_admin.id
        )
        db.add(recipient)
    
    # Create advocacy topics
    topics_data = [
        {
            "slug": "digital-blackout",
            "display_title": "Digital Blackout in Iran",
            "description": "Internet shutdowns and communication restrictions preventing Iranians from connecting with the world"
        },
        {
            "slug": "mass-executions", 
            "display_title": "Mass Executions of Protesters",
            "description": "Increased executions of protesters and political prisoners by the Iranian regime"
        },
        {
            "slug": "woman-life-freedom",
            "display_title": "Woman Life Freedom Movement", 
            "description": "Ongoing protests for women's rights, freedom, and human dignity in Iran"
        },
        {
            "slug": "protesters-killed",
            "display_title": "State Violence Against Protesters",
            "description": "Security forces killing peaceful protesters demanding their basic rights"
        },
        {
            "slug": "political-prisoners",
            "display_title": "Political Prisoners and Arbitrary Detention", 
            "description": "Thousands of political prisoners, journalists, and activists detained without fair trial"
        },
        {
            "slug": "torture-detention",
            "display_title": "Torture and Abuse in Detention",
            "description": "Systematic torture and abuse of detainees in Iranian prisons"
        },
        {
            "slug": "press-freedom",
            "display_title": "Press Freedom and Journalist Safety",
            "description": "Suppression of independent media and targeting of journalists covering protests"
        },
        {
            "slug": "international-sanctions",
            "display_title": "Need for International Sanctions",
            "description": "Call for stronger international sanctions against Iranian regime officials"
        }
    ]
    
    for topic_data in topics_data:
        topic = AdvocacyTopic(
            **topic_data,
            is_active=True,
            approval_status="approved",
            created_by_admin_id=super_admin.id,
            approved_by_admin_id=super_admin.id
        )
        db.add(topic)

    db.commit()
    
    print("✅ Database seeded successfully!")
    print(f"   Super Admin: admin@actforiran.org / admin123")
    print(f"   Countries: {len(TOP_COUNTRIES)} created")
    print(f"   Recipients: {len(recipients_data)} created") 
    print(f"   Topics: {len(topics_data)} created")

def init_db():
    from models import Base as ModelBase

    ModelBase.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()
