from typing import List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from models import Bookmark, SyncLog, SyncAction

class SyncResult:
    def __init__(self):
        self.added = 0
        self.updated = 0
        self.deleted = 0
        self.conflicts = 0
        self.merged_bookmarks: List[Dict] = []

def smart_merge(
    db: Session,
    user_id: int,
    local_bookmarks: List[Dict[str, Any]]
) -> SyncResult:
    """
    智能合并书签
    策略:
    - 新增: 云端/本地独有的书签 → 合并保留
    - 修改: 同 URL 不同标题 → 取最新
    - 删除: 本地标记删除 → 云端也删除
    """
    result = SyncResult()
    
    # 获取云端书签 (未删除的)
    cloud_bookmarks = db.query(Bookmark).filter(
        Bookmark.user_id == user_id,
        Bookmark.deleted_at.is_(None)
    ).all()
    
    # 建立云端 URL 索引
    cloud_by_url: Dict[str, Bookmark] = {}
    for bm in cloud_bookmarks:
        if bm.url:
            cloud_by_url[bm.url] = bm
    
    # 建立本地 URL 索引
    local_by_url: Dict[str, Dict] = {}
    for bm in local_bookmarks:
        url = bm.get("url")
        if url:
            local_by_url[url] = bm
    
    # 处理本地书签
    for local_bm in local_bookmarks:
        url = local_bm.get("url")
        if not url:
            continue
        
        title = local_bm.get("title", "")
        folder_path = local_bm.get("folderPath", "")
        chrome_id = local_bm.get("id", "")
        is_deleted = local_bm.get("deleted", False)
        local_updated = local_bm.get("dateAdded", 0)
        
        if url in cloud_by_url:
            cloud_bm = cloud_by_url[url]
            
            if is_deleted:
                # 本地删除 → 标记云端删除
                cloud_bm.deleted_at = datetime.utcnow()
                result.deleted += 1
            else:
                # 比较更新时间，取最新
                cloud_updated = cloud_bm.updated_at.timestamp() * 1000 if cloud_bm.updated_at else 0
                
                if local_updated > cloud_updated:
                    # 本地更新
                    cloud_bm.title = title
                    cloud_bm.folder_path = folder_path
                    cloud_bm.chrome_id = chrome_id
                    cloud_bm.updated_at = datetime.utcnow()
                    result.updated += 1
        else:
            if not is_deleted:
                # 本地独有 → 添加到云端
                new_bm = Bookmark(
                    user_id=user_id,
                    chrome_id=chrome_id,
                    url=url,
                    title=title,
                    folder_path=folder_path
                )
                db.add(new_bm)
                result.added += 1
    
    # 检查云端独有的书签 (本地不存在的)
    for url, cloud_bm in cloud_by_url.items():
        if url not in local_by_url:
            # 云端独有，保留 (会返回给客户端)
            pass
    
    db.commit()
    
    # 获取合并后的完整书签列表
    merged = db.query(Bookmark).filter(
        Bookmark.user_id == user_id,
        Bookmark.deleted_at.is_(None)
    ).all()
    
    result.merged_bookmarks = [
        {
            "id": bm.chrome_id or str(bm.id),
            "url": bm.url,
            "title": bm.title,
            "folderPath": bm.folder_path,
            "dateAdded": int(bm.created_at.timestamp() * 1000) if bm.created_at else 0
        }
        for bm in merged
    ]
    
    # 记录同步日志
    log = SyncLog(
        user_id=user_id,
        action=SyncAction.merge,
        added=result.added,
        updated=result.updated,
        deleted=result.deleted,
        conflicts=result.conflicts
    )
    db.add(log)
    db.commit()
    
    return result
