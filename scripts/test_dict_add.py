import sys
sys.path.insert(0, "backend")
from dotenv import load_dotenv
load_dotenv("backend/.env")
import pyotp, httpx
from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import _decrypt_mfa_secret

with SessionLocal() as db:
    admin = db.query(User).filter(User.username == "admin").first()
    totp = pyotp.TOTP(_decrypt_mfa_secret(admin))
    otp = totp.now()

r = httpx.post("http://127.0.0.1:8000/admin/login", data={"username": "admin", "password": "AdminSecure@2026", "otp": otp})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Add dictionary item
r_add = httpx.post("http://127.0.0.1:8000/admin/dictionary", headers=headers, json={
    "source_text": "Trí tuệ nhân tạo",
    "translated_text": "Artificial Intelligence",
    "source_lang": "vi",
    "target_lang": "en"
})
print("Add status:", r_add.status_code, r_add.json())

# Query dictionary
r_list = httpx.get("http://127.0.0.1:8000/admin/dictionary", headers=headers)
print("Dictionary entries:", r_list.json())
