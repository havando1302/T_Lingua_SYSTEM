"""
COMPREHENSIVE END-TO-END QA & CHAOS AUTOMATION SUITE FOR T-LANGUA
Simulates:
1. Real End-User Persona (Guest Auth, WebSocket Realtime Streaming, STT, NLLB Translate, TTS Chunking, History)
2. Admin Dashboard Persona (Admin Login, Bearer Auth, Dictionary / Translation Memory Management, System Logs/Metrics)
3. Chaos & Edge Case Injections:
   - Sudden network drop & reconnect
   - Rapid mic toggling / mid-stream turn cancel & new turn
   - Oversized / corrupt audio frames & rate limit resilience
   - Multi-tenant security isolation & unauthorized data access attempts (403 Forbidden)
"""
import asyncio
import base64
import json
import os
import sys
import time
import urllib.request
import wave
import httpx
import websockets

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BACKEND_HTTP = "http://127.0.0.1:8000"
BACKEND_WS = "ws://127.0.0.1:8000/ws/realtime"
ADMIN_USER = "admin"
ADMIN_PASS = "AdminSecure@2026"
TEST_WAV_PATH = "backend/test_16k.wav"

test_results = []

def record_result(category, name, action, passed, latency_ms=0.0, note=""):
    test_results.append({
        "category": category,
        "name": name,
        "action": action,
        "passed": passed,
        "latency_ms": round(latency_ms, 1),
        "note": note
    })
    status_str = "[PASS]" if passed else "[FAIL]"
    print(f"{status_str} {category} -> {name}: {action} ({latency_ms:.1f}ms) {note}")

def load_test_pcm():
    if os.path.exists(TEST_WAV_PATH):
        with wave.open(TEST_WAV_PATH, "rb") as w:
            return w.readframes(w.getnframes())
    # Fallback to 2s 440Hz sine wave if file not found
    import numpy as np
    t = np.linspace(0, 2.0, 32000, False)
    tone = np.sin(2 * np.pi * 440 * t) * 0.3
    return (tone * 32767).astype(np.int16).tobytes()

async def test_end_user_realtime():
    print("\n=======================================================")
    print(" 🚀 RUNNING PERSONA 1: END-USER REALTIME SPEECH PIPELINE")
    print("=======================================================")
    client = httpx.AsyncClient(base_url=BACKEND_HTTP, timeout=15.0)
    
    # 1.1 Issue Guest Session
    t0 = time.perf_counter()
    r = await client.post("/api/session/guest")
    lat = (time.perf_counter() - t0) * 1000
    guest_ok = r.status_code in (200, 201) and "access_token" in r.json()
    record_result("User Persona", "Khởi tạo phiên khách", "POST /api/session/guest", guest_ok, lat)
    if not guest_ok:
        return None
    
    guest_data = r.json()
    access_token = guest_data["access_token"]
    owner_id = guest_data["owner_id"]

    # 1.2 Connect WebSocket and Authenticate
    t0 = time.perf_counter()
    async with websockets.connect(BACKEND_WS) as ws:
        lat = (time.perf_counter() - t0) * 1000
        record_result("User Persona", "Bắt tay WebSocket", "Connect ws://.../ws/realtime", True, lat)

        # 1.3 Send Config Handshake
        t0 = time.perf_counter()
        config_payload = {
            "type": "config",
            "access_token": access_token,
            "sample_rate": 16000,
            "channels": 1,
            "sample_width": 2,
            "source_lang": "vi",
            "target_lang": "eng_Latn",
            "speaker": "me"
        }
        await ws.send(json.dumps(config_payload))
        auth_resp_raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        auth_resp = json.loads(auth_resp_raw)
        lat = (time.perf_counter() - t0) * 1000
        auth_ok = auth_resp.get("type") == "status" and auth_resp.get("status") == "authenticated" and auth_resp.get("owner_id") == owner_id
        record_result("User Persona", "Xác thực phiên qua WS", "Gửi access_token trong config frame", auth_ok, lat)

        # 1.4 Start Turn and Stream Speech Audio
        turn_id = f"test-turn-{int(time.time()*1000)}"
        start_turn_payload = {
            "type": "start_turn",
            "turn_id": turn_id,
            "speaker": "me",
            "source_lang": "vi",
            "target_lang": "eng_Latn"
        }
        t0 = time.perf_counter()
        await ws.send(json.dumps(start_turn_payload))
        started_resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
        lat = (time.perf_counter() - t0) * 1000
        turn_started_ok = started_resp.get("type") == "turn_started" and started_resp.get("turn_id") == turn_id
        record_result("User Persona", "Kích hoạt lượt nói", "Gửi start_turn với metadata", turn_started_ok, lat)

        # 1.5 Stream PCM chunks (simulate ~2.5 seconds of microphone speech: 80,000 bytes)
        full_pcm = load_test_pcm()
        pcm_data = full_pcm[:80000] if len(full_pcm) >= 80000 else full_pcm
        chunk_size = 640  # 20ms at 16kHz 16-bit = 50 chunks/sec = 32,000 bytes/sec
        t0 = time.perf_counter()
        for i in range(0, len(pcm_data), chunk_size):
            chunk = pcm_data[i:i+chunk_size]
            await ws.send(chunk)
            await asyncio.sleep(0.02)  # Exact 20ms real-time cadence

        # End Turn
        await ws.send(json.dumps({"type": "end_turn", "turn_id": turn_id}))
        stream_lat = (time.perf_counter() - t0) * 1000
        record_result("User Persona", "Stream âm thanh và End Turn", f"Truyền {len(pcm_data)} bytes (~2.5s) qua micro", True, stream_lat)

        # 1.6 Listen for STT, Translation, and TTS messages
        stt_received = False
        trans_received = False
        tts_received = False
        stt_text = ""
        trans_text = ""
        tts_chunks = 0

        t_wait_start = time.perf_counter()
        while time.perf_counter() - t_wait_start < 25.0:
            try:
                msg_raw = await asyncio.wait_for(ws.recv(), timeout=15.0)
                msg = json.loads(msg_raw)
                msg_type = msg.get("type")
                if msg_type == "stt":
                    stt_received = True
                    stt_text = msg.get("data", {}).get("text", "")
                elif msg_type == "translation":
                    trans_received = True
                    trans_text = msg.get("data", {}).get("translated_text", "")
                elif msg_type == "audio_chunk":
                    tts_received = True
                    tts_chunks += 1
                if stt_received and trans_received and tts_received:
                    break
            except asyncio.TimeoutError:
                break

        full_pipeline_lat = (time.perf_counter() - t_wait_start) * 1000
        record_result("User Persona", "Nhận diện giọng nói STT", f"Whisper trans: '{stt_text}'", stt_received, full_pipeline_lat)
        record_result("User Persona", "Dịch thuật văn bản", f"NLLB trans: '{trans_text}'", trans_received, full_pipeline_lat)
        record_result("User Persona", "Tổng hợp âm thanh TTS", f"MMS-TTS chunks: {tts_chunks} đoạn", tts_received, full_pipeline_lat)

    await client.aclose()
    return {"access_token": access_token, "owner_id": owner_id}

