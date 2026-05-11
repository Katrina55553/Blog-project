import logging
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

from auth import create_access_token, get_current_user, verify_password
from crud import create_user, get_user_by_username
from crud import (
    create_post,
    get_posts,
    get_post_by_slug,
    get_post_by_id,
    update_post,
    delete_post,
    get_all_tags,
    create_comment,
)
from database import Base, engine, get_db
from models import User, Post, Tag, Comment, post_tags  # noqa: F401
from schemas import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    PostCreate,
    PostUpdate,
    PostDetailResponse,
    CommentCreate,
    CommentResponse,
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
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Blog API", lifespan=lifespan)
app.state.limiter = limiter


# ── Middleware ──

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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


# ── Public post routes ──

@app.get("/api/posts")
def list_posts(page: int = 1, size: int = 10, tag: str = "", db: Session = Depends(get_db)):
    posts, total = get_posts(db, page=page, size=size, tag=tag)
    items = []
    for p in posts:
        items.append({
            "id": p.id,
            "title": p.title,
            "slug": p.slug,
            "summary": p.summary,
            "author_id": p.author_id,
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
def detail_post(slug: str, db: Session = Depends(get_db)):
    post = get_post_by_slug(db, slug)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


# ── Admin post routes ──

@app.post("/api/admin/posts", response_model=PostDetailResponse, status_code=201)
@limiter.limit("10/minute")
def create_post_route(request: Request, data: PostCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
    return post


@app.put("/api/admin/posts/{post_id}", response_model=PostDetailResponse)
@limiter.limit("10/minute")
def update_post_route(request: Request, post_id: int, data: PostUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your post")
    payload = data.model_dump(exclude_unset=True)
    if payload.get("title"):
        payload["title"] = sanitize(payload["title"])
    if payload.get("slug"):
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
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your post")
    delete_post(db, post)


# ── Tag routes ──

@app.get("/api/tags", response_model=list[TagResponse])
def list_tags(db: Session = Depends(get_db)):
    return get_all_tags(db)


# ── Comment routes ──

@app.post("/api/comments", response_model=CommentResponse, status_code=201)
@limiter.limit("10/minute")
def create_comment_route(request: Request, data: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_comment(db, current_user.id, data.post_id, sanitize(data.content))


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
