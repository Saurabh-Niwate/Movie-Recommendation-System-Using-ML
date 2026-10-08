"""Tier 3: Cross-Feature Interactions - Neel vs Nitin Divergence & Jaccard Contrast.

Verifies:
- Jaccard similarity between Neel's and Nitin's top-10 recommendations is <= 0.20
- Neel recommendation row has > 60% Action/Sci-Fi genre concentration
- Nitin recommendation row has > 60% Drama/Romance genre concentration
- Hero billboards for Neel and Nitin are distinct titles
"""


def test_neel_vs_nitin_low_jaccard_overlap(client):
    """T3.1.1: Verify Jaccard similarity between Neel's and Nitin's top-10 recommendations <= 0.20."""
    res_neel = client.get("/api/v1/profiles/neel/recommendations?limit=10")
    res_nitin = client.get("/api/v1/profiles/nitin/recommendations?limit=10")

    assert res_neel.status_code == 200
    assert res_nitin.status_code == 200

    neel_ids = {it["movie_id"] for it in res_neel.json()["items"]}
    nitin_ids = {it["movie_id"] for it in res_nitin.json()["items"]}

    intersection = neel_ids.intersection(nitin_ids)
    union = neel_ids.union(nitin_ids)
    jaccard = len(intersection) / len(union)

    assert jaccard <= 0.20, (
        f"Jaccard similarity too high: {jaccard:.3f} > 0.20. Overlapping titles: {intersection}"
    )


def test_neel_action_scifi_genre_concentration(client):
    """T3.1.2: Verify Neel top-10 recommendations have > 60% Action/Sci-Fi concentration."""
    response = client.get("/api/v1/profiles/neel/recommendations?limit=10")
    assert response.status_code == 200
    items = response.json()["items"]
    target_genres = {"Action", "Sci-Fi", "Adventure", "Thriller"}

    matching_count = sum(1 for it in items if any(g in target_genres for g in it["genres"]))
    concentration = matching_count / len(items)
    assert concentration >= 0.60, f"Neel Action/Sci-Fi concentration too low: {concentration:.1%}"


def test_nitin_drama_romance_genre_concentration(client):
    """T3.1.3: Verify Nitin top-10 recommendations have > 60% Drama/Romance concentration."""
    response = client.get("/api/v1/profiles/nitin/recommendations?limit=10")
    assert response.status_code == 200
    items = response.json()["items"]
    target_genres = {"Drama", "Romance", "War"}

    matching_count = sum(1 for it in items if any(g in target_genres for g in it["genres"]))
    concentration = matching_count / len(items)
    assert concentration >= 0.60, f"Nitin Drama/Romance concentration too low: {concentration:.1%}"


def test_neel_vs_nitin_distinct_billboards(client):
    """T3.1.4: Verify Neel and Nitin receive distinct billboard hero movies."""
    b_neel = client.get("/api/v1/recommendations/billboard?profile_id=neel").json()
    b_nitin = client.get("/api/v1/recommendations/billboard?profile_id=nitin").json()

    assert b_neel["movie_id"] != b_nitin["movie_id"], (
        f"Neel and Nitin got identical hero title: {b_neel['title']}"
    )
    assert any(g in {"Action", "Sci-Fi", "Adventure"} for g in b_neel["genres"])
    assert any(g in {"Drama", "Romance"} for g in b_nitin["genres"])
