from typing import List, Optional
from html import escape
from pydantic import BaseModel, EmailStr, Field, validator

def _sanitize_text(value: str) -> str:
    if value is None:
        return value
    return escape(value.strip(), quote=False)


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
    country_code: str
    recipient_ids: List[int]
    topic_ids: List[int]
    sender_citizenship_status: str
    sender_citizenship_country_code: Optional[str] = None
    is_resident: Optional[bool] = None
    user_name: Optional[str] = None
    campaign_id: Optional[int] = None  # Track which campaign was used

    _user_name_no_html = validator("user_name", allow_reuse=True)(_sanitize_text)


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
    country_code: str
    recipient_ids: List[int]
    topic_ids: List[int]
    sender_citizenship_status: str
    sender_citizenship_country_code: Optional[str] = None
    user_name: Optional[str] = None
    campaign_id: Optional[int] = None
    subject: Optional[str] = None
    body: Optional[str] = None

    _user_name_no_html = validator("user_name", allow_reuse=True)(_sanitize_text)
    _subject_no_html = validator("subject", allow_reuse=True)(_sanitize_text)
    _body_no_html = validator("body", allow_reuse=True)(_sanitize_text)


class TickerMessageCreate(BaseModel):
    message_text: str
    is_active: Optional[bool] = True
    display_order: Optional[int] = None

    _message_no_html = validator("message_text", allow_reuse=True)(_sanitize_text)


class TickerMessageUpdate(BaseModel):
    message_text: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None

    _message_no_html = validator("message_text", allow_reuse=True)(_sanitize_text)


class AdminLoginRequest(BaseModel):
    email: str
    password: str

    _email_no_html = validator("email", allow_reuse=True)(_sanitize_text)


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
    name: str

    _name_no_html = validator("name", allow_reuse=True)(_sanitize_text)


class PoliticalRecipientCreate(BaseModel):
    full_name: str
    email_address: str
    role_id: int
    custom_title: Optional[str] = None
    media_outlets: Optional[str] = None
    country_code: str

    _full_name_no_html = validator("full_name", allow_reuse=True)(_sanitize_text)
    _custom_title_no_html = validator("custom_title", allow_reuse=True)(_sanitize_text)
    _media_outlets_no_html = validator("media_outlets", allow_reuse=True)(_sanitize_text)


class PoliticalRecipientUpdate(BaseModel):
    full_name: Optional[str] = None
    email_address: Optional[str] = None
    role_id: Optional[int] = None
    custom_title: Optional[str] = None
    media_outlets: Optional[str] = None
    country_code: Optional[str] = None
    is_active: Optional[bool] = None

    _full_name_no_html = validator("full_name", allow_reuse=True)(_sanitize_text)
    _custom_title_no_html = validator("custom_title", allow_reuse=True)(_sanitize_text)
    _media_outlets_no_html = validator("media_outlets", allow_reuse=True)(_sanitize_text)


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
    slug: str
    display_title: str
    description: Optional[str] = None
    recipient_ids: Optional[List[int]] = []

    _slug_no_html = validator("slug", allow_reuse=True)(_sanitize_text)
    _title_no_html = validator("display_title", allow_reuse=True)(_sanitize_text)
    _description_no_html = validator("description", allow_reuse=True)(_sanitize_text)


class AdvocacyTopicUpdate(BaseModel):
    slug: Optional[str] = None
    display_title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    recipient_ids: Optional[List[int]] = None

    _slug_no_html = validator("slug", allow_reuse=True)(_sanitize_text)
    _title_no_html = validator("display_title", allow_reuse=True)(_sanitize_text)
    _description_no_html = validator("description", allow_reuse=True)(_sanitize_text)


class AdvocacyTopicAdminOut(BaseModel):
    id: int
    slug: str
    display_title: str
    description: Optional[str] = None
    recipient_ids: Optional[List[int]] = []
    approval_status: str
    is_active: bool


class ApprovalRequest(BaseModel):
    reason: Optional[str] = None


class CampaignCreate(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    country_code: Optional[str] = None
    recipient_ids: Optional[List[int]] = []
    topic_ids: List[int]
    is_hot: bool = False
    display_order: int = 0
    is_active: bool = True

    _title_no_html = validator("title", allow_reuse=True)(_sanitize_text)
    _slug_no_html = validator("slug", allow_reuse=True)(_sanitize_text)
    _description_no_html = validator("description", allow_reuse=True)(_sanitize_text)
    _icon_no_html = validator("icon", allow_reuse=True)(_sanitize_text)


class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    country_code: Optional[str] = None
    recipient_ids: Optional[List[int]] = None
    topic_ids: Optional[List[int]] = None
    is_hot: Optional[bool] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

    _title_no_html = validator("title", allow_reuse=True)(_sanitize_text)
    _slug_no_html = validator("slug", allow_reuse=True)(_sanitize_text)
    _description_no_html = validator("description", allow_reuse=True)(_sanitize_text)
    _icon_no_html = validator("icon", allow_reuse=True)(_sanitize_text)


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
