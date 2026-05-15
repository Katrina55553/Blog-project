-- 001_blog_to_forum.sql
-- 将博客数据模型迁移为论坛数据模型

BEGIN;

-- 1. 重命名 posts → topics
ALTER TABLE posts RENAME TO topics;

-- 2. 删除废弃列
ALTER TABLE topics DROP COLUMN slug;
ALTER TABLE topics DROP COLUMN summary;
ALTER TABLE topics DROP COLUMN status;

-- 3. 添加 view_count
ALTER TABLE topics ADD COLUMN view_count INTEGER DEFAULT 0;

-- 4. 重命名评论外键
ALTER TABLE comments RENAME COLUMN post_id TO topic_id;

-- 5. 删除旧的 likes 表，重建
DROP TABLE IF EXISTS likes;
CREATE TABLE likes (
    user_id INTEGER NOT NULL REFERENCES users(id),
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    PRIMARY KEY (user_id, topic_id)
);

-- 6. 删除 post_tags 和 tags
DROP TABLE IF EXISTS post_tags;
DROP TABLE IF EXISTS tags;

-- 7. 新建 notifications 表
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    type VARCHAR NOT NULL DEFAULT 'reply',
    topic_id INTEGER REFERENCES topics(id),
    comment_id INTEGER REFERENCES comments(id),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. users 扩展
ALTER TABLE users ADD COLUMN topic_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN comment_count INTEGER DEFAULT 0;

COMMIT;
