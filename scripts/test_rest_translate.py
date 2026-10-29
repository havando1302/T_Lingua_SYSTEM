import io
import time
import httpx
import numpy as np
import scipy.io.wavfile
import soundfile as sf

BACKEND_HTTP = "http://127.0.0.1:8000"

def test_rest_translate():
    with httpx.Client(base_url=BACKEND_HTTP, timeout=30.0) as client:
        r = client.post("/api/session/guest")
        guest = r.json()
        token = guest["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        wav_path = "outputs/am_thanh/001_FRESH_VI_EN_001.wav"
        data, sr = sf.read(wav_path)
        # Convert float to int16 PCM WAV
        data_int16 = (np.clip(data, -1.0, 1.0) * 32767).astype(np.int16)
        bio = io.BytesIO()
        sf.write(bio, data_int16, 16000, subtype='PCM_16', format='WAV')
        bio.seek(0)

        t0 = time.perf_counter()
        files = {"file": ("test.wav", bio.read(), "audio/wav")}
        data_form = {"source_lang": "vi", "target_lang": "en"}
        r2 = client.post("/translate", files=files, data=data_form, headers=headers)
        elapsed = (time.perf_counter() - t0) * 1000

        print(f"Status: {r2.status_code}, Elapsed: {elapsed:.1f}ms")
        print("Response:", r2.json())

test_rest_translate()
