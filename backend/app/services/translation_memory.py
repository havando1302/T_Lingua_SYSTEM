"""Database-backed translation memory with volatile guest dictionaries.

The JSON implementation is retained only for one-time migration, recovery
tooling and isolated compatibility tests. Production reads and writes the
``translation_memory_entries`` database table.
"""
import json
import hashlib
import os
import re
import shutil
import tempfile
import threading
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Optional

from app.services.translation_cache import invalidate_all, invalidate_owner

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
_TM_FILE = os.path.join(_DATA_DIR, "translation_memory.json")
_DEFAULT_TM_FILE = _TM_FILE
_FORMAT_MARKER = "\0tm:format"
_FORMAT_VALUE = {"key_encoding": "2"}
_KEY_PREFIX = "\0tm:v2:"
_lock = threading.RLock()
_memory: dict[str, dict[str, str]] = {}
_guest_memory: dict[str, dict[str, str]] = {}
_guest_expiry: dict[str, datetime] = {}

_DEFAULT_CLASSIFICATIONS = {
    "xin chào": ("vi", "en"),
    "tạm biệt": ("vi", "en"),
    "chào buổi sáng": ("vi", "en"),
    "chào buổi tối": ("vi", "en"),
    "chúc ngủ ngon": ("vi", "en"),
    "one": ("en", "vi"),
}


def normalize_lang_code(code: Optional[str]) -> str:
    if not code:
        return ""
    clean = code.strip().lower()
    return {"vie": "vi", "vie_latn": "vi", "eng": "en", "eng_latn": "en"}.get(clean, clean)


