"""数据库连接。本地 SQLite / 线上 Postgres 靠 DATABASE_URL 切换,代码不用改。"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

# SQLite 需要这个参数才能在多线程的 FastAPI 里用
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入:每个请求一个 session,用完自动关。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
