import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
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

    print("🌱 Seeding initial data...")

    # Get admin credentials from environment or use defaults
    # Support both SUPER_ADMIN_* and INITIAL_ADMIN_* for backward compatibility
    super_admin_email = os.getenv("SUPER_ADMIN_EMAIL") or os.getenv("INITIAL_ADMIN_EMAIL", "admin@actforiran.org")
    super_admin_password = os.getenv("SUPER_ADMIN_PASSWORD") or os.getenv("INITIAL_ADMIN_PASSWORD", "admin123")
    admin_email = os.getenv("ADMIN_EMAIL", "moderator@actforiran.org")
    admin_password = os.getenv("ADMIN_PASSWORD", "moderator123")

    # Ensure super admin exists (and sync password)
    super_admin = db.query(Administrator).filter(Administrator.email == super_admin_email).first()
    if not super_admin:
        super_admin = Administrator(
            email=super_admin_email,
            password_hash=get_password_hash(super_admin_password),
            role="super_admin",
            is_active=True
        )
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)
    else:
        super_admin.password_hash = get_password_hash(super_admin_password)
        super_admin.role = "super_admin"
        super_admin.is_active = True
        db.add(super_admin)
        db.commit()

    # Ensure normal admin exists (and sync password)
    normal_admin = db.query(Administrator).filter(Administrator.email == admin_email).first()
    if not normal_admin:
        normal_admin = Administrator(
            email=admin_email,
            password_hash=get_password_hash(admin_password),
            role="admin",
            is_active=True,
            created_by_admin_id=super_admin.id
        )
        db.add(normal_admin)
        db.commit()
        db.refresh(normal_admin)
    else:
        normal_admin.password_hash = get_password_hash(admin_password)
        normal_admin.role = "admin"
        normal_admin.is_active = True
        db.add(normal_admin)
        db.commit()

    # Seed countries (with Persian names and flags)
    if db.query(Country).count() == 0:
        db.bulk_insert_mappings(
            Country,
            [{"code": c["code"], "name": c["name"], "name_persian": c.get("name_persian", c["name"]), "flag": c["flag"], "is_active": True} for c in TOP_COUNTRIES],
        )

    # Seed roles (insert any missing defaults)
    existing_roles = {r.name for r in db.query(RecipientRole).all()}
    missing_roles = [
        {
            "name": role,
            "is_active": True,
            "is_system_default": True,
            "created_by_admin_id": super_admin.id,
        }
        for role in DEFAULT_RECIPIENT_ROLES
        if role not in existing_roles
    ]
    if missing_roles:
        db.bulk_insert_mappings(RecipientRole, missing_roles)

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
    
    if db.query(PoliticalRecipient).count() == 0:
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
    
    if db.query(AdvocacyTopic).count() == 0:
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
    
    # Seed hot campaigns (only if none exist)
    from models import Campaign
    if db.query(Campaign).count() == 0:
        print("📢 Creating hot campaigns...")
        
        # Get some topic IDs for campaigns
        mahsa_topic = db.query(AdvocacyTopic).filter(AdvocacyTopic.slug == "mahsa-amini").first()
        womens_rights_topic = db.query(AdvocacyTopic).filter(AdvocacyTopic.slug == "womens-rights").first()
        executions_topic = db.query(AdvocacyTopic).filter(AdvocacyTopic.slug == "death-penalty").first()
        sanctions_topic = db.query(AdvocacyTopic).filter(AdvocacyTopic.slug == "international-sanctions").first()
        protesters_topic = db.query(AdvocacyTopic).filter(AdvocacyTopic.slug == "political-prisoners").first()
        
        # Get some recipient IDs by country
        us_recipients = db.query(PoliticalRecipient).filter(
            PoliticalRecipient.country_code == "USA"
        ).limit(5).all()
        uk_recipients = db.query(PoliticalRecipient).filter(
            PoliticalRecipient.country_code == "GBR"
        ).limit(5).all()
        germany_recipients = db.query(PoliticalRecipient).filter(
            PoliticalRecipient.country_code == "DEU"
        ).limit(5).all()
        france_recipients = db.query(PoliticalRecipient).filter(
            PoliticalRecipient.country_code == "FRA"
        ).limit(5).all()
        canada_recipients = db.query(PoliticalRecipient).filter(
            PoliticalRecipient.country_code == "CAN"
        ).limit(5).all()
        
        campaigns_data = [
            {
                "title": "Stop Executions of Iranian Protesters",
                "description": "Urgent action needed: Iran is executing peaceful protesters. Contact your representatives to demand international intervention.",
                "slug": "stop-executions",
                "icon": "⚖️",
                "country_code": "USA",
                "recipient_ids": [r.id for r in us_recipients],
                "topic_ids": [executions_topic.id, protesters_topic.id, sanctions_topic.id] if executions_topic and protesters_topic and sanctions_topic else [],
                "is_hot": True,
                "is_active": True,
                "display_order": 1
            },
            {
                "title": "Support Iranian Women's Rights Movement",
                "description": "Join the global movement supporting Iranian women fighting for freedom. Urge UK officials to take action.",
                "slug": "womens-rights-uk",
                "icon": "✊",
                "country_code": "GBR",
                "recipient_ids": [r.id for r in uk_recipients],
                "topic_ids": [womens_rights_topic.id, mahsa_topic.id] if womens_rights_topic and mahsa_topic else [],
                "is_hot": True,
                "is_active": True,
                "display_order": 2
            },
            {
                "title": "Sanction Iranian Regime Officials",
                "description": "Call on German government to impose stronger sanctions on Iranian officials responsible for human rights violations.",
                "slug": "sanctions-germany",
                "icon": "🚫",
                "country_code": "DEU",
                "recipient_ids": [r.id for r in germany_recipients],
                "topic_ids": [sanctions_topic.id, executions_topic.id] if sanctions_topic and executions_topic else [],
                "is_hot": True,
                "is_active": True,
                "display_order": 3
            },
            {
                "title": "Free Political Prisoners in Iran",
                "description": "Thousands of peaceful protesters are imprisoned in Iran. Contact French officials to demand their release.",
                "slug": "free-prisoners-france",
                "icon": "🔓",
                "country_code": "FRA",
                "recipient_ids": [r.id for r in france_recipients],
                "topic_ids": [protesters_topic.id, sanctions_topic.id] if protesters_topic and sanctions_topic else [],
                "is_hot": True,
                "is_active": True,
                "display_order": 4
            },
            {
                "title": "Support Woman Life Freedom Movement",
                "description": "Stand with the Woman Life Freedom movement. Urge Canadian officials to support Iranian people's fight for democracy.",
                "slug": "woman-life-freedom-canada",
                "icon": "💜",
                "country_code": "CAN",
                "recipient_ids": [r.id for r in canada_recipients],
                "topic_ids": [womens_rights_topic.id, mahsa_topic.id, sanctions_topic.id] if womens_rights_topic and mahsa_topic and sanctions_topic else [],
                "is_hot": True,
                "is_active": True,
                "display_order": 5
            }
        ]
        
        for campaign_data in campaigns_data:
            if campaign_data["recipient_ids"] and campaign_data["topic_ids"]:  # Only create if we have valid data
                campaign = Campaign(
                    **campaign_data,
                    created_by_admin_id=super_admin.id,
                    approval_status="approved",
                    approved_by_admin_id=super_admin.id
                )
                db.add(campaign)
        
        db.commit()
        print(f"   Campaigns: {len(campaigns_data)} created")
    
    print("✅ Database seeded successfully!")
    print(f"   Super Admin: {super_admin_email} / {super_admin_password}")
    print(f"   Normal Admin: {admin_email} / {admin_password}")
    print(f"   Countries: {len(TOP_COUNTRIES)} created")
    print(f"   Recipients: {len(recipients_data)} created") 
    print(f"   Topics: {len(topics_data)} created")

