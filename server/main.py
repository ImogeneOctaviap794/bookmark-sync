from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from models import init_db, get_db, User
from auth import hash_password
from routers import user, bookmark, admin, analyze

settings = get_settings()

app = FastAPI(
    title="Bookmark Sync API",
    description="云端书签同步服务",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(user.router)
app.include_router(bookmark.router)
app.include_router(admin.router)
app.include_router(analyze.router)

@app.on_event("startup")
async def startup():
    # 初始化数据库
    init_db()
    
    # 创建默认管理员
    db = next(get_db())
    admin_user = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if not admin_user:
        admin_user = User(
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Created admin user: {settings.ADMIN_EMAIL}")
    db.close()

@app.get("/")
async def root():
    return {"message": "Bookmark Sync API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
