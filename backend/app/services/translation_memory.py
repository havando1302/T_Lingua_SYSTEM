"""
Translation Memory Service
--------------------------
Bộ nhớ dịch giúp hệ thống "nhớ" các bản dịch đúng.
Hỗ trợ đa người dùng bằng client_id.
"""
import json
import os
import re
import threading
from typing import Optional

_DATA_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    ),
    "data"
)

_TM_FILE = os.path.join(_DATA_DIR, "translation_memory.json")

_lock = threading.Lock()

# In-memory cache for fast lookup. Structure: { client_id: { source: target } }
_memory: dict[str, dict[str, str]] = {}


def _normalize(text: str) -> str:
    """Chuẩn hóa text để so sánh: lowercase, bỏ dấu câu thừa, trim."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    # Bỏ dấu câu ở đầu/cuối để matching linh hoạt hơn.
    text = text.strip(".,!?;:\"'")
    return text.lower()


def _load() -> None:
    """Load translation memory từ file JSON vào bộ nhớ."""
    global _memory
    if not os.path.exists(_TM_FILE):
        _memory = {}
        return
    try:
        with open(_TM_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        
        _memory = {}
        # Hỗ trợ backward compatibility (nếu file cũ chỉ là 1 dict phẳng)
        if raw and not any(isinstance(v, dict) for v in raw.values()):
            _memory["default"] = {_normalize(k): v for k, v in raw.items()}
        else:
            for client_id, tm_dict in raw.items():
                _memory[client_id] = {_normalize(k): v for k, v in tm_dict.items()}
    except (json.JSONDecodeError, IOError):
        _memory = {}


def _save() -> None:
    """Lưu translation memory ra file JSON."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    try:
        with open(_TM_FILE, "w", encoding="utf-8") as f:
            json.dump(
                _memory,
                f,
                ensure_ascii=False,
                indent=2
            )
    except IOError as e:
        print(f"Không thể lưu bộ nhớ dịch: {e}")


# Load khi import module.
_load()
total_entries = sum(len(tm) for tm in _memory.values())
print(f"Đã tải bộ nhớ dịch: {total_entries} mục từ {len(_memory)} users")


def lookup(text: str, client_id: str = "default") -> Optional[str]:
    """
    Tra cứu bản dịch trong Translation Memory của client cụ thể.
    """
    key = _normalize(text)
    if not key:
        return None
    with _lock:
        client_tm = _memory.get(client_id, {})
        return client_tm.get(key)


def add(source_text: str, translated_text: str, client_id: str = "default") -> bool:
    """
    Thêm hoặc cập nhật một cặp dịch vào Translation Memory.
    """
    key = _normalize(source_text)
    if not key or not translated_text.strip():
        return False

    with _lock:
        if client_id not in _memory:
            _memory[client_id] = {}
        _memory[client_id][key] = translated_text.strip()
        _save()

    print(f"[{client_id}] Đã thêm vào bộ nhớ dịch: \"{source_text}\" -> \"{translated_text}\"")
    return True


def delete(source_text: str, client_id: str = "default") -> bool:
    """
    Xóa một cặp dịch khỏi Translation Memory.
    """
    key = _normalize(source_text)
    with _lock:
        client_tm = _memory.get(client_id)
        if client_tm and key in client_tm:
            removed = client_tm.pop(key)
            _save()
            print(f"[{client_id}] Đã xóa khỏi bộ nhớ dịch: \"{source_text}\" (trước đó: \"{removed}\")")
            return True
    return False


def get_all(client_id: str = "default") -> dict[str, str]:
    """Trả về toàn bộ Translation Memory của client."""
    with _lock:
        return dict(_memory.get(client_id, {}))


def count(client_id: str = "default") -> int:
    """Số lượng entries trong Translation Memory."""
    with _lock:
        return len(_memory.get(client_id, {}))

def get_glossary_prompt(client_id: str = "default") -> str:
    """
    Tạo danh sách từ vựng dạng chuỗi (comma-separated) từ Translation Memory
    để làm initial_prompt cho Whisper (STT).
    """
    with _lock:
        client_tm = _memory.get(client_id, {})
        # Lấy tất cả các từ khóa nguồn (source text)
        keywords = list(client_tm.keys())
        if not keywords:
            return ""
        # Whisper hoạt động tốt với danh sách từ cách nhau bằng dấu phẩy
        return ", ".join(keywords)
