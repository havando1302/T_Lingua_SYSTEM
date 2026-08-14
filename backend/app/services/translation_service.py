import time
import re
import os
import torch
from typing import Optional
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM
)

from app.core.config import (
    DEVICE,
    NLLB_MODEL,
    SOURCE_LANG,
    TARGET_LANG
)

from app.services import translation_memory as tm

print("Đang tải NLLB...")

USE_INT8 = os.getenv("NLLB_INT8", "0") == "1"
USE_BETTER_TRANSFORMER = os.getenv("NLLB_BETTER_TRANSFORMER", "0") == "1"
USE_TORCH_COMPILE = os.getenv("NLLB_TORCH_COMPILE", "0") == "1"

# 1. Khởi tạo Tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    NLLB_MODEL
)

# 2. Khởi tạo Model và đưa vào thiết bị xử lý (CPU/GPU)
if USE_INT8:
    model = AutoModelForSeq2SeqLM.from_pretrained(
        NLLB_MODEL,
        load_in_8bit=True,
        device_map="auto"
    )
else:
    torch_dtype = torch.float16 if DEVICE == "cuda" else None
    model = AutoModelForSeq2SeqLM.from_pretrained(
        NLLB_MODEL,
        torch_dtype=torch_dtype
    ).to(DEVICE)

    # Optional speed tweaks for inference on GPU. Safe no-op on CPU.
    if DEVICE == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

# Avoid max_length vs max_new_tokens warning by clearing default max_length.
try:
    model.generation_config.max_length = None
except Exception:
    pass

if USE_BETTER_TRANSFORMER:
    try:
        # BetterTransformer from optimum is deprecated since Transformers 4.36+.
        # SDPA (Scaled Dot Product Attention) is now natively supported.
        model = model.to_bettertransformer()
        print("Đã bật BetterTransformer (SDPA)")
    except Exception as e:
        print(f"BetterTransformer không khả dụng: {e}")

if USE_TORCH_COMPILE:
    try:
        model = torch.compile(model)
    except Exception as e:
        print(f"torch.compile không khả dụng: {e}")

print("Đã tải xong NLLB")

def _normalize_stt_text(text: str) -> str:
    if not text:
        return text

    # Collapse repeated punctuation and normalize comma spacing from STT artifacts.
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r",\s*,+", ", ", text)
    text = re.sub(r"([,.!?])\1+", r"\1", text)
    return text.strip()


def translate_text(
    text: str,
    context: str = "",
    source_lang: Optional[str] = None,
    target_lang: Optional[str] = None
) -> dict:
    """
    Hàm dịch văn bản: ưu tiên Translation Memory, fallback sang NLLB.
    """
    start = time.time()

    # Normalize noisy STT output before translation.
    text = _normalize_stt_text(text)

    # === BƯỚC 1: Tra cứu Translation Memory trước ===
    tm_result = tm.lookup(text)
    if tm_result is not None:
        latency = round(time.time() - start, 2)
        print(f"[TM TRUNG] \"{text}\" -> \"{tm_result}\" ({latency}s)")
        return {
            "translated_text": tm_result,
            "latency": latency,
            "source": "translation_memory"
        }

    # === BƯỚC 2: Không có trong TM → gọi NLLB model ===
    # Ensure correct source language to prevent hallucinations.
    resolved_source = source_lang or SOURCE_LANG
    resolved_target = target_lang or TARGET_LANG
    tokenizer.src_lang = resolved_source

    # Mã hóa văn bản đầu vào
    inputs = tokenizer(
        text,
        return_tensors="pt"
    ).to(DEVICE)

    # Sinh văn bản dịch (Sử dụng Beam Search để tối ưu chất lượng)
    with torch.inference_mode():
        target_token_id = tokenizer.convert_tokens_to_ids(resolved_target)
        if target_token_id is None:
            raise ValueError(f"Invalid target language: {resolved_target}")

        translated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=target_token_id,
            max_new_tokens=128,
            num_beams=5,
            no_repeat_ngram_size=3,
            early_stopping=True
        )

    # Giải mã token thành văn bản tiếng Anh
    translated = tokenizer.batch_decode(
        translated_tokens,
        skip_special_tokens=True
    )[0]

    translated = translated.lstrip("- ").strip()

    # Tính toán độ trễ (Latency)
    latency = round(
        time.time() - start,
        2
    )

    print(f"[NLLB] \"{text}\" -> \"{translated}\" ({latency}s)")

    return {
        "translated_text": translated,
        "latency": latency,
        "source": "nllb_model"
    }