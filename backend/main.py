import logging
import os
import time
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
from crud import create_user, get_user_by_username
from crud import (
    build_comment_tree,
    change_password,
    create_post,
    get_posts,
    get_post_by_slug,
    get_post_by_id,
    get_posts_by_user,
    get_user_profile,
    update_post,
    update_user,
    delete_post,
    get_all_tags,
    create_comment,
    like_post,
    unlike_post,
)
from database import Base, engine, ensure_schema, get_db
from models import User, Post, Tag, Comment, post_tags  # noqa: F401
from schemas import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
    PasswordChange,
    PostCreate,
    PostUpdate,
    PostDetailResponse,
    CommentCreate,
    CommentResponse,
    UserProfileResponse,
    TagResponse,
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


app = FastAPI(title="Blog API", lifespan=lifespan)
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
    logger.error(f"500 on {request.method} {request.url.path}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc):
    return JSONResponse(status_code=429, content={"detail": "Too many requests"})


# ── Helpers ──

def sanitize(text: str) -> str:
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


# ── Routes ──

@app.get("/")
def root():
    return {"message": "Blog API"}


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


# ── Public post routes ──

@app.get("/api/posts")
def list_posts(page: int = 1, size: int = 10, tag: str = "", q: str = "", db: Session = Depends(get_db)):
    posts, total = get_posts(db, page=page, size=size, tag=tag, q=q)
    items = []
    for p in posts:
        items.append({
            "id": p.id,
            "title": p.title,
            "slug": p.slug,
            "summary": p.summary,
            "author": {"id": p.author.id, "username": p.author.username, "avatar": p.author.avatar} if p.author else None,
            "created_at": p.created_at,
            "tags": [t.name for t in p.tags],
        })
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0,
    }


@app.get("/api/posts/{slug}", response_model=PostDetailResponse)
def detail_post(slug: str, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)):
    post = get_post_by_slug(db, slug)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    is_liked = any(u.id == current_user.id for u in post.likes) if current_user else False
    return {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "content": post.content,
        "summary": post.summary,
        "author": {"id": post.author.id, "username": post.author.username, "avatar": post.author.avatar} if post.author else None,
        "status": post.status,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "tags": [t.name for t in post.tags],
        "likes_count": len(post.likes),
        "is_liked": is_liked,
        "comments": build_comment_tree(post.comments),
    }


# ── Admin post routes ──

def _author_or_admin(post: Post, user: User):
    if post.author_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your post")


@app.get("/api/admin/posts")
def list_my_posts(page: int = 1, size: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    posts, total = get_posts_by_user(db, current_user.id, page=page, size=size)
    items = []
    for p in posts:
        items.append({
            "id": p.id,
            "title": p.title,
            "slug": p.slug,
            "summary": p.summary,
            "author": {"id": p.author.id, "username": p.author.username, "avatar": p.author.avatar} if p.author else None,
            "status": p.status,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "tags": [t.name for t in p.tags],
        })
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0,
    }


@app.post("/api/admin/posts", response_model=PostDetailResponse, status_code=201)
@limiter.limit("10/minute")
def create_post_route(request: Request, data: PostCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if get_post_by_slug(db, data.slug):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
    return create_post(
        db, current_user.id,
        sanitize(data.title),
        sanitize(data.slug),
        sanitize(data.content),
        sanitize(data.summary),
        data.tags,
    )


@app.get("/api/admin/posts/{post_id}", response_model=PostDetailResponse)
def get_post_route(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    _author_or_admin(post, current_user)
    return post


@app.put("/api/admin/posts/{post_id}", response_model=PostDetailResponse)
@limiter.limit("10/minute")
def update_post_route(request: Request, post_id: int, data: PostUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    _author_or_admin(post, current_user)
    payload = data.model_dump(exclude_unset=True)
    if payload.get("slug"):
        existing = get_post_by_slug(db, payload["slug"])
        if existing and existing.id != post_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
        payload["slug"] = sanitize(payload["slug"])
    if payload.get("content"):
        payload["content"] = sanitize(payload["content"])
    if payload.get("summary"):
        payload["summary"] = sanitize(payload["summary"])
    return update_post(db, post, payload)


@app.delete("/api/admin/posts/{post_id}", status_code=204)
@limiter.limit("10/minute")
def delete_post_route(request: Request, post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    _author_or_admin(post, current_user)
    delete_post(db, post)


# ── User routes ──

@app.get("/api/users/{username}", response_model=UserProfileResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    profile = get_user_profile(db, username)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"posts": profile["posts"], **UserResponse.model_validate(profile["user"]).model_dump()}


# ── Tag routes ──

@app.get("/api/tags", response_model=list[TagResponse])
def list_tags(db: Session = Depends(get_db)):
    return get_all_tags(db)


# ── Like routes ──

@app.post("/api/likes/{post_id}")
def like_route(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return like_post(db, current_user.id, post_id)


@app.delete("/api/likes/{post_id}")
def unlike_route(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return unlike_post(db, current_user.id, post_id)


# ── Comment routes ──

@app.post("/api/comments", response_model=CommentResponse, status_code=201)
@limiter.limit("10/minute")
def create_comment_route(request: Request, data: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not get_post_by_id(db, data.post_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    try:
        return create_comment(db, current_user.id, data.post_id, sanitize(data.content), data.parent_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
