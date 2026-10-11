"""CineMatch Security & Authentication Utilities.

Provides password hashing via PBKDF2-HMAC-SHA256 with cryptographically secure salts,
and JWT generation and verification using HMAC-SHA256 (HS256).
Zero external pip dependencies required.
"""

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import secrets
from typing import Any, Dict, Optional, Union

from app.core.config import settings


# =====================================================================
# PASSWORD HASHING (PBKDF2-HMAC-SHA256)
# =====================================================================

PBKDF2_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 100_000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Hash plain text password with PBKDF2-HMAC-SHA256 and unique random salt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_hex(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${salt}${derived}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against PBKDF2 formatted hash using constant-time comparison."""
    if not plain_password or not hashed_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) == 4 and parts[0] == PBKDF2_ALGORITHM:
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            expected_hash = parts[3]
            candidate_hash = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt,
                iterations,
            ).hex()
            return hmac.compare_digest(candidate_hash, expected_hash)
        elif len(parts) == 3 and parts[0] == PBKDF2_ALGORITHM:
            salt = bytes.fromhex(parts[1])
            expected_hash = parts[2]
            candidate_hash = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt,
                PBKDF2_ITERATIONS,
            ).hex()
            return hmac.compare_digest(candidate_hash, expected_hash)
        return False
    except Exception:
        return False


# =====================================================================
# JWT TOKENS (RFC 7519 HS256 IMPLEMENTATION)
# =====================================================================

def _b64url_encode(data: bytes) -> str:
    """Base64 URL-safe encode without padding '=' characters."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    """Base64 URL-safe decode restoring required '=' padding."""
    rem = len(data) % 4
    if rem:
        data += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(
    data: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[Union[timedelta, int]] = None,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Generate an HS256 signed JWT token containing claims and expiration."""
    payload: Dict[str, Any] = {}
    if isinstance(data, dict):
        payload.update(data)
    elif isinstance(data, str):
        payload["sub"] = data
    if user_id:
        payload["sub"] = user_id
    if email:
        payload["email"] = email
    for k, v in kwargs.items():
        payload[k] = v

    now = datetime.now(timezone.utc)
    if isinstance(expires_delta, timedelta):
        expire = now + expires_delta
    elif isinstance(expires_delta, (int, float)):
        expire = now + timedelta(seconds=float(expires_delta))
    else:
        expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload.setdefault("iat", int(now.timestamp()))
    payload.setdefault("exp", int(expire.timestamp()))

    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    header_b64 = _b64url_encode(header_json)
    payload_b64 = _b64url_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    secret = settings.jwt_secret_key.encode("utf-8")
    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and verify an HS256 signed JWT token.

    Raises ValueError on invalid format, signature mismatch, or expired token.
    """
    if not token or not isinstance(token, str):
        raise ValueError("Invalid token")

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Token must have exactly 3 parts")

    header_b64, payload_b64, sig_b64 = parts

    try:
        header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception as exc:
        raise ValueError("Malformed token header or payload") from exc

    if header.get("alg") != settings.jwt_algorithm:
        raise ValueError(f"Unsupported token algorithm: {header.get('alg')}")

    # Verify signature
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    secret = settings.jwt_secret_key.encode("utf-8")
    expected_sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(sig_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature")

    # Verify expiration
    exp = payload.get("exp")
    if exp is not None:
        now_ts = datetime.now(timezone.utc).timestamp()
        if now_ts > exp:
            raise ValueError("Token has expired")

    return payload
