"""Milestone M1 Iteration 2 Empirical Stress and Adversarial Verification Suite.

Author: Challenger 1 (EMPIRICAL CHALLENGER)
Focus areas:
1. High-concurrency duplicate registration race conditions (ZERO 500 crashes, exact 409 Conflict).
2. Unauthenticated watchlist access rejection (HTTP 401 Unauthorized across all variants).
3. Cross-user isolation and IDOR tamper prevention in watchlist and ratings.
4. Timing side-channel mitigation verification in auth signin.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def _register_user(email_prefix: str) -> dict:
    email = f"{email_prefix}_{uuid.uuid4().hex[:8]}@cinematch.io"
    res = client.post("/api/v1/auth/signup", json={"email": email, "password": "Password123!"})
    assert res.status_code == 201
    data = res.json()
    return {
        "email": email,
        "token": data["token"],
        "user_id": data["user"]["id"],
        "headers": {"Authorization": f"Bearer {data['token']}"},
    }


# =====================================================================
# 1. CONCURRENCY RACE CONDITIONS (SIGNUP)
# =====================================================================

def test_high_concurrency_30_duplicate_signups():
    """Stress test 30 concurrent requests attempting exact duplicate email signup."""
    target_email = f"stress_race30_{uuid.uuid4().hex[:8]}@test.io"
    concurrency = 30

    def attempt_signup(idx: int):
        return client.post(
            "/api/v1/auth/signup",
            json={
                "email": target_email,
                "password": f"Pass123!_{idx}",
                "name": f"Contender {idx}",
            },
        )

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(attempt_signup, i) for i in range(concurrency)]
        responses = [f.result() for f in as_completed(futures)]

    codes = [r.status_code for r in responses]
    count_201 = codes.count(201)
    count_409 = codes.count(409)
    count_500 = codes.count(500)

    print(f"\n[30-Thread Concurrency Signup Results]")
    print(f"  HTTP 201 Created:  {count_201}")
    print(f"  HTTP 409 Conflict: {count_409}")
    print(f"  HTTP 500 Crash:    {count_500}")

    assert count_500 == 0, f"Found {count_500} unhandled HTTP 500 server crashes under concurrency!"
    assert count_201 == 1, f"Expected exactly 1 success, got {count_201}"
    assert count_409 == concurrency - 1, f"Expected {concurrency - 1} 409 Conflicts, got {count_409}"


def test_concurrent_signups_with_mixed_case_and_whitespace():
    """Stress test 20 concurrent requests submitting case variations and whitespace padding."""
    base_name = f"mixedcase_{uuid.uuid4().hex[:6]}"
    domain = "stress-test.org"
    concurrency = 20

    def attempt_variant(idx: int):
        if idx % 4 == 0:
            email = f"  {base_name.upper()}@{domain.upper()}  "
        elif idx % 4 == 1:
            email = f"{base_name.capitalize()}@{domain}"
        elif idx % 4 == 2:
            email = f"{base_name.lower()}@{domain.upper()}"
        else:
            email = f" {base_name.lower()}@{domain} "

        return client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": f"Password123!_{idx}", "name": f"Variant {idx}"},
        )

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(attempt_variant, i) for i in range(concurrency)]
        responses = [f.result() for f in as_completed(futures)]

    codes = [r.status_code for r in responses]
    assert codes.count(500) == 0, "Crash detected on mixed-case concurrency"
    assert codes.count(201) == 1, f"Expected 1 created, got {codes.count(201)}"
    assert codes.count(409) == concurrency - 1


# =====================================================================
# 2. UNAUTHENTICATED WATCHLIST ACCESS REJECTION (HTTP 401)
# =====================================================================

def test_unauthenticated_watchlist_endpoints_strictly_rejected_401():
    """Verify all unauthenticated access variants to /watchlist return 401."""
    vic = _register_user("victim_wl_sec")
    vic_id = vic["user_id"]

    # 1. GET /api/v1/watchlist without header
    r1 = client.get("/api/v1/watchlist")
    assert r1.status_code == 401, f"GET /watchlist returned {r1.status_code}"

    # 2. GET /api/v1/watchlist?profile_id={victim} without header
    r2 = client.get(f"/api/v1/watchlist?profile_id={vic_id}")
    assert r2.status_code == 401, f"GET /watchlist?profile_id={vic_id} returned {r2.status_code}"

    # 3. GET /api/v1/watchlist with x-profile-id header without auth
    r3 = client.get("/api/v1/watchlist", headers={"x-profile-id": vic_id})
    assert r3.status_code == 401, f"GET with x-profile-id returned {r3.status_code}"

    # 4. POST /api/v1/watchlist without header
    r4 = client.post("/api/v1/watchlist", json={"movie_id": 1})
    assert r4.status_code == 401, f"POST /watchlist returned {r4.status_code}"

    # 5. POST /api/v1/watchlist with spoofed body profile_id without auth
    r5 = client.post("/api/v1/watchlist", json={"profile_id": vic_id, "movie_id": 1})
    assert r5.status_code == 401, f"POST /watchlist with body profile_id returned {r5.status_code}"

    # 6. POST /api/v1/watchlist/{movie_id} without header
    r6 = client.post("/api/v1/watchlist/1")
    assert r6.status_code == 401, f"POST /watchlist/1 returned {r6.status_code}"

    # 7. POST /api/v1/watchlist/{movie_id}?profile_id={victim} without header
    r7 = client.post(f"/api/v1/watchlist/1?profile_id={vic_id}")
    assert r7.status_code == 401, f"POST /watchlist/1?profile_id returned {r7.status_code}"

    # 8. DELETE /api/v1/watchlist/{movie_id} without header
    r8 = client.delete("/api/v1/watchlist/1")
    assert r8.status_code == 401, f"DELETE /watchlist/1 returned {r8.status_code}"

    # 9. DELETE /api/v1/watchlist/{movie_id}?profile_id={victim} without header
    r9 = client.delete(f"/api/v1/watchlist/1?profile_id={vic_id}")
    assert r9.status_code == 401, f"DELETE /watchlist/1?profile_id returned {r9.status_code}"


# =====================================================================
# 3. CROSS-USER WATCHLIST ISOLATION AND IDOR PROTECTION
# =====================================================================

def test_authenticated_user_cannot_access_or_tamper_victim_watchlist():
    """Verify User A's token cannot read, inject into, or delete User B's watchlist."""
    user_a = _register_user("attacker_a")
    user_b = _register_user("victim_b")

    # Seed User B with movie 2571
    r_b_add = client.post("/api/v1/watchlist/2571", headers=user_b["headers"])
    assert r_b_add.status_code == 201

    # User A tries to read User B's watchlist via query param
    r_read = client.get(f"/api/v1/watchlist?profile_id={user_b['user_id']}", headers=user_a["headers"])
    assert r_read.status_code == 200
    a_items = [i["movie_id"] for i in r_read.json()]
    assert 2571 not in a_items, "User A saw User B's movie in watchlist!"

    # User A tries to inject movie 318 into User B's watchlist via JSON payload
    r_inj = client.post(
        "/api/v1/watchlist",
        json={"profile_id": user_b["user_id"], "movie_id": 318},
        headers=user_a["headers"],
    )
    assert r_inj.status_code == 201

    # Verify movie 318 was added to User A, NOT User B
    b_wl = client.get("/api/v1/watchlist", headers=user_b["headers"]).json()
    b_ids = [i["movie_id"] for i in b_wl]
    assert 318 not in b_ids, "User A successfully injected an item into User B's watchlist!"
    assert 2571 in b_ids, "User B's original item was missing!"

    # User A tries to delete User B's movie 2571
    r_del = client.delete(f"/api/v1/watchlist/2571?profile_id={user_b['user_id']}", headers=user_a["headers"])
    assert r_del.status_code in (200, 404)

    # Verify User B still has movie 2571
    b_wl_after = client.get("/api/v1/watchlist", headers=user_b["headers"]).json()
    b_ids_after = [i["movie_id"] for i in b_wl_after]
    assert 2571 in b_ids_after, "User A successfully deleted User B's watchlist item!"


# =====================================================================
# 4. TIMING SIDE-CHANNEL MITIGATION (SIGNIN)
# =====================================================================

def test_signin_timing_attack_mitigation_statistical_analysis():
    """Statistically measure execution times of existing user vs non-existent user."""
    target = _register_user("timing_stat_user")
    ghost_email = f"ghost_unregistered_{uuid.uuid4().hex[:8]}@test.io"

    # Warmup
    for _ in range(5):
        client.post("/api/v1/auth/signin", json={"email": target["email"], "password": "WrongPassword123!"})
        client.post("/api/v1/auth/signin", json={"email": ghost_email, "password": "WrongPassword123!"})

    n_samples = 25
    times_existing = []
    times_ghost = []

    for _ in range(n_samples):
        # Measure existing user with wrong password
        t0 = time.perf_counter()
        r1 = client.post("/api/v1/auth/signin", json={"email": target["email"], "password": "WrongPassword123!"})
        t1 = time.perf_counter()
        assert r1.status_code == 401
        times_existing.append((t1 - t0) * 1000.0)

        # Measure non-existent user
        t2 = time.perf_counter()
        r2 = client.post("/api/v1/auth/signin", json={"email": ghost_email, "password": "WrongPassword123!"})
        t3 = time.perf_counter()
        assert r2.status_code == 401
        times_ghost.append((t3 - t2) * 1000.0)

    mean_exist = statistics.mean(times_existing)
    std_exist = statistics.stdev(times_existing)
    mean_ghost = statistics.mean(times_ghost)
    std_ghost = statistics.stdev(times_ghost)
    delta_ms = abs(mean_exist - mean_ghost)
    ratio = mean_exist / mean_ghost if mean_ghost > 0 else 999.0

    print(f"\n[Statistical Timing Side-Channel Report (N={n_samples})]")
    print(f"  Existing User (wrong pwd): mean={mean_exist:.2f}ms, stdev={std_exist:.2f}ms")
    print(f"  Ghost User (non-existent): mean={mean_ghost:.2f}ms, stdev={std_ghost:.2f}ms")
    print(f"  Absolute Delta:            {delta_ms:.2f}ms")
    print(f"  Latency Ratio:             {ratio:.2f}x")

    # Both must take > 100ms due to PBKDF2 100,000 iterations (cannot be instantaneous ~10ms)
    assert mean_exist > 100.0, f"Existing user took only {mean_exist:.2f}ms; PBKDF2 not executing?"
    assert mean_ghost > 100.0, f"Ghost user took only {mean_ghost:.2f}ms; dummy hash verification missing!"
    # Disparity must be small (within reasonable variance, ratio between 0.7x and 1.3x)
    assert 0.7 <= ratio <= 1.3, f"Timing ratio {ratio:.2f}x indicates significant side-channel disparity!"


# =====================================================================
# 5. RATINGS IDOR AND AUTHORIZATION PROTECTION
# =====================================================================

def test_ratings_unauthenticated_and_cross_user_protection():
    """Verify unauthenticated ratings submission is rejected and cross-user ratings cannot spoof victim."""
    # 1. Unauthenticated rating submission without profile_id -> 401
    r_noauth = client.post("/api/v1/ratings", json={"movie_id": 1, "rating": 4.5})
    assert r_noauth.status_code == 401

    # 2. Authenticated User A tries to spoof victim's profile_id
    user_a = _register_user("rater_a")
    user_b = _register_user("rater_b")

    # User A submits rating claiming profile_id = user_b['user_id']
    r_spoof = client.post(
        "/api/v1/ratings",
        json={"profile_id": user_b["user_id"], "movie_id": 1, "rating": 5.0},
        headers=user_a["headers"],
    )
    assert r_spoof.status_code == 200

    # Verify victim User B's profile was NOT modified
    me_b = client.get("/api/v1/auth/me", headers=user_b["headers"]).json()
    assert me_b["ratings_count"] == 0, "Victim User B's ratings_count was mutated by User A!"
    assert me_b["is_cold_start"] is True

    # Verify User A was the one credited with the rating
    me_a = client.get("/api/v1/auth/me", headers=user_a["headers"]).json()
    assert me_a["ratings_count"] == 1, "User A's ratings_count was not credited!"
