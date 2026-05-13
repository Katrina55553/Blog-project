import os
from collections.abc import Generator
from urllib.parse import urlparse, unquote

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://blog:blog@localhost:5432/blog")

# 将连接参数拆开传递，避免 Windows 上 psycopg2 因 DSN 字符串中的非 ASCII 字符导致编解码错误
_parsed = urlparse(DATABASE_URL)
_connect_args = {
    "host": _parsed.hostname or "localhost",
    "dbname": _parsed.path.lstrip("/") or "blog",
    "client_encoding": "utf8",
}
if _parsed.port:
    _connect_args["port"] = _parsed.port
if _parsed.username:
    _connect_args["user"] = unquote(_parsed.username)
if _parsed.password:
    _connect_args["password"] = unquote(_parsed.password)

engine = create_engine("postgresql+psycopg2://", connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def ensure_schema():
    """Create tables and apply lightweight migrations."""
    # PostgreSQL 15+ 默认撤销了 public schema 的 CREATE 权限，需要显式授权
    with engine.begin() as conn:
        conn.execute(text("GRANT CREATE ON SCHEMA public TO CURRENT_USER"))

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 为已存在的 comments 表添加 parent_id 列（支持嵌套评论）
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE comments ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES comments(id)"
        ))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
