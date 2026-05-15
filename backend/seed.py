from database import Base, SessionLocal, engine
from models import Topic, User
from auth import hash_password


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    admin = db.query(User).filter_by(username="admin").first()
    if not admin:
        admin = User(username="admin", password_hash=hash_password("admin123"), is_admin=True)
        db.add(admin)
        db.flush()

    existing = db.query(Topic).first()
    if not existing:
        topic = Topic(
            title="欢迎来到论坛",
            content="这是论坛的第一个帖子。欢迎加入社区讨论！\n\n## 论坛规则\n\n- 请保持友善和尊重\n- 支持 Markdown 格式\n- 点击左上角 **发帖** 开始新话题",
            author_id=admin.id,
        )
        db.add(topic)
        db.commit()
        print("Seed data inserted: admin user + 1 topic")
    else:
        print("Seed data already exists, skipping")

    db.close()


if __name__ == "__main__":
    seed()
