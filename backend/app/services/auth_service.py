"""Service orchestrating user authentication, registration, and session token generation."""

import logging
import secrets
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.profile import Profile
from app.models.user import User
from app.schemas.auth import (
    UserSignupRequest,
    UserSigninRequest,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger("cinematch.auth_service")

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=256&q=80"
DUMMY_PASSWORD_HASH = "pbkdf2_sha256$100000$00112233445566778899aabbccddeeff$0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


class AuthService:
    """Authentication business logic service."""

    def signup(self, db: Session, payload: UserSignupRequest) -> TokenResponse:
        """Register a new user account, create twin profile, and return JWT token."""
        normalized_email = payload.email.strip().lower()

        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        user_id = f"usr_{secrets.token_hex(6)}"
        user_name = payload.name.strip() if payload.name and payload.name.strip() else normalized_email.split("@")[0].capitalize()

        user = User(
            id=user_id,
            email=normalized_email,
            hashed_password=hash_password(payload.password),
            name=user_name,
            avatar=DEFAULT_AVATAR,
            ratings_count=0,
            is_cold_start=True,
            taste_vector=None,
        )
        db.add(user)

        # Create twin Profile row so Foreign Keys in ratings and user_lists are satisfied
        profile = db.query(Profile).filter(Profile.id == user_id).first()
        if not profile:
            profile = Profile(
                id=user_id,
                name=user_name,
                avatar=DEFAULT_AVATAR,
                bio="Movie enthusiast",
                taste_cluster="General",
                is_demo=False,
                ratings_count=0,
                is_cold_start=True,
            )
            db.add(profile)

        try:
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        token = create_access_token({"sub": user.id, "email": user.email})

        return TokenResponse(
            token=token,
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    def signin(self, db: Session, payload: UserSigninRequest) -> TokenResponse:
        """Authenticate user by email and password, returning JWT token."""
        normalized_email = payload.email.strip().lower()

        user = db.query(User).filter(User.email == normalized_email).first()
        if not user:
            # Perform dummy password verification with a constant dummy hash to prevent timing-based user enumeration
            verify_password(payload.password, DUMMY_PASSWORD_HASH)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        is_valid = verify_password(payload.password, user.hashed_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        token = create_access_token({"sub": user.id, "email": user.email})

        return TokenResponse(
            token=token,
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def seed_default_users(self, db: Session) -> None:
        """Seed default user accounts for demo personas and testing."""
        seed_specs = [
            {"id": "alex", "email": "alex@cinematch.io", "name": "Alex Morgan", "ratings_count": 0, "is_cold_start": True},
            {"id": "demo", "email": "demo@cinematch.io", "name": "Demo User", "ratings_count": 0, "is_cold_start": True},
            {"id": "neel", "email": "neel@cinematch.io", "name": "Neel", "ratings_count": 18, "is_cold_start": False},
            {"id": "nitin", "email": "nitin@cinematch.io", "name": "Nitin", "ratings_count": 14, "is_cold_start": False},
            {"id": "mukesh", "email": "mukesh@cinematch.io", "name": "Mukesh", "ratings_count": 0, "is_cold_start": True},
        ]
        default_pwd_hash = hash_password("Password123!")

        for spec in seed_specs:
            user = db.query(User).filter(User.email == spec["email"]).first()
            if not user:
                user = db.query(User).filter(User.id == spec["id"]).first()
            if not user:
                user = User(
                    id=spec["id"],
                    email=spec["email"],
                    hashed_password=default_pwd_hash,
                    name=spec["name"],
                    avatar=f"/avatars/{spec['id']}.png" if spec["id"] in ("neel", "nitin", "mukesh") else DEFAULT_AVATAR,
                    ratings_count=spec["ratings_count"],
                    is_cold_start=spec["is_cold_start"],
                )
                db.add(user)
                logger.info("Seeded default user account: %s (%s)", spec["email"], spec["id"])

            # Ensure companion Profile exists
            profile = db.query(Profile).filter(Profile.id == spec["id"]).first()
            if not profile:
                profile = Profile(
                    id=spec["id"],
                    name=spec["name"],
                    avatar=user.avatar or DEFAULT_AVATAR,
                    bio=f"CineMatch account for {spec['name']}",
                    ratings_count=spec["ratings_count"],
                    is_cold_start=spec["is_cold_start"],
                    is_demo=True,
                )
                db.add(profile)

        db.commit()


auth_service = AuthService()
