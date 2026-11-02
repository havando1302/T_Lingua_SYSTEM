"""Shared rules for internal translation markers and glossary eligibility."""
import re

PROTECTED_ENTITY = re.compile(
    r"(?<!\w)[+-]?[A-Za-z]*\d+(?:[.,:/-]\d+)*[A-Za-z%]*(?!\w)", re.IGNORECASE,
)


# NLLB can insert whitespace or punctuation between any marker characters.
_GAP = r"[\s._\-\u200b]*"
INTERNAL_PLACEHOLDER = re.compile(
    # The suffix is intentionally unrestricted: real NLLB output can misspell
    # GLOSSARY as GLOSARY or repeat TL before ENTITY. The reserved prefix is
    # enough to reject such leaks without guessing which value they represent.
    _GAP.join("ZXQTL"), re.IGNORECASE,
)


def has_internal_placeholder(text: str) -> bool:
    return bool(INTERNAL_PLACEHOLDER.search(text))


def is_glossary_term(text: str) -> bool:
    text = text.strip()
    return bool(text and len(text) <= 100 and len(text.split()) <= 8
                and not has_internal_placeholder(text))
