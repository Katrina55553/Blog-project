from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_user, verify_password
from crud import create_user, get_user_by_username
from crud import create_post, get_posts, get_post_by_slug, get_post_by_id, update_post, delete_post
from database import Base, engine, get_db
from models import User, Post, Tag, Comment, post_tags  # noqa: F401
from schemas import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    PostCreate,
    PostUpdate,
    PostListResponse,
    PostDetailResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Blog API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Blog API"}


# ── Auth routes ──

@app.post("/api/auth/register", response_model=UserResponse, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if get_user_by_username(db, data.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    return create_user(db, data.username, data.password)


@app.post("/api/auth/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
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
def create_post_route(data: PostCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_post(db, current_user.id, data.title, data.slug, data.content, data.summary, data.tags)


@app.put("/api/admin/posts/{post_id}", response_model=PostDetailResponse)
def update_post_route(post_id: int, data: PostUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your post")
    return update_post(db, post, data.model_dump(exclude_unset=True))


@app.delete("/api/admin/posts/{post_id}", status_code=204)
def delete_post_route(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your post")
    delete_post(db, post)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)