"""Pydantic schemas for authentication requests, responses, and token exchange."""

from datetime import datetime
import re
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserSignupRequest(BaseModel):
    """Payload for user registration."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password with minimum 6 characters")
    name: Optional[str] = Field(None, description="Display name")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email format")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6 or not v.strip():
            raise ValueError("Password must be at least 6 characters long and cannot be whitespace")
        return v


class UserSigninRequest(BaseModel):
    """Payload for user login."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    """Public user account response."""

    id: str
    email: str
    name: str
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    ratings_count: int = 0
    is_cold_start: bool = True
    taste_vector: Optional[List[float]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def populate_full_name(self) -> "UserResponse":
        if not self.full_name:
            self.full_name = self.name
        return self


class UserDetailResponse(UserResponse):
    """Detailed user account response."""

    updated_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Authentication token response accommodating both token and access_token consumers."""

    token: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse
    user_id: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    ratings_count: Optional[int] = None
    is_cold_start: Optional[bool] = None

    @model_validator(mode="after")
    def populate_compatibility_fields(self) -> "TokenResponse":
        if not self.access_token:
            self.access_token = self.token
        if self.user:
            if not self.user_id:
                self.user_id = self.user.id
            if not self.email:
                self.email = self.user.email
            if not self.full_name:
                self.full_name = self.user.full_name or self.user.name
            if self.ratings_count is None:
                self.ratings_count = self.user.ratings_count
            if self.is_cold_start is None:
                self.is_cold_start = self.user.is_cold_start
        return self
