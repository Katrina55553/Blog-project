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


# ── Comment ──

class CommentCreate(BaseModel):
    content: str
    post_id: int


class CommentResponse(BaseModel):
    id: int
    content: str
    post_id: int
    user_id: int
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("username", mode="before")
    @classmethod
    def extract_username(cls, v):
        return getattr(v, "username", v)


# ── Post responses (after CommentResponse) ──

class AuthorInfo(BaseModel):
    id: int
    username: str
    avatar: str

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    id: int
    title: str
    slug: str
    summary: str
    author: AuthorInfo
    created_at: datetime
    tags: list[str]

    model_config = {"from_attributes": True}

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags(cls, v):
        return [getattr(t, "name", t) for t in v]


class PostDetailResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    summary: str
    author: AuthorInfo
    status: str
    created_at: datetime
    updated_at: datetime
    tags: list[str]
    comments: list[CommentResponse] = []

    model_config = {"from_attributes": True}

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags(cls, v):
        return [getattr(t, "name", t) for t in v]


class UserProfileResponse(BaseModel):
    id: int
    username: str
    avatar: str
    bio: str
    github_url: str
    created_at: datetime
    posts: list[PostListResponse] = []

    model_config = {"from_attributes": True}


# ── Tag ──

class TagResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
