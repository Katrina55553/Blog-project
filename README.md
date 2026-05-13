# Blog Project / 博客项目

A minimalist, high-performance personal technical blog system powered by **Vue 3** + **FastAPI**.

基于 **Vue 3** + **FastAPI** 的极简高性能个人技术博客系统。

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

| Method | Path                      | Description / 说明                       |
| ------ | ------------------------- | ---------------------------------------- |
| GET    | `/api/posts`              | Article list (?page=&size=&tag=&q=)      |
| GET    | `/api/posts/{slug}`       | Article detail + nested comments + likes |
| GET    | `/api/tags`               | All tags                                 |
| GET    | `/api/users/{username}`   | User profile + published posts           |
| POST   | `/api/auth/register`      | Register                                 |
| POST   | `/api/auth/login`         | Login → JWT                              |

### Authenticated / 需登录

| Method | Path                       | Description / 说明                |
| ------ | -------------------------- | --------------------------------- |
| GET    | `/api/auth/me`             | Current user info                 |
| PUT    | `/api/auth/me`             | Update avatar, bio, github_url    |
| PUT    | `/api/auth/password`       | Change password                   |
| GET    | `/api/admin/posts`         | My articles (paginated)           |
| POST   | `/api/admin/posts`         | Create article                    |
| GET    | `/api/admin/posts/{id}`    | Get for editing (author or admin) |
| PUT    | `/api/admin/posts/{id}`    | Update (author or admin)          |
| DELETE | `/api/admin/posts/{id}`    | Delete (author or admin)          |
| POST   | `/api/comments`            | Post comment (or reply)           |
| POST   | `/api/likes/{post_id}`     | Like (idempotent)                 |
| DELETE | `/api/likes/{post_id}`     | Unlike                            |

## Project Structure / 项目结构

```
blog-project/
├── backend/
│   ├── main.py          # FastAPI app, routes, middleware
│   ├── models.py        # SQLAlchemy ORM (User, Post, Tag, Comment, likes)
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── crud.py          # Database CRUD + build_comment_tree()
│   ├── auth.py          # JWT, bcrypt, get_current_user, get_optional_user
│   ├── database.py      # SQLAlchemy engine & session (PostgreSQL)
│   ├── seed.py          # Idempotent test data seeder
│   └── requirements.txt # Direct deps only
├── frontend/src/
│   ├── App.vue          # Navbar, theme, hamburger, global components
│   ├── style.css        # 26 CSS variables, light/dark theme
│   ├── router/index.js  # 10 routes, lazy-load, auth guard, scrollBehavior
│   ├── stores/auth.js   # Pinia: user, token, localStorage persistence
│   ├── api/             # Axios client & API modules
│   │   ├── client.js    # Axios instance, auth interceptor, 401 redirect
│   │   ├── auth.js      # register(), login(), getMe(), updateMe()
│   │   ├── post.js      # Post CRUD + getMyPosts()
│   │   ├── comment.js   # createComment(postId, content, parentId?)
│   │   ├── like.js      # likePost(), unlikePost()
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
│       ├── HomeView.vue         # Article list + search + tag filter
│       ├── PostDetailView.vue   # Article detail + nested comments + likes
│       ├── LoginView.vue        # Login form
│       ├── RegisterView.vue     # Registration form
│       ├── AdminDashboard.vue   # My articles table
│       ├── AdminPostEdit.vue    # Markdown editor (textarea + live preview)
│       ├── UserProfile.vue      # User info + their published posts
│       ├── ProfileEdit.vue      # Edit avatar, bio, github_url
│       └── NotFoundView.vue     # 404 page
├── docker-compose.yml  # PostgreSQL 16 + backend + frontend
├── .env.example        # Environment variable template
└── TODO.md             # Priority-sorted feature backlog
```

## Features / 功能

| Feature / 功能                | Description / 说明                          |
| ----------------------------- | ------------------------------------------- |
| Article CRUD / 文章管理        | Markdown rendering (highlight.js)           |
| Nested comments / 评论嵌套回复  | Multi-level threaded replies (楼中楼)        |
| Likes / 点赞                   | Idempotent like/unlike, persists across visits |
| Tag filtering / 标签筛选       | Click to filter by tag                      |
| Full-text search / 全文搜索     | Searches title + content                    |
| User profiles / 用户主页        | Avatar, bio, GitHub link                    |
| Profile editing / 编辑资料      | Avatar, bio, GitHub, password change        |
| Admin dashboard / 后台管理      | Personal article management                 |
| JWT auth / JWT 认证             | 24h expiry, bcrypt hashing                  |
| Toast notifications / 消息提示  | Success/error toast (replaces alert)         |
| Confirm dialog / 确认弹窗       | Modal confirm (replaces confirm)             |
| Back to top / 回到顶部          | Floating button with smooth scroll           |
| Responsive layout / 响应式      | Hamburger menu at ≤640px                    |
| Dark mode / 暗色模式            | Toggle + auto-detect system preference       |
| Skeleton loading / 骨架屏       | Shimmer animations on all data views         |
| Rate limiting / 速率限制        | Auth and write endpoints (slowapi)           |
| HTML sanitization / HTML 过滤   | Bleach whitelist-based filtering            |
| Docker deploy / 容器化部署      | Multi-service docker-compose                 |