def _normalize(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return text.strip(" .,!?;:\"'").lower()


def _pair(source_lang: Optional[str], target_lang: Optional[str]) -> tuple[str, str]:
    source, target = normalize_lang_code(source_lang), normalize_lang_code(target_lang)
    if bool(source) != bool(target):
        raise ValueError("Both source and target language are required")
    return source, target


def _owner(client_id: str) -> None:
    if not isinstance(client_id, str) or not client_id or client_id == "*" or any(ord(c) < 32 for c in client_id):
        raise ValueError("Invalid dictionary owner")


def _key(source: str, source_lang: str = "", target_lang: str = "") -> str:
    return _KEY_PREFIX + json.dumps([source, source_lang, target_lang], ensure_ascii=False, separators=(",", ":"))


def _decode(key: str) -> tuple[str, str, str]:
    if not key.startswith(_KEY_PREFIX):
        raise ValueError("Invalid dictionary key")
    value = json.loads(key[len(_KEY_PREFIX):])
    if not isinstance(value, list) or len(value) != 3 or not all(isinstance(part, str) for part in value):
        raise ValueError("Invalid dictionary key")
    source, source_lang, target_lang = value
    if not source or _normalize(source) != source or _pair(source_lang, target_lang) != (source_lang, target_lang):
        raise ValueError("Invalid dictionary key")
    return source, source_lang, target_lang


def _load() -> None:
    global _memory
    with _lock:
        try:
            if not os.path.exists(_TM_FILE):
                loaded = {}
            else:
                with open(_TM_FILE, "r", encoding="utf-8") as source:
                    raw = json.load(source)
                if not isinstance(raw, dict):
                    raise ValueError
                encoded = raw.get(_FORMAT_MARKER) == _FORMAT_VALUE
                if encoded:
                    raw.pop(_FORMAT_MARKER)
                elif raw and all(isinstance(value, str) for value in raw.values()):
                    raw = {"default": raw}
                loaded = {}
                for owner, entries in raw.items():
                    _owner(owner)
                    if not isinstance(entries, dict):
                        raise ValueError
                    loaded[owner] = {}
                    for source, target in entries.items():
                        if not isinstance(source, str) or not isinstance(target, str):
                            raise ValueError
                        if encoded:
                            text, src, tgt = _decode(source)
                        else:
                            # With no format marker even strings that resemble encoded keys
                            # are legacy text. Migration never guesses new language pairs.
                            text = _normalize(source)
                            src, tgt = _DEFAULT_CLASSIFICATIONS.get(text, ("", ""))
                        if not text:
                            continue
                        loaded[owner][_key(text, src, tgt)] = target
            _memory = loaded
            invalidate_all()
        except (OSError, ValueError, TypeError):
            # Keep current memory intact, rather than silently overwrite corrupt data.
            raise RuntimeError("Translation memory is unreadable; restore a verified backup") from None


def _save() -> None:
    directory = os.path.dirname(os.path.abspath(_TM_FILE))
    os.makedirs(directory, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".tm-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            json.dump({_FORMAT_MARKER: _FORMAT_VALUE, **_memory}, target, ensure_ascii=False, indent=2)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, _TM_FILE)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _expire_guests() -> None:
    now = datetime.now(timezone.utc)
    for owner in [owner for owner, expiry in _guest_expiry.items() if expiry <= now]:
        _guest_expiry.pop(owner, None)
        _guest_memory.pop(owner, None)
        invalidate_owner(owner)


def register_guest(owner_id: str, expires_at: datetime) -> None:
    _owner(owner_id)
    with _lock:
        _expire_guests()
        if owner_id not in _guest_expiry and len(_guest_expiry) >= 500:
            raise ValueError("Guest memory capacity reached")
        expiry = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
        if expiry <= datetime.now(timezone.utc):
            raise ValueError("Guest session expired")
        _guest_expiry[owner_id] = expiry
        _guest_memory.setdefault(owner_id, {})


def forget_guest(owner_id: str) -> None:
    with _lock:
        _guest_memory.pop(owner_id, None)
        _guest_expiry.pop(owner_id, None)
        invalidate_owner(owner_id)


def _store(client_id: str) -> dict:
    _expire_guests()
    return _guest_memory if client_id in _guest_expiry else _memory


def lookup(text: str, client_id: str = "default", source_lang: Optional[str] = None, target_lang: Optional[str] = None) -> Optional[str]:
    source = _normalize(text)
    if not source:
        return None
    pair = _pair(source_lang, target_lang)
    with _lock:
        entries = _store(client_id).get(client_id, {})
        if pair != ("", ""):
            exact = entries.get(_key(source, *pair))
            if exact is not None:
                return exact
            # Legacy entries without known languages retain their original behavior.
            return entries.get(_key(source))
        plain = entries.get(_key(source))
        if plain is not None:
            return plain
        for entry_key, target in reversed(list(entries.items())):
            if _decode(entry_key)[0] == source:
                return target
        return None


def lookup_fuzzy(
    text: str, client_id: str = "default", source_lang: Optional[str] = None,
    target_lang: Optional[str] = None, *, threshold: float = 0.92,
    ambiguity_margin: float = 0.03,
) -> Optional[str]:
    """Return a conservative, direction-aware fuzzy match.

    Short inputs are deliberately excluded and the best candidate must be both
    above the threshold and clearly better than the runner-up.  This prevents a
    near match from silently overriding the model when context is ambiguous.
    """
    source = _normalize(text)
    if len(source) < 8 or len(source.split()) < 2:
        return None
    if not 0.8 <= threshold <= 1.0 or not 0.0 <= ambiguity_margin <= 0.2:
        raise ValueError("Invalid fuzzy matching threshold")
    pair = _pair(source_lang, target_lang)
    candidates: list[tuple[float, str]] = []
    with _lock:
        entries = _store(client_id).get(client_id, {})
        for entry_key, translated in entries.items():
            candidate, src, tgt = _decode(entry_key)
            if pair != ("", "") and (src, tgt) not in (pair, ("", "")):
                continue
            if candidate == source:
                return translated
            if abs(len(candidate) - len(source)) > max(4, int(len(source) * 0.2)):
                continue
            score = SequenceMatcher(None, source, candidate, autojunk=False).ratio()
            if score >= threshold:
                candidates.append((score, translated))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    if len(candidates) > 1 and candidates[0][0] - candidates[1][0] < ambiguity_margin:
        return None
    return candidates[0][1]


def _commit(client_id: str, store: dict, entries: dict[str, str]) -> None:
    existed = client_id in store
    previous = store.get(client_id)
    if previous == entries:
        return
    store[client_id] = entries
    if store is _memory:
        try:
            _save()
        except Exception:
            if existed:
                store[client_id] = previous
            else:
                store.pop(client_id, None)
            raise
    invalidate_owner(client_id)


def add_many(
    entries: list[dict], client_id: str = "default", *, volatile: bool = False,
    source_lang: Optional[str] = None, target_lang: Optional[str] = None,
    max_entries: Optional[int] = None,
) -> int:
    """Validate a whole batch, then atomically persist it and invalidate once.

    Rows contain source_text, translated_text and optional source_lang/target_lang.
    An unspecified pair updates a unique tagged term without dropping its metadata;
    ambiguous terms require an explicit language pair.
    """
    _owner(client_id)
    default_pair = _pair(source_lang, target_lang)
    prepared = []
    for row in entries:
        if not isinstance(row, dict) or not isinstance(row.get("source_text"), str) or not isinstance(row.get("translated_text"), str):
            raise ValueError("Dictionary entries require source and translated text")
        source, target = _normalize(row["source_text"]), row["translated_text"].strip()
        if not source or not target:
            raise ValueError("Dictionary entries must not be empty")
        src, tgt = _pair(row.get("source_lang", default_pair[0]), row.get("target_lang", default_pair[1]))
        prepared.append((source, target, src, tgt))
    if not prepared:
        return 0
    with _lock:
        store = _store(client_id)
        if volatile and client_id not in _guest_expiry:
            raise ValueError("Guest session expired")
        updated = dict(store.get(client_id, {}))
        for source, target, src, tgt in prepared:
            plain_key = _key(source)
            if src:
                # Assigning a direction to a legacy term removes its ambiguous fallback.
                updated.pop(plain_key, None)
                entry_key = _key(source, src, tgt)
            elif plain_key in updated:
                entry_key = plain_key
            else:
                matches = [key for key in updated if _decode(key)[0] == source]
                if len(matches) > 1:
                    raise ValueError("Specify a language pair for a term with multiple translations")
                entry_key = matches[0] if matches else plain_key
            # Preserve most recently edited ordering for the legacy dict projection.
            updated.pop(entry_key, None)
            updated[entry_key] = target
        if max_entries is not None and len(updated) > max_entries:
            raise ValueError("Dictionary capacity reached")
        if store is _guest_memory:
            total = sum(len(items) for owner, items in _guest_memory.items() if owner != client_id)
            if len(updated) > 50 or total + len(updated) > 1000:
                raise ValueError("Guest dictionary capacity reached")
        _commit(client_id, store, updated)
    return len(prepared)


def add(
    source_text: str, translated_text: str, client_id: str = "default", *,
    volatile: bool = False, source_lang: Optional[str] = None, target_lang: Optional[str] = None,
) -> bool:
    if not _normalize(source_text) or not translated_text.strip():
        return False
    return bool(add_many(
        [{"source_text": source_text, "translated_text": translated_text}],
        client_id, volatile=volatile, source_lang=source_lang, target_lang=target_lang,
    ))


def delete(source_text: str, client_id: str = "default", source_lang: Optional[str] = None, target_lang: Optional[str] = None) -> bool:
    source, pair = _normalize(source_text), _pair(source_lang, target_lang)
    with _lock:
        store = _store(client_id)
        previous = store.get(client_id, {})
        if pair != ("", ""):
            remove = {_key(source, *pair)}
        else:
            remove = {key for key in previous if _decode(key)[0] == source}
        updated = {key: value for key, value in previous.items() if key not in remove}
        if len(updated) == len(previous):
            return False
        _commit(client_id, store, updated)
        return True


def get_entries(client_id: str = "default") -> list[dict]:
    """Lossless public rows for listing/export, including all language directions."""
    with _lock:
        result = []
        for key, target in _store(client_id).get(client_id, {}).items():
            source, src, tgt = _decode(key)
            result.append({"source_text": source, "translated_text": target,
                           "source_lang": src or None, "target_lang": tgt or None})
        return result


def get_all(client_id: str = "default", source_lang: Optional[str] = None, target_lang: Optional[str] = None) -> dict[str, str]:
    pair = _pair(source_lang, target_lang)
    result = {}
    for row in get_entries(client_id):
        row_pair = (row["source_lang"] or "", row["target_lang"] or "")
        if pair == ("", "") or row_pair in (pair, ("", "")):
            result[row["source_text"]] = row["translated_text"]
    return result


def count(client_id: str = "default") -> int:
    with _lock:
        return len(_store(client_id).get(client_id, {}))


def get_glossary_prompt(client_id: str = "default") -> str:
    return ", ".join(get_all(client_id))


class ITranslationMemoryRepository:
    def lookup(self, text: str, client_id: str = "default", source_lang: Optional[str] = None, target_lang: Optional[str] = None) -> Optional[str]:
        raise NotImplementedError

    def add(self, source_text: str, translated_text: str, client_id: str = "default", *, volatile: bool = False, source_lang: Optional[str] = None, target_lang: Optional[str] = None) -> bool:
        raise NotImplementedError

    def lookup_fuzzy(self, text: str, client_id: str = "default", source_lang: Optional[str] = None, target_lang: Optional[str] = None, *, threshold: float = 0.92) -> Optional[str]:
        raise NotImplementedError

    def delete(self, source_text: str, client_id: str = "default", source_lang: Optional[str] = None, target_lang: Optional[str] = None) -> bool:
        raise NotImplementedError

    def get_all(self, client_id: str = "default") -> dict[str, str]:
        raise NotImplementedError

    def count(self, client_id: str = "default") -> int:
        raise NotImplementedError

    def get_entries(self, client_id: str = "default") -> list[dict]:
        raise NotImplementedError

    def add_many(self, entries: list[dict], client_id: str = "default", **kwargs) -> int:
        raise NotImplementedError

    def get_glossary_prompt(self, client_id: str = "default") -> str:
        raise NotImplementedError


class JsonTranslationMemoryRepository(ITranslationMemoryRepository):
    def lookup(self, text: str, client_id: str = "default", source_lang: Optional[str] = None, target_lang: Optional[str] = None) -> Optional[str]:
        return lookup(text, client_id, source_lang, target_lang)

    def add(self, source_text: str, translated_text: str, client_id: str = "default", *, volatile: bool = False, source_lang: Optional[str] = None, target_lang: Optional[str] = None, db=None) -> bool:
        return add(source_text, translated_text, client_id, volatile=volatile, source_lang=source_lang, target_lang=target_lang)

    def lookup_fuzzy(self, text: str, client_id: str = "default", source_lang: Optional[str] = None, target_lang: Optional[str] = None, *, threshold: float = 0.92) -> Optional[str]:
        return lookup_fuzzy(text, client_id, source_lang, target_lang, threshold=threshold)

    def delete(self, source_text: str, client_id: str = "default", source_lang: Optional[str] = None, target_lang: Optional[str] = None, *, db=None) -> bool:
        return delete(source_text, client_id, source_lang, target_lang)

    def get_all(self, client_id: str = "default", source_lang: Optional[str] = None,
                target_lang: Optional[str] = None, *, db=None) -> dict[str, str]:
        return get_all(client_id, source_lang, target_lang)

    def count(self, client_id: str = "default", *, db=None) -> int:
        return count(client_id)

    def get_entries(self, client_id: str = "default", **kwargs) -> list[dict]:
        return get_entries(client_id)

    def add_many(self, entries: list[dict], client_id: str = "default", **kwargs) -> int:
        kwargs.pop("db", None)
        return add_many(entries, client_id, **kwargs)

    def get_glossary_prompt(self, client_id: str = "default") -> str:
        return get_glossary_prompt(client_id)


class DatabaseTranslationMemoryRepository(ITranslationMemoryRepository):
    """Database-backed Translation Memory; only authenticated guest entries remain volatile."""

    @staticmethod
    def _is_guest(client_id: str) -> bool:
        with _lock:
            _expire_guests()
            return client_id in _guest_expiry

    @staticmethod
    def _session(db=None):
        if db is not None:
            return db, False
        from app.db.database import SessionLocal
        from app.db.models import TranslationMemoryEntry
        session = SessionLocal()
        bind = session.get_bind()
        if bind.dialect.name == "sqlite" and (bind.url.database is None or bind.url.database == ":memory:"):
            TranslationMemoryEntry.__table__.create(bind=bind, checkfirst=True)
        return session, True

    @staticmethod
    def _finish(db, owned: bool, *, commit: bool = False) -> None:
        if owned:
            try:
                if commit:
                    db.commit()
            finally:
                db.close()

    def lookup(self, text: str, client_id: str = "default", source_lang: Optional[str] = None,
               target_lang: Optional[str] = None, *, db=None) -> Optional[str]:
        if self._is_guest(client_id):
            return lookup(text, client_id, source_lang, target_lang)
        source = _normalize(text)
        if not source:
            return None
        pair = _pair(source_lang, target_lang)
        from app.db.models import TranslationMemoryEntry
        session, owned = self._session(db)
        try:
            query = session.query(TranslationMemoryEntry).filter(
                TranslationMemoryEntry.owner_id == client_id,
                TranslationMemoryEntry.source_text_normalized == source,
                TranslationMemoryEntry.norm_version == 1,
            )
            rows = query.order_by(TranslationMemoryEntry.updated_at.desc(), TranslationMemoryEntry.id.desc()).all()
            if pair != ("", ""):
                exact = next((row for row in rows if (row.source_lang, row.target_lang) == pair), None)
                fallback = next((row for row in rows if (row.source_lang, row.target_lang) == ("", "")), None)
                row = exact or fallback
            else:
                row = next((item for item in rows if (item.source_lang, item.target_lang) == ("", "")), None)
                row = row or (rows[0] if rows else None)
            return row.translated_text if row else None
        finally:
            self._finish(session, owned)

    def lookup_fuzzy(self, text: str, client_id: str = "default", source_lang: Optional[str] = None,
                     target_lang: Optional[str] = None, *, threshold: float = 0.92,
                     ambiguity_margin: float = 0.03, db=None) -> Optional[str]:
        if self._is_guest(client_id):
            return lookup_fuzzy(text, client_id, source_lang, target_lang,
                                threshold=threshold, ambiguity_margin=ambiguity_margin)
        source = _normalize(text)
        if len(source) < 8 or len(source.split()) < 2:
            return None
        if not 0.8 <= threshold <= 1.0 or not 0.0 <= ambiguity_margin <= 0.2:
            raise ValueError("Invalid fuzzy matching threshold")
        pair = _pair(source_lang, target_lang)
        from app.db.models import TranslationMemoryEntry
        session, owned = self._session(db)
        try:
            rows = session.query(TranslationMemoryEntry).filter(
                TranslationMemoryEntry.owner_id == client_id,
                TranslationMemoryEntry.norm_version == 1,
            ).all()
            candidates: list[tuple[float, str]] = []
            for row in rows:
                if pair != ("", "") and (row.source_lang, row.target_lang) not in (pair, ("", "")):
                    continue
                candidate = row.source_text_normalized
                if candidate == source:
                    return row.translated_text
                if abs(len(candidate) - len(source)) > max(4, int(len(source) * 0.2)):
                    continue
                score = SequenceMatcher(None, source, candidate, autojunk=False).ratio()
                if score >= threshold:
                    candidates.append((score, row.translated_text))
            if not candidates:
                return None
            candidates.sort(key=lambda item: item[0], reverse=True)
            if len(candidates) > 1 and candidates[0][0] - candidates[1][0] < ambiguity_margin:
                return None
            return candidates[0][1]
        finally:
            self._finish(session, owned)

    def add_many(self, entries: list[dict], client_id: str = "default", *, volatile: bool = False,
                 source_lang: Optional[str] = None, target_lang: Optional[str] = None,
                 max_entries: Optional[int] = None, db=None) -> int:
        _owner(client_id)
        if volatile or self._is_guest(client_id):
            return add_many(entries, client_id, volatile=volatile, source_lang=source_lang,
                            target_lang=target_lang, max_entries=max_entries)
        default_pair = _pair(source_lang, target_lang)
        prepared = []
        for row in entries:
            if not isinstance(row, dict) or not isinstance(row.get("source_text"), str) or not isinstance(row.get("translated_text"), str):
                raise ValueError("Dictionary entries require source and translated text")
            source, target = _normalize(row["source_text"]), row["translated_text"].strip()
            if not source or not target:
                raise ValueError("Dictionary entries must not be empty")
            src, tgt = _pair(row.get("source_lang", default_pair[0]), row.get("target_lang", default_pair[1]))
            prepared.append((source, target, src, tgt, row["source_text"].strip()))
        if not prepared:
            return 0

        from app.db.models import TranslationMemoryEntry
        session, owned = self._session(db)
        try:
            existing = session.query(TranslationMemoryEntry).filter(
                TranslationMemoryEntry.owner_id == client_id,
                TranslationMemoryEntry.norm_version == 1,
            ).all()
            by_key = {(row.source_text_normalized, row.source_lang, row.target_lang): row for row in existing}
            planned: list[tuple[str, str, str, str, str]] = []
            for source, target, src, tgt, original in prepared:
                if src:
                    key = (source, src, tgt)
                else:
                    plain_key = (source, "", "")
                    if plain_key in by_key:
                        key = plain_key
                    else:
                        matches = [candidate for candidate in by_key if candidate[0] == source]
                        if len(matches) > 1:
                            raise ValueError("Specify a language pair for a term with multiple translations")
                        key = matches[0] if matches else plain_key
                planned.append((source, target, key[1], key[2], original))
                by_key.setdefault(key, None)
            if max_entries is not None and len(by_key) > max_entries:
                raise ValueError("Dictionary capacity reached")

            for source, target, src, tgt, original in planned:
                if src:
                    legacy = session.query(TranslationMemoryEntry).filter(
                        TranslationMemoryEntry.owner_id == client_id,
                        TranslationMemoryEntry.source_text_normalized == source,
                        TranslationMemoryEntry.source_lang == "",
                        TranslationMemoryEntry.target_lang == "",
                        TranslationMemoryEntry.norm_version == 1,
                    ).first()
                    if legacy is not None:
                        session.delete(legacy)
                row = session.query(TranslationMemoryEntry).filter(
                    TranslationMemoryEntry.owner_id == client_id,
                    TranslationMemoryEntry.source_text_normalized == source,
                    TranslationMemoryEntry.source_lang == src,
                    TranslationMemoryEntry.target_lang == tgt,
                    TranslationMemoryEntry.norm_version == 1,
                ).first()
                if row is None:
                    row = TranslationMemoryEntry(
                        owner_id=client_id, source_lang=src, target_lang=tgt,
                        source_text=original, source_text_normalized=source,
                        translated_text=target, norm_version=1,
                        is_approved=client_id == "global:approved",
                    )
                    session.add(row)
                else:
                    row.source_text = original
                    row.translated_text = target
                    row.is_approved = client_id == "global:approved"
                    row.updated_at = datetime.utcnow()
            session.flush()
            self._finish(session, owned, commit=True)
            invalidate_owner(client_id)
            return len(prepared)
        except Exception:
            if owned:
                session.rollback()
                session.close()
            raise

    def add(self, source_text: str, translated_text: str, client_id: str = "default", *,
            volatile: bool = False, source_lang: Optional[str] = None,
            target_lang: Optional[str] = None, db=None) -> bool:
        if not _normalize(source_text) or not translated_text.strip():
            return False
        return bool(self.add_many(
            [{"source_text": source_text, "translated_text": translated_text}], client_id,
            volatile=volatile, source_lang=source_lang, target_lang=target_lang, db=db,
        ))

    def delete(self, source_text: str, client_id: str = "default", source_lang: Optional[str] = None,
               target_lang: Optional[str] = None, *, db=None) -> bool:
        if self._is_guest(client_id):
            return delete(source_text, client_id, source_lang, target_lang)
        source, pair = _normalize(source_text), _pair(source_lang, target_lang)
        from app.db.models import TranslationMemoryEntry
        session, owned = self._session(db)
        try:
            query = session.query(TranslationMemoryEntry).filter(
                TranslationMemoryEntry.owner_id == client_id,
                TranslationMemoryEntry.source_text_normalized == source,
                TranslationMemoryEntry.norm_version == 1,
            )
            if pair != ("", ""):
                query = query.filter(
                    TranslationMemoryEntry.source_lang == pair[0],
                    TranslationMemoryEntry.target_lang == pair[1],
                )
            rows = query.all()
            if not rows:
                self._finish(session, owned)
                return False
            for row in rows:
                session.delete(row)
            session.flush()
            self._finish(session, owned, commit=True)
            invalidate_owner(client_id)
            return True
        except Exception:
            if owned:
                session.rollback()
                session.close()
            raise

    def get_entries(self, client_id: str = "default", *, db=None) -> list[dict]:
        if self._is_guest(client_id):
            return get_entries(client_id)
        from app.db.models import TranslationMemoryEntry
        session, owned = self._session(db)
        try:
            rows = session.query(TranslationMemoryEntry).filter(
                TranslationMemoryEntry.owner_id == client_id,
                TranslationMemoryEntry.norm_version == 1,
            ).order_by(TranslationMemoryEntry.source_text_normalized,
                       TranslationMemoryEntry.source_lang, TranslationMemoryEntry.target_lang).all()
            return [{
                "source_text": row.source_text,
                "translated_text": row.translated_text,
                "source_lang": row.source_lang or None,
                "target_lang": row.target_lang or None,
            } for row in rows]
        finally:
            self._finish(session, owned)

    def get_all(self, client_id: str = "default", source_lang: Optional[str] = None,
                target_lang: Optional[str] = None, *, db=None) -> dict[str, str]:
        pair = _pair(source_lang, target_lang)
        result = {}
        for row in self.get_entries(client_id, db=db):
            row_pair = (row["source_lang"] or "", row["target_lang"] or "")
            if pair == ("", "") or row_pair in (pair, ("", "")):
                result[row["source_text"]] = row["translated_text"]
        return result

    def count(self, client_id: str = "default", *, db=None) -> int:
        if self._is_guest(client_id):
            return count(client_id)
        from app.db.models import TranslationMemoryEntry
        session, owned = self._session(db)
        try:
            return session.query(TranslationMemoryEntry).filter(
                TranslationMemoryEntry.owner_id == client_id,
                TranslationMemoryEntry.norm_version == 1,
            ).count()
        finally:
            self._finish(session, owned)

    def get_glossary_prompt(self, client_id: str = "default") -> str:
        return ", ".join(self.get_all(client_id))


_json_repository = JsonTranslationMemoryRepository()
_database_repository = DatabaseTranslationMemoryRepository()


def get_tm_repository() -> ITranslationMemoryRepository:
    # Isolated legacy tests and recovery tooling can explicitly redirect the
    # JSON path. Production always uses the database repository.
    return _json_repository if os.path.abspath(_TM_FILE) != os.path.abspath(_DEFAULT_TM_FILE) else _database_repository


def migrate_legacy_json_to_database(db) -> dict:
    """Import the legacy JSON store once, preserving the source file as a checksum-named backup."""
    from app.db.models import SystemSetting, TranslationMemoryEntry

    marker_key = "translation_memory_database_migration"
    marker = db.query(SystemSetting).filter(SystemSetting.key == marker_key).first()
    if marker is not None:
        database_entries = db.query(TranslationMemoryEntry).count()
        try:
            marked_entries = int(json.loads(marker.value).get("entries", 0))
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
            marked_entries = 0
        if database_entries:
            return {"applied": False, "entries": database_entries}
        if marked_entries:
            raise RuntimeError(
                "Translation Memory migration marker exists but the database table is empty; "
                "restore a verified database or legacy JSON backup"
            )
        # A historical empty marker must not permanently block recovery if a
        # valid legacy backup is restored later.
    if not os.path.exists(_TM_FILE):
        return {"applied": False, "entries": 0}

    _load()
    available_entries = sum(len(entries) for entries in _memory.values())
    if available_entries == 0:
        return {"applied": False, "entries": 0}
    with open(_TM_FILE, "rb") as source:
        digest = hashlib.sha256(source.read()).hexdigest()
    backup_path = f"{_TM_FILE}.pre-db-{digest[:12]}.bak"
    if not os.path.exists(backup_path):
        shutil.copy2(_TM_FILE, backup_path)

    imported = 0
    owners = 0
    for owner, encoded_entries in _memory.items():
        rows = []
        for entry_key, translated in encoded_entries.items():
            source, source_lang, target_lang = _decode(entry_key)
            rows.append({
                "source_text": source,
                "translated_text": translated,
                "source_lang": source_lang,
                "target_lang": target_lang,
            })
        if rows:
            imported += _database_repository.add_many(rows, owner, db=db)
            owners += 1
    marker_value = json.dumps(
        {"sha256": digest, "entries": imported, "owners": owners}, separators=(",", ":")
    )
    if marker is None:
        db.add(SystemSetting(
            key=marker_key,
            value=marker_value,
            description="One-time migration of translation_memory.json into translation_memory_entries",
        ))
    else:
        marker.value = marker_value
        marker.description = "One-time migration of translation_memory.json into translation_memory_entries"
    db.flush()
    return {"applied": True, "entries": imported, "owners": owners, "backup": backup_path}


# Do not eagerly load the legacy file. A corrupt or missing retired JSON file
# must not prevent a database-backed backend from starting. The one-time
# migration loads and validates it explicitly before importing any row.
