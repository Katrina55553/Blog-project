from datetime import datetime

from pydantic import BaseModel


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
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Post ──

class PostCreate(BaseModel):
    title: str
    slug: str
    content: str = ""
    summary: str = ""
    tags: list[str] = []


class PostUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    content: str | None = None
    summary: str | None = None
    tags: list[str] | None = None


class PostListResponse(BaseModel):
    id: int
    title: str
    slug: str
    summary: str
    author_id: int
    created_at: datetime
    tags: list[str]

    model_config = {"from_attributes": True}


class PostDetailResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    summary: str
    author_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    tags: list[str]

    model_config = {"from_attributes": True}


# ── Tag ──

class TagResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


# ── Comment ──

class CommentCreate(BaseModel):
    content: str
    post_id: int


class CommentResponse(BaseModel):
    id: int
    content: str
    post_id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
