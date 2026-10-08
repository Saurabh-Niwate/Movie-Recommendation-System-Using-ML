"""Tier 2: Boundary & Corner Cases - Pagination & Recommendation Limit Bounds.

Verifies:
- Minimum valid limit=1
- Standard limit=20
- High boundary limit=100
- Zero limit (limit=0) rejected with 422
- Negative limit (limit=-5) rejected with 422
- Exorbitant limit (>100) rejected with 422
"""


def test_recommendations_limit_minimum_1(client):
    """T2.5.1: Verify limit=1 returns exactly 1 top recommendation."""
    response = client.get("/api/v1/profiles/neel/recommendations?limit=1")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1


def test_recommendations_limit_standard_20(client):
    """T2.5.2: Verify default/standard limit=20 returns 20 recommendations."""
    response = client.get("/api/v1/profiles/neel/recommendations?limit=20")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 20


def test_recommendations_limit_maximum_100(client):
    """T2.5.3: Verify maximum boundary limit=100 is supported."""
    response = client.get("/api/v1/profiles/neel/recommendations?limit=100")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) <= 100


def test_recommendations_limit_zero_rejected(client):
    """T2.5.4: Verify limit=0 is rejected with 422 validation error."""
    response = client.get("/api/v1/profiles/neel/recommendations?limit=0")
    assert response.status_code == 422


def test_recommendations_limit_negative_rejected(client):
    """T2.5.5: Verify negative limits are rejected with 422 validation error."""
    for neg in [-1, -10]:
        response = client.get(f"/api/v1/profiles/neel/recommendations?limit={neg}")
        assert response.status_code == 422


def test_recommendations_limit_exceeding_max_rejected(client):
    """T2.5.6: Verify limit exceeding upper boundary (>100) is rejected with 422."""
    response = client.get("/api/v1/profiles/neel/recommendations?limit=101")
    assert response.status_code == 422
