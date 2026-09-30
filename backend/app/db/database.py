from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Đường dẫn file SQLite lưu tại thư mục data (cùng chỗ với translation_memory.json)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

from app.core.auth_settings import get_auth_settings

SQLALCHEMY_DATABASE_URL = get_auth_settings().DATABASE_URL
database_url = make_url(SQLALCHEMY_DATABASE_URL)
if database_url.get_backend_name() == "sqlite" and database_url.database and database_url.database != ":memory:":
    # Resolve relative paths from backend, independent of the launching shell.
    if not os.path.isabs(database_url.database):
        database_url = database_url.set(database=os.path.abspath(os.path.join(BASE_DIR, database_url.database)))
    SQLALCHEMY_DATABASE_URL = database_url

if database_url.get_backend_name() == "sqlite":
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # Đối với PostgreSQL (Supabase)
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency để sử dụng trong FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
