import sys
sys.stdout.reconfigure(encoding='utf-8')
import httpx

BACKEND_HTTP = "http://127.0.0.1:8000"

with httpx.Client(base_url=BACKEND_HTTP, timeout=10.0) as client:
    r = client.post("/api/session/guest")
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Flag translation
    payload = {
        "source_text": "Cửa hàng an nhiên giảm giá 12% cho đèn bản trong tuần này. Người kiểm tra xác nhận vào đầu giờ sáng thứ hai.",
        "translated_text": "The natural light store is offering a 12% discount on the original lights this week. The examiner confirmed it early Monday morning.",
        "source_lang": "vi",
        "target_lang": "en",
        "input_mode": "voice"
    }
    r_flag = client.post("/api/flag-translation", json=payload, headers=headers)
    print("Flag response status:", r_flag.status_code, r_flag.text)