def run_migrations(db: Session):
    """Run database migrations to add new columns if they don't exist"""
    from sqlalchemy import text
    
    print("🔄 Checking for database migrations...")
    
    migrations = []
    
    # Check administrators table
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='administrators' AND column_name='is_active'
        """))
        if not result.fetchone():
            migrations.append("ALTER TABLE administrators ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            print("   ➕ Need to add is_active to administrators")
    except Exception as e:
        print(f"   ⚠️  Could not check administrators.is_active: {e}")
    
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='administrators' AND column_name='created_by_admin_id'
        """))
        if not result.fetchone():
            migrations.append("ALTER TABLE administrators ADD COLUMN created_by_admin_id INTEGER REFERENCES administrators(id)")
            print("   ➕ Need to add created_by_admin_id to administrators")
    except Exception as e:
        print(f"   ⚠️  Could not check administrators.created_by_admin_id: {e}")
    
    # Check countries table
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='countries' AND column_name='name_persian'
        """))
        if not result.fetchone():
            migrations.append("ALTER TABLE countries ADD COLUMN name_persian VARCHAR(100)")
            print("   ➕ Need to add name_persian to countries")
    except Exception as e:
        print(f"   ⚠️  Could not check countries.name_persian: {e}")
    
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='countries' AND column_name='flag'
        """))
        if not result.fetchone():
            migrations.append("ALTER TABLE countries ADD COLUMN flag VARCHAR(10)")
            print("   ➕ Need to add flag to countries")
    except Exception as e:
        print(f"   ⚠️  Could not check countries.flag: {e}")
    
    # Check campaigns table
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='campaigns' AND column_name='approval_status'
        """))
        if not result.fetchone():
            migrations.append("ALTER TABLE campaigns ADD COLUMN approval_status VARCHAR(20) DEFAULT 'pending'")
            print("   ➕ Need to add approval_status to campaigns")
    except Exception as e:
        print(f"   ⚠️  Could not check campaigns.approval_status: {e}")
    
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='campaigns' AND column_name='approved_by_admin_id'
        """))
        if not result.fetchone():
            migrations.append("ALTER TABLE campaigns ADD COLUMN approved_by_admin_id INTEGER REFERENCES administrators(id)")
            print("   ➕ Need to add approved_by_admin_id to campaigns")
    except Exception as e:
        print(f"   ⚠️  Could not check campaigns.approved_by_admin_id: {e}")
    
    # Check email_generation_logs table
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='email_generation_logs' AND column_name='campaign_id'
        """))
        if not result.fetchone():
            migrations.append("ALTER TABLE email_generation_logs ADD COLUMN campaign_id INTEGER REFERENCES campaigns(id)")
            print("   ➕ Need to add campaign_id to email_generation_logs")
    except Exception as e:
        print(f"   ⚠️  Could not check email_generation_logs.campaign_id: {e}")
    
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='email_generation_logs' AND column_name='sender_user_name'
        """))
        if not result.fetchone():
            migrations.append("ALTER TABLE email_generation_logs ADD COLUMN sender_user_name VARCHAR(255)")
            print("   ➕ Need to add sender_user_name to email_generation_logs")
    except Exception as e:
        print(f"   ⚠️  Could not check email_generation_logs.sender_user_name: {e}")

    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='email_generation_logs' AND column_name='sender_citizenship_status'
        """))
        if not result.fetchone():
            migrations.append("ALTER TABLE email_generation_logs ADD COLUMN sender_citizenship_status VARCHAR(50)")
            print("   ➕ Need to add sender_citizenship_status to email_generation_logs")
    except Exception as e:
        print(f"   ⚠️  Could not check email_generation_logs.sender_citizenship_status: {e}")

    # Check political_recipients table
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='political_recipients' AND column_name='media_outlets'
        """))
        if not result.fetchone():
            migrations.append("ALTER TABLE political_recipients ADD COLUMN media_outlets TEXT")
            print("   ➕ Need to add media_outlets to political_recipients")
    except Exception as e:
        print(f"   ⚠️  Could not check political_recipients.media_outlets: {e}")
    
    # Run migrations
    if migrations:
        print(f"🔧 Running {len(migrations)} migration(s)...")
        for migration in migrations:
            try:
                db.execute(text(migration))
                db.commit()
                print(f"   ✅ {migration}")
            except Exception as e:
                print(f"   ❌ Failed: {migration}")
                print(f"      Error: {e}")
                db.rollback()
    else:
        print("✅ Database schema is up to date")

def init_db():
    from models import Base as ModelBase

    ModelBase.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        run_migrations(db)
        seed_defaults(db)
    finally:
        db.close()
