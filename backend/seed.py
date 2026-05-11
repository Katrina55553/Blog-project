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

    tag_python = Tag(name="Python")
    tag_fastapi = Tag(name="FastAPI")
    db.add_all([tag_python, tag_fastapi])
    db.flush()

    post = Post(
        title="Hello World",
        slug="hello-world",
        content="This is my first blog post. Welcome to my blog!",
        summary="First post",
        author_id=admin.id,
        tags=[tag_python, tag_fastapi],
    )
    db.add(post)
    db.commit()
    db.close()
    print("Seed data inserted: admin user + 2 tags + 1 post")


if __name__ == "__main__":
    seed()
