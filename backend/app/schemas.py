from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


class MessageResponse(BaseModel):
    message: str


class AccessLogResponse(BaseModel):
    name: str
    email: EmailStr
    login_at: datetime
    logout_at: datetime | None

    model_config = {"from_attributes": True}


class AccessLogPaginationResponse(BaseModel):
    items: list[AccessLogResponse]
    page: int
    limit: int
    total: int
    pages: int
