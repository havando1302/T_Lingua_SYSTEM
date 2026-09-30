import re


_REPLACEMENTS = (
    # === Lời chào / Giao tiếp cơ bản ===
    ("Xin trào", "Xin chào"),
    ("Sin chào", "Xin chào"),
    ("xin trào", "xin chào"),
    ("Tam biệt", "Tạm biệt"),
    ("tam biệt", "tạm biệt"),
    ("Cám ơn", "Cảm ơn"),
    ("cam ơn", "cảm ơn"),

    # === Đồng âm / Sai thanh điệu ===
    ("ống dẫn gà", "ống dẫn gas"),
    ("rõ rì", "rò rỉ"),
    ("bò hành", "bảo hành"),
    ("sửa chứa", "sửa chữa"),
    ("Ban đáng làm", "Bạn đang làm"),
    ("Kỷ nắng việt", "Kỹ năng việt"),
    ("bán đang", "bạn đang"),
    ("Bán có", "Bạn có"),
    ("bán có", "bạn có"),
    ("bán khỏe", "bạn khỏe"),
    ("Bán khỏe", "Bạn khỏe"),
    ("tôi rất vui đước", "tôi rất vui được"),
    ("gặp bán", "gặp bạn"),

    # === Sai phụ âm đầu ===
    ("dời sống", "đời sống"),
    ("dạy học", "dậy học"),
    ("giáo giục", "giáo dục"),
    ("trương trình", "chương trình"),
    ("Chương chình", "Chương trình"),

    # === Số / Đơn vị ===
    ("một chăm", "một trăm"),
    ("hai chăm", "hai trăm"),
    ("một chiệu", "một triệu"),
    ("một ngìn", "một nghìn"),

    # === Từ vựng phổ biến ===
    ("điện thoạch", "điện thoại"),
    ("máy tín", "máy tính"),
    ("intenet", "internet"),
    ("phầm mềm", "phần mềm"),
    ("ứng dụn", "ứng dụng"),
    ("thời tiếc", "thời tiết"),
    ("nhiệc độ", "nhiệt độ"),
    ("sở thụ", "sở thú"),
    # Short Vietnamese clips are sometimes decoded phonetically.  These
    # variants were reproduced with large-v3-turbo and the real app output.
    ("Sjá þú", "Sở thú"),
    ("thở thú", "sở thú"),
    ("tờ thu", "sở thú"),
)


def _preserve_capitalization(replacement: str, matched: str) -> str:
    if not matched:
        return replacement

    if matched[0].isupper():
        return replacement[:1].upper() + replacement[1:]

    return replacement


def refine_text_rule_based(text: str) -> str:
    if not text:
        return text

    updated = text
    for source, target in _REPLACEMENTS:
        pattern = re.compile(re.escape(source), flags=re.IGNORECASE)
        updated = pattern.sub(
            lambda match: _preserve_capitalization(target, match.group(0)),
            updated
        )

    return updated


def correct_text_semantics(text: str, _context_text: str | None = None) -> str:
    return refine_text_rule_based(text)
