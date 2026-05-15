# Blog → Forum 改造实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将个人博客系统渐进改造为无版块扁平论坛，所有注册用户可发帖/回复/点赞。

**Architecture:** 渐进改造。Post → Topic，Tag/PostTag 删除，新增 Notification。后端 models→crud→routes 逐层替换，前端 router→views 逐层适配。基础设施（auth、主题、composable）全部复用。

**Tech Stack:** FastAPI + SQLAlchemy + PostgreSQL + Vue 3 + Pinia + Vue Router + ByteMD + marked + highlight.js

---

### Task 1: 数据库迁移

**Files:**
- Create: `backend/migrations/001_blog_to_forum.sql`

- [ ] **Step 1: 编写迁移 SQL**

```sql
-- 001_blog_to_forum.sql
-- 将博客数据模型迁移为论坛数据模型

BEGIN;

-- 1. 重命名 posts → topics
ALTER TABLE posts RENAME TO topics;

-- 2. 删除废弃列
ALTER TABLE topics DROP COLUMN slug;
ALTER TABLE topics DROP COLUMN summary;
ALTER TABLE topics DROP COLUMN status;

-- 3. 添加 view_count
ALTER TABLE topics ADD COLUMN view_count INTEGER DEFAULT 0;

-- 4. 重命名评论外键
ALTER TABLE comments RENAME COLUMN post_id TO topic_id;

-- 5. 删除旧的 likes 表，重建
DROP TABLE IF EXISTS likes;
CREATE TABLE likes (
    user_id INTEGER NOT NULL REFERENCES users(id),
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    PRIMARY KEY (user_id, topic_id)
);

-- 6. 删除 post_tags 和 tags
DROP TABLE IF EXISTS post_tags;
DROP TABLE IF EXISTS tags;

-- 7. 新建 notifications 表
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    type VARCHAR NOT NULL DEFAULT 'reply',
    topic_id INTEGER REFERENCES topics(id),
    comment_id INTEGER REFERENCES comments(id),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. users 扩展
ALTER TABLE users ADD COLUMN topic_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN comment_count INTEGER DEFAULT 0;

COMMIT;
```

- [ ] **Step 2: 执行迁移**

```bash
cd backend
source venv/Scripts/activate
python -c "
from database import engine, ensure_schema
ensure_schema()
with engine.connect() as conn:
    with open('migrations/001_blog_to_forum.sql') as f:
        conn.execute(text(f.read()))
    conn.commit()
print('Migration complete.')
"
```

- [ ] **Step 3: 验证表结构**

```bash
cd backend && source venv/Scripts/activate && python -c "
from database import engine
from sqlalchemy import text
with engine.connect() as conn:
    for t in ['topics', 'comments', 'likes', 'notifications', 'users']:
        cols = conn.execute(text(f\"SELECT column_name FROM information_schema.columns WHERE table_name='{t}'\"))
        print(f'{t}:', [r[0] for r in cols])
"
```

Expected: topics 有 id/title/content/author_id/view_count/created_at/updated_at，无 slug/summary/status。comments 有 topic_id 无 post_id。notifications 表存在。

- [ ] **Step 4: 提交**

```bash
git add backend/migrations/
git commit -m "feat: add blog-to-forum database migration"
```

---

### Task 2: 后端 models.py — Post → Topic，删除 Tag

**Files:**
- Modify: `backend/models.py`

- [ ] **Step 1: 重写 models.py**

将整个文件替换为：

```python
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    avatar = Column(String, default="")
    bio = Column(String, default="")
    github_url = Column(String, default="")
    is_admin = Column(Boolean, default=False)
    topic_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    topics = relationship("Topic", back_populates="author")
    comments = relationship("Comment", back_populates="author")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, default="")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    author = relationship("User", back_populates="topics")
    comments = relationship("Comment", back_populates="topic", cascade="all, delete-orphan")
    likes = relationship("User", secondary="likes")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    topic = relationship("Topic", back_populates="comments")
    author = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side="Comment.id", back_populates="replies")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")

    @property
    def username(self):
        return self.author.username if self.author else ""


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False, default="reply")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# likes table for Topic.likes relationship
likes = Table(
    "likes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("topic_id", Integer, ForeignKey("topics.id"), primary_key=True),
)
```

- [ ] **Step 2: 提交**

```bash
git add backend/models.py
git commit -m "refactor: rename Post to Topic, remove Tag, add Notification model"
```

---

### Task 3: 后端 schemas.py — 适配新模型

**Files:**
- Modify: `backend/schemas.py`

- [ ] **Step 1: 重写 schemas.py**

```python
from datetime import datetime

from pydantic import BaseModel, field_validator


# ── Auth ──

class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User ──

class UserResponse(BaseModel):
    id: int
    username: str
    avatar: str
    bio: str
    github_url: str
    is_admin: bool
    topic_count: int = 0
    comment_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    avatar: str | None = None
    bio: str | None = None
    github_url: str | None = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


# ── Topic ──

class TopicCreate(BaseModel):
    title: str
    content: str = ""


class TopicUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


# ── Comment ──

class CommentCreate(BaseModel):
    content: str
    topic_id: int
    parent_id: int | None = None


class CommentResponse(BaseModel):
    id: int
    content: str
    topic_id: int
    user_id: int
    username: str
    parent_id: int | None = None
    created_at: datetime
    replies: list["CommentResponse"] = []

    model_config = {"from_attributes": True}

    @field_validator("username", mode="before")
    @classmethod
    def extract_username(cls, v):
        return getattr(v, "username", v)


# ── Topic responses ──

class AuthorInfo(BaseModel):
    id: int
    username: str
    avatar: str

    model_config = {"from_attributes": True}


class TopicListResponse(BaseModel):
    id: int
    title: str
    author: AuthorInfo | None = None
    view_count: int = 0
    comment_count: int = 0
    likes_count: int = 0
    last_comment_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TopicDetailResponse(BaseModel):
    id: int
    title: str
    content: str
    author: AuthorInfo | None = None
    view_count: int = 0
    created_at: datetime
    updated_at: datetime
    likes_count: int = 0
    is_liked: bool = False
    comments: list[CommentResponse] = []

    model_config = {"from_attributes": True}


# ── User profile ──

class UserProfileResponse(BaseModel):
    id: int
    username: str
    avatar: str
    bio: str
    github_url: str
    topic_count: int = 0
    comment_count: int = 0
    created_at: datetime
    topics: list[TopicListResponse] = []

    model_config = {"from_attributes": True}


# ── Notification ──

class NotificationResponse(BaseModel):
    id: int
    type: str
    topic_id: int | None = None
    comment_id: int | None = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: 提交**

```bash
git add backend/schemas.py
git commit -m "refactor: update schemas for forum (Topic, Notification, remove Tag)"
```

---

### Task 4: 后端 crud.py — 适配新模型 + 通知 CRUD

**Files:**
- Modify: `backend/crud.py`

- [ ] **Step 1: 重写 crud.py**

```python
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from auth import hash_password
from models import Comment, Notification, Topic, User, likes


# ── User ──

def create_user(db: Session, username: str, password: str) -> User:
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter_by(username=username).first()


def update_user(db: Session, user: User, data: dict) -> User:
    for field in ("avatar", "bio", "github_url"):
        if data.get(field) is not None:
            setattr(user, field, data[field])
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    db.commit()


