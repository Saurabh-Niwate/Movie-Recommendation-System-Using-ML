import pytest
from app.services.cache import RecommendationCache


def test_cache_set_get():
    cache = RecommendationCache(maxsize=10, ttl=60.0)
    cache.set("key1", {"data": 123}, profile_id="neel")
    assert cache.get("key1") == {"data": 123}
    assert cache.get("key2") is None


def test_cache_profile_invalidation():
    cache = RecommendationCache(maxsize=10, ttl=60.0)
    cache.set("neel:funk_svd:top_picks:20", [1, 2, 3], profile_id="neel")
    cache.set("neel:item_knn:top_picks:20", [4, 5, 6], profile_id="neel")
    cache.set("nitin:funk_svd:top_picks:20", [7, 8, 9], profile_id="nitin")

    assert cache.get("neel:funk_svd:top_picks:20") is not None
    assert cache.get("nitin:funk_svd:top_picks:20") is not None

    evicted = cache.invalidate_profile("neel")
    assert evicted >= 2
    assert cache.get("neel:funk_svd:top_picks:20") is None
    assert cache.get("neel:item_knn:top_picks:20") is None
    # Nitin remains untouched
    assert cache.get("nitin:funk_svd:top_picks:20") == [7, 8, 9]


def test_cache_clear():
    cache = RecommendationCache(maxsize=10, ttl=60.0)
    cache.set("k1", 1, profile_id="p1")
    cache.set("k2", 2, profile_id="p2")
    cache.clear()
    assert cache.get("k1") is None
    assert cache.get("k2") is None
