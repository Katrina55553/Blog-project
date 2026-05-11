from database import SessionLocal
from models import Post, Tag, User
from auth import hash_password


def seed():
    db = SessionLocal()

    admin = db.query(User).filter_by(username="admin").first()
    if not admin:
        admin = User(username="admin", password_hash=hash_password("admin123"))
        db.add(admin)
        db.flush()

    tags = {}
    for name in ["Python", "FastAPI"]:
        tag = db.query(Tag).filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags[name] = tag

    existing = db.query(Post).filter_by(slug="hello-world").first()
    if not existing:
        post = Post(
            title="Hello World",
            slug="hello-world",
            content="This is my first blog post. Welcome to my blog!",
            summary="First post",
            author_id=admin.id,
            tags=list(tags.values()),
        )
        db.add(post)
        db.commit()
        print("Seed data inserted: admin user + 2 tags + 1 post")
    else:
        print("Seed data already exists, skipping")

    db.close()


if __name__ == "__main__":
    seed()
