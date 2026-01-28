from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB
from sqlalchemy.orm import relationship

from database import Base


class Administrator(Base):
    __tablename__ = "administrators"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)


class Country(Base):
    __tablename__ = "countries"

    code = Column(String(3), primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class RecipientRole(Base):
    __tablename__ = "recipient_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_system_default = Column(Boolean, default=False)
    created_by_admin_id = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PoliticalRecipient(Base):
    __tablename__ = "political_recipients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email_address = Column(String(255), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("recipient_roles.id"), nullable=False)
    custom_title = Column(String(255), nullable=True)
    country_code = Column(String(3), ForeignKey("countries.code"), nullable=False)
    is_active = Column(Boolean, default=True)
    approval_status = Column(String(20), default="pending")
    created_by_admin_id = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    approved_by_admin_id = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    country = relationship("Country")
    role = relationship("RecipientRole")


class AdvocacyTopic(Base):
    __tablename__ = "advocacy_topics"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, nullable=False)
    display_title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    approval_status = Column(String(20), default="pending")
    created_by_admin_id = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    approved_by_admin_id = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Campaign(Base):
    """Predefined campaigns (hot topics) set by admins"""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    icon = Column(String(10), nullable=True)  # Emoji icon
    
    # Predefined selections
    country_code = Column(String(3), ForeignKey("countries.code"), nullable=False)
    recipient_ids = Column(JSONB, nullable=False)  # Array of recipient IDs
    topic_ids = Column(JSONB, nullable=False)  # Array of topic IDs
    
    # Settings
    is_hot = Column(Boolean, default=False)  # Show on main page
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    
    # Metadata
    created_by_admin_id = Column(Integer, ForeignKey("administrators.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    country = relationship("Country")
    created_by = relationship("Administrator")

class EmailGenerationLog(Base):
    __tablename__ = "email_generation_logs"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)  # Track campaign usage
    sender_ip_address = Column(INET, nullable=True)
    sender_country_code = Column(String(3), nullable=True)
    sender_country_name = Column(String(100), nullable=True)
    sender_user_name = Column(String(255), nullable=True)  # Track user name
    is_country_resident = Column(Boolean, nullable=True)
    selected_recipient_country = Column(String(100), nullable=True)
    recipient_ids = Column(ARRAY(Integer), nullable=True)
    topic_ids = Column(ARRAY(Integer), nullable=True)
    generated_subject = Column(Text, nullable=True)
    generated_body = Column(Text, nullable=True)
    generation_successful = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    ai_model_used = Column(String(50), nullable=True)
    ai_tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    campaign = relationship("Campaign")


class AdminActivityLog(Base):
    __tablename__ = "admin_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    action_type = Column(String(50), nullable=False)
    target_entity_type = Column(String(50), nullable=True)
    target_entity_id = Column(Integer, nullable=True)
    action_details = Column(JSONB, nullable=True)
    ip_address = Column(INET, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
