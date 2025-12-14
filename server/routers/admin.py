from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from models import User, Bookmark, SyncLog, UserStatus, get_db
from auth import get_admin_user, hash_password, create_token, verify_password

router = APIRouter(prefix="/admin", tags=["admin"])

class AdminLoginRequest(BaseModel):
    email: str
    password: str

class AdminLoginResponse(BaseModel):
    token: str
    email: str

class StatsResponse(BaseModel):
    total_users: int
    active_users: int
    disabled_users: int
    total_bookmarks: int
    total_syncs: int
    today_syncs: int

class UserListItem(BaseModel):
    id: int
    email: str
    status: str
    is_admin: bool
    bookmark_count: int
    last_sync_at: Optional[str]
    created_at: str

class UserDetailResponse(BaseModel):
    id: int
    email: str
    status: str
    is_admin: bool
    bookmark_count: int
    sync_count: int
    last_sync_at: Optional[str]
    created_at: str
    bookmarks: List[dict]
    recent_syncs: List[dict]

class UpdateUserRequest(BaseModel):
    status: Optional[str] = None
    is_admin: Optional[bool] = None

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(req: AdminLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    token = create_token(user.id, user.email, user.is_admin)
    return AdminLoginResponse(token=token, email=user.email)

@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.status == UserStatus.active).count()
    disabled_users = db.query(User).filter(User.status == UserStatus.disabled).count()
    total_bookmarks = db.query(Bookmark).filter(Bookmark.deleted_at.is_(None)).count()
    total_syncs = db.query(SyncLog).count()
    
    today = datetime.utcnow().date()
    today_syncs = db.query(SyncLog).filter(
        func.date(SyncLog.created_at) == today
    ).count()
    
    return StatsResponse(
        total_users=total_users,
        active_users=active_users,
        disabled_users=disabled_users,
        total_bookmarks=total_bookmarks,
        total_syncs=total_syncs,
        today_syncs=today_syncs
    )

@router.get("/users", response_model=List[UserListItem])
async def list_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    result = []
    for user in users:
        bookmark_count = db.query(Bookmark).filter(
            Bookmark.user_id == user.id,
            Bookmark.deleted_at.is_(None)
        ).count()
        
        result.append(UserListItem(
            id=user.id,
            email=user.email,
            status=user.status.value,
            is_admin=user.is_admin,
            bookmark_count=bookmark_count,
            last_sync_at=user.last_sync_at.isoformat() if user.last_sync_at else None,
            created_at=user.created_at.isoformat()
        ))
    
    return result

@router.get("/user/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    bookmarks = db.query(Bookmark).filter(
        Bookmark.user_id == user_id,
        Bookmark.deleted_at.is_(None)
    ).order_by(Bookmark.created_at.desc()).limit(100).all()
    
    syncs = db.query(SyncLog).filter(
        SyncLog.user_id == user_id
    ).order_by(SyncLog.created_at.desc()).limit(20).all()
    
    return UserDetailResponse(
        id=user.id,
        email=user.email,
        status=user.status.value,
        is_admin=user.is_admin,
        bookmark_count=len(bookmarks),
        sync_count=len(syncs),
        last_sync_at=user.last_sync_at.isoformat() if user.last_sync_at else None,
        created_at=user.created_at.isoformat(),
        bookmarks=[
            {
                "id": bm.id,
                "url": bm.url,
                "title": bm.title,
                "folderPath": bm.folder_path,
                "created_at": bm.created_at.isoformat()
            }
            for bm in bookmarks
        ],
        recent_syncs=[
            {
                "id": s.id,
                "action": s.action.value,
                "added": s.added,
                "updated": s.updated,
                "deleted": s.deleted,
                "created_at": s.created_at.isoformat()
            }
            for s in syncs
        ]
    )

@router.put("/user/{user_id}")
async def update_user(
    user_id: int,
    req: UpdateUserRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if req.status:
        user.status = UserStatus(req.status)
    if req.is_admin is not None:
        user.is_admin = req.is_admin
    
    db.commit()
    return {"success": True}

@router.delete("/user/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    db.delete(user)
    db.commit()
    return {"success": True}
