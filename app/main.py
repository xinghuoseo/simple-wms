from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .database import Base, engine
from .routers import auth, issues, materials, purchases, suppliers, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="仓库管理系统", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(materials.router)
app.include_router(suppliers.router)
app.include_router(purchases.router)
app.include_router(issues.router)


@app.on_event("startup")
def init_admin():
    """首次启动自动创建默认管理员 admin/admin123"""
    from sqlalchemy.orm import Session

    from .auth import hash_password
    from .database import SessionLocal
    from .models import User

    with SessionLocal() as db:  # type: Session
        if db.query(User).filter(User.username == "admin").first() is None:
            db.add(User(username="admin", password_hash=hash_password("admin123"), real_name="管理员"))
            db.commit()


# 托管前端静态文件（nginx 全部反代到后端，由后端直接返回页面）
_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

if os.path.isdir(_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        """前端路由 / 静态文件兜底：有文件返回文件，否则返回 index.html"""
        file_path = os.path.join(_DIST, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_DIST, "index.html"))
