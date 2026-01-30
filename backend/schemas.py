from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator

def _reject_html(value: str) -> str:
    if value is None:
        return value
    if "<" in value or ">" in value:
        raise ValueError("Invalid characters in input")
    return value.strip()


class CountryOut(BaseModel):
    code: str
    name: str
    name_persian: Optional[str] = None
    flag: Optional[str] = None


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
    sender_citizenship_status: str
    sender_citizenship_country_code: Optional[str] = Field(None, min_length=3, max_length=3)
    is_resident: Optional[bool] = None
    user_name: Optional[str] = None
    campaign_id: Optional[int] = None  # Track which campaign was used

    _user_name_no_html = validator("user_name", allow_reuse=True)(_reject_html)


class RecipientEmailOut(BaseModel):
    name: str
    email: EmailStr


class GenerateEmailResponse(BaseModel):
    subject: str
    body: str
    recipients: List[RecipientEmailOut]
    mailto_link: str
    groups: Optional[list] = None


class EmailGroupOut(BaseModel):
    subject: str
    body: str
    recipients: List[RecipientEmailOut]
    recipient_ids: List[int]
    mailto_link: str


class GenerateEmailGroupsResponse(BaseModel):
    groups: List[EmailGroupOut]


class LogEmailSendRequest(BaseModel):
    country_code: str = Field(..., min_length=3, max_length=3)
    recipient_ids: List[int] = Field(..., min_length=1)
    topic_ids: List[int] = Field(..., min_length=1)
    sender_citizenship_status: str
    sender_citizenship_country_code: Optional[str] = Field(None, min_length=3, max_length=3)
    user_name: Optional[str] = None
    campaign_id: Optional[int] = None
    subject: Optional[str] = None
    body: Optional[str] = None

    _user_name_no_html = validator("user_name", allow_reuse=True)(_reject_html)
    _subject_no_html = validator("subject", allow_reuse=True)(_reject_html)
    _body_no_html = validator("body", allow_reuse=True)(_reject_html)


class TickerMessageCreate(BaseModel):
    message_text: str = Field(..., min_length=1, max_length=500)
    is_active: Optional[bool] = True
    display_order: Optional[int] = None

    _message_no_html = validator("message_text", allow_reuse=True)(_reject_html)


class TickerMessageUpdate(BaseModel):
    message_text: Optional[str] = Field(None, min_length=1, max_length=500)
    is_active: Optional[bool] = None
    display_order: Optional[int] = None

    _message_no_html = validator("message_text", allow_reuse=True)(_reject_html)


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

    _email_no_html = validator("email", allow_reuse=True)(_reject_html)


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    csrf_token: Optional[str] = None


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

    _name_no_html = validator("name", allow_reuse=True)(_reject_html)


class PoliticalRecipientCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email_address: EmailStr
    role_id: int
    custom_title: Optional[str] = Field(None, max_length=255)
    media_outlets: Optional[str] = None
    country_code: str = Field(..., min_length=3, max_length=3)

    _full_name_no_html = validator("full_name", allow_reuse=True)(_reject_html)
    _custom_title_no_html = validator("custom_title", allow_reuse=True)(_reject_html)
    _media_outlets_no_html = validator("media_outlets", allow_reuse=True)(_reject_html)


class PoliticalRecipientUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email_address: Optional[EmailStr] = None
    role_id: Optional[int] = None
    custom_title: Optional[str] = Field(None, max_length=255)
    media_outlets: Optional[str] = None
    country_code: Optional[str] = Field(None, min_length=3, max_length=3)
    is_active: Optional[bool] = None

    _full_name_no_html = validator("full_name", allow_reuse=True)(_reject_html)
    _custom_title_no_html = validator("custom_title", allow_reuse=True)(_reject_html)
    _media_outlets_no_html = validator("media_outlets", allow_reuse=True)(_reject_html)


class PoliticalRecipientAdminOut(BaseModel):
    id: int
    full_name: str
    email_address: EmailStr
    role_id: int
    role_name: str
    custom_title: Optional[str] = None
    media_outlets: Optional[str] = None
    country_code: str
    country_name: str
    approval_status: str
    is_active: bool


class AdvocacyTopicCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=100)
    display_title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None

    _slug_no_html = validator("slug", allow_reuse=True)(_reject_html)
    _title_no_html = validator("display_title", allow_reuse=True)(_reject_html)
    _description_no_html = validator("description", allow_reuse=True)(_reject_html)


class AdvocacyTopicUpdate(BaseModel):
    slug: Optional[str] = Field(None, min_length=2, max_length=100)
    display_title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None

    _slug_no_html = validator("slug", allow_reuse=True)(_reject_html)
    _title_no_html = validator("display_title", allow_reuse=True)(_reject_html)
    _description_no_html = validator("description", allow_reuse=True)(_reject_html)


class AdvocacyTopicAdminOut(BaseModel):
    id: int
    slug: str
    display_title: str
    description: Optional[str] = None
    approval_status: str
    is_active: bool


class ApprovalRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


class CampaignCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    country_code: Optional[str] = Field(None, min_length=3, max_length=3)
    recipient_ids: List[int]
    topic_ids: List[int]
    is_hot: bool = False
    display_order: int = 0
    is_active: bool = True

    _title_no_html = validator("title", allow_reuse=True)(_reject_html)
    _slug_no_html = validator("slug", allow_reuse=True)(_reject_html)
    _description_no_html = validator("description", allow_reuse=True)(_reject_html)
    _icon_no_html = validator("icon", allow_reuse=True)(_reject_html)


class CampaignUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    slug: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    country_code: Optional[str] = Field(None, min_length=3, max_length=3)
    recipient_ids: Optional[List[int]] = None
    topic_ids: Optional[List[int]] = None
    is_hot: Optional[bool] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

    _title_no_html = validator("title", allow_reuse=True)(_reject_html)
    _slug_no_html = validator("slug", allow_reuse=True)(_reject_html)
    _description_no_html = validator("description", allow_reuse=True)(_reject_html)
    _icon_no_html = validator("icon", allow_reuse=True)(_reject_html)


class CampaignOut(BaseModel):
    id: int
    title: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    country_code: Optional[str] = None
    recipient_ids: List[int]
    topic_ids: List[int]
    is_hot: bool
    is_active: bool
    display_order: int
    approval_status: str
