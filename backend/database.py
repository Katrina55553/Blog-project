import os
from collections.abc import Generator
from urllib.parse import unquote, urlparse

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL as EngineURL
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://blog:blog@localhost:5432/blog")

_parsed = urlparse(DATABASE_URL)

engine_url = EngineURL.create(
    "postgresql+psycopg2",
    username=unquote(_parsed.username) if _parsed.username else None,
    password=unquote(_parsed.password) if _parsed.password else None,
    host=_parsed.hostname,
    port=_parsed.port,
    database=_parsed.path.lstrip("/") or "blog",
)

engine = create_engine(engine_url, connect_args={"client_encoding": "utf8"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def ensure_schema():
    """Create tables and apply lightweight migrations."""
    # PostgreSQL 15+ 默认撤销了 public schema 的 CREATE 权限，需要显式授权。
    # 云数据库（RDS、Supabase 等）可能不允许 GRANT，失败时只警告不崩溃。
    try:
        with engine.begin() as conn:
            conn.execute(text("GRANT CREATE ON SCHEMA public TO CURRENT_USER"))
    except Exception:
        import logging
        logging.getLogger("blog").warning(
            "无法在 public schema 上授权 CREATE（云数据库通常已预先配置好权限），跳过"
        )

    Base.metadata.create_all(bind=engine)

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