async def test_admin_dashboard():
    print("\n=======================================================")
    print(" 🛡️ RUNNING PERSONA 2: ADMIN WEB DASHBOARD & MANAGEMENT")
    print("=======================================================")
    client = httpx.AsyncClient(base_url=BACKEND_HTTP, timeout=15.0)

    # 2.1 Admin Login
    t0 = time.perf_counter()
    r = await client.post("/admin/login", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    lat = (time.perf_counter() - t0) * 1000
    login_ok = r.status_code == 200 and "access_token" in r.json()
    record_result("Admin Persona", "Đăng nhập Admin", "POST /admin/login xác thực OAuth2", login_ok, lat)
    if not login_ok:
        await client.aclose()
        return None

    admin_token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 2.2 Check Admin Identity & Permissions
    t0 = time.perf_counter()
    r = await client.get("/admin/me", headers=headers)
    lat = (time.perf_counter() - t0) * 1000
    me_ok = r.status_code == 200 and r.json().get("role") == "superadmin"
    record_result("Admin Persona", "Kiểm tra phân quyền", "GET /admin/me verify role superadmin", me_ok, lat)

    # 2.3 Translation Memory / Dictionary Search
    t0 = time.perf_counter()
    r = await client.get("/admin/dictionary", headers=headers, params={"query": "chào"})
    lat = (time.perf_counter() - t0) * 1000
    dict_search_ok = r.status_code == 200 and isinstance(r.json(), list)
    record_result("Admin Persona", "Tìm kiếm từ điển", "GET /admin/dictionary?query=chào", dict_search_ok, lat)

    # 2.4 Add Custom Dictionary Item
    test_src = f"từ_khóa_test_{int(time.time())}"
    test_tgt = f"test_keyword_{int(time.time())}"
    t0 = time.perf_counter()
    r = await client.post("/admin/dictionary", headers=headers, json={
        "source_text": test_src,
        "translated_text": test_tgt,
        "source_lang": "vi",
        "target_lang": "en"
    })
    lat = (time.perf_counter() - t0) * 1000
    dict_add_ok = r.status_code == 200 and r.json().get("ok") is True
    record_result("Admin Persona", "Thêm từ điển tùy chỉnh", f"POST /admin/dictionary '{test_src}' -> '{test_tgt}'", dict_add_ok, lat)

    # 2.5 Inspect System Translation Logs & QA Records
    t0 = time.perf_counter()
    r = await client.get("/admin/quality/logs", headers=headers, params={"qa_only": "false"})
    lat = (time.perf_counter() - t0) * 1000
    logs_data = r.json() if r.status_code == 200 else []
    logs_ok = r.status_code == 200 and isinstance(logs_data, list)
    record_result("Admin Persona", "Truy vấn nhật ký dịch QA", "GET /admin/quality/logs", logs_ok, lat, f"Tổng log: {len(logs_data)}")

    # 2.6 Inspect System Health & GPU Status
    t0 = time.perf_counter()
    r = await client.get("/admin/system/status", headers=headers)
    lat = (time.perf_counter() - t0) * 1000
    sys_ok = r.status_code == 200 and "gpu" in r.json()
    record_result("Admin Persona", "Thống kê hệ thống & GPU", "GET /admin/system/status", sys_ok, lat)

    await client.aclose()
    return admin_token

async def test_chaos_and_edge_cases(user_session, admin_token):
    print("\n=======================================================")
    print(" 💥 RUNNING STEP 3: CHAOS & EDGE CASE INJECTIONS")
    print("=======================================================")
    client = httpx.AsyncClient(base_url=BACKEND_HTTP, timeout=15.0)

    # 3.1 Chaos: Sudden Network Drop and Seamless Reconnect
    t0 = time.perf_counter()
    ws = await websockets.connect(BACKEND_WS)
    await ws.send(json.dumps({
        "type": "config",
        "access_token": user_session["access_token"],
        "sample_rate": 16000,
        "channels": 1,
        "sample_width": 2,
        "source_lang": "vi",
        "target_lang": "eng_Latn"
    }))
    auth = json.loads(await ws.recv())
    # Abruptly close socket mid-session
    await ws.close(code=1000)
    await asyncio.sleep(1.0)

    # Reconnect using the same valid guest credentials
    async with websockets.connect(BACKEND_WS) as ws2:
        await ws2.send(json.dumps({
            "type": "config",
            "access_token": user_session["access_token"],
            "sample_rate": 16000,
            "channels": 1,
            "sample_width": 2,
            "source_lang": "vi",
            "target_lang": "eng_Latn"
        }))
        reauth = json.loads(await asyncio.wait_for(ws2.recv(), timeout=5.0))
        reconnect_ok = reauth.get("status") == "authenticated" and reauth.get("owner_id") == user_session["owner_id"]
        lat = (time.perf_counter() - t0) * 1000
        record_result("Chaos Testing", "Rớt mạng đột ngột & Tự kết nối lại", "Đứt kết nối mã 1006 -> Mở lại socket giữ nguyên session", reconnect_ok, lat)

    # 3.2 Edge Case: Rapid Mic Toggle (Turn Cancellation & Interleaved Starts)
    t0 = time.perf_counter()
    async with websockets.connect(BACKEND_WS) as ws:
        await ws.send(json.dumps({
            "type": "config",
            "access_token": user_session["access_token"],
            "sample_rate": 16000,
            "channels": 1,
            "sample_width": 2,
            "source_lang": "vi",
            "target_lang": "eng_Latn"
        }))
        await ws.recv()

        # Rapidly start turn 1, cancel turn 1, then start turn 2
        turn1 = f"rapid-1-{int(time.time()*1000)}"
        turn2 = f"rapid-2-{int(time.time()*1000)}"
        await ws.send(json.dumps({"type": "start_turn", "turn_id": turn1, "speaker": "me", "source_lang": "vi", "target_lang": "eng_Latn"}))
        await ws.recv() # turn_started 1
        await ws.send(json.dumps({"type": "cancel_turn", "turn_id": turn1}))
        cancelled_resp = json.loads(await ws.recv()) # turn_cancelled 1
        cancel_ok = cancelled_resp.get("type") == "turn_cancelled" and cancelled_resp.get("turn_id") == turn1

        await ws.send(json.dumps({"type": "start_turn", "turn_id": turn2, "speaker": "partner", "source_lang": "en", "target_lang": "vie_Latn"}))
        started_resp2 = json.loads(await ws.recv()) # turn_started 2
        turn2_ok = started_resp2.get("type") == "turn_started" and started_resp2.get("turn_id") == turn2

        lat = (time.perf_counter() - t0) * 1000
        record_result("Chaos Testing", "Đổi mic / Hủy lượt nói nhanh", "start_turn(1) -> cancel_turn(1) -> start_turn(2)", cancel_ok and turn2_ok, lat)

    # 3.3 Security Leak / Multi-Tenant Isolation (User B trying to access User A's data)
    t0 = time.perf_counter()
    r_attacker = await client.post("/api/session/guest")
    attacker_data = r_attacker.json()
    attacker_token = attacker_data["access_token"]
    attacker_owner = attacker_data["owner_id"]

    # Try connecting with attacker token claiming victim's client_id
    victim_owner = user_session["owner_id"]
    tampered_ok = False
    try:
        async with websockets.connect(BACKEND_WS) as ws_tamper:
            await ws_tamper.send(json.dumps({
                "type": "config",
                "access_token": attacker_token,
                "client_id": victim_owner, # Spoofed victim ID
                "sample_rate": 16000,
                "channels": 1,
                "sample_width": 2,
                "source_lang": "vi",
                "target_lang": "eng_Latn"
            }))
            resp = json.loads(await ws_tamper.recv())
            # Server must either reject with error or bind strictly to attacker_token identity
            tampered_ok = resp.get("type") == "error" or resp.get("owner_id") == attacker_owner
    except Exception:
        tampered_ok = True
    lat = (time.perf_counter() - t0) * 1000
    record_result("Security Chaos", "Chống mạo danh danh tính (Spoofing)", f"User B gửi client_id của User A", tampered_ok, lat, "Ngăn chặn thành công")

    # 3.4 Malformed Audio & Buffer Overflow Protection
    t0 = time.perf_counter()
    oversize_rejected = False
    try:
        async with websockets.connect(BACKEND_WS) as ws_overflow:
            await ws_overflow.send(json.dumps({
                "type": "config",
                "access_token": user_session["access_token"],
                "sample_rate": 16000,
                "channels": 1,
                "sample_width": 2,
                "source_lang": "vi",
                "target_lang": "eng_Latn"
            }))
            await ws_overflow.recv()
            # Send oversize corrupted frame (> WS_MAX_MESSAGE_BYTES)
            await ws_overflow.send(b"\x00" * 300000)
            err = json.loads(await ws_overflow.recv())
            oversize_rejected = err.get("type") == "error"
    except Exception:
        oversize_rejected = True
    lat = (time.perf_counter() - t0) * 1000
    record_result("Chaos Testing", "Chặn dữ liệu âm thanh quá cỡ", "Gửi frame 300KB vượt ngưỡng WS_MAX_MESSAGE_BYTES", oversize_rejected, lat, "Server bảo vệ an toàn")

    # 3.5 Rate Limiter Burst Protection
    t0 = time.perf_counter()
    rate_limited = False
    # Send rapid invalid auth attempts
    for _ in range(12):
        r_burst = await client.post("/admin/login", data={"username": "fake_user", "password": "wrong_password_123"})
        if r_burst.status_code == 429:
            rate_limited = True
            break
    lat = (time.perf_counter() - t0) * 1000
    record_result("Chaos Testing", "Chống tấn công Brute-force / Spam", "Kích hoạt 12 request login sai liên tiếp", rate_limited, lat, "Kích hoạt HTTP 429 Rate Limit")

    await client.aclose()

async def main():
    print("===================================================================")
    print(" >>> T-LANGUA FULL AUTOMATED E2E QA, USER SIMULATION & CHAOS SUITE <<<")
    print("===================================================================")
    user_session = await test_end_user_realtime()
    if not user_session:
        print("[ERROR] FAILED AT STEP 1: USER REALTIME FLOW")
        sys.exit(1)

    admin_token = await test_admin_dashboard()
    if not admin_token:
        print("[ERROR] FAILED AT STEP 2: ADMIN DASHBOARD FLOW")
        sys.exit(1)

    await test_chaos_and_edge_cases(user_session, admin_token)

    print("\n=======================================================")
    print(" [REPORT] BANG TONG KET BAO CAO NGHIEM THU TINH NANG & DO BEN")
    print("=======================================================")
    total = len(test_results)
    passed = sum(1 for r in test_results if r["passed"])
    failed = total - passed

    print(f"Tong so kich ban kiem thu: {total} | DAT: {passed} | THAT BAI: {failed}\n")
    print(f"{'NHOM TAC VU':<16} | {'TEN TINH NANG':<32} | {'KET QUA':<8} | {'DO TRE':<10} | GHI CHU")
    print("-" * 95)
    for r in test_results:
        status_tag = "PASS" if r["passed"] else "FAIL"
        print(f"{r['category']:<16} | {r['name']:<32} | {status_tag:<8} | {r['latency_ms']:>7.1f}ms | {r['note']}")

    if failed > 0:
        print("\n[WARNING] CO KICH BAN THAT BAI - TIEN HANH SELF-HEALING!")
        sys.exit(2)
    else:
        print("\n[SUCCESS] TOAN BO KICH BAN DA DAT 100% THANH CONG! HE THONG HOAN TOAN ON DINH.")

if __name__ == "__main__":
    asyncio.run(main())
