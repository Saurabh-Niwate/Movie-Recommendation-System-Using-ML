"""Tier 1: Single-User Authentication & Account Architecture E2E Tests.

Verifies:
- User signup POST /api/v1/auth/signup (HTTP 201 Created with JWT token and User response)
- User signin POST /api/v1/auth/signin (HTTP 200 OK with token and User response)
- Profile retrieval GET /api/v1/auth/me (HTTP 200 with Bearer authorization)
- Email normalization (whitespace stripping, lowercasing)
- Error handling: duplicate email returns 409 Conflict
- Error handling: invalid password returns 401 Unauthorized
- Error handling: malformed email or short password returns 400/422
- Error handling: missing or invalid Bearer token returns 401 Unauthorized
- Multi-user isolation (separate IDs, independent state, zero persona mixing)
"""

import pytest


def test_signup_success_returns_201_token_and_user_profile(client):
    """T1.1.1: Verify signup registers a new unique user and returns 201 with auth token."""
    payload = {
        "email": "sarah.connor@cyberdyne.org",
        "password": "Password123!",
        "name": "Sarah Connor",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"

    data = response.json()
    assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 10
    assert "user" in data
    user = data["user"]
    assert "id" in user and user["id"].startswith("usr_")
    assert user["email"] == "sarah.connor@cyberdyne.org"
    assert user["name"] == "Sarah Connor"
    assert user["ratings_count"] == 0
    assert user["is_cold_start"] is True
    assert user.get("taste_vector") is None


def test_signup_email_normalization(client):
    """T1.1.2: Verify email is trimmed and normalized to lowercase during signup."""
    payload = {
        "email": "   Alex.Murphy@DetroitPolice.COM   ",
        "password": "RoboCopPassword123",
        "name": "Alex Murphy",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201

    user = response.json()["user"]
    assert user["email"] == "alex.murphy@detroitpolice.com"


def test_signup_duplicate_email_rejected_409(client):
    """T1.1.3: Verify attempting to register an existing email returns 409 Conflict."""
    payload = {
        "email": "ellen.ripley@weyland-yutani.com",
        "password": "XenomorphPassword1",
        "name": "Ellen Ripley",
    }
    first_res = client.post("/api/v1/auth/signup", json=payload)
    assert first_res.status_code == 201

    # Second signup with case variation
    duplicate_payload = {
        "email": "  ELLEN.RIPLEY@Weyland-Yutani.com  ",
        "password": "AnotherPassword123",
        "name": "Ellen Ripley Duplicate",
    }
    second_res = client.post("/api/v1/auth/signup", json=duplicate_payload)
    assert second_res.status_code == 409, f"Expected 409 Conflict, got {second_res.status_code}"
    error = second_res.json()
    assert "detail" in error
    assert "already exists" in error["detail"].lower() or "registered" in error["detail"].lower()


@pytest.mark.parametrize("invalid_email", [
    "not-an-email",
    "user@",
    "@domain.com",
    "user@domain",
    "",
    "   ",
])
def test_signup_invalid_email_format_rejected(client, invalid_email):
    """T1.1.4: Verify malformed email addresses are rejected with 400 or 422."""
    payload = {
        "email": invalid_email,
        "password": "ValidPassword123",
        "name": "Test User",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code in (400, 422), f"Expected 400 or 422 for '{invalid_email}', got {response.status_code}"


@pytest.mark.parametrize("short_password", [
    "",
    "123",
    "abcde",
    "     ",
])
def test_signup_short_or_empty_password_rejected(client, short_password):
    """T1.1.5: Verify passwords shorter than 6 characters are rejected with 400 or 422."""
    payload = {
        "email": "valid.user@example.com",
        "password": short_password,
        "name": "Valid Name",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code in (400, 422), f"Expected 400 or 422 for password '{short_password}', got {response.status_code}"


def test_signin_success_returns_200_and_valid_token(client):
    """T1.1.6: Verify valid email and password signin returns 200 OK and token."""
    signup_payload = {
        "email": "neo@matrix.io",
        "password": "RedPillPassword123",
        "name": "Thomas Anderson",
    }
    client.post("/api/v1/auth/signup", json=signup_payload)

    signin_payload = {
        "email": "neo@matrix.io",
        "password": "RedPillPassword123",
    }
    response = client.post("/api/v1/auth/signin", json=signin_payload)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "neo@matrix.io"
    assert data["user"]["name"] == "Thomas Anderson"


def test_signin_case_insensitive_email(client):
    """T1.1.7: Verify signin allows uppercase or mixed case email matching."""
    client.post("/api/v1/auth/signup", json={
        "email": "trinity@matrix.io",
        "password": "WhiteRabbit123",
        "name": "Trinity",
    })

    signin_res = client.post("/api/v1/auth/signin", json={
        "email": "TRINITY@MATRIX.IO",
        "password": "WhiteRabbit123",
    })
    assert signin_res.status_code == 200
    assert signin_res.json()["user"]["email"] == "trinity@matrix.io"


def test_signin_wrong_password_rejected_401(client):
    """T1.1.8: Verify signin with wrong password returns 401 Unauthorized."""
    client.post("/api/v1/auth/signup", json={
        "email": "morpheus@matrix.io",
        "password": "Nebuchadnezzar123",
        "name": "Morpheus",
    })

    signin_res = client.post("/api/v1/auth/signin", json={
        "email": "morpheus@matrix.io",
        "password": "WrongPassword999",
    })
    assert signin_res.status_code == 401
    assert "invalid" in signin_res.json()["detail"].lower()


def test_signin_nonexistent_email_rejected_401(client):
    """T1.1.9: Verify signin with unregistered email returns 401 Unauthorized."""
    signin_res = client.post("/api/v1/auth/signin", json={
        "email": "ghost.user@doesnotexist.com",
        "password": "AnyPassword123",
    })
    assert signin_res.status_code == 401
    assert "invalid" in signin_res.json()["detail"].lower()


def test_auth_me_with_valid_bearer_token(client):
    """T1.1.10: Verify GET /api/v1/auth/me returns active user details using Bearer token."""
    signup_res = client.post("/api/v1/auth/signup", json={
        "email": "agent.smith@matrix.io",
        "password": "Inevitable123!",
        "name": "Agent Smith",
    })
    token = signup_res.json()["token"]
    user_id = signup_res.json()["user"]["id"]

    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["id"] == user_id
    assert me_data["email"] == "agent.smith@matrix.io"
    assert me_data["name"] == "Agent Smith"
    assert me_data["ratings_count"] == 0
    assert me_data["is_cold_start"] is True


def test_auth_me_missing_token_returns_401(client):
    """T1.1.11: Verify GET /api/v1/auth/me without authorization header returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_auth_me_invalid_token_returns_401(client):
    """T1.1.12: Verify GET /api/v1/auth/me with invalid Bearer token returns 401."""
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer malformed_token_xyz_12345"})
    assert response.status_code == 401


def test_multi_user_account_isolation_no_persona_leakage(client):
    """T1.1.13: Verify User A and User B have completely distinct IDs and tokens with zero persona mixing."""
    res_a = client.post("/api/v1/auth/signup", json={
        "email": "user.alpha@cinema.io",
        "password": "AlphaPassword123",
        "name": "User Alpha",
    })
    res_b = client.post("/api/v1/auth/signup", json={
        "email": "user.beta@cinema.io",
        "password": "BetaPassword123",
        "name": "User Beta",
    })

    user_a = res_a.json()["user"]
    user_b = res_b.json()["user"]
    token_a = res_a.json()["token"]
    token_b = res_b.json()["token"]

    assert user_a["id"] != user_b["id"]
    assert token_a != token_b

    # Verify token A retrieves User A and token B retrieves User B
    me_a = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"}).json()
    me_b = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"}).json()

    assert me_a["email"] == "user.alpha@cinema.io"
    assert me_b["email"] == "user.beta@cinema.io"
    assert me_a["id"] != me_b["id"]

    # Verify no legacy persona switcher leakage
    assert user_a["id"] not in ("neel", "nitin", "mukesh")
    assert user_b["id"] not in ("neel", "nitin", "mukesh")
