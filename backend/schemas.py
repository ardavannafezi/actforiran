from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class CountryOut(BaseModel):
    code: str
    name: str


class CountriesResponse(BaseModel):
    countries: List[CountryOut]


class RecipientOut(BaseModel):
    id: int
    full_name: str
    email_address: EmailStr
    display_title: str
    country_code: str
    country_name: str


class RecipientsResponse(BaseModel):
    recipients: List[RecipientOut]


class TopicOut(BaseModel):
    id: int
    slug: str
    display_title: str
    description: Optional[str] = None


class TopicsResponse(BaseModel):
    topics: List[TopicOut]


class GenerateEmailRequest(BaseModel):
    country_code: str = Field(..., min_length=3, max_length=3)
    recipient_ids: List[int] = Field(..., min_length=1)
    topic_ids: List[int] = Field(..., min_length=1)
    is_resident: bool
    user_name: Optional[str] = None
    topic_ids: List[int] = Field(..., min_length=1)
    is_resident: bool


class RecipientEmailOut(BaseModel):
    name: str
    email: EmailStr


class GenerateEmailResponse(BaseModel):
    subject: str
    body: str
    recipients: List[RecipientEmailOut]
    mailto_link: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str


class AdminMeResponse(BaseModel):
    id: int
    email: EmailStr
    role: str


class RecipientRoleOut(BaseModel):
    id: int
    name: str
    is_active: bool


class RecipientRoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class PoliticalRecipientCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email_address: EmailStr
    role_id: int
    custom_title: Optional[str] = Field(None, max_length=255)
    country_code: str = Field(..., min_length=3, max_length=3)


class PoliticalRecipientUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email_address: Optional[EmailStr] = None
    role_id: Optional[int] = None
    custom_title: Optional[str] = Field(None, max_length=255)
    country_code: Optional[str] = Field(None, min_length=3, max_length=3)
    is_active: Optional[bool] = None


class PoliticalRecipientAdminOut(BaseModel):
    id: int
    full_name: str
    email_address: EmailStr
    role_id: int
    role_name: str
    custom_title: Optional[str] = None
    country_code: str
    country_name: str
    approval_status: str
    is_active: bool


class AdvocacyTopicCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=100)
    display_title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None


class AdvocacyTopicUpdate(BaseModel):
    slug: Optional[str] = Field(None, min_length=2, max_length=100)
    display_title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AdvocacyTopicAdminOut(BaseModel):
    id: int
    slug: str
    display_title: str
    description: Optional[str] = None
    approval_status: str
    is_active: bool


class ApprovalRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)
