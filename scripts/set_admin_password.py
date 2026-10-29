import sys
sys.path.insert(0, "backend")
from dotenv import load_dotenv
load_dotenv("backend/.env")
from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash, _decrypt_mfa_secret
import pyotp

with SessionLocal() as db:
    admin = db.query(User).filter(User.username == "admin").first()
    admin.password_hash = get_password_hash("AdminSecure@2026")
    db.commit()
    print("Admin password updated to AdminSecure@2026")
    try:
        secret = _decrypt_mfa_secret(admin)
        totp = pyotp.TOTP(secret)
        print("MFA Secret Decrypted:", secret)
        print("Current TOTP code:", totp.now())
    except Exception as e:
        print("MFA decrypt failed:", e)
