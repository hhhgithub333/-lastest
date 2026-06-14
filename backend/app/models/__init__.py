from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# 数据库
DATABASE_URL = "sqlite:///./tts.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# database.py
# ORM模型
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    engine = Column(String(50), default="qwen")
    voice = Column(String(100), default="Cherry")
    speed = Column(Float, default=1.0)
    captured_text = Column(Text, nullable=True)

# chemas.py
class UserCreate(BaseModel): username: str; password: str
class UserLogin(BaseModel): username: str; password: str
class UserSettingsUpdate(BaseModel): engine: str = None; voice: str = None; speed: float = None
class UserSettingsResponse(BaseModel): engine: str; voice: str; speed: float

# 密码与JWT
pwd_context = CryptContext(schemes=["pbkdf2_sha256"])
SECRET_KEY = "my-secret-key"
ALGORITHM = "HS256"
def get_password_hash(password): return pwd_context.hash(password)
def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)
def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=7)
    return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()