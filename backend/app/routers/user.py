from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from ..models.database import get_db, User, UserSettings  # 追加 UserSettings 导入
from ..models.schemas import UserCreate, UserLogin, UserResponse, Token, UserSettingsUpdate, UserSettingsResponse
from ..models.auth import verify_password, get_password_hash, create_access_token


router = APIRouter(prefix="/user", tags=["用户"])


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建新用户
    db_user = User(
        username=user.username,
        password=get_password_hash(user.password),
        email=user.email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 验证密码
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 更新最后登录时间
    db_user.last_login = datetime.utcnow()
    db.commit()

    # 创建 token
    access_token = create_access_token(data={"sub": db_user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }

@router.get("/settings", response_model=UserSettingsResponse)
def get_settings(username: str, db: Session = Depends(get_db)):
    """
    获取用户设置。
    前端在登录成功后调用此接口，将返回的设置覆盖到 TTSStore / TTSManager。
    """
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    settings = db.query(UserSettings).filter(UserSettings.user_id == db_user.id).first()
    if not settings:
        # 用户从未保存过设置，返回默认值
        return UserSettingsResponse(
            engine="qwen",
            voice="Cherry",
            speed=1.0,
            reference_audio_path=None,
            captured_text=None
        )

    return settings


@router.put("/settings")
def save_settings(username: str, settings: UserSettingsUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    db_settings = db.query(UserSettings).filter(UserSettings.user_id == db_user.id).first()

    if not db_settings:
        # 首次保存，创建记录
        db_settings = UserSettings(user_id=db_user.id)
        db.add(db_settings)

    # 只更新传入的非空字段
    if settings.engine is not None:
        db_settings.engine = settings.engine
    if settings.voice is not None:
        db_settings.voice = settings.voice
    if settings.speed is not None:
        db_settings.speed = settings.speed
    if settings.reference_audio_path is not None:
        db_settings.reference_audio_path = settings.reference_audio_path
    if settings.captured_text is not None:
        db_settings.captured_text = settings.captured_text

    db_settings.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "设置已保存"}

