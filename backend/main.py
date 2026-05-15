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
