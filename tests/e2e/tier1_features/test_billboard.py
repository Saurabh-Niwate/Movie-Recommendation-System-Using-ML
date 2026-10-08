"""Tier 1: Feature Coverage - Hero Billboard Section.

Verifies:
- Hero movie recommendation personalization per profile (Neel vs Nitin)
- Cold-start hero fallback for Mukesh
- Full metadata schema completeness
- Match score validity boundaries
- Default profile fallback handling
"""


def test_billboard_neel_action_scifi(client):
    """T1.2.1: Verify Neel hero billboard movie features Action or Sci-Fi with high match %."""
    response = client.get("/api/v1/recommendations/billboard?profile_id=neel")
    assert response.status_code == 200
    hero = response.json()
    assert "genres" in hero
    hero_genres = set(hero["genres"])
    assert hero_genres.intersection({"Action", "Sci-Fi", "Adventure", "Thriller"})
    assert hero["match_percentage"] >= 85


def test_billboard_nitin_drama_romance(client):
    """T1.2.2: Verify Nitin hero billboard movie features Drama or Romance with high match %."""
    response = client.get("/api/v1/recommendations/billboard?profile_id=nitin")
    assert response.status_code == 200
    hero = response.json()
    assert "genres" in hero
    hero_genres = set(hero["genres"])
    assert hero_genres.intersection({"Drama", "Romance", "War"})
    assert hero["match_percentage"] >= 85


def test_billboard_mukesh_cold_start(client):
    """T1.2.3: Verify Mukesh billboard returns popular baseline hero title without crashing."""
    response = client.get("/api/v1/recommendations/billboard?profile_id=mukesh")
    assert response.status_code == 200
    hero = response.json()
    assert hero.get("title")
    assert "movie_id" in hero
    assert hero["match_percentage"] >= 50


def test_billboard_metadata_completeness(client):
    """T1.2.4: Verify billboard payload contains complete metadata for UI rendering."""
    response = client.get("/api/v1/recommendations/billboard?profile_id=neel")
    assert response.status_code == 200
    hero = response.json()
    required_fields = [
        "movie_id",
        "title",
        "synopsis",
        "backdrop_path",
        "poster_path",
        "match_percentage",
        "genres",
        "year",
    ]
    for field in required_fields:
        assert field in hero, f"Missing billboard field: {field}"
        assert hero[field] is not None, f"Billboard field {field} is null"


def test_billboard_match_score_bounds(client):
    """T1.2.5: Verify billboard match percentage is strictly bounded between 50% and 100%."""
    response = client.get("/api/v1/recommendations/billboard?profile_id=neel")
    assert response.status_code == 200
    hero = response.json()
    score = hero["match_percentage"]
    assert isinstance(score, int)
    assert 50 <= score <= 100, f"Expected match score in [50, 100], got {score}"


def test_billboard_default_profile_neel(client):
    """T1.2.6: Verify omitting profile_id defaults to default profile cleanly."""
    response = client.get("/api/v1/recommendations/billboard")
    assert response.status_code == 200
    hero = response.json()
    assert "movie_id" in hero
    assert "title" in hero
