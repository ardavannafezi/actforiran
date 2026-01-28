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
