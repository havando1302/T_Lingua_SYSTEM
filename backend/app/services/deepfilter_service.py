import sys
import types
import importlib
import numpy as np
import torch
import torchaudio

try:
    common_module = importlib.import_module("torchaudio.backend.common")
    AudioMetaData = common_module.AudioMetaData
except ModuleNotFoundError:
    if not hasattr(torchaudio, "backend"):
        torchaudio.backend = types.ModuleType("torchaudio.backend")
        sys.modules["torchaudio.backend"] = torchaudio.backend
    if not hasattr(torchaudio.backend, "common"):
        common = types.ModuleType("torchaudio.backend.common")
        common.AudioMetaData = getattr(torchaudio, "AudioMetaData", None)
        sys.modules["torchaudio.backend.common"] = common
        torchaudio.backend.common = common

from df.enhance import enhance, init_df

print("Loading DeepFilterNet...")

model, df_state, _ = init_df()

print("DeepFilterNet loaded")


def denoise_numpy(audio_np: np.ndarray) -> np.ndarray:

    audio_tensor = torch.from_numpy(
        audio_np
    ).float()

    with torch.inference_mode():
        enhanced = enhance(
            model,
            df_state,
            audio_tensor.unsqueeze(0)
        )

    return (
        enhanced
        .squeeze(0)
        .cpu()
        .numpy()
        .astype(np.float32)
    )