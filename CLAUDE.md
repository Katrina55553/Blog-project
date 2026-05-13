# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A personal technical blog system — minimalist, high-performance. Full-stack: Vue 3 frontend, FastAPI backend, SQLite database, JWT authentication.

## Commands

```bash
# Backend
cd backend
source venv/Scripts/activate   # or venv\Scripts\activate.bat on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev                     # :5173, proxies /api → :8000
npm run build                   # production build → dist/
npm run preview                 # preview production build locally

# Seed test data (backend venv)
cd backend && python seed.py    # admin / admin123
```

Both servers must run simultaneously. Frontend dev server proxies `/api` to backend via `vite.config.js`.

Swagger docs at `http://localhost:8000/docs` — useful for testing endpoints during development.

There is no test suite or linter configured yet.

## Backend Architecture

```
backend/
├── main.py          # FastAPI app, all routes, middleware (CORS, logging, rate limit)
├── models.py        # SQLAlchemy ORM: User, Post, Tag, Comment, likes, post_tags
├── schemas.py       # Pydantic request/response models with field_validators
├── crud.py          # Pure DB access functions (no HTTP concerns)
├── auth.py          # bcrypt hashing, JWT create/decode, get_current_user, require_admin
├── database.py      # SQLAlchemy engine, session, Base, get_db dependency
├── seed.py          # Idempotent test data seeder
└── requirements.txt
```

### Key patterns

- **Public routes** under `/api/`, **admin routes** under `/api/admin/`
- **`get_current_user`** dependency resolves User from JWT, used by all protected routes
- **`require_admin`** dependency (auth.py) wraps get_current_user + checks is_admin — available for future use
- **`get_db`** dependency provides per-request SQLAlchemy session
- **`_author_or_admin(post, user)`** helper: permits action if user is the author OR has is_admin=True
- Content is sanitized with `bleach` (whitelist-based HTML filtering) on create/update
- Rate limiting via `slowapi`: 5/min register, 10/min login/post/comment
- Request logging middleware logs method, path, status, and duration
- Unified JSON error responses for 404, 500, 429
- Slug uniqueness checked before create/update (409 Conflict on duplicate)
- Post existence checked before creating comment (404 if missing)
- `|` in post list response dicts uses `joinedload(Post.author)` and `joinedload(Post.tags)`

### API endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/posts` | No | Paginated list (?page=&size=&tag=&q=) |
| GET | `/api/posts/{slug}` | No | Article detail + comments + likes_count |
| GET | `/api/tags` | No | All tags |
| GET | `/api/users/{username}` | No | User profile + published posts |
| POST | `/api/auth/register` | No | Register |
| POST | `/api/auth/login` | No | Login → JWT |
| GET | `/api/auth/me` | Yes | Current user info |
| PUT | `/api/auth/me` | Yes | Update avatar, bio, github_url |
| GET | `/api/admin/posts` | Yes | Current user's posts (paginated) |
| POST | `/api/admin/posts` | Yes | Create article |
| GET | `/api/admin/posts/{id}` | Yes | Get article for editing (author or admin) |
| PUT | `/api/admin/posts/{id}` | Yes | Update (author or admin, 403 otherwise) |
| DELETE | `/api/admin/posts/{id}` | Yes | Delete (author or admin, 403 otherwise) |
| POST | `/api/comments` | Yes | Post a comment |
| POST | `/api/likes/{post_id}` | Yes | Like a post |
| DELETE | `/api/likes/{post_id}` | Yes | Unlike a post |

## Frontend Architecture

