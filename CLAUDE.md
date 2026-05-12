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
├── models.py        # SQLAlchemy ORM: User, Post, Tag, Comment, post_tags
├── schemas.py       # Pydantic request/response models with field_validators
├── crud.py          # Pure DB access functions (no HTTP concerns)
├── auth.py          # bcrypt hashing, JWT create/decode, get_current_user dependency
├── database.py      # SQLAlchemy engine, session, Base, get_db dependency
├── seed.py          # Idempotent test data seeder
└── requirements.txt
```

### Key patterns

- **Public routes** under `/api/`, **admin routes** under `/api/admin/`
- **`get_current_user`** dependency resolves User from JWT, used by all protected routes
- **`get_db`** dependency provides per-request SQLAlchemy session
- Content is sanitized with `bleach` (whitelist-based HTML filtering) on create/update
- Rate limiting via `slowapi`: 5/min register, 10/min login/post/comment
- Request logging middleware logs method, path, status, and duration
- Unified JSON error responses for 404, 500, 429

### API endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/posts` | No | Paginated list (?page=&size=&tag=) |
| GET | `/api/posts/{slug}` | No | Article detail + comments |
| GET | `/api/tags` | No | All tags |
| POST | `/api/auth/register` | No | Register |
| POST | `/api/auth/login` | No | Login → JWT |
| GET | `/api/auth/me` | Yes | Current user info |
| POST | `/api/admin/posts` | Yes | Create article |
| GET | `/api/admin/posts/{id}` | Yes | Get article for editing |
| PUT | `/api/admin/posts/{id}` | Yes | Update (author only, 403 otherwise) |
| DELETE | `/api/admin/posts/{id}` | Yes | Delete (author only, 403 otherwise) |
| POST | `/api/comments` | Yes | Post a comment |

## Frontend Architecture

```
frontend/src/
├── App.vue           # Navbar, theme toggle, hamburger menu, router-view
├── main.js           # App bootstrap: Pinia + Router
├── style.css         # Global styles: 26 CSS variables, light/dark theme
├── router/index.js   # 8 routes, lazy-loaded, beforeEach auth guard
├── stores/auth.js    # Pinia: user, token, localStorage persistence
├── api/
│   ├── client.js     # Axios instance, auth interceptor, 401 redirect
│   ├── auth.js       # register(), login(), getMe()
│   ├── post.js       # CRUD functions
│   └── comment.js    # createComment()
└── views/
    ├── HomeView.vue         # Article list, pagination, tag filter, skeleton loading
    ├── PostDetailView.vue   # Markdown rendering (marked + highlight.js), comments, author actions
    ├── LoginView.vue        # Login form with redirect support
    ├── RegisterView.vue     # Registration form with validation
    ├── AdminDashboard.vue   # My articles table, edit/delete
    ├── AdminPostEdit.vue    # Markdown editor (textarea + live preview), new/edit modes
    └── NotFoundView.vue     # 404 page
```

### Key patterns

- **Auth guard**: `router.beforeEach` checks localStorage token for `/admin/*` routes, redirects to `/login` with `?redirect=` param
- **Theme system**: 26 CSS custom properties (colors, shadows, fonts, spacing). Dark mode toggle in navbar, persisted to localStorage, auto-detects `prefers-color-scheme` on first visit
- **Responsive**: Hamburger menu at ≤640px, sticky navbar
- **Loading states**: Skeleton shimmer animations on HomeView (card list) and PostDetailView (content)
- **Error states**: Retry buttons on load failure
- **Comment model**: `username` property delegates to `author.username` relationship for Pydantic serialization
- **Slug generation**: Frontend auto-generates slug from title via `@input` on the title field. Paste events don't trigger this (known limitation) — use `@change` if fixing that
- **Dead code**: `components/HelloWorld.vue` is the default Vite scaffold component and is unused

## Database

SQLite for development (file-based, zero config). The README references PostgreSQL for production, but no PostgreSQL setup or migration tooling is implemented yet.

- **users**: id, username, password_hash, avatar, bio, github_url, created_at
- **posts**: id, title, slug, content, summary, author_id (FK), status, created_at, updated_at
- **tags**: id, name
- **post_tags**: post_id, tag_id (many-to-many)
- **comments**: id, content, post_id, user_id, created_at

## Security

- Passwords hashed with bcrypt (passlib)
- JWT with 24h expiry (python-jose, HS256)
- HTML sanitization via bleach (whitelist tags/attributes only)
- Rate limiting via slowapi on auth and write endpoints
- CORS restricted to `localhost:5173`
- **JWT `sub` type gotcha**: `payload.get("sub")` returns a string, but `User.id` is an integer. SQLAlchemy's `filter_by` handles the coercion, so it works, but if you ever use `filter(User.id == ...)` or direct comparison, you must cast to `int` first