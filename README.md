# Blog Project / 博客项目

A minimalist, high-performance personal technical blog system powered by **Vue 3** + **FastAPI**.
基于 **Vue 3** + **FastAPI** 的极简高性能个人技术博客系统。

## Tech Stack / 技术栈

| Layer 层    | Technology 技术                          |
| ----------- | ---------------------------------------- |
| Frontend 前端 | Vue 3 · Vite · Vue Router · Pinia · Axios |
| Backend 后端  | FastAPI · SQLAlchemy · JWT               |
| Database 数据库 | SQLite (dev) / PostgreSQL (prod)         |
| Auth 认证    | JWT (24h expiry, bcrypt hashing)          |

## Getting Started / 快速开始

### Prerequisites / 环境要求

- Python 3.12+
- Node.js 24+

### Backend / 后端

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows: venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API: `http://localhost:8000` · Swagger: `http://localhost:8000/docs`

### Frontend / 前端

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173` (API proxy → `:8000`)

### Seed Data / 测试数据

```bash
cd backend
venv/Scripts/python seed.py
```

Creates test user `admin / admin123` with a sample post.
创建测试用户 `admin / admin123` 及一篇示例文章。

## API Overview / API 概览

### Public / 公开接口

| Method | Path                     | Description / 说明                       |
| ------ | ------------------------ | ---------------------------------------- |
| GET    | `/api/posts`             | Article list 文章列表 (?page=&size=&tag=&q=) |
| GET    | `/api/posts/{slug}`      | Article detail 文章详情 + comments + likes |
| GET    | `/api/tags`              | All tags 所有标签                          |
| GET    | `/api/users/{username}`  | User profile 用户主页 + their posts        |
| POST   | `/api/auth/register`     | Register 注册                              |
| POST   | `/api/auth/login`        | Login 登录 (returns JWT)                   |

### Authenticated / 需登录

| Method | Path                       | Description / 说明                         |
| ------ | -------------------------- | ------------------------------------------ |
| GET    | `/api/auth/me`             | Current user info 当前用户信息               |
| PUT    | `/api/auth/me`             | Update profile 更新资料 (avatar, bio, github) |
| GET    | `/api/admin/posts`         | My articles 我的文章 (paginated)             |
| POST   | `/api/admin/posts`         | Create article 创建文章                      |
| GET    | `/api/admin/posts/{id}`    | Get for editing 获取文章用于编辑             |
| PUT    | `/api/admin/posts/{id}`    | Update 更新 (author or admin)               |
| DELETE | `/api/admin/posts/{id}`    | Delete 删除 (author or admin)               |
| POST   | `/api/comments`            | Post comment 发表评论                        |
| POST   | `/api/likes/{post_id}`     | Like 点赞                                   |
| DELETE | `/api/likes/{post_id}`     | Unlike 取消点赞                              |

## Project Structure / 项目结构

```
blog-project/
├── backend/
│   ├── main.py          # FastAPI app & routes 应用和路由
│   ├── models.py        # SQLAlchemy ORM models 数据模型
│   ├── schemas.py       # Pydantic request/response schemas 请求响应模型
│   ├── crud.py          # Database CRUD functions 数据库操作
│   ├── auth.py          # JWT & password utilities 认证工具
│   ├── database.py      # SQLAlchemy engine & session 数据库引擎
│   └── seed.py          # Test data seeder 测试数据种子
└── frontend/
    └── src/
        ├── App.vue           # Navbar, theme toggle, search 导航/主题/搜索
        ├── style.css         # Global CSS variables & themes 全局样式
        ├── router/index.js   # Vue Router config 路由配置
        ├── stores/auth.js    # Pinia auth store 认证状态
        ├── api/              # Axios client & API modules 接口模块
        │   ├── client.js     # Axios instance, auth interceptor
        │   ├── auth.js       # Login, register, profile
        │   ├── post.js       # Post CRUD
        │   ├── comment.js    # Comment creation
        │   ├── like.js       # Like/unlike
        │   └── user.js       # User profile
        └── views/            # Page components 页面组件
            ├── HomeView.vue         # Article list 文章列表
            ├── PostDetailView.vue   # Article detail 文章详情
            ├── LoginView.vue        # Login 登录
            ├── RegisterView.vue     # Register 注册
            ├── AdminDashboard.vue   # My articles 我的文章
            ├── AdminPostEdit.vue    # Markdown editor 编辑器
            ├── UserProfile.vue      # User profile 用户主页
            ├── ProfileEdit.vue      # Edit profile 编辑资料
            └── NotFoundView.vue     # 404 page
```

## Features / 功能

| Feature 功能                  | Description 说明                              |
| ----------------------------- | --------------------------------------------- |
| Article CRUD 文章管理          | Markdown rendering (highlight.js) 代码高亮     |
| Tag filtering 标签筛选         | Click to filter by tag 点击标签筛选            |
| Full-text search 全文搜索      | Searches title + content 搜索标题和正文         |
| Comment system 评论系统        | Logged-in users can comment 登录后可评论        |
| Likes 点赞                    | Like/unlike posts 点赞/取消点赞                 |
| User profiles 用户主页         | Avatar, bio, GitHub link 头像/简介/GitHub      |
| Profile editing 个人资料       | Edit avatar, bio, github 编辑头像/简介/GitHub  |
| Admin dashboard 后台管理       | Personal article management 个人文章管理        |
| Admin permission 管理员权限    | Admins can manage all posts 管理员可管理所有文章 |
| JWT authentication JWT 认证   | 24h expiry, bcrypt hashing                    |
| Responsive layout 响应式布局   | Hamburger menu on mobile 移动端汉堡菜单          |
| Dark mode 暗色模式             | Auto-detects system preference 自动检测系统偏好  |
| Skeleton loading 骨架屏加载    | Shimmer animations 闪烁动画                    |
| Rate limiting 速率限制         | Auth and write endpoints 认证和写入接口          |
| HTML sanitization HTML 过滤   | Bleach whitelist-based 基于白名单过滤            |
