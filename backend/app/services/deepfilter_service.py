"""
DeepFilterNet noise reduction service with sample rate adaptation.
Model được load bởi ModelManager — service chỉ xử lý inference.
Có thể disable qua ENABLE_DEEPFILTER=false trong .env.
"""
import numpy as np
import torch
from scipy.signal import resample_poly
import logging
import threading
from typing import Any, Callable, cast

logger = logging.getLogger(__name__)
_inference_lock = threading.RLock()


def _get_deepfilter():
    """Lấy DeepFilterNet model + state từ ModelManager."""
    from app.ai.model_manager import model_manager
    if model_manager.deepfilter_model is None:
        return None, None
    return model_manager.deepfilter_model, model_manager.deepfilter_state


def _get_df_sample_rate(df_state: Any) -> int:
    """Xác định sample rate yêu cầu của DeepFilterNet (thường là 48000Hz)."""
    if df_state is None:
        return 48000
    if hasattr(df_state, "sr"):
        sr_attr = df_state.sr
        if callable(sr_attr):
            return int(cast(Callable[[], int], sr_attr)())
        return int(sr_attr)
    return 48000


def denoise_numpy(audio_np: np.ndarray, input_sr: int = 16000,
                  atten_lim_db: float | None = 12.0,
                  min_duration_seconds: float = 0.0) -> np.ndarray:
    """
    Loại bỏ nhiễu nền bằng DeepFilterNet.
    Tự động thích ứng tần số lấy mẫu (16kHz STT <-> 48kHz DeepFilterNet).
    Nếu model không được load hoặc gặp lỗi, an toàn trả về audio gốc.
    """
    if audio_np is None or len(audio_np) == 0:
        return audio_np
    # DeepFilter can soften short Vietnamese consonants after the 16k -> 48k ->
    # 16k round trip. Microphone noise suppression is sufficient for commands;
    # reserve neural denoising for longer utterances where it is more useful.
    if len(audio_np) < int(input_sr * min_duration_seconds):
        return audio_np

    model, df_state = _get_deepfilter()
    if model is None or df_state is None:
        return audio_np

    try:
        from df.enhance import enhance

        df_sr = _get_df_sample_rate(df_state)

        # 1. Resample nếu input_sr khác sample rate của DeepFilterNet (thường 16k -> 48k)
        if input_sr == 16000 and df_sr == 48000:
            df_input = resample_poly(audio_np, 3, 1).astype(np.float32)
        elif input_sr != df_sr:
            # Tỷ lệ tổng quát
            from math import gcd
            g = gcd(input_sr, df_sr)
            df_input = resample_poly(audio_np, df_sr // g, input_sr // g).astype(np.float32)
        else:
            df_input = audio_np.astype(np.float32)

        audio_tensor = torch.from_numpy(df_input).float()

        # 2. Xử lý giảm nhiễu
        # The model and DF state use shared buffers across inference calls.
        with _inference_lock, torch.inference_mode():
            enhanced = enhance(model, df_state, audio_tensor.unsqueeze(0), atten_lim_db=atten_lim_db)

        enhanced_np = (
            enhanced
            .squeeze(0)
            .cpu()
            .numpy()
            .astype(np.float32)
        )

        # 3. Resample ngược lại về input_sr cho Whisper STT (48k -> 16k)
        if input_sr == 16000 and df_sr == 48000:
            output_np = resample_poly(enhanced_np, 1, 3).astype(np.float32)
        elif input_sr != df_sr:
            from math import gcd
            g = gcd(input_sr, df_sr)
            output_np = resample_poly(enhanced_np, input_sr // g, df_sr // g).astype(np.float32)
        else:
            output_np = enhanced_np

        if len(output_np) != len(audio_np) or not np.isfinite(output_np).all():
            raise ValueError("Invalid denoised waveform")
        return output_np
    except Exception as error:
        logger.warning("denoise_failed error_type=%s", type(error).__name__)
        # Khi có bất kỳ lỗi nào trong pipeline giảm nhiễu, fallback về âm thanh gốc
        return audio_np