# ── Topic ──

def create_topic(db: Session, author_id: int, title: str, content: str) -> Topic:
    topic = Topic(title=title, content=content, author_id=author_id)
    db.add(topic)
    # 更新用户发帖计数
    db.query(User).filter_by(id=author_id).update({"topic_count": User.topic_count + 1})
    db.commit()
    db.refresh(topic)
    return topic


def get_topics(db: Session, page: int = 1, size: int = 10, q: str = ""):
    query = db.query(Topic).options(joinedload(Topic.author))
    if q:
        query = query.filter(or_(Topic.title.ilike(f"%{q}%"), Topic.content.ilike(f"%{q}%")))
    total = query.count()
    topics = (
        query.order_by(Topic.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    # 追加每个 topic 的 reply count 和 likes count
    result = []
    for t in topics:
        comment_count = db.query(func.count(Comment.id)).filter_by(topic_id=t.id).scalar()
        like_count = db.query(func.count(likes.c.user_id)).filter(likes.c.topic_id == t.id).scalar()
        last_comment = (
            db.query(Comment).filter_by(topic_id=t.id).order_by(Comment.created_at.desc()).first()
        )
        result.append({
            "id": t.id,
            "title": t.title,
            "author": {"id": t.author.id, "username": t.author.username, "avatar": t.author.avatar} if t.author else None,
            "view_count": t.view_count,
            "comment_count": comment_count,
            "likes_count": like_count,
            "last_comment_at": last_comment.created_at if last_comment else None,
            "created_at": t.created_at,
        })
    return result, total


def get_topic_by_id(db: Session, topic_id: int) -> Topic | None:
    return (
        db.query(Topic)
        .options(
            joinedload(Topic.author),
            joinedload(Topic.comments).joinedload(Comment.author),
            joinedload(Topic.likes),
        )
        .filter_by(id=topic_id)
        .first()
    )


def get_topic_for_edit(db: Session, topic_id: int) -> Topic | None:
    return db.query(Topic).options(joinedload(Topic.author)).filter_by(id=topic_id).first()


def get_topics_by_user(db: Session, user_id: int, page: int = 1, size: int = 10):
    query = db.query(Topic).options(joinedload(Topic.author)).filter_by(author_id=user_id)
    total = query.count()
    topics = (
        query.order_by(Topic.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    result = []
    for t in topics:
        comment_count = db.query(func.count(Comment.id)).filter_by(topic_id=t.id).scalar()
        like_count = db.query(func.count(likes.c.user_id)).filter(likes.c.topic_id == t.id).scalar()
        result.append({
            "id": t.id,
            "title": t.title,
            "author": {"id": t.author.id, "username": t.author.username, "avatar": t.author.avatar} if t.author else None,
            "view_count": t.view_count,
            "comment_count": comment_count,
            "likes_count": like_count,
            "last_comment_at": None,
            "created_at": t.created_at,
        })
    return result, total


def update_topic(db: Session, topic: Topic, data: dict) -> Topic:
    for field in ("title", "content"):
        if data.get(field) is not None:
            setattr(topic, field, data[field])
    db.commit()
    db.refresh(topic)
    return topic


def delete_topic(db: Session, topic: Topic) -> None:
    user_id = topic.author_id
    db.delete(topic)
    db.query(User).filter_by(id=user_id).update({"topic_count": User.topic_count - 1})
    db.commit()


def increment_view_count(db: Session, topic: Topic) -> None:
    topic.view_count = (topic.view_count or 0) + 1
    db.commit()


# ── Like ──

def like_topic(db: Session, user_id: int, topic_id: int) -> dict:
    from sqlalchemy.exc import IntegrityError
    try:
        db.execute(likes.insert().values(user_id=user_id, topic_id=topic_id))
        db.commit()
    except IntegrityError:
        db.rollback()
    count = db.query(func.count(likes.c.user_id)).filter(likes.c.topic_id == topic_id).scalar()
    return {"liked": True, "likes_count": count}


def unlike_topic(db: Session, user_id: int, topic_id: int) -> dict:
    db.execute(likes.delete().where(likes.c.user_id == user_id, likes.c.topic_id == topic_id))
    db.commit()
    count = db.query(func.count(likes.c.user_id)).filter(likes.c.topic_id == topic_id).scalar()
    return {"liked": False, "likes_count": count}


# ── Comment ──

def create_comment(db: Session, user_id: int, topic_id: int, content: str, parent_id: int | None = None) -> Comment:
    if parent_id:
        parent = db.query(Comment).filter_by(id=parent_id, topic_id=topic_id).first()
        if not parent:
            raise ValueError("Parent comment not found under this topic")
    comment = Comment(content=content, topic_id=topic_id, user_id=user_id, parent_id=parent_id)
    db.add(comment)
    # 更新用户评论计数
    db.query(User).filter_by(id=user_id).update({"comment_count": User.comment_count + 1})
    db.commit()
    db.refresh(comment)

    # 发送通知：回复帖子时通知帖子作者（不自通知）
    topic = db.query(Topic).filter_by(id=topic_id).first()
    if topic and topic.author_id != user_id:
        notif = Notification(
            user_id=topic.author_id,
            type="reply",
            topic_id=topic_id,
            comment_id=comment.id,
        )
        db.add(notif)

    # 如果回复的是某人的评论，通知被回复者（不自通知）
    if parent_id and parent and parent.user_id != user_id and parent.user_id != topic.author_id:
        notif = Notification(
            user_id=parent.user_id,
            type="reply",
            topic_id=topic_id,
            comment_id=comment.id,
        )
        db.add(notif)

    db.commit()
    return comment


def get_comment_by_id(db: Session, comment_id: int) -> Comment | None:
    return db.query(Comment).filter_by(id=comment_id).first()


def delete_comment(db: Session, comment: Comment) -> None:
    user_id = comment.user_id
    db.delete(comment)
    db.query(User).filter_by(id=user_id).update({"comment_count": User.comment_count - 1})
    db.commit()


def build_comment_tree(comments: list[Comment]) -> list[dict]:
    lookup = {}
    roots = []
    for c in comments:
        node = {
            "id": c.id,
            "content": c.content,
            "topic_id": c.topic_id,
            "user_id": c.user_id,
            "username": c.username,
            "parent_id": c.parent_id,
            "created_at": c.created_at,
            "replies": [],
        }
        lookup[c.id] = node

    for node in lookup.values():
        pid = node["parent_id"]
        if pid and pid in lookup:
            lookup[pid]["replies"].append(node)
        else:
            roots.append(node)

    return roots


# ── User Profile ──

def get_user_profile(db: Session, username: str) -> dict | None:
    user = db.query(User).filter_by(username=username).first()
    if not user:
        return None
    topics, _ = get_topics_by_user(db, user.id, page=1, size=20)
    return {"user": user, "topics": topics}


# ── Notification ──

def get_notifications(db: Session, user_id: int, page: int = 1, size: int = 20):
    query = db.query(Notification).filter_by(user_id=user_id)
    total = query.count()
    items = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return items, total


def get_unread_notification_count(db: Session, user_id: int) -> int:
    return db.query(func.count(Notification.id)).filter_by(user_id=user_id, is_read=False).scalar()


def mark_notification_read(db: Session, notif_id: int, user_id: int) -> None:
    db.query(Notification).filter_by(id=notif_id, user_id=user_id).update({"is_read": True})
    db.commit()


def mark_all_notifications_read(db: Session, user_id: int) -> None:
    db.query(Notification).filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.commit()
```

- [ ] **Step 2: 提交**

```bash
git add backend/crud.py
git commit -m "refactor: update CRUD for Topic model, add notification functions"
```

---

### Task 5: 后端 main.py — 更新路由

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: 重写 main.py**

将整个文件替换为：

```python
import logging
import os
import time
import traceback
from contextlib import asynccontextmanager

import bleach
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_user, get_optional_user, hash_password, verify_password
from crud import (
    build_comment_tree,
    change_password,
    create_comment,
    create_topic,
    create_user,
    delete_comment,
    delete_topic,
    get_comment_by_id,
    get_notifications,
    get_topic_by_id,
    get_topic_for_edit,
    get_topics,
    get_unread_notification_count,
    get_user_by_username,
    get_user_profile,
    increment_view_count,
    like_topic,
    mark_all_notifications_read,
    mark_notification_read,
    unlike_topic,
    update_topic,
    update_user,
)
from database import Base, engine, ensure_schema, get_db
from models import Comment, Notification, Topic, User  # noqa: F401
from schemas import (
    CommentCreate,
    CommentResponse,
    NotificationResponse,
    PasswordChange,
    TokenResponse,
    TopicCreate,
    TopicDetailResponse,
    TopicUpdate,
    UserLogin,
    UserProfileResponse,
    UserRegister,
    UserResponse,
    UserUpdate,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("blog")

ALLOWED_TAGS = ["b", "i", "em", "strong", "a", "p", "br", "ul", "ol", "li",
                "pre", "code", "h1", "h2", "h3", "h4", "h5", "h6",
                "blockquote", "img", "table", "thead", "tbody", "tr", "th", "td", "hr"]
ALLOWED_ATTRS = {"a": ["href", "title"], "img": ["src", "alt"], "code": ["class"]}

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_schema()
    yield


app = FastAPI(title="Forum API", lifespan=lifespan)
app.state.limiter = limiter


# ── Middleware ──

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("CORS_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"{request.method} {request.url.path} {response.status_code} ({duration:.3f}s)")
    return response


# ── Error handlers ──

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Not found"})


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"500 on {request.method} {request.url.path}: {exc}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc):
    return JSONResponse(status_code=429, content={"detail": "Too many requests"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Helpers ──

def sanitize(text: str) -> str:
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def _author_or_admin(topic: Topic, user: User):
    if topic.author_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your topic")


def _comment_author_or_admin(comment: Comment, user: User):
    if comment.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your comment")


# ── Root ──

@app.get("/")
def root():
    return {"message": "Forum API"}


# ── Auth routes ──

@app.post("/api/auth/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/minute")
def register(request: Request, data: UserRegister, db: Session = Depends(get_db)):
    if get_user_by_username(db, data.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    return create_user(db, data.username, data.password)


@app.post("/api/auth/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, data: UserLogin, db: Session = Depends(get_db)):
    user = get_user_by_username(db, data.username)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@app.get("/api/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.put("/api/auth/me", response_model=UserResponse)
def update_me(data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_user(db, current_user, data.model_dump(exclude_unset=True))


@app.put("/api/auth/password")
def update_password(data: PasswordChange, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="原密码错误")
    change_password(db, current_user, data.new_password)
    return {"message": "密码已更新"}


# ── Topic routes ──

@app.get("/api/topics")
def list_topics(page: int = 1, size: int = 10, q: str = "", db: Session = Depends(get_db)):
    items, total = get_topics(db, page=page, size=size, q=q)
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0,
    }


@app.get("/api/topics/{topic_id}", response_model=TopicDetailResponse)
def detail_topic(topic_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)):
    topic = get_topic_by_id(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    increment_view_count(db, topic)
    is_liked = any(u.id == current_user.id for u in topic.likes) if current_user else False
    return {
        "id": topic.id,
        "title": topic.title,
        "content": topic.content,
        "author": {"id": topic.author.id, "username": topic.author.username, "avatar": topic.author.avatar} if topic.author else None,
        "view_count": topic.view_count,
        "created_at": topic.created_at,
        "updated_at": topic.updated_at,
        "likes_count": len(topic.likes),
        "is_liked": is_liked,
        "comments": build_comment_tree(topic.comments),
    }


@app.post("/api/topics", response_model=TopicDetailResponse, status_code=201)
@limiter.limit("10/minute")
def create_topic_route(request: Request, data: TopicCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_topic(db, current_user.id, sanitize(data.title), sanitize(data.content))


@app.get("/api/topics/{topic_id}/edit")
def get_topic_for_edit_route(topic_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    topic = get_topic_for_edit(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    _author_or_admin(topic, current_user)
    return {"id": topic.id, "title": topic.title, "content": topic.content}


@app.put("/api/topics/{topic_id}", response_model=TopicDetailResponse)
@limiter.limit("10/minute")
def update_topic_route(request: Request, topic_id: int, data: TopicUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    topic = get_topic_for_edit(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    _author_or_admin(topic, current_user)
    payload = data.model_dump(exclude_unset=True)
    if payload.get("title"):
        payload["title"] = sanitize(payload["title"])
    if payload.get("content"):
        payload["content"] = sanitize(payload["content"])
    return update_topic(db, topic, payload)


@app.delete("/api/topics/{topic_id}", status_code=204)
@limiter.limit("10/minute")
def delete_topic_route(request: Request, topic_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    topic = get_topic_for_edit(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    _author_or_admin(topic, current_user)
    delete_topic(db, topic)


# ── User routes ──

@app.get("/api/users/{username}", response_model=UserProfileResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    profile = get_user_profile(db, username)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"topics": profile["topics"], **UserResponse.model_validate(profile["user"]).model_dump()}


# ── Like routes ──

@app.post("/api/likes/{topic_id}")
def like_route(topic_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    topic = get_topic_for_edit(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return like_topic(db, current_user.id, topic_id)


@app.delete("/api/likes/{topic_id}")
def unlike_route(topic_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    topic = get_topic_for_edit(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return unlike_topic(db, current_user.id, topic_id)


# ── Comment routes ──

@app.post("/api/comments", response_model=CommentResponse, status_code=201)
@limiter.limit("10/minute")
def create_comment_route(request: Request, data: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not get_topic_for_edit(db, data.topic_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    try:
        return create_comment(db, current_user.id, data.topic_id, sanitize(data.content), data.parent_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.delete("/api/comments/{comment_id}", status_code=204)
def delete_comment_route(comment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    comment = get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    _comment_author_or_admin(comment, current_user)
    delete_comment(db, comment)


# ── Notification routes ──

@app.get("/api/notifications")
def list_notifications(page: int = 1, size: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items, total = get_notifications(db, current_user.id, page=page, size=size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0,
    }


@app.get("/api/notifications/unread-count")
def unread_notification_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"count": get_unread_notification_count(db, current_user.id)}


@app.put("/api/notifications/{notif_id}/read")
def read_notification(notif_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mark_notification_read(db, notif_id, current_user.id)
    return {"message": "ok"}


@app.put("/api/notifications/read-all")
def read_all_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mark_all_notifications_read(db, current_user.id)
    return {"message": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
```

- [ ] **Step 2: 提交**

```bash
git add backend/main.py
git commit -m "refactor: update routes for forum (Topic, Notification endpoints)"
```

---

### Task 6: 前端 API 层 — 重命名和新增

**Files:**
- Modify: `frontend/src/api/post.js` → rename to `frontend/src/api/topic.js`
- Create: `frontend/src/api/notification.js`
- Delete: `frontend/src/api/post.js`

- [ ] **Step 1: 创建 topic.js**

```javascript
import client from "./client";

export function getTopics(page = 1, size = 10, q = "") {
  return client.get("/topics", { params: { page, size, q } });
}

export function getTopicById(id) {
  return client.get(`/topics/${id}`);
}

export function getTopicForEdit(id) {
  return client.get(`/topics/${id}/edit`);
}

export function createTopic(data) {
  return client.post("/topics", data);
}

export function updateTopic(id, data) {
  return client.put(`/topics/${id}`, data);
}

export function deleteTopic(id) {
  return client.delete(`/topics/${id}`);
}
```

- [ ] **Step 2: 创建 notification.js**

```javascript
import client from "./client";

export function getNotifications(page = 1, size = 20) {
  return client.get("/notifications", { params: { page, size } });
}

export function getUnreadCount() {
  return client.get("/notifications/unread-count");
}

export function markRead(id) {
  return client.put(`/notifications/${id}/read`);
}

export function markAllRead() {
  return client.put("/notifications/read-all");
}
```

- [ ] **Step 3: 更新 comment.js，将 post_id 改为 topic_id**

修改 `frontend/src/api/comment.js`：

```javascript
import client from "./client";

export function createComment(topicId, content, parentId = null) {
  return client.post("/comments", { content, topic_id: topicId, parent_id: parentId });
}

export function deleteComment(id) {
  return client.delete(`/comments/${id}`);
}
```

- [ ] **Step 4: 更新 like.js，参数名和路径**

修改 `frontend/src/api/like.js`：

```javascript
import client from "./client";

export function likeTopic(topicId) {
  return client.post(`/likes/${topicId}`);
}

export function unlikeTopic(topicId) {
  return client.delete(`/likes/${topicId}`);
}
```

- [ ] **Step 5: 删除旧文件**

删除 `frontend/src/api/post.js`

- [ ] **Step 6: 验证所有 api 文件语法无误**

```bash
cd frontend && npx eslint src/api/topic.js src/api/notification.js src/api/comment.js src/api/like.js --fix 2>&1 || true
```

- [ ] **Step 7: 提交**

```bash
git add frontend/src/api/
git rm frontend/src/api/post.js 2>/dev/null; git add frontend/src/api/post.js 2>/dev/null
git commit -m "refactor: update frontend API layer for forum (topic, notification, like)"
```

---

### Task 7: 前端路由 — 更新路由和名称

**Files:**
- Modify: `frontend/src/router/index.js`

- [ ] **Step 1: 重写路由配置**

```javascript
import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "home",
    component: () => import("../views/HomeView.vue"),
    meta: { title: "首页" },
  },
  {
    path: "/topic/new",
    name: "topic-new",
    component: () => import("../views/TopicEditView.vue"),
    meta: { requiresAuth: true, title: "发帖" },
  },
  {
    path: "/topic/:id",
    name: "topic-detail",
    component: () => import("../views/TopicDetailView.vue"),
    meta: { title: "帖子" },
  },
  {
    path: "/topic/:id/edit",
    name: "topic-edit",
    component: () => import("../views/TopicEditView.vue"),
    meta: { requiresAuth: true, title: "编辑" },
  },
  {
    path: "/notifications",
    name: "notifications",
    component: () => import("../views/NotificationsView.vue"),
    meta: { requiresAuth: true, title: "通知" },
  },
  {
    path: "/login",
    name: "login",
    component: () => import("../views/LoginView.vue"),
    meta: { title: "登录" },
  },
  {
    path: "/register",
    name: "register",
    component: () => import("../views/RegisterView.vue"),
    meta: { title: "注册" },
  },
  {
    path: "/profile/edit",
    name: "profile-edit",
    component: () => import("../views/ProfileEdit.vue"),
    meta: { requiresAuth: true, title: "编辑资料" },
  },
  {
    path: "/user/:username",
    name: "user-profile",
    component: () => import("../views/UserProfile.vue"),
    meta: { title: "用户主页" },
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("../views/NotFoundView.vue"),
    meta: { title: "404" },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach((to) => {
  const token = localStorage.getItem("token");
  if (to.meta.requiresAuth && !token) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
});

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - Forum` : "Forum";
});

export default router;
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/router/index.js
git commit -m "refactor: update routes for forum (remove admin routes, add topic/notifications)"
```

---

### Task 8: 前端 App.vue — 更新导航栏

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 更新 script 和 template**

修改 `frontend/src/App.vue`，变更以下部分：

**script setup 中添加：**
```javascript
import { getUnreadCount } from "./api/notification";

const unreadCount = ref(0);
let notifTimer = null;

function goNotifications() {
  userMenuOpen.value = false;
  router.push("/notifications");
}

onMounted(() => {
  initTheme();
  auth.restoreUser();
  document.addEventListener("click", onDocClick);
  if (auth.user) {
    fetchUnreadCount();
    notifTimer = setInterval(fetchUnreadCount, 30000);
  }
});

onBeforeUnmount(() => {
  document.removeEventListener("click", onDocClick);
  if (notifTimer) clearInterval(notifTimer);
});

async function fetchUnreadCount() {
  try {
    const res = await getUnreadCount();
    unreadCount.value = res.data.count;
  } catch {
    // ignore
  }
}
```

**template 中 brand 文字改为：**
```html
<router-link to="/" class="brand" @click="closeMenu">Forum</router-link>
```

**template 中导航链接替换：**
将原来的：
```html
<template v-if="auth.user">
  <router-link to="/admin" @click="closeMenu">后台</router-link>
  <router-link to="/admin/posts/new" @click="closeMenu">写文章</router-link>
</template>
<template v-else>
  <router-link to="/login" @click="closeMenu">登录</router-link>
  <router-link to="/register" @click="closeMenu">注册</router-link>
</template>
```

替换为：
```html
<template v-if="auth.user">
  <router-link to="/topic/new" @click="closeMenu">发帖</router-link>
</template>
<template v-else>
  <router-link to="/login" @click="closeMenu">登录</router-link>
  <router-link to="/register" @click="closeMenu">注册</router-link>
</template>
```

在 `theme-toggle` 按钮之前，添加通知按钮：
```html
<router-link v-if="auth.user" to="/notifications" class="notif-bell" :aria-label="'通知'">
  🔔
  <span v-if="unreadCount > 0" class="notif-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
</router-link>
```

**style 中添加通知样式：**
```css
.notif-bell {
  position: relative;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  font-size: 0.85rem;
  flex-shrink: 0;
}
.notif-bell:hover { border-color: var(--color-text); }
.notif-badge {
  position: absolute;
  top: -4px;
  right: -6px;
  background: var(--color-danger);
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 3px;
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat: update navbar for forum (add notification bell, replace admin links)"
```

---

### Task 9: 前端 HomeView — 帖子列表

**Files:**
- Modify: `frontend/src/views/HomeView.vue`

- [ ] **Step 1: 重写 HomeView.vue**

```vue
<script setup>
import { ref, onMounted, watch, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getTopics } from "../api/topic";

const route = useRoute();
const router = useRouter();

const topics = ref([]);
const total = ref(0);
const pages = ref(0);
const page = ref(1);
const searchInput = ref(route.query.q || "");
const loading = ref(true);
const error = ref("");

const q = computed(() => route.query.q || "");
const size = 10;

async function fetchTopics() {
  loading.value = true;
  error.value = "";
  try {
    const res = await getTopics(page.value, size, q.value);
    topics.value = res.data.items;
    total.value = res.data.total;
    pages.value = res.data.pages;
  } catch {
    error.value = "加载失败，请稍后重试";
  } finally {
    loading.value = false;
  }
}

function goPage(p) {
  page.value = p;
}

function doSearch() {
  const val = searchInput.value.trim();
  page.value = 1;
  if (val) {
    router.push({ name: "home", query: { q: val } });
  } else {
    router.push({ name: "home" });
  }
}

function formatTime(t) {
  if (!t) return "";
  const diff = Date.now() - new Date(t).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  return new Date(t).toLocaleDateString();
}

onMounted(fetchTopics);
watch(page, fetchTopics);
watch(q, () => {
  page.value = 1;
  fetchTopics();
});
</script>

<template>
  <div class="home">
    <form class="search-bar" @submit.prevent="doSearch">
      <input v-model="searchInput" type="search" placeholder="搜索帖子..." class="search-input" />
    </form>

    <h1 v-if="q">搜索: "{{ q }}"</h1>
    <h1 v-else>最新帖子</h1>

    <p v-if="q && !loading" class="search-info">
      找到 {{ total }} 个帖子
      <router-link to="/" class="btn-clear">清除搜索</router-link>
    </p>

    <div v-if="loading" class="skeleton-list">
      <div v-for="n in 5" :key="n" class="skeleton-row">
        <div class="skeleton-line w-70"></div>
        <div class="skeleton-line w-40"></div>
      </div>
    </div>
    <div v-else-if="error" class="state error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchTopics">重试</button>
    </div>
    <div v-else-if="topics.length === 0" class="state">暂无帖子</div>

    <div v-else class="topic-list">
      <div v-for="t in topics" :key="t.id" class="topic-row">
        <div class="topic-main">
          <router-link :to="`/topic/${t.id}`" class="topic-title">{{ t.title }}</router-link>
          <div class="topic-meta">
            <router-link :to="`/user/${t.author?.username}`" class="author">{{ t.author?.username }}</router-link>
            <span>{{ formatTime(t.created_at) }}</span>
          </div>
        </div>
        <div class="topic-stats">
          <span title="回复">💬 {{ t.comment_count }}</span>
          <span title="点赞">❤️ {{ t.likes_count }}</span>
        </div>
      </div>

      <div v-if="pages > 1" class="pagination">
        <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
        <span v-for="p in pages" :key="p">
          <button :class="{ current: p === page }" @click="goPage(p)">{{ p }}</button>
        </span>
        <button :disabled="page >= pages" @click="goPage(pages)">下一页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home { max-width: 700px; margin: 0 auto; }
h1 { margin-bottom: 0.5rem; color: var(--color-text); }

.search-bar { margin-bottom: 1.5rem; }
.search-input {
  width: 100%;
  padding: 0.7rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 1rem;
  box-sizing: border-box;
  background: var(--color-bg);
  color: var(--color-text);
  outline: none;
  transition: border-color 0.2s;
}
.search-input:focus { border-color: var(--color-primary); }

.search-info {
  margin-bottom: 1rem;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.btn-clear {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 3px;
  padding: 0.15rem 0.5rem;
  cursor: pointer;
  color: var(--color-text-muted);
  font-size: 0.8rem;
  text-decoration: none;
}
.btn-clear:hover { color: var(--color-text); border-color: var(--color-text); }
.state { text-align: center; padding: 2rem; color: var(--color-text-muted); }
.error { color: var(--color-danger); }
.btn-retry {
  margin-top: 0.5rem;
  padding: 0.4rem 1.2rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-retry:hover { border-color: var(--color-primary); color: var(--color-primary); }

/* Skeleton */
.skeleton-list { display: flex; flex-direction: column; gap: 0.6rem; }
.skeleton-row {
  padding: 1rem 1.4rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.skeleton-line {
  height: 14px;
  background: var(--color-border);
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
}
.skeleton-line.w-70 { width: 70%; }
.skeleton-line.w-40 { width: 40%; }
@keyframes shimmer {
  0% { opacity: 0.4; }
  50% { opacity: 0.8; }
  100% { opacity: 0.4; }
}

/* Topic list */
.topic-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.4rem;
  margin-bottom: 0.5rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius);
  transition: background 0.2s;
}
.topic-row:hover { background: var(--color-card-hover); }
.topic-main { flex: 1; min-width: 0; }
.topic-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-text);
  text-decoration: none;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.topic-title:hover { color: var(--color-primary); }
.topic-meta {
  display: flex;
  gap: 0.6rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-top: 0.3rem;
}
.author { color: var(--color-text-muted); text-decoration: none; }
.author:hover { color: var(--color-primary); }
.topic-stats {
  display: flex;
  gap: 0.8rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
  flex-shrink: 0;
  margin-left: 1rem;
}
.pagination {
  display: flex;
  justify-content: center;
  gap: 0.4rem;
  margin-top: 2rem;
}
.pagination button {
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text);
  border-radius: 4px;
  cursor: pointer;
}
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.pagination button.current { background: var(--color-text); color: var(--color-bg); border-color: var(--color-text); }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/HomeView.vue
git commit -m "feat: rewrite HomeView as forum topic list"
```

---

### Task 10: 前端 TopicDetailView — 帖子详情（新建）

**Files:**
- Create: `frontend/src/views/TopicDetailView.vue`
- 后续 Task 12 将删除 PostDetailView.vue

- [ ] **Step 1: 创建 TopicDetailView.vue**

```vue
<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { marked } from "marked";
import hljs from "highlight.js";
import "highlight.js/styles/github-dark.css";
import { getTopicById, deleteTopic } from "../api/topic";
import { createComment } from "../api/comment";
import { likeTopic, unlikeTopic } from "../api/like";
import { useAuthStore } from "../stores/auth";
import CommentItem from "../components/CommentItem.vue";
import { showConfirm } from "../composables/confirm";
import { showToast } from "../composables/toast";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const topic = ref(null);
const loading = ref(true);
const error = ref("");

const commentText = ref("");
const commentLoading = ref(false);
const commentError = ref("");

const likeLoading = ref(false);

function isLiked() {
  return topic.value?.is_liked || false;
}

async function handleLike() {
  if (!auth.user) {
    router.push("/login");
    return;
  }
  likeLoading.value = true;
  try {
    if (isLiked()) {
      const res = await unlikeTopic(topic.value.id);
      topic.value.likes_count = res.data.likes_count;
      topic.value.is_liked = false;
    } else {
      const res = await likeTopic(topic.value.id);
      topic.value.likes_count = res.data.likes_count;
      topic.value.is_liked = true;
    }
  } catch {
    // ignore duplicate
  } finally {
    likeLoading.value = false;
  }
}

marked.setOptions({
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  },
});

const isAuthor = computed(() =>
  auth.user && topic.value && auth.user.id === topic.value.author?.id,
);

const isAdmin = computed(() => auth.user?.is_admin);

const renderedContent = computed(() => {
  if (!topic.value?.content) return "";
  return marked(topic.value.content);
});

function handleEdit() {
  router.push(`/topic/${topic.value.id}/edit`);
}

async function handleDelete() {
  if (!await showConfirm("确定删除这个帖子？")) return;
  try {
    await deleteTopic(topic.value.id);
    router.push("/");
    showToast.success("删除成功");
  } catch {
    showToast.error("删除失败");
  }
}

async function fetchTopic() {
  loading.value = true;
  error.value = "";
  try {
    const res = await getTopicById(route.params.id);
    topic.value = res.data;
  } catch {
    error.value = "帖子不存在或加载失败";
  } finally {
    loading.value = false;
  }
}

async function handleComment(parentId = null, content = null) {
  const text = content || commentText.value;
  if (!text.trim()) return;
  commentLoading.value = true;
  commentError.value = "";
  try {
    await createComment(topic.value.id, text, parentId);
    if (!parentId) commentText.value = "";
    await fetchTopic();
  } catch (e) {
    commentError.value = e.response?.data?.detail || "评论失败";
  } finally {
    commentLoading.value = false;
  }
}

function handleReplyCreated({ parentId, content }) {
  handleComment(parentId, content);
}

async function handleCommentDeleted() {
  await fetchTopic();
}

onMounted(fetchTopic);
</script>

<template>
  <div class="topic-detail">
    <div v-if="loading" class="skeleton-detail">
      <div class="skeleton-line w-70 h-32"></div>
      <div class="skeleton-line w-40 h-14"></div>
      <div class="skeleton-line w-100 h-14"></div>
      <div class="skeleton-line w-100 h-14"></div>
      <div class="skeleton-line w-80 h-14"></div>
    </div>
    <div v-else-if="error" class="state error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchTopic">重试</button>
    </div>

    <article v-else>
      <h1>{{ topic.title }}</h1>
      <div class="meta">
        <router-link :to="`/user/${topic.author?.username}`" class="author">{{ topic.author?.username }}</router-link>
        <span>{{ new Date(topic.created_at).toLocaleDateString() }}</span>
        <span>👁️ {{ topic.view_count || 0 }}</span>
        <button
          class="like-btn"
          :class="{ liked: isLiked() }"
          :disabled="likeLoading"
          @click="handleLike"
        >
          {{ isLiked() ? '❤️' : '🤍' }} {{ topic.likes_count || 0 }}
        </button>
      </div>
      <div v-if="isAuthor || isAdmin" class="author-actions">
        <button class="btn-edit" @click="handleEdit">编辑</button>
        <button class="btn-delete" @click="handleDelete">删除</button>
      </div>
      <div class="content" v-html="renderedContent"></div>

      <section class="comments">
        <h3>回复 ({{ topic.comments?.length || 0 }})</h3>

        <div v-if="auth.user" class="comment-form">
          <textarea
            v-model="commentText"
            placeholder="写下你的回复..."
            rows="3"
          ></textarea>
          <div class="comment-actions">
            <button :disabled="commentLoading" @click="handleComment()">
              {{ commentLoading ? "提交中..." : "发表回复" }}
            </button>
            <span v-if="commentError" class="error">{{ commentError }}</span>
          </div>
        </div>
        <p v-else class="login-hint">
          <router-link to="/login">登录</router-link> 后发表回复
        </p>

        <div v-if="topic.comments?.length" class="comment-list">
          <CommentItem
            v-for="c in topic.comments"
            :key="c.id"
            :comment="c"
            :auth="auth.user"
            @reply-created="handleReplyCreated"
            @comment-deleted="handleCommentDeleted"
          />
        </div>
        <p v-else class="state">暂无回复</p>
      </section>
    </article>
  </div>
</template>

<style scoped>
.topic-detail { max-width: 700px; margin: 0 auto; }
.state { text-align: center; padding: 2rem; color: var(--color-text-muted); }
.error { color: var(--color-danger); }
.btn-retry {
  margin-top: 0.5rem;
  padding: 0.4rem 1.2rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-retry:hover { border-color: var(--color-primary); color: var(--color-primary); }

.skeleton-detail {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.skeleton-line {
  background: var(--color-border);
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
}
.skeleton-line.w-70 { width: 70%; }
.skeleton-line.w-40 { width: 40%; }
.skeleton-line.w-80 { width: 80%; }
.skeleton-line.w-100 { width: 100%; }
.skeleton-line.h-32 { height: 32px; }
.skeleton-line.h-14 { height: 14px; }
@keyframes shimmer {
  0% { opacity: 0.4; }
  50% { opacity: 0.8; }
  100% { opacity: 0.4; }
}

h1 { font-size: 1.8rem; margin-bottom: 0.5rem; color: var(--color-text); }
.meta {
  display: flex;
  gap: 0.8rem;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  align-items: center;
}
.author { color: var(--color-text-muted); text-decoration: none; }
.author:hover { color: var(--color-primary); }
.like-btn {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 0.2rem 0.6rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}
.like-btn:hover { border-color: var(--color-danger); }
.like-btn.liked { border-color: var(--color-danger); }
.like-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.author-actions {
  margin-bottom: 1.5rem;
  display: flex;
  gap: 0.5rem;
}
.author-actions button {
  padding: 0.3rem 0.9rem;
  border: 1px solid var(--color-border);
  border-radius: 3px;
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
  font-size: 0.85rem;
}
.btn-edit:hover { border-color: var(--color-primary); color: var(--color-primary); }
.btn-delete { color: var(--color-danger); }
.btn-delete:hover { background: var(--color-danger-bg); border-color: var(--color-danger); }

.content {
  line-height: 1.8;
  font-size: 1.05rem;
  color: var(--color-text);
}
.content :deep(pre) {
  background: var(--color-pre-bg);
  padding: 1rem;
  border-radius: var(--radius);
  overflow-x: auto;
}
.content :deep(code) {
  font-family: var(--font-mono);
  font-size: 0.9rem;
}
.content :deep(p > code) {
  background: var(--color-code-bg);
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
}
.content :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  margin-left: 0;
  padding-left: 1rem;
  color: var(--color-text-secondary);
}
.content :deep(img) { max-width: 100%; }
.content :deep(table) {
  border-collapse: collapse;
  width: 100%;
}
.content :deep(th), .content :deep(td) {
  border: 1px solid var(--color-border);
  padding: 0.5rem;
  text-align: left;
}

.comments {
  margin-top: 3rem;
  border-top: 1px solid var(--color-border);
  padding-top: 1.5rem;
}
.comments h3 { margin-bottom: 1rem; color: var(--color-text); }
.login-hint { font-size: 0.9rem; color: var(--color-text-muted); }
.comment-form textarea {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  resize: vertical;
  font-size: 0.95rem;
  box-sizing: border-box;
  background: var(--color-bg);
  color: var(--color-text);
}
.comment-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
}
.comment-actions button {
  padding: 0.5rem 1.2rem;
  background: var(--color-text);
  color: var(--color-bg);
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
}
.comment-actions button:disabled { opacity: 0.5; }
.comment-list { margin-top: 1rem; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/TopicDetailView.vue
git commit -m "feat: add TopicDetailView (forum post detail with replies)"
```

---

### Task 11: 前端 TopicEditView — 发帖/编辑（新建）

**Files:**
- Create: `frontend/src/views/TopicEditView.vue`

- [ ] **Step 1: 创建 TopicEditView.vue**

```vue
<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { marked } from "marked";
import { createTopic, updateTopic, getTopicForEdit } from "../api/topic";
import { showToast } from "../composables/toast";

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);
const title = ref("");
const content = ref("");
const loading = ref(false);
const pageLoading = ref(false);
const error = ref("");

const previewHtml = computed(() => {
  if (!content.value) return "<em>暂无内容</em>";
  return marked(content.value);
});

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);
const title = ref("");
const content = ref("");
const loading = ref(false);
const pageLoading = ref(false);
const error = ref("");

async function init() {
  if (isEdit.value) {
    pageLoading.value = true;
    try {
      const res = await getTopicForEdit(route.params.id);
      title.value = res.data.title;
      content.value = res.data.content;
    } catch {
      error.value = "加载失败";
    } finally {
      pageLoading.value = false;
    }
  }
}

async function handleSubmit() {
  if (!title.value.trim()) {
    error.value = "标题不能为空";
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    if (isEdit.value) {
      const res = await updateTopic(route.params.id, {
        title: title.value.trim(),
        content: content.value,
      });
      router.push(`/topic/${res.data.id}`);
      showToast.success("更新成功");
    } else {
      const res = await createTopic({
        title: title.value.trim(),
        content: content.value,
      });
      router.push(`/topic/${res.data.id}`);
      showToast.success("发帖成功");
    }
  } catch (e) {
    error.value = e.response?.data?.detail || "操作失败";
  } finally {
    loading.value = false;
  }
}

onMounted(init);
</script>

<template>
  <div class="topic-edit">
    <h1>{{ isEdit ? "编辑帖子" : "发布新帖" }}</h1>

    <div v-if="pageLoading" class="skeleton-form">
      <div class="skeleton-line w-100 h-40"></div>
      <div class="skeleton-line w-100 h-200"></div>
    </div>

    <form v-else @submit.prevent="handleSubmit" class="edit-form">
      <div class="field">
        <label for="title">标题</label>
        <input
          id="title"
          v-model="title"
          type="text"
          placeholder="输入帖子标题..."
          maxlength="200"
        />
      </div>

      <div class="field">
        <label for="content">内容 (Markdown)</label>
        <div class="editor-wrap">
          <textarea
            id="content"
            v-model="content"
            placeholder="支持 Markdown 语法..."
            rows="18"
          ></textarea>
          <div class="preview" v-html="previewHtml"></div>
        </div>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <div class="actions">
        <button type="submit" :disabled="loading">
          {{ loading ? "提交中..." : (isEdit ? "更新" : "发布") }}
        </button>
        <button type="button" class="btn-cancel" @click="router.back()">取消</button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.topic-edit { max-width: 700px; margin: 0 auto; }
h1 { margin-bottom: 1.5rem; color: var(--color-text); }

.skeleton-form { display: flex; flex-direction: column; gap: 1rem; }
.skeleton-line {
  background: var(--color-border);
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
}
.skeleton-line.w-100 { width: 100%; }
.skeleton-line.h-40 { height: 40px; }
.skeleton-line.h-200 { height: 200px; }
@keyframes shimmer {
  0% { opacity: 0.4; }
  50% { opacity: 0.8; }
  100% { opacity: 0.4; }
}

.field { margin-bottom: 1.2rem; }
.field label {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 600;
  color: var(--color-text);
  font-size: 0.95rem;
}
.field input {
  width: 100%;
  padding: 0.6rem 0.8rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 1rem;
  box-sizing: border-box;
  background: var(--color-bg);
  color: var(--color-text);
}
.field input:focus { border-color: var(--color-primary); outline: none; }

.editor-wrap { display: flex; gap: 1rem; }
.editor-wrap textarea,
.editor-wrap .preview {
  flex: 1;
  min-height: 360px;
  padding: 0.6rem 0.8rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 0.95rem;
  line-height: 1.6;
  background: var(--color-bg);
  color: var(--color-text);
  resize: vertical;
}
.editor-wrap textarea:focus { border-color: var(--color-primary); outline: none; }
.editor-wrap .preview {
  overflow-y: auto;
  background: var(--color-bg-secondary);
}

.error { color: var(--color-danger); font-size: 0.9rem; }
.actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}
.actions button {
  padding: 0.6rem 1.5rem;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.95rem;
}
.actions button[type="submit"] {
  background: var(--color-text);
  color: var(--color-bg);
}
.actions button[type="submit"]:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-cancel {
  background: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border) !important;
}
.btn-cancel:hover { border-color: var(--color-text) !important; }

@media (max-width: 640px) {
  .editor-wrap { flex-direction: column; }
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/TopicEditView.vue
git commit -m "feat: add TopicEditView (create/edit forum post)"
```

---

### Task 12: 前端 NotificationsView — 通知页（新建）

**Files:**
- Create: `frontend/src/views/NotificationsView.vue`

- [ ] **Step 1: 创建 NotificationsView.vue**

```vue
<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { getNotifications, markRead, markAllRead, getUnreadCount } from "../api/notification";

const router = useRouter();

const items = ref([]);
const total = ref(0);
const pages = ref(0);
const page = ref(1);
const loading = ref(true);
const error = ref("");
const size = 20;

async function fetchNotifications() {
  loading.value = true;
  error.value = "";
  try {
    const res = await getNotifications(page.value, size);
    items.value = res.data.items;
    total.value = res.data.total;
    pages.value = res.data.pages;
  } catch {
    error.value = "加载失败";
  } finally {
    loading.value = false;
  }
}

async function goTopic(notif) {
  if (!notif.is_read) {
    await markRead(notif.id);
    notif.is_read = true;
  }
  if (notif.topic_id) {
    router.push(`/topic/${notif.topic_id}`);
  }
}

async function handleMarkAll() {
  await markAllRead();
  items.value.forEach((n) => (n.is_read = true));
}

function goPage(p) {
  page.value = p;
}

function formatTime(t) {
  if (!t) return "";
  const diff = Date.now() - new Date(t).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  return new Date(t).toLocaleDateString();
}

onMounted(fetchNotifications);
</script>

<template>
  <div class="notifications">
    <div class="notif-header">
      <h1>通知</h1>
      <button v-if="items.some((n) => !n.is_read)" class="btn-mark-all" @click="handleMarkAll">
        全部已读
      </button>
    </div>

    <div v-if="loading" class="state">加载中...</div>
    <div v-else-if="error" class="state error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchNotifications">重试</button>
    </div>
    <div v-else-if="items.length === 0" class="state">暂无通知</div>

    <div v-else class="notif-list">
      <div
        v-for="n in items"
        :key="n.id"
        class="notif-item"
        :class="{ unread: !n.is_read }"
        @click="goTopic(n)"
      >
        <span class="notif-type">💬</span>
        <span class="notif-text">有人回复了你的帖子</span>
        <span class="notif-time">{{ formatTime(n.created_at) }}</span>
      </div>

      <div v-if="pages > 1" class="pagination">
        <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
        <span v-for="p in pages" :key="p">
          <button :class="{ current: p === page }" @click="goPage(p)">{{ p }}</button>
        </span>
        <button :disabled="page >= pages" @click="goPage(pages)">下一页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notifications { max-width: 700px; margin: 0 auto; }
.notif-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}
.notif-header h1 { margin: 0; color: var(--color-text); }
.btn-mark-all {
  padding: 0.4rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
  font-size: 0.85rem;
}
.btn-mark-all:hover { border-color: var(--color-primary); color: var(--color-primary); }

.state { text-align: center; padding: 2rem; color: var(--color-text-muted); }
.error { color: var(--color-danger); }
.btn-retry {
  margin-top: 0.5rem;
  padding: 0.4rem 1.2rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-retry:hover { border-color: var(--color-primary); color: var(--color-primary); }

.notif-list { display: flex; flex-direction: column; gap: 0.3rem; }
.notif-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.9rem 1.2rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.2s;
}
.notif-item:hover { background: var(--color-card-hover); }
.notif-item.unread {
  border-left: 3px solid var(--color-primary);
  background: var(--color-card-hover);
}
.notif-type { font-size: 1.1rem; flex-shrink: 0; }
.notif-text { flex: 1; font-size: 0.95rem; color: var(--color-text); }
.notif-time { font-size: 0.8rem; color: var(--color-text-muted); flex-shrink: 0; }

.pagination {
  display: flex;
  justify-content: center;
  gap: 0.4rem;
  margin-top: 2rem;
}
.pagination button {
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text);
  border-radius: 4px;
  cursor: pointer;
}
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.pagination button.current { background: var(--color-text); color: var(--color-bg); border-color: var(--color-text); }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/NotificationsView.vue
git commit -m "feat: add NotificationsView with read/unread support"
```

---

### Task 13: 前端 UserProfile — 更新用户主页

**Files:**
- Modify: `frontend/src/views/UserProfile.vue`

- [ ] **Step 1: 重写 UserProfile.vue**

```vue
<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { getUserProfile } from "../api/user";

const route = useRoute();
const profile = ref(null);
const loading = ref(true);
const error = ref("");

async function fetchProfile() {
  loading.value = true;
  error.value = "";
  try {
    const res = await getUserProfile(route.params.username);
    profile.value = res.data;
  } catch {
    error.value = "用户不存在或加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(fetchProfile);
</script>

<template>
  <div class="user-profile">
    <div v-if="loading" class="state">加载中...</div>
    <div v-else-if="error" class="state error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchProfile">重试</button>
    </div>
    <div v-else-if="profile">
      <div class="profile-header">
        <div class="avatar">{{ profile.username[0]?.toUpperCase() }}</div>
        <h1>{{ profile.username }}</h1>
        <div class="stats">
          <span>帖子 {{ profile.topic_count || 0 }}</span>
          <span>回复 {{ profile.comment_count || 0 }}</span>
        </div>
        <p v-if="profile.bio" class="bio">{{ profile.bio }}</p>
        <a v-if="profile.github_url" :href="profile.github_url" target="_blank" class="github-link">
          GitHub
        </a>
        <p class="join-date">加入于 {{ new Date(profile.created_at).toLocaleDateString() }}</p>
      </div>
      <section class="user-topics">
        <h2>帖子</h2>
        <div v-if="profile.topics?.length">
          <article v-for="t in profile.topics" :key="t.id" class="card">
            <router-link :to="`/topic/${t.id}`" class="card-link" :aria-label="t.title"></router-link>
            <h2 class="title">{{ t.title }}</h2>
            <div class="meta">
              <span>{{ new Date(t.created_at).toLocaleDateString() }}</span>
              <span>💬 {{ t.comment_count || 0 }}</span>
              <span>❤️ {{ t.likes_count || 0 }}</span>
            </div>
          </article>
        </div>
        <p v-else class="state">暂无帖子</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.user-profile { max-width: 700px; margin: 0 auto; }
.state { text-align: center; padding: 2rem; color: var(--color-text-muted); }
.error { color: var(--color-danger); }
.btn-retry {
  margin-top: 0.5rem;
  padding: 0.4rem 1.2rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-retry:hover { border-color: var(--color-primary); color: var(--color-primary); }

.profile-header {
  text-align: center;
  padding: 2rem 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 2rem;
}
.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-size: 2rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
}
.stats {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  margin-bottom: 0.8rem;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}
h1 { color: var(--color-text); margin-bottom: 0.5rem; }
.bio { color: var(--color-text-secondary); max-width: 400px; margin: 0 auto 0.5rem; }
.github-link {
  display: inline-block;
  color: var(--color-primary);
  text-decoration: none;
  font-size: 0.9rem;
}
.join-date { color: var(--color-text-muted); font-size: 0.85rem; margin-top: 0.5rem; }

.user-topics h2 { margin-bottom: 1rem; color: var(--color-text); font-size: 1.2rem; }

.card {
  position: relative;
  padding: 1.2rem 1.4rem;
  margin-bottom: 0.6rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius);
  transition: background 0.2s;
}
.card:hover { background: var(--color-card-hover); }
.card-link {
  position: absolute;
  inset: 0;
  z-index: 1;
}
.title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.3rem 0;
}
.card:hover .title { color: var(--color-primary); }
.meta {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/UserProfile.vue
git commit -m "refactor: update UserProfile for forum stats and topic links"
```

---

### Task 14: 清理旧文件

**Files:**
- Delete: `frontend/src/views/PostDetailView.vue`
- Delete: `frontend/src/views/AdminDashboard.vue`
- Delete: `frontend/src/views/AdminPostEdit.vue`

- [ ] **Step 1: 删除旧视图文件**

```bash
rm frontend/src/views/PostDetailView.vue
rm frontend/src/views/AdminDashboard.vue
rm frontend/src/views/AdminPostEdit.vue
```

- [ ] **Step 2: 提交**

```bash
git add -u frontend/src/views/
git commit -m "chore: remove old blog views (PostDetail, AdminDashboard, AdminPostEdit)"
```

---

### Task 15: 端到端验证

- [ ] **Step 1: 启动后端验证无 import 错误**

```bash
cd backend
source venv/Scripts/activate
python -c "from main import app; print('Backend loads OK:', app.title)"
```

Expected: `Backend loads OK: Forum API`

- [ ] **Step 2: 启动前端验证无编译错误**

```bash
cd frontend
npm run build 2>&1
```

Expected: build 成功，无报错。

- [ ] **Step 3: 手动验证功能清单**

启动前后端后，逐项验证：

| 功能 | 验证方法 |
|------|----------|
| 注册/登录 | 注册新用户，登录，登出 |
| 首页帖子列表 | 访问 `/`，确认看到空状态或帖子 |
| 发帖 | 点击"发帖"，输入标题和 Markdown 内容，发布 |
| 查看帖子 | 在首页点击帖子，确认详情页渲染正常 |
| 编辑帖子 | 作者点击编辑，修改内容，更新 |
| 删除帖子 | 作者点击删除，确认后删除 |
| 评论 | 在帖子下发表评论 |
| 嵌套回复 | 回复一条评论 |
| 点赞 | 点赞/取消点赞 |
| 通知 | 用另一个账号回复帖子，检查原账号通知 |
| 用户主页 | 访问 `/user/xxx`，确认统计正确 |
| 搜索 | 搜索关键词，确认结果 |
| 暗色主题 | 切换暗色/亮色 |
| 响应式 | 缩小浏览器宽度，确认移动端布局 |

- [ ] **Step 4: 提交（如有修复）**

```bash
git add -A
git commit -m "fix: end-to-end verification fixes"
```
