import io
import time
import asyncio
import httpx
import numpy as np
import soundfile as sf

BACKEND_HTTP = "http://127.0.0.1:8000"

def get_pcm_wav(wav_path):
    data, sr = sf.read(wav_path)
    data_int16 = (np.clip(data, -1.0, 1.0) * 32767).astype(np.int16)
    bio = io.BytesIO()
    sf.write(bio, data_int16, 16000, subtype='PCM_16', format='WAV')
    bio.seek(0)
    return bio.read()

async def send_one(client, token, wav_path, src_lang, tgt_lang, idx):
    wav_bytes = get_pcm_wav(wav_path)
    t0 = time.perf_counter()
    files = {"file": (f"test_{idx}.wav", wav_bytes, "audio/wav")}
    data_form = {"source_lang": src_lang, "target_lang": tgt_lang}
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.post("/translate", files=files, data=data_form, headers=headers)
    elapsed = (time.perf_counter() - t0) * 1000
    res = r.json()
    print(f"Sample {idx}: Status {r.status_code}, Latency: {elapsed:.1f}ms | STT: {res.get('original_text', '')[:40]}... | Trans: {res.get('translated_text', '')[:40]}...")
    return elapsed

async def main():
    async with httpx.AsyncClient(base_url=BACKEND_HTTP, timeout=60.0) as client:
        r = await client.post("/api/session/guest")
        token = r.json()["access_token"]
        
        print("Testing 2 concurrent requests...")
        t0 = time.perf_counter()
        results = await asyncio.gather(
            send_one(client, token, "outputs/am_thanh/001_FRESH_VI_EN_001.wav", "vi", "en", 1),
            send_one(client, token, "outputs/am_thanh/002_FRESH_VI_EN_002.wav", "vi", "en", 2)
        )
        total = (time.perf_counter() - t0) * 1000
        print(f"2 concurrent requests total elapsed: {total:.1f}ms (Average per item: {total/2:.1f}ms)")

asyncio.run(main())
