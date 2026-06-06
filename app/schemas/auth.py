from pydantic import BaseModel, Field, field_validator

from app.core.auth_service import is_valid_email


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, value: str) -> str:
        if not is_valid_email(value):
            raise ValueError("Invalid email address")
        return value.strip()


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, value: str) -> str:
        if not is_valid_email(value):
            raise ValueError("Invalid email address")
        return value.strip()


class UserPublic(BaseModel):
    id: str
    email: str
    username: str
    role: str
    status: str
    created_at: str | None = None
    last_login_at: str | None = None


class AuthResponse(BaseModel):
    user: UserPublic
    access_token: str
    expires_in: int


class ApiKeyCreateRequest(BaseModel):
    label: str = Field(default="default", max_length=64)


class ApiKeyCreatedResponse(BaseModel):
    id: str
    key_prefix: str
    label: str
    api_key: str


class ApiKeyListItem(BaseModel):
    id: str
    key_prefix: str
    label: str
    created_at: str
    last_used_at: str | None = None
