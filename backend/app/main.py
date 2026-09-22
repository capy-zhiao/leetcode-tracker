"""FastAPI 应用入口。

跑起来后访问 http://localhost:8000/docs 就能看到自动生成的交互式 API 文档
—— 这是 FastAPI 白送的,portfolio 上很好看。
"""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import llm
from .config import settings
from .database import Base, engine
from .deps import require_api_key
from .routers import mock, problems, review, stats

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用启动时建表(SQLite 本地开发够用;正式迁移该上 Alembic)。"""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="LeetCode Tracker API",
    description="基于记忆曲线(SRS)的 NeetCode 250 刷题追踪器",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health():
    return {
        "status": "ok",
        "llm_enabled": llm.is_enabled(),
        "daily_caps": {"review": settings.daily_review_cap, "new": settings.daily_new_cap},
    }


for r in (problems.router, review.router, stats.router, mock.router):
    app.include_router(r, dependencies=[Depends(require_api_key)])
