"""Bounded, process-local translation cache with owner/global invalidation."""
import logging
import threading
import time
import weakref
from collections import OrderedDict
from typing import Any, Optional

logger = logging.getLogger(__name__)
VersionSnapshot = tuple[int, int]
_instances: weakref.WeakSet = weakref.WeakSet()
_instances_lock = threading.Lock()


def _language(code: str) -> str:
    code = code.strip().lower()
    return {"vie": "vi", "vie_latn": "vi", "eng": "en", "eng_latn": "en"}.get(code, code)


class TranslationMemoryCache:
    def __init__(self, max_entries: int = 5000, default_ttl_s: float = 3600.0):
        if max_entries < 0 or default_ttl_s < 0:
            raise ValueError("Cache capacity and TTL must be non-negative")
        self._max_entries = max_entries
        self._default_ttl_s = default_ttl_s
        self._cache: OrderedDict[tuple, tuple[str, float]] = OrderedDict()
        self._lock = threading.Lock()
        self._tm_versions: dict[str, int] = {}
        self._hits = 0
        self._misses = 0
        with _instances_lock:
            _instances.add(self)

    def get_version(self, owner_id: str) -> int:
        """Compatibility accessor; use get_version_snapshot for cache writes."""
        with self._lock:
            return self._tm_versions.get(owner_id, 1)

    def _version(self, owner_id: str) -> VersionSnapshot:
        return self._tm_versions.get(owner_id, 1), self._tm_versions.get("*", 1)

    def get_version_snapshot(self, owner_id: str) -> VersionSnapshot:
        """Capture before lookup/inference so a later dictionary edit wins."""
        with self._lock:
            return self._version(owner_id)

    def bump_version(self, owner_id: str) -> int:
        with self._lock:
            self._tm_versions[owner_id] = self._tm_versions.get(owner_id, 1) + 1
            if owner_id == "global:approved":
                self._tm_versions["*"] = self._tm_versions.get("*", 1) + 1
                self._cache.clear()
            else:
                for key in [key for key in self._cache if key[0] == owner_id]:
                    del self._cache[key]
            logger.debug("translation_cache_version_bumped owner_id=%s", owner_id)
            return self._tm_versions[owner_id]

    def _key(self, owner_id: str, source_lang: str, target_lang: str, text: str) -> tuple:
        return owner_id, _language(source_lang), _language(target_lang), text, self._version(owner_id)

    def get(self, owner_id: str, source_lang: str, target_lang: str, normalized_text: str) -> Optional[str]:
        with self._lock:
            key = self._key(owner_id, source_lang, target_lang, normalized_text)
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            value, expiry = entry
            if time.monotonic() >= expiry:
                del self._cache[key]
                self._misses += 1
                return None
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def put(
        self, owner_id: str, source_lang: str, target_lang: str,
        normalized_text: str, translation: str, ttl_s: Optional[float] = None,
        *, expected_version: Optional[VersionSnapshot] = None,
    ) -> bool:
        with self._lock:
            if expected_version is not None and expected_version != self._version(owner_id):
                return False
            ttl = self._default_ttl_s if ttl_s is None else ttl_s
            if self._max_entries == 0 or ttl <= 0 or not translation:
                return False
            key = self._key(owner_id, source_lang, target_lang, normalized_text)
            self._cache[key] = (translation, time.monotonic() + ttl)
            self._cache.move_to_end(key)
            while len(self._cache) > self._max_entries:
                self._cache.popitem(last=False)
            return True

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            # Discard writes from computations already in flight before clear/reload.
            self._tm_versions["*"] = self._tm_versions.get("*", 1) + 1
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict[str, Any]:
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache), "max_size": self._max_entries,
                "hits": self._hits, "misses": self._misses,
                "hit_rate": round(self._hits / total, 3) if total else 0.0,
            }


def invalidate_owner(owner_id: str) -> None:
    """Dictionary mutations invalidate the shared cache and injected caches alike."""
    with _instances_lock:
        caches = list(_instances)
    for cache in caches:
        cache.bump_version(owner_id)


def invalidate_all() -> None:
    with _instances_lock:
        caches = list(_instances)
    for cache in caches:
        cache.clear()


GLOBAL_TRANSLATION_CACHE = TranslationMemoryCache()
