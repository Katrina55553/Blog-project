from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from auth import hash_password
from models import Comment, Post, Tag, User, likes


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


# ── Post ──

def _get_or_create_tags(db: Session, tag_names: list[str]) -> list[Tag]:
    tags = []
    for name in tag_names:
        tag = db.query(Tag).filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


def create_post(db: Session, author_id: int, title: str, slug: str,
                content: str, summary: str, tags: list[str]) -> Post:
    post = Post(
        title=title,
        slug=slug,
        content=content,
        summary=summary,
        author_id=author_id,
        tags=_get_or_create_tags(db, tags),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_posts(db: Session, page: int = 1, size: int = 10, tag: str = "", q: str = ""):
    query = db.query(Post).options(joinedload(Post.author), joinedload(Post.tags))
    if tag:
        query = query.join(Post.tags).filter(Tag.name == tag)
    if q:
        query = query.filter(or_(Post.title.ilike(f"%{q}%"), Post.content.ilike(f"%{q}%")))
    total = query.count()
    posts = (
        query.order_by(Post.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return posts, total


def get_post_by_slug(db: Session, slug: str) -> Post | None:
    return (
        db.query(Post)
        .options(joinedload(Post.author), joinedload(Post.tags), joinedload(Post.comments).joinedload(Comment.author), joinedload(Post.likes))
        .filter_by(slug=slug)
        .first()
    )


def get_post_by_id(db: Session, post_id: int) -> Post | None:
    return db.query(Post).options(joinedload(Post.author), joinedload(Post.tags)).filter_by(id=post_id).first()


def get_posts_by_user(db: Session, user_id: int, page: int = 1, size: int = 10):
    query = db.query(Post).options(joinedload(Post.author), joinedload(Post.tags)).filter_by(author_id=user_id)
    total = query.count()
    posts = (
        query.order_by(Post.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return posts, total


def update_post(db: Session, post: Post, data: dict) -> Post:
    for field in ("title", "slug", "content", "summary"):
        if data.get(field) is not None:
            setattr(post, field, data[field])
    if data.get("tags") is not None:
        post.tags = _get_or_create_tags(db, data["tags"])
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post: Post) -> None:
    db.delete(post)
    db.commit()


# ── Tag ──

def get_all_tags(db: Session) -> list[Tag]:
    return db.query(Tag).all()


def get_user_profile(db: Session, username: str) -> dict | None:
    user = db.query(User).filter_by(username=username).first()
    if not user:
        return None
    posts = (
        db.query(Post)
        .options(joinedload(Post.tags))
        .filter_by(author_id=user.id, status="published")
        .order_by(Post.created_at.desc())
        .all()
    )
    return {"user": user, "posts": posts}


# ── Like ──

def like_post(db: Session, user_id: int, post_id: int) -> dict:
    db.execute(likes.insert().values(user_id=user_id, post_id=post_id))
    db.commit()
    count = db.query(likes).filter_by(post_id=post_id).count()
    return {"liked": True, "likes_count": count}


def unlike_post(db: Session, user_id: int, post_id: int) -> dict:
    db.execute(likes.delete().where(likes.c.user_id == user_id, likes.c.post_id == post_id))
    db.commit()
    count = db.query(likes).filter_by(post_id=post_id).count()
    return {"liked": False, "likes_count": count}


# ── Comment ──

def create_comment(db: Session, user_id: int, post_id: int, content: str) -> Comment:
    comment = Comment(content=content, post_id=post_id, user_id=user_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
