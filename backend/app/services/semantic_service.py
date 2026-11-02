import os
import re
from difflib import SequenceMatcher
from typing import Iterable

from app.utils.dictionary import refine_text_rule_based


def _build_prompt(text: str, context: str) -> str:
    return (
        "Ban la tro ly hieu dinh STT. Sua loi chinh ta va dong am trong cau. "
        "Giu nguyen y nghia. Khong them noi dung moi.\n"
        f"Ngu canh gan nhat: {context}\n"
        f"Cau can sua: {text}\n"
        "Tra ve duy nhat cau da sua."
    )


def get_runtime_glossary(
    client_id: str | None,
    source_lang: str | None = None,
    target_lang: str | None = None,
) -> list[dict[str, str | None]]:
    """Load approved and owner glossary rows for one language direction."""
    from app.services import translation_memory as tm

    source = tm.normalize_lang_code(source_lang)
    target = tm.normalize_lang_code(target_lang)
    owners = ["global:approved"]
    if client_id and client_id != "global:approved":
        owners.append(client_id)
    result: list[dict[str, str | None]] = []
    seen: set[tuple[str, str, str]] = set()
    repository = tm.get_tm_repository()
    for owner in owners:
        for row in repository.get_entries(owner):
            row_source = tm.normalize_lang_code(row.get("source_lang"))
            row_target = tm.normalize_lang_code(row.get("target_lang"))
            if source and row_source and row_source != source:
                continue
            if target and row_target and row_target != target:
                continue
            key = (str(row.get("source_text", "")).casefold(), row_source, row_target)
            if not key[0] or key in seen:
                continue
            seen.add(key)
            result.append(row)
    return result


def build_glossary_prompt(
    entries: Iterable[dict[str, str | None]], *, max_chars: int = 300,
) -> str:
    """Build a bounded Whisper spelling hint from source-side terms."""
    terms: list[str] = []
    used = 0
    for row in entries:
        term = str(row.get("source_text") or "").strip()
        if not term or len(term) > 80:
            continue
        added = len(term) + (2 if terms else 0)
        if used + added > max_chars:
            break
        terms.append(term)
        used += added
    return ", ".join(terms)


def _proper_term(term: str) -> bool:
    words = re.findall(r"[^\W\d_]+", term, flags=re.UNICODE)
    return bool(words) and (
        (len(words) == 1 and words[0][:1].isupper())
        or any(word[:1].isupper() for word in words[1:])
    )


def _apply_glossary_spelling(
    text: str, entries: Iterable[dict[str, str | None]], *, threshold: float = 0.88,
) -> str:
    """Correct close acoustic spellings only for proper-name glossary terms."""
    updated = text
    candidates = sorted(
        {
            str(row.get("source_text") or "").strip()
            for row in entries
            if _proper_term(str(row.get("source_text") or "").strip())
        },
        key=len,
        reverse=True,
    )
    for canonical in candidates:
        canonical_words = canonical.split()
        if not 1 <= len(canonical_words) <= 6 or len(canonical) > 80:
            continue
        tokens = list(re.finditer(r"[^\W_]+", updated, flags=re.UNICODE))
        width = len(canonical_words)
        best: tuple[float, int, int] | None = None
        for start in range(0, len(tokens) - width + 1):
            begin, end = tokens[start].start(), tokens[start + width - 1].end()
            phrase = updated[begin:end]
            score = SequenceMatcher(
                None, phrase.casefold(), canonical.casefold(), autojunk=False,
            ).ratio()
            if score >= threshold and (best is None or score > best[0]):
                best = (score, begin, end)
        if best is not None and updated[best[1]:best[2]].casefold() != canonical.casefold():
            updated = updated[:best[1]] + canonical + updated[best[2]:]
    return updated


def correct_text_semantics(
    text: str,
    context: str,
    glossary_entries: Iterable[dict[str, str | None]] | None = None,
) -> str:
    """
    Khung ham de hieu dinh STT theo ngu canh.
    Hien tai la stub, co the thay the bang LLM local hoac API.
    """
    if not text:
        return text

    text = re.sub(r"\s+", " ", text).strip()

    text = refine_text_rule_based(text)

    mode = os.getenv("SEMANTIC_CORRECTION_MODE", "none").lower()
    if mode in {"local", "api"} and glossary_entries:
        text = _apply_glossary_spelling(text, glossary_entries)

    # Whisper small can end an advisory sentence with "?" because the embedded
    # "... xem ... hay không" is interrogative. That punctuation reverses the
    # meaning when NLLB translates the whole sentence as a direct question.
    if re.search(r"^(?:bạn|anh|chị|quý khách) nên\b.*\bđể\b.*\bxem\b.*\bhay không\?$", text, re.IGNORECASE):
        text = text[:-1] + "."

    if mode == "none":
        return text

    return text
