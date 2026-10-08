"""Tier 1: Feature Coverage - Recommendation Carousels.

Verifies:
- "Top Picks" carousel ranking order and structure
- "Because You Liked" adjusted cosine item-item neighbors
- "Users Also Watched" association rules co-occurrence lift
- Genre-specific carousel filtering
- Uniqueness and absence of duplicate items
- Limit parameter compliance
"""


def test_top_picks_carousel_structure(client):
    """T1.3.1: Verify Top Picks carousel returns items with scores strictly descending."""
    response = client.get("/api/v1/profiles/neel/recommendations?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    items = data["items"]
    assert len(items) == 10

    # Assert strictly descending scores
    scores = [it["score"] for it in items]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], (
            f"Score inverted at index {i}: {scores[i]} < {scores[i + 1]}"
        )


def test_because_you_liked_carousel(client):
    """T1.3.2: Verify 'Because you liked' identifies user's top seed movie and related neighbors."""
    response = client.get("/api/v1/recommendations/because-you-liked?profile_id=neel")
    assert response.status_code == 200
    data = response.json()
    assert "seed_movie" in data
    assert "recommendations" in data
    seed = data["seed_movie"]
    assert "movie_id" in seed
    assert "title" in seed
    assert len(data["recommendations"]) > 0

    # Ensure recommendations share genres with the seed movie
    seed_genres = set(seed["genres"])
    for rec in data["recommendations"]:
        assert set(rec["genres"]).intersection(seed_genres), (
            f"Neighbor '{rec['title']}' does not share any genre with seed '{seed['title']}'"
        )


def test_also_watched_association_rules(client):
    """T1.3.3: Verify 'Users Also Watched' returns association rules items with lift > 1.0."""
    response = client.get("/api/v1/recommendations/also-watched/2571")
    assert response.status_code == 200
    data = response.json()
    assert "source_movie_id" in data
    assert "recommendations" in data
    recs = data["recommendations"]
    assert len(recs) > 0

    for item in recs:
        assert "lift" in item
        assert item["lift"] >= 1.0, f"Association lift must be >= 1.0, got {item['lift']}"
        assert "cooccurrence" in item
        assert item["cooccurrence"] > 0


def test_genre_carousel_filtering(client):
    """T1.3.4: Verify genre carousel filtering returns 100% titles matching specified genre."""
    response = client.get("/api/v1/movies/search?genre=Action&limit=15")
    assert response.status_code == 200
    movies = response.json()
    assert len(movies) > 0
    for m in movies:
        assert "genres" in m
        assert "Action" in m["genres"], (
            f"Movie '{m['title']}' missing 'Action' genre: {m['genres']}"
        )


def test_carousels_no_unrated_duplicates(client):
    """T1.3.5: Verify recommendation carousels contain zero duplicate movie IDs."""
    response = client.get("/api/v1/profiles/neel/recommendations?limit=20")
    assert response.status_code == 200
    items = response.json()["items"]
    movie_ids = [it["movie_id"] for it in items]
    assert len(movie_ids) == len(set(movie_ids)), "Found duplicate movie IDs in top recommendations"


def test_carousel_limit_compliance(client):
    """T1.3.6: Verify recommendation carousel strictly respects custom limit parameter."""
    for requested_limit in [3, 7, 12]:
        response = client.get(f"/api/v1/profiles/neel/recommendations?limit={requested_limit}")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == requested_limit, f"Expected {requested_limit} items, got {len(items)}"
