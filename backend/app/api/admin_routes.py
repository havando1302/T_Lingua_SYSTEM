from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
import csv
import io
import openpyxl
from pydantic import BaseModel
from typing import List, Optional
import os
import psutil
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.db.database import get_db
from app.db.models import User, TranslationLog, ApiKey, SystemSetting
from app.services import translation_memory as tm

# Cấu hình JWT
SECRET_KEY = "super_secret_key_translator_admin" # Trong thực tế nên lấy từ env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 ngày

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")

router = APIRouter(prefix="/admin", tags=["Admin"])

# --- Models ---
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "employee"

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    
    model_config = {"from_attributes": True}

class ApiKeyCreate(BaseModel):
    name: str

class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key: str
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}

class SettingUpdate(BaseModel):
    value: str

class SettingResponse(BaseModel):
    id: int
    key: str
    value: str
    description: str
    
    model_config = {"from_attributes": True}

class DictionaryItem(BaseModel):
    source_text: str
    translated_text: str


# --- Utils ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Yêu cầu quyền Admin")
    return current_user

# --- AUTH ---
@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tài khoản hoặc mật khẩu",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# --- USER MANAGEMENT ---
@router.get("/users", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username đã tồn tại")
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, password_hash=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "superadmin":
        raise HTTPException(status_code=403, detail="Không thể xóa superadmin")
    db.delete(user)
    db.commit()
    return {"ok": True}

# --- DASHBOARD / METRICS ---
@router.get("/metrics/dashboard")
def get_dashboard_metrics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_translations = db.query(TranslationLog).count()
    flagged_translations = db.query(TranslationLog).filter(TranslationLog.is_flagged == True).count()
    
    # Calculate average latency
    avg_latency = db.query(func.avg(TranslationLog.latency)).scalar() or 0.0
    
    # Count unique clients
    unique_clients = db.query(func.count(func.distinct(TranslationLog.client_id))).scalar() or 0
    
    return {
        "total_translations": total_translations,
        "flagged_translations": flagged_translations,
        "avg_latency": round(avg_latency, 3),
        "unique_clients": unique_clients
    }

# --- LOGS / QA ---
@router.get("/quality/logs")
def get_quality_logs(search: str = None, flagged_only: bool = False, skip: int = 0, limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(TranslationLog)
    if flagged_only:
        query = query.filter(TranslationLog.is_flagged == True)
    if search:
        query = query.filter(TranslationLog.source_text.ilike(f"%{search}%") | TranslationLog.translated_text.ilike(f"%{search}%"))
    logs = query.order_by(TranslationLog.id.desc()).offset(skip).limit(limit).all()
    return logs

class ResolveLogRequest(BaseModel):
    corrected_text: str

@router.post("/quality/logs/{log_id}/resolve")
def resolve_log(log_id: int, req: ResolveLogRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    log = db.query(TranslationLog).filter(TranslationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    # Cập nhật DB
    log.is_flagged = False
    log.translated_text = req.corrected_text
    db.commit()
    
    # Thêm thẳng vào Translation Memory để dạy AI (lưu vào Global namespace 'default')
    tm.add(log.source_text, req.corrected_text, client_id="default")
    
    return {"ok": True, "message": "Đã giải quyết và thêm vào Từ điển"}

# --- SYSTEM & HARDWARE ---
@router.get("/system/status")
def get_system_status(user: User = Depends(get_current_user)):
    cpu_percent = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu_usage": cpu_percent,
        "ram_usage": ram.percent,
        "ram_total": round(ram.total / (1024**3), 2), # GB
        "disk_usage": disk.percent,
        "disk_total": round(disk.total / (1024**3), 2)
    }

# --- ANALYTICS TIMESERIES ---
@router.get("/metrics/timeseries")
def get_metrics_timeseries(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Lấy dữ liệu 7 ngày gần nhất
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    logs = db.query(TranslationLog).filter(TranslationLog.created_at >= seven_days_ago).all()
    
    # Gom nhóm theo ngày
    daily_stats = {}
    for log in logs:
        day_str = log.created_at.strftime("%Y-%m-%d")
        if day_str not in daily_stats:
            daily_stats[day_str] = {"date": day_str, "requests": 0, "avg_latency": 0.0}
        daily_stats[day_str]["requests"] += 1
        # Cộng dồn latency để tính trung bình sau
        daily_stats[day_str]["avg_latency"] += (log.latency or 0)
        
    result = []
    for day, stats in daily_stats.items():
        if stats["requests"] > 0:
            stats["avg_latency"] = round(stats["avg_latency"] / stats["requests"], 3)
        result.append(stats)
    
    # Sắp xếp theo ngày tăng dần
    result.sort(key=lambda x: x["date"])
    
    if not result:
        # Trả về dữ liệu mẫu nếu chưa có data để test UI
        return [
            {"date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"), "requests": 10 + i*5, "avg_latency": 0.5 + (i*0.1)}
            for i in range(6, -1, -1)
        ]
        
    return result

# --- API KEYS ---
@router.get("/apikeys", response_model=List[ApiKeyResponse])
def get_api_keys(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(ApiKey).all()

@router.post("/apikeys", response_model=ApiKeyResponse)
def create_api_key(req: ApiKeyCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    import secrets
    new_key = secrets.token_hex(16)
    db_key = ApiKey(name=req.name, key=new_key)
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key

@router.delete("/apikeys/{key_id}")
def delete_api_key(key_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    db_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not db_key:
        raise HTTPException(status_code=404, detail="Key not found")
    db.delete(db_key)
    db.commit()
    return {"ok": True}

# --- SETTINGS ---
@router.get("/settings", response_model=List[SettingResponse])
def get_settings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(SystemSetting).all()

@router.put("/settings/{setting_key}", response_model=SettingResponse)
def update_setting(setting_key: str, req: SettingUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    setting = db.query(SystemSetting).filter(SystemSetting.key == setting_key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    setting.value = req.value
    db.commit()
    db.refresh(setting)
    return setting

# --- DICTIONARY (TRANSLATION MEMORY) ---
@router.get("/dictionary")
def get_dictionary(user: User = Depends(get_current_user)):
    data = tm.get_all("default")
    # Trả về danh sách object để dễ hiển thị
    return [{"source_text": k, "translated_text": v} for k, v in data.items()]

@router.post("/dictionary")
def add_dictionary_item(item: DictionaryItem, user: User = Depends(get_current_user)):
    success = tm.add(item.source_text, item.translated_text, client_id="default")
    if not success:
        raise HTTPException(status_code=400, detail="Invalid data")
    return {"ok": True}

@router.post("/dictionary/upload")
async def upload_dictionary_csv(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file CSV hoặc Excel (.xlsx)")
    
    contents = await file.read()
    added = 0

    if filename.endswith('.csv'):
        try:
            text = contents.decode('utf-8-sig')
        except Exception:
            raise HTTPException(status_code=400, detail="File CSV phải có định dạng UTF-8")
        
        reader = csv.reader(io.StringIO(text))
        for row in reader:
            if len(row) >= 2:
                source = str(row[0]).strip()
                target = str(row[1]).strip()
                if source and target:
                    tm.add(source, target, client_id="default")
                    added += 1
    else:
        # Excel (.xlsx)
        try:
            wb = openpyxl.load_workbook(filename=io.BytesIO(contents), data_only=True)
            ws = wb.active
            for row in ws.iter_rows(values_only=True):
                if row and len(row) >= 2:
                    source = str(row[0]).strip() if row[0] is not None else ""
                    target = str(row[1]).strip() if row[1] is not None else ""
                    if source and target:
                        tm.add(source, target, client_id="default")
                        added += 1
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Không thể đọc file Excel: {str(e)}")
                
    return {"ok": True, "added": added}

@router.delete("/dictionary/{source_text}")
def delete_dictionary_item(source_text: str, user: User = Depends(get_current_user)):
    import urllib.parse
    source_text = urllib.parse.unquote(source_text)
    success = tm.delete(source_text, client_id="default")
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}
