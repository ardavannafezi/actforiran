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
    fm_ministry_role = db.query(RecipientRole).filter_by(name="Foreign Ministry").first()
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

    # Additional EU leaders (provided list, verified public emails)
    extra_recipients = [
        {"full_name": "Christian Stocker", "email_address": "service@bka.gv.at", "role_id": pm_role.id, "country_code": "AUT"},
        {"full_name": "Bart De Wever", "email_address": "contact@premier.be", "role_id": pm_role.id, "country_code": "BEL"},
        {"full_name": "Rossen Jeliazkov", "email_address": "gis@government.bg", "role_id": pm_role.id, "country_code": "BGR"},
        {"full_name": "Andrej Plenković", "email_address": "gradjani@vlada.hr", "role_id": pm_role.id, "country_code": "HRV"},
        {"full_name": "Andrej Babiš", "email_address": "posta@vlada.gov.cz", "role_id": pm_role.id, "country_code": "CZE"},
        {"full_name": "Mette Frederiksen", "email_address": "stm@stm.dk", "role_id": pm_role.id, "country_code": "DNK"},
        {"full_name": "Kristen Michal", "email_address": "riigikantselei@riigikantselei.ee", "role_id": pm_role.id, "country_code": "EST"},
        {"full_name": "Petteri Orpo", "email_address": "kirjaamo@vnk.fi", "role_id": pm_role.id, "country_code": "FIN"},
        {"full_name": "Friedrich Merz", "email_address": "poststelle@bk.bund.de", "role_id": chancellor_role.id, "country_code": "DEU"},
        {"full_name": "Kyriakos Mitsotakis", "email_address": "primeminister@primeminister.gr", "role_id": pm_role.id, "country_code": "GRC"},
        {"full_name": "Viktor Orbán", "email_address": "orbanviktor@orbanviktor.hu", "role_id": pm_role.id, "country_code": "HUN"},
        {"full_name": "Micheál Martin", "email_address": "info@taoiseach.gov.ie", "role_id": pm_role.id, "country_code": "IRL"},
        {"full_name": "Giorgia Meloni", "email_address": "chigicomunicazione@governo.it", "role_id": pm_role.id, "country_code": "ITA"},
        {"full_name": "Giorgia Meloni", "email_address": "presidente@pec.governo.it", "role_id": pm_role.id, "country_code": "ITA"},
        {"full_name": "Evika Siliņa", "email_address": "ieva.ziberga@mk.gov.lv", "role_id": pm_role.id, "country_code": "LVA"},
        {"full_name": "Luc Frieden", "email_address": "ministere.etat@me.etat.lu", "role_id": pm_role.id, "country_code": "LUX"},
        {"full_name": "Robert Abela", "email_address": "info.pps@gov.mt", "role_id": pm_role.id, "country_code": "MLT"},
        {"full_name": "Robert Abela", "email_address": "foi.opm@gov.mt", "role_id": pm_role.id, "country_code": "MLT"},
        {"full_name": "Donald Tusk", "email_address": "kontakt@kprm.gov.pl", "role_id": pm_role.id, "country_code": "POL"},
        {"full_name": "Luís Montenegro", "email_address": "gabinete.pm@pm.gov.pt", "role_id": pm_role.id, "country_code": "PRT"},
        {"full_name": "Robert Fico", "email_address": "premier@vlada.gov.sk", "role_id": pm_role.id, "country_code": "SVK"},
        {"full_name": "Robert Golob", "email_address": "gp.kpv@gov.si", "role_id": pm_role.id, "country_code": "SVN"},
        {"full_name": "Ulf Kristersson", "email_address": "statsradsberedningen.registrator@regeringskansliet.se", "role_id": pm_role.id, "country_code": "SWE"},
        {"full_name": "Nikos Christodoulides", "email_address": "info@presidency.gov.cy", "role_id": president_role.id, "country_code": "CYP"},
        {"full_name": "Gitanas Nausėda", "email_address": "kanceliarija@president.lt", "role_id": president_role.id, "country_code": "LTU"},
        {"full_name": "Nicușor Dan", "email_address": "procetatean@presidency.ro", "role_id": president_role.id, "country_code": "ROU"}
    ]

    # Foreign ministries (institutional contacts)
    if fm_ministry_role:
        extra_recipients.extend([
            {"full_name": "Federal Ministry for European and International Affairs", "email_address": "post@bmeia.gv.at", "role_id": fm_ministry_role.id, "country_code": "AUT"},
            {"full_name": "Federal Public Service Foreign Affairs", "email_address": "contact@diplomatie.belgium.be", "role_id": fm_ministry_role.id, "country_code": "BEL"},
            {"full_name": "Ministry of Foreign Affairs", "email_address": "mfa@mfa.bg", "role_id": fm_ministry_role.id, "country_code": "BGR"},
            {"full_name": "Ministry of Foreign and European Affairs", "email_address": "info@mvep.hr", "role_id": fm_ministry_role.id, "country_code": "HRV"},
            {"full_name": "Ministry of Foreign Affairs", "email_address": "epodatelna@mzv.cz", "role_id": fm_ministry_role.id, "country_code": "CZE"},
            {"full_name": "Ministry of Foreign Affairs", "email_address": "um@um.dk", "role_id": fm_ministry_role.id, "country_code": "DNK"},
            {"full_name": "Ministry of Foreign Affairs", "email_address": "info@mfa.ee", "role_id": fm_ministry_role.id, "country_code": "EST"},
            {"full_name": "Ministry for Foreign Affairs", "email_address": "kirjaamo.um@gov.fi", "role_id": fm_ministry_role.id, "country_code": "FIN"},
            {"full_name": "Federal Foreign Office", "email_address": "poststelle@auswaertiges-amt.de", "role_id": fm_ministry_role.id, "country_code": "DEU"},
            {"full_name": "Ministry of Foreign Affairs", "email_address": "info@mfa.gr", "role_id": fm_ministry_role.id, "country_code": "GRC"},
            {"full_name": "Ministry of Foreign Affairs and Trade", "email_address": "info@mfa.gov.hu", "role_id": fm_ministry_role.id, "country_code": "HUN"},
            {"full_name": "Department of Foreign Affairs", "email_address": "correspondence@dfa.ie", "role_id": fm_ministry_role.id, "country_code": "IRL"},
            {"full_name": "Ministry of Foreign Affairs and International Cooperation", "email_address": "urp@esteri.it", "role_id": fm_ministry_role.id, "country_code": "ITA"},
            {"full_name": "Ministry of Foreign Affairs", "email_address": "info@mfa.gov.lv", "role_id": fm_ministry_role.id, "country_code": "LVA"},
            {"full_name": "Ministry of Foreign and European Affairs", "email_address": "info.mae@mae.etat.lu", "role_id": fm_ministry_role.id, "country_code": "LUX"},
            {"full_name": "Ministry for Foreign and European Affairs", "email_address": "foreignaffairs@gov.mt", "role_id": fm_ministry_role.id, "country_code": "MLT"},
            {"full_name": "Ministry of Foreign Affairs", "email_address": "minbuza@minbuza.nl", "role_id": fm_ministry_role.id, "country_code": "NLD"},
            {"full_name": "Ministry of Foreign Affairs", "email_address": "kancelaria@mfa.gov.pl", "role_id": fm_ministry_role.id, "country_code": "POL"},
            {"full_name": "Ministry of Foreign Affairs", "email_address": "mne@mne.pt", "role_id": fm_ministry_role.id, "country_code": "PRT"},
            {"full_name": "Ministry of Foreign and European Affairs", "email_address": "podatelna@mzv.sk", "role_id": fm_ministry_role.id, "country_code": "SVK"},
            {"full_name": "Ministry of Foreign and European Affairs", "email_address": "gp.mzz@gov.si", "role_id": fm_ministry_role.id, "country_code": "SVN"},
            {"full_name": "Ministry of Foreign Affairs, EU and Cooperation", "email_address": "informacion.maec@maec.es", "role_id": fm_ministry_role.id, "country_code": "ESP"},
            {"full_name": "Ministry for Foreign Affairs", "email_address": "ud.registrator@gov.se", "role_id": fm_ministry_role.id, "country_code": "SWE"},
            {"full_name": "Ministry of Foreign Affairs", "email_address": "info@mfa.gov.cy", "role_id": fm_ministry_role.id, "country_code": "CYP"},
            {"full_name": "Ministry for Europe and Foreign Affairs", "email_address": "contact.diplomatie@diplomatie.gouv.fr", "role_id": fm_ministry_role.id, "country_code": "FRA"},
            {"full_name": "Ministry of Foreign Affairs", "email_address": "urm@urm.lt", "role_id": fm_ministry_role.id, "country_code": "LTU"},
            {"full_name": "Ministry of Foreign Affairs", "email_address": "comunicare@mae.ro", "role_id": fm_ministry_role.id, "country_code": "ROU"}
        ])
    else:
        print("⚠️ Foreign Ministry role missing; skipping foreign ministry contacts")

    recipients_data.extend(extra_recipients)
    
    existing_emails = {
        r.email_address.lower()
        for r in db.query(PoliticalRecipient.email_address).all()
        if r.email_address
    }
    for recipient_data in recipients_data:
        email = recipient_data.get("email_address", "").lower()
        if not email or email in existing_emails:
            continue
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
                "recipient_ids": [r.id for r in us_recipients],
                "is_hot": True,
                "is_active": True,
                "display_order": 1
            },
            {
                "title": "Support Iranian Women's Rights Movement",
                "description": "Join the global movement supporting Iranian women fighting for freedom. Urge UK officials to take action.",
                "slug": "womens-rights-uk",
                "icon": "✊",
                "recipient_ids": [r.id for r in uk_recipients],
                "is_hot": True,
                "is_active": True,
                "display_order": 2
            },
            {
                "title": "Sanction Iranian Regime Officials",
                "description": "Call on German government to impose stronger sanctions on Iranian officials responsible for human rights violations.",
                "slug": "sanctions-germany",
                "icon": "🚫",
                "recipient_ids": [r.id for r in germany_recipients],
                "is_hot": True,
                "is_active": True,
                "display_order": 3
            },
            {
                "title": "Free Political Prisoners in Iran",
                "description": "Thousands of peaceful protesters are imprisoned in Iran. Contact French officials to demand their release.",
                "slug": "free-prisoners-france",
                "icon": "🔓",
                "recipient_ids": [r.id for r in france_recipients],
                "is_hot": True,
                "is_active": True,
                "display_order": 4
            },
            {
                "title": "Support Woman Life Freedom Movement",
                "description": "Stand with the Woman Life Freedom movement. Urge Canadian officials to support Iranian people's fight for democracy.",
                "slug": "woman-life-freedom-canada",
                "icon": "💜",
                "recipient_ids": [r.id for r in canada_recipients],
                "is_hot": True,
                "is_active": True,
                "display_order": 5
            }
        ]
        
        for campaign_data in campaigns_data:
            if campaign_data["recipient_ids"]:  # Only create if we have valid data
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
    
    # Check advocacy_topics table for recipient_ids and country_code
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='advocacy_topics' AND column_name='recipient_ids'
        """))
        if not result.fetchone():
            migrations.append("ALTER TABLE advocacy_topics ADD COLUMN recipient_ids JSONB")
            print("   ➕ Need to add recipient_ids to advocacy_topics")
    except Exception as e:
        print(f"   ⚠️  Could not check advocacy_topics.recipient_ids: {e}")
    
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='advocacy_topics' AND column_name='country_code'
        """))
        if not result.fetchone():
            migrations.append("ALTER TABLE advocacy_topics ADD COLUMN country_code VARCHAR(3) REFERENCES countries(code)")
            print("   ➕ Need to add country_code to advocacy_topics")
    except Exception as e:
        print(f"   ⚠️  Could not check advocacy_topics.country_code: {e}")
    
    # Check campaigns table - remove topic_ids column if exists, ensure recipient_ids is NOT NULL
    try:
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='campaigns' AND column_name='topic_ids'
        """))
        if result.fetchone():
            # First set recipient_ids for campaigns that might not have it
            migrations.append("UPDATE campaigns SET recipient_ids = '[]'::jsonb WHERE recipient_ids IS NULL")
            # Then drop topic_ids
            migrations.append("ALTER TABLE campaigns DROP COLUMN IF EXISTS topic_ids")
            # Drop country_code too
            migrations.append("ALTER TABLE campaigns DROP COLUMN IF EXISTS country_code")
            print("   ➕ Need to remove topic_ids and country_code from campaigns")
    except Exception as e:
        print(f"   ⚠️  Could not check campaigns.topic_ids: {e}")
    
    # Auto-approve all existing topics (topics don't need approval)
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM advocacy_topics WHERE approval_status = 'pending'
        """))
        pending_count = result.fetchone()[0]
        if pending_count > 0:
            migrations.append("UPDATE advocacy_topics SET approval_status = 'approved' WHERE approval_status = 'pending'")
            print(f"   ➕ Need to auto-approve {pending_count} pending topics")
    except Exception as e:
        print(f"   ⚠️  Could not check advocacy_topics: {e}")
    
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
