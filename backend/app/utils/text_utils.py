"""
Text utilities for TTS streaming.
Chia nhỏ văn bản thành các câu/cụm từ ngắn để phục vụ TTS streaming.
"""
import re

# Độ dài tối thiểu và tối đa của 1 chunk (ký tự).
# Nếu câu quá ngắn, gộp với câu sau để VITS không bị vụn âm.
# Nếu câu không có dấu chấm phẩy quá dài, chia nhỏ theo ranh giới từ để tránh quá tải GPU/VRAM.
MIN_CHUNK_LENGTH = 15
MAX_CHUNK_LENGTH = 150


def split_text_for_streaming(text: str) -> list[str]:
    """
    Tách văn bản thành các câu/cụm từ ngắn để phục vụ TTS streaming.

    Chiến lược:
    1. Tách theo dấu câu: . ! ? ; , (giữ lại dấu câu ở cuối câu)
    2. Nếu một đoạn câu dài hơn MAX_CHUNK_LENGTH (không có dấu câu), chia theo ranh giới từ
    3. Gộp các câu quá ngắn (< MIN_CHUNK_LENGTH ký tự) với câu tiếp theo
    4. Trả về danh sách câu đã tối ưu
    """
    if not text or not text.strip():
        return []

    max_chunk_length = globals().get("MAX_CHUNK_LENGTH", 150)
    min_chunk_length = globals().get("MIN_CHUNK_LENGTH", 15)

    def _split_long_part(part: str, max_len: int) -> list[str]:
        words = part.split()
        if not words:
            return []
        res: list[str] = []
        curr: list[str] = []
        curr_len = 0
        for w in words:
            w_len = len(w) + (1 if curr else 0)
            if curr_len + w_len > max_len and curr:
                res.append(" ".join(curr))
                curr = [w]
                curr_len = len(w)
            else:
                curr.append(w)
                curr_len += w_len
        if curr:
            res.append(" ".join(curr))
        return res

    # Bước 1: Tách theo dấu kết thúc câu (giữ lại dấu câu)
    raw_parts = re.split(r'(?<=[.!?;,])\s+', text.strip())

    # Bước 2: Giới hạn độ dài từng phân đoạn
    bounded_parts: list[str] = []
    for p in raw_parts:
        p = p.strip()
        if not p:
            continue
        if len(p) > max_chunk_length:
            bounded_parts.extend(_split_long_part(p, max_chunk_length))
        else:
            bounded_parts.append(p)

    # Bước 3: Gộp câu quá ngắn
    chunks: list[str] = []
    buffer = ""

    for part in bounded_parts:
        part = part.strip()
        if not part:
            continue

        if buffer:
            buffer += " " + part
        else:
            buffer = part

        if len(buffer) >= min_chunk_length:
            chunks.append(buffer)
            buffer = ""

    # Đuôi còn sót
    if buffer:
        if chunks:
            chunks[-1] += " " + buffer  # Gộp vào câu cuối
        else:
            chunks.append(buffer)

    return chunks
