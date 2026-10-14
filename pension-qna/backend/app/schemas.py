from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def validate_email(value: str) -> str:
    normalized = value.strip().lower()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise ValueError("올바른 이메일 주소를 입력해 주세요.")
    return normalized


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=7, max_length=30)

    _validate_email = field_validator("email")(validate_email)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)

    _validate_email = field_validator("email")(validate_email)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class PublicUser(BaseModel):
    id: int
    email: str
    name: str
    phone: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: PublicUser
