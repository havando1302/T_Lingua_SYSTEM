import asyncio
import json
import time
import httpx
import websockets
import numpy as np
import scipy.io.wavfile

BACKEND_HTTP = "http://127.0.0.1:8000"
BACKEND_WS = "ws://127.0.0.1:8000/ws/realtime"

async def test_single_sample():
    async with httpx.AsyncClient(base_url=BACKEND_HTTP, timeout=10.0) as client:
        r = await client.post("/api/session/guest")
        guest = r.json()
        token = guest["access_token"]
        owner_id = guest["owner_id"]

    wav_path = "outputs/am_thanh/001_FRESH_VI_EN_001.wav"
    sr, audio = scipy.io.wavfile.read(wav_path)
    if audio.dtype == np.float32 or audio.dtype == np.float64:
        pcm_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    else:
        pcm_int16 = audio.astype(np.int16)
    pcm_bytes = pcm_int16.tobytes()

    print(f"Loaded {wav_path}: {len(pcm_bytes)} bytes, sr={sr}, duration={len(audio)/sr:.2f}s")

    async with websockets.connect(BACKEND_WS) as ws:
        # Config
        await ws.send(json.dumps({
            "type": "config",
            "access_token": token,
            "sample_rate": 16000,
            "channels": 1,
            "sample_width": 2,
            "source_lang": "vi",
            "target_lang": "eng_Latn"
        }))
        auth_resp = json.loads(await ws.recv())
        print("Auth response:", auth_resp)

        turn_id = f"test-001-{int(time.time()*1000)}"
        t0 = time.perf_counter()
        await ws.send(json.dumps({
            "type": "start_turn",
            "turn_id": turn_id,
            "speaker": "me",
            "source_lang": "vi",
            "target_lang": "eng_Latn"
        }))
        await ws.recv() # turn_started

        # Stream audio chunks (3200 bytes = 100ms)
        chunk_size = 3200
        for i in range(0, len(pcm_bytes), chunk_size):
            await ws.send(pcm_bytes[i:i+chunk_size])
            await asyncio.sleep(0.005)

        t_stream_done = time.perf_counter()
        await ws.send(json.dumps({"type": "end_turn", "turn_id": turn_id}))

        stt_text = ""
        trans_text = ""
        tts_chunks = 0
        t_stt = 0
        t_trans = 0
        t_tts = 0

        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=15.0)
                msg = json.loads(raw)
                mtype = msg.get("type")
                now = time.perf_counter()
                if mtype == "stt":
                    stt_text = msg.get("data", {}).get("text", "")
                    t_stt = (now - t_stream_done) * 1000
                    print(f"[{t_stt:.1f}ms] STT: {stt_text}")
                elif mtype == "translation":
                    trans_text = msg.get("data", {}).get("translated_text", "")
                    t_trans = (now - t_stream_done) * 1000
                    print(f"[{t_trans:.1f}ms] Translation: {trans_text}")
                elif mtype == "audio_chunk":
                    tts_chunks += 1
                    if tts_chunks == 1:
                        t_tts = (now - t_stream_done) * 1000
                        print(f"[{t_tts:.1f}ms] First TTS chunk received")
                if stt_text and trans_text and tts_chunks >= 1:
                    break
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                break

        total_time = (time.perf_counter() - t0) * 1000
        print(f"Total time: {total_time:.1f}ms, TTS chunks: {tts_chunks}")

asyncio.run(test_single_sample())
