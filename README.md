# Forum / 论坛系统

A minimalist, high-performance community forum powered by **Vue 3** + **FastAPI**.

基于 **Vue 3** + **FastAPI** 的极简高性能社区论坛。

## Tech Stack / 技术栈

| Layer 层     | Technology 技术                           |
| ------------ | ----------------------------------------- |
| Frontend 前端 | Vue 3 · Vite · Vue Router · Pinia · Axios |
| Backend 后端  | FastAPI · SQLAlchemy · JWT                |
| Database 数据库 | PostgreSQL (dev + prod)                   |
| Auth 认证     | JWT (24h expiry, bcrypt)                  |
| Deploy 部署   | Docker · docker-compose                   |

## Getting Started / 快速开始

### Option A: Docker (recommended) / Docker 部署

```bash
cp .env.example .env
# Edit .env — fill in SECRET_KEY
docker compose up -d
```

App: `http://localhost:80` · API: `http://localhost:8000`

### Option B: Manual / 手动启动

**Prerequisites / 环境要求:** Python 3.12+ / Node.js 24+ / PostgreSQL

```bash
# Database — start via Docker or local install
docker compose up db -d        # PG only, or use local PostgreSQL

# Backend
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows: venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

API: `http://localhost:8000` · Swagger: `http://localhost:8000/docs` · App: `http://localhost:5173`

### Seed Data / 测试数据

```bash
cd backend
source venv/Scripts/activate   # or venv\Scripts\activate.bat
python seed.py                 # admin / admin123
```

## API Overview / API 概览

### Public / 公开

| Method | Path                      | Description / 说明                    |
| ------ | ------------------------- | ------------------------------------- |
| GET    | `/api/topics`             | Topic list (?page=&size=&q=)          |
| GET    | `/api/topics/{id}`        | Topic detail + nested comments + likes |
| GET    | `/api/users/{username}`   | User profile + their topics           |
| POST   | `/api/auth/register`      | Register                              |
| POST   | `/api/auth/login`         | Login → JWT                           |

### Authenticated / 需登录

| Method | Path                          | Description / 说明             |
| ------ | ----------------------------- | ------------------------------ |
| GET    | `/api/auth/me`                | Current user info              |
| PUT    | `/api/auth/me`                | Update avatar, bio, github_url |
| PUT    | `/api/auth/password`          | Change password                |
| GET    | `/api/topics/{id}/edit`       | Get topic for editing          |
| POST   | `/api/topics`                 | Create topic                   |
| PUT    | `/api/topics/{id}`            | Update topic (author/admin)    |
| DELETE | `/api/topics/{id}`            | Delete topic (author/admin)    |
| POST   | `/api/comments`               | Post comment (or reply)        |
| DELETE | `/api/comments/{id}`          | Delete comment (author/admin)  |
| POST   | `/api/likes/{topic_id}`       | Like (idempotent)              |
| DELETE | `/api/likes/{topic_id}`       | Unlike                         |
| GET    | `/api/notifications`          | Notification list              |
| GET    | `/api/notifications/unread-count` | Unread count              |
| PUT    | `/api/notifications/{id}/read` | Mark as read                  |
| PUT    | `/api/notifications/read-all` | Mark all read                  |

## Project Structure / 项目结构

```
forum/
├── backend/
│   ├── main.py          # FastAPI app, routes, middleware
│   ├── models.py        # SQLAlchemy ORM (User, Topic, Comment, Notification, likes)
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── crud.py          # Database CRUD + build_comment_tree()
│   ├── auth.py          # JWT, bcrypt, get_current_user, get_optional_user
│   ├── database.py      # SQLAlchemy engine & session (PostgreSQL)
│   ├── migrations/      # SQL migration scripts
│   ├── seed.py          # Idempotent test data seeder
│   └── requirements.txt # Direct deps only
├── frontend/src/
│   ├── App.vue          # Navbar, notification bell, theme, hamburger, global components
│   ├── style.css        # 26 CSS variables, light/dark theme
│   ├── router/index.js  # 10 routes, lazy-load, auth guard, scrollBehavior
│   ├── stores/auth.js   # Pinia: user, token, localStorage persistence
│   ├── api/             # Axios client & API modules
│   │   ├── client.js    # Axios instance, auth interceptor, 401 redirect
│   │   ├── auth.js      # register(), login(), getMe(), updateMe()
│   │   ├── topic.js     # Topic CRUD functions
│   │   ├── comment.js   # createComment(), deleteComment()
│   │   ├── like.js      # likeTopic(), unlikeTopic()
│   │   ├── notification.js # Notification API
│   │   └── user.js      # getUserProfile()
│   ├── components/      # Shared components
│   │   ├── AppToast.vue       # Toast notification display
│   │   ├── BackToTop.vue      # Floating back-to-top button
│   │   ├── CommentItem.vue    # Recursive nested comment rendering
│   │   └── ConfirmDialog.vue  # Modal confirmation dialog
│   ├── composables/     # Module-level reactive state
│   │   ├── toast.js     # showToast.success/error/info()
│   │   └── confirm.js   # showConfirm(msg) → Promise<boolean>
│   └── views/           # Page components (lazy-loaded)
│       ├── HomeView.vue         # Topic list + search + pagination
│       ├── TopicDetailView.vue   # Topic detail + nested comments + likes
│       ├── TopicEditView.vue    # Markdown editor (textarea + live preview)
│       ├── NotificationsView.vue # Notification list with read/unread states
│       ├── LoginView.vue        # Login form
│       ├── RegisterView.vue     # Registration form
│       ├── UserProfile.vue      # User info + their topics
│       ├── ProfileEdit.vue      # Edit avatar, bio, github_url
│       └── NotFoundView.vue     # 404 page
├── docs/superpowers/   # Design specs & implementation plans
├── docker-compose.yml  # PostgreSQL 16 + backend + frontend
└── .env.example        # Environment variable template
```

## Features / 功能

| Feature / 功能                | Description / 说明                          |
| ----------------------------- | ------------------------------------------- |
| Topic CRUD / 帖子管理           | Markdown rendering (highlight.js)           |
| Nested comments / 评论嵌套回复  | Multi-level threaded replies (楼中楼)        |
| Likes / 点赞                   | Idempotent like/unlike                      |
| Full-text search / 全文搜索     | Searches title + content                    |
| Notifications / 通知提醒        | Reply notifications with unread badge       |
| User profiles / 用户主页        | Avatar, bio, topic/comment counts           |
| Profile editing / 编辑资料      | Avatar, bio, GitHub, password change        |
| JWT auth / JWT 认证             | 24h expiry, bcrypt hashing                  |
| Toast notifications / 消息提示  | Success/error toast                         |
| Confirm dialog / 确认弹窗       | Modal confirm for destructive actions       |
| Back to top / 回到顶部          | Floating button with smooth scroll           |
| Responsive layout / 响应式      | Hamburger menu at ≤640px                    |
| Dark mode / 暗色模式            | Toggle + auto-detect system preference       |
| Skeleton loading / 骨架屏       | Shimmer animations on all data views         |
| Rate limiting / 速率限制        | Auth and write endpoints (slowapi)           |
| HTML sanitization / HTML 过滤   | Bleach whitelist-based filtering            |
| Docker deploy / 容器化部署      | Multi-service docker-compose                 |
