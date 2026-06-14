from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

DATABASE_URL = "sqlite:///./tts.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(200), nullable=False)
    email = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)  # 新增：上次登录时间

    # 一对一关联用户设置
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # TTS 相关设置
    engine = Column(String(50), default="qwen")         # 上次选中的引擎
    voice = Column(String(100), default="Cherry")       # 上次选中的音色
    speed = Column(Float, default=1.0)                  # 播放倍速

    # 参考音频路径（文件存磁盘，此处存路径字符串）
    reference_audio_path = Column(String(500), nullable=True)

    # 上次捕获的文本内容
    captured_text = Column(Text, nullable=True)

    # 更新时间
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 关联到用户
    user = relationship("User", back_populates="settings")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 创建表
Base.metadata.create_all(bind=engine)
