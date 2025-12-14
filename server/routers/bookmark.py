from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from models import User, Bookmark, SyncLog, get_db
from auth import get_current_user
from sync import smart_merge

router = APIRouter(prefix="/api", tags=["bookmark"])

class BookmarkItem(BaseModel):
    id: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    folderPath: Optional[str] = None
    dateAdded: Optional[int] = None
    deleted: Optional[bool] = False

class SyncRequest(BaseModel):
    bookmarks: List[BookmarkItem]

class SyncResponse(BaseModel):
    success: bool
    added: int
    updated: int
    deleted: int
    conflicts: int
    bookmarks: List[BookmarkItem]
    last_sync_at: str

class StatusResponse(BaseModel):
    logged_in: bool
    email: Optional[str]
    last_sync_at: Optional[str]
    bookmark_count: int
    sync_count: int

@router.post("/sync", response_model=SyncResponse)
async def sync_bookmarks(
    req: SyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 转换为字典列表
    local_bookmarks = [bm.model_dump() for bm in req.bookmarks]
    
    # 执行智能合并
    result = smart_merge(db, current_user.id, local_bookmarks)
    
    # 更新用户最后同步时间
    current_user.last_sync_at = datetime.utcnow()
    db.commit()
    
    return SyncResponse(
        success=True,
        added=result.added,
        updated=result.updated,
        deleted=result.deleted,
        conflicts=result.conflicts,
        bookmarks=[BookmarkItem(**bm) for bm in result.merged_bookmarks],
        last_sync_at=current_user.last_sync_at.isoformat()
    )

@router.get("/bookmarks", response_model=List[BookmarkItem])
async def get_bookmarks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bookmarks = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.deleted_at.is_(None)
    ).all()
    
    return [
        BookmarkItem(
            id=bm.chrome_id or str(bm.id),
            url=bm.url,
            title=bm.title,
            folderPath=bm.folder_path,
            dateAdded=int(bm.created_at.timestamp() * 1000) if bm.created_at else None
        )
        for bm in bookmarks
    ]

@router.get("/status", response_model=StatusResponse)
async def get_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bookmark_count = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.deleted_at.is_(None)
    ).count()
    
    sync_count = db.query(SyncLog).filter(
        SyncLog.user_id == current_user.id
    ).count()
    
    return StatusResponse(
        logged_in=True,
        email=current_user.email,
        last_sync_at=current_user.last_sync_at.isoformat() if current_user.last_sync_at else None,
        bookmark_count=bookmark_count,
        sync_count=sync_count
    )
