import os
import re

from app.utils.dictionary import refine_text_rule_based


def _build_prompt(text: str, context: str) -> str:
    return (
        "Ban la tro ly hieu dinh STT. Sua loi chinh ta va dong am trong cau. "
        "Giu nguyen y nghia. Khong them noi dung moi.\n"
        f"Ngu canh gan nhat: {context}\n"
        f"Cau can sua: {text}\n"
        "Tra ve duy nhat cau da sua."
    )


def correct_text_semantics(text: str, context: str) -> str:
    """
    Khung ham de hieu dinh STT theo ngu canh.
    Hien tai la stub, co the thay the bang LLM local hoac API.
    """
    if not text:
        return text

    text = re.sub(r"\s+", " ", text).strip()

    text = refine_text_rule_based(text)

    mode = os.getenv("SEMANTIC_CORRECTION_MODE", "none").lower()
    if mode == "none":
        return text

    return text
