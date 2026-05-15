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
    db.query(User).filter_by(id=user_id).update({"comment_count": User.comment_count + 1})
    db.commit()
    db.refresh(comment)

    # Notify topic author (don't self-notify)
    topic = db.query(Topic).filter_by(id=topic_id).first()
    if topic and topic.author_id != user_id:
        notif = Notification(
            user_id=topic.author_id,
            type="reply",
            topic_id=topic_id,
            comment_id=comment.id,
        )
        db.add(notif)

    # Notify parent comment author (don't self-notify, don't double-notify topic author)
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
