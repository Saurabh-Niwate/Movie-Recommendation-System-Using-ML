from typing import Any, Optional, Dict, List
import cachetools
import threading


class RecommendationCache:
    """Thread-safe TTLCache for recommendation results with profile-level invalidation."""

    def __init__(self, maxsize: int = 2000, ttl: float = 60.0):
        self.ttl = ttl
        self.maxsize = maxsize
        self._cache: cachetools.TTLCache = cachetools.TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = threading.Lock()
        # Keep track of keys per profile for O(1) invalidation
        self._profile_keys: Dict[str, set] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache if not expired."""
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: Any, profile_id: Optional[str] = None) -> None:
        """Store value in cache associated with an optional profile_id."""
        with self._lock:
            self._cache[key] = value
            if profile_id:
                if profile_id not in self._profile_keys:
                    self._profile_keys[profile_id] = set()
                self._profile_keys[profile_id].add(key)

    def invalidate_profile(self, profile_id: str) -> int:
        """Evict all cached entries belonging to profile_id."""
        count = 0
        with self._lock:
            # Check profile keys map
            keys = self._profile_keys.pop(profile_id, set())
            for k in keys:
                if k in self._cache:
                    del self._cache[k]
                    count += 1

            # Also check prefix matches for safety
            prefix = f"{profile_id}:"
            matching_keys = [k for k in self._cache.keys() if isinstance(k, str) and k.startswith(prefix)]
            for k in matching_keys:
                if k in self._cache:
                    del self._cache[k]
                    count += 1

        return count

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()
            self._profile_keys.clear()


# Global cache instance
cache_service = RecommendationCache(maxsize=2000, ttl=60.0)


def get_cache_service() -> RecommendationCache:
    """Dependency returning the global recommendation cache."""
    return cache_service
