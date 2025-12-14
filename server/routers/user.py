from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from models import User, get_db
from auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/api", tags=["user"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    token: str
    email: str
    
class UserInfoResponse(BaseModel):
    id: int
    email: str
    last_sync_at: Optional[str]
    created_at: str

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Check password length
    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码至少6位"
        )
    
    # Check if email exists
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # Create user
    user = User(
        email=req.email,
        password_hash=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate token
    token = create_token(user.id, user.email, user.is_admin)
    
    return TokenResponse(token=token, email=user.email)

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )
    
    token = create_token(user.id, user.email, user.is_admin)
    
    return TokenResponse(token=token, email=user.email)

@router.get("/me", response_model=UserInfoResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserInfoResponse(
        id=current_user.id,
        email=current_user.email,
        last_sync_at=current_user.last_sync_at.isoformat() if current_user.last_sync_at else None,
        created_at=current_user.created_at.isoformat()
    )