```
frontend/src/
├── App.vue           # Navbar, theme toggle, hamburger menu, router-view
├── main.js           # App bootstrap: Pinia + Router
├── style.css         # Global styles: 26 CSS variables, light/dark theme
├── router/index.js   # 10 routes, lazy-loaded, beforeEach auth guard, scrollBehavior, afterEach title
├── stores/auth.js    # Pinia: user, token, localStorage persistence, login calls restoreUser()
├── api/
│   ├── client.js     # Axios instance, auth interceptor, 401 redirect with ?redirect=
│   ├── auth.js       # register(), login(), getMe(), updateMe()
│   ├── post.js       # CRUD functions + getMyPosts()
│   ├── comment.js    # createComment()
│   ├── like.js       # likePost(), unlikePost()
│   └── user.js       # getUserProfile()
└── views/
    ├── HomeView.vue         # Article list, pagination, tag filter, full-text search
    ├── PostDetailView.vue   # Markdown rendering (marked + highlight.js), comments, likes, author actions
    ├── LoginView.vue        # Login form with redirect support, autocomplete attrs
    ├── RegisterView.vue     # Registration form with validation, autocomplete attrs
    ├── AdminDashboard.vue   # My articles table, pagination, skeleton loading, edit/delete
    ├── AdminPostEdit.vue    # Markdown editor (textarea + live preview), new/edit modes
    ├── UserProfile.vue      # User info (avatar, bio, github) + their published posts
    ├── ProfileEdit.vue      # Edit avatar, bio, github_url
    └── NotFoundView.vue     # 404 page
```

### Key patterns

- **Auth guard**: `router.beforeEach` checks localStorage token for `/admin/*` and `/profile/*` routes, redirects to `/login` with `?redirect=` param
- **Admin guard**: `_author_or_admin` backend helper; frontend nav shows admin links for all logged-in users (personal dashboard)
- **Theme system**: 26 CSS custom properties (colors, shadows, fonts, spacing). Dark mode toggle in navbar, persisted to localStorage, auto-detects `prefers-color-scheme` on first visit
- **Responsive**: Hamburger menu at ≤640px, sticky navbar, outside-click to close
- **Loading states**: Skeleton shimmer animations on HomeView (card list), PostDetailView (content), AdminDashboard (table rows), AdminPostEdit (form fields)
- **Error states**: Retry buttons on load failure across all data-fetching views
- **Comment model**: `username` property delegates to `author.username` relationship for Pydantic serialization
- **Slug generation**: Frontend auto-generates slug from title via `watch(title)` (handles paste too)
- **Search**: Full-width search input on HomeView; backend uses `or_(Post.title.ilike(), Post.content.ilike())` via `?q=` param
- **Likes**: `likes` table (user_id + post_id composite PK); like count in post responses; `is_liked` tracked client-side
- **Post responses**: `author` object (id, username, avatar) eagerly loaded; `tags` coerced from ORM objects to strings
- **Pagination**: Snake-case params (page, size); returns items, total, page, size, pages
- **Page titles**: `router.afterEach` sets `document.title` from route meta (format: "Page - My Blog")
- **Login flow**: `login()` stores token + partial user, immediately calls `restoreUser()` to get full user with `id` and `is_admin`

## Database

PostgreSQL for both dev and production. Default connection: `postgresql://blog:blog@localhost:5432/blog`.

**Local PG via Docker:** `docker compose up db -d` starts just the PostgreSQL 16 container. Override via `DATABASE_URL` env var if needed.

- **users**: id, username, password_hash, avatar, bio, github_url, is_admin, created_at
- **posts**: id, title, slug, content, summary, author_id (FK), status, created_at, updated_at
- **tags**: id, name
- **post_tags**: post_id, tag_id (many-to-many)
- **comments**: id, content, post_id, user_id, created_at
- **likes**: user_id, post_id (composite PK, many-to-many between users and posts)

## Security

- Passwords hashed with bcrypt (passlib)
- JWT with 24h expiry (python-jose, HS256)
- SECRET_KEY read from `os.environ.get("SECRET_KEY", "dev-fallback")`
- HTML sanitization via bleach (whitelist tags/attributes only)
- Rate limiting via slowapi on auth and write endpoints
- CORS origin configurable via `CORS_ORIGIN` env var (default `localhost:5173`)
- JWT `sub` claim explicitly cast to `int` in `get_current_user` to avoid type mismatch
