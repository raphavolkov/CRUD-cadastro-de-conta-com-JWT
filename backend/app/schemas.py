from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


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
