import os
import sys

# Thêm thư mục gốc vào path để import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.database import engine, SessionLocal, Base
from app.db.models import User, SystemSetting
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    print("Đang khởi tạo Database...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Kiểm tra xem đã có admin chưa
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        print("Tạo tài khoản Super Admin mặc định: admin / admin123")
        hashed_password = pwd_context.hash("admin123")
        new_admin = User(
            username="admin",
            password_hash=hashed_password,
            role="superadmin"
        )
        db.add(new_admin)
        db.commit()
    else:
        print("Tài khoản Super Admin đã tồn tại.")
        
    # Tạo các cấu hình hệ thống mặc định
    default_settings = [
        {"key": "max_chars_per_request", "value": "5000", "description": "Giới hạn số ký tự mỗi lần dịch"},
        {"key": "enable_cache", "value": "true", "description": "Bật/Tắt bộ nhớ đệm dịch thuật"},
        {"key": "rate_limit_rpm", "value": "60", "description": "Số request tối đa mỗi phút (Rate Limit)"},
    ]
    for s in default_settings:
        existing = db.query(SystemSetting).filter(SystemSetting.key == s["key"]).first()
        if not existing:
            new_setting = SystemSetting(key=s["key"], value=s["value"], description=s["description"])
            db.add(new_setting)
    
    db.commit()
    db.close()
    print("Khởi tạo Database hoàn tất!")

if __name__ == "__main__":
    init_db()
