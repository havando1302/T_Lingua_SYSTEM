"""
Compatibility patches for torchaudio / DeepFilterNet.
Import this module BEFORE any torchaudio-dependent code.

These patches were originally inline in run.py and are extracted
here so they can be applied consistently regardless of entry point
(run.py, Colab notebook, pytest, etc.).
"""
import sys
import types


def apply_torch_patches() -> None:
    """Apply all necessary monkey-patches for torch ecosystem."""

    # --- Patch 1: torch.float8_e8m0fnu ---
    # Some newer DeepFilterNet / torch versions reference this dtype
    # which may not exist in the installed torch build.
    import torch
    if not hasattr(torch, "float8_e8m0fnu"):
        torch.float8_e8m0fnu = torch.float8_e4m3fn

    # --- Patch 2: torchaudio.backend.common.AudioMetaData ---
    # DeepFilterNet imports AudioMetaData from torchaudio.backend.common
    # which was removed in newer torchaudio versions.
    class MockAudioMetaData:
        def __init__(
            self,
            sample_rate: int = 48000,
            num_frames: int = 0,
            num_channels: int = 1,
            bits_per_sample: int = 16,
            encoding: str = "PCM_S",
        ):
            self.sample_rate = sample_rate
            self.num_frames = num_frames
            self.num_channels = num_channels
            self.bits_per_sample = bits_per_sample
            self.encoding = encoding

    # Register mock module into sys.modules
    info_module = types.ModuleType("torchaudio.info")
    info_module.AudioMetaData = MockAudioMetaData
    sys.modules["torchaudio.info"] = info_module

    # Guard against Windows Application Control blocking torchaudio.lib._torchaudio
    try:
        import torchaudio.lib._torchaudio
    except (ImportError, OSError):
        dummy_ext = types.ModuleType("torchaudio.lib._torchaudio")
        sys.modules["torchaudio.lib._torchaudio"] = dummy_ext
        try:
            import transformers.utils.import_utils as _tf_utils
            _tf_utils.is_torchaudio_available = lambda: False
        except Exception:
            pass

    try:
        import torchaudio

        # Ensure torchaudio.backend.common exists
        if not hasattr(torchaudio, "backend"):
            torchaudio.backend = types.ModuleType("torchaudio.backend")
            sys.modules["torchaudio.backend"] = torchaudio.backend

        if not hasattr(torchaudio.backend, "common"):
            common = types.ModuleType("torchaudio.backend.common")
            common.AudioMetaData = MockAudioMetaData
            sys.modules["torchaudio.backend.common"] = common
            torchaudio.backend.common = common

        torchaudio.AudioMetaData = MockAudioMetaData
    except Exception:
        pass

    # --- Patch 3: safe resample ---
    # Guard against extra kwargs that some callers pass.
    try:
        from torchaudio.functional import resample as _original_resample

        def _safe_resample(audio, orig_sr, new_sr, **_kwargs):
            return _original_resample(audio, orig_sr, new_sr)

        import torchaudio.functional
        torchaudio.functional.resample = _safe_resample
    except Exception:
        pass
