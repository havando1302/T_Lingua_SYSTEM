"""Shared rules for internal translation markers and glossary eligibility."""
import re


# NLLB can insert whitespace or punctuation between any marker characters.
_GAP = r"[\s._\-\u200b]*"
INTERNAL_PLACEHOLDER = re.compile(
    _GAP.join("ZXQTL") + _GAP + "(?:" + _GAP.join("ENTITY")
    + "|" + _GAP.join("GLOSSARY") + ")", re.IGNORECASE,
)


def has_internal_placeholder(text: str) -> bool:
    return bool(INTERNAL_PLACEHOLDER.search(text))


def is_glossary_term(text: str) -> bool:
    text = text.strip()
    return bool(text and len(text) <= 100 and len(text.split()) <= 8
                and not has_internal_placeholder(text))
