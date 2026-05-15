# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A minimalist, high-performance community forum system. Full-stack: Vue 3 frontend, FastAPI backend, PostgreSQL database, JWT authentication, Docker deployment.

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
├── models.py        # SQLAlchemy ORM: User, Topic, Comment, Notification, likes
├── schemas.py       # Pydantic request/response models with field_validators
├── crud.py          # Pure DB access functions (no HTTP concerns)
├── auth.py          # bcrypt hashing, JWT create/decode, get_current_user, get_optional_user
├── database.py      # SQLAlchemy engine, session, Base, get_db dependency
├── migrations/      # SQL migration scripts (001_blog_to_forum.sql)
├── seed.py          # Idempotent test data seeder
└── requirements.txt
```

### Key patterns

- All routes under `/api/` prefix, no separate admin sub-path
- **`get_current_user`** dependency resolves User from JWT, used by all protected routes
- **`get_optional_user`** dependency returns User or None — used by public routes that need auth context
- **`get_db`** dependency provides per-request SQLAlchemy session
- **`_author_or_admin(topic, user)`** helper: permits action if user is the author OR has is_admin=True
- **`_comment_author_or_admin(comment, user)`** helper: same pattern for comments
- Content is sanitized with `bleach` (whitelist-based HTML filtering) on create/update
- Rate limiting via `slowapi`: 5/min register, 10/min login/topic/comment
- Request logging middleware logs method, path, status, and duration
- Unified JSON error responses for 404, 500, 429
- Topic existence checked before creating comment (404 if missing)
- Comment parent_id validated against topic_id (ValueError → 400)
- `topic_count` and `comment_count` on users updated atomically via `User.topic_count + 1` expressions
- `view_count` incremented on topic detail view
- `is_liked` resolved server-side via `get_optional_user` on topic detail
- Notification records created on comment: topic author + parent comment author (no self-notification)

### API endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/topics` | No | Topic list (?page=&size=&q=) |
| GET | `/api/topics/{id}` | No | Topic detail + comments + likes_count + is_liked |
| GET | `/api/users/{username}` | No | User profile + their topics |
| POST | `/api/auth/register` | No | Register |
| POST | `/api/auth/login` | No | Login → JWT |
| GET | `/api/auth/me` | Yes | Current user info |
| PUT | `/api/auth/me` | Yes | Update avatar, bio, github_url |
| PUT | `/api/auth/password` | Yes | Change password |
| GET | `/api/topics/{id}/edit` | Yes | Get topic for editing (author/admin) |
| POST | `/api/topics` | Yes | Create topic |
| PUT | `/api/topics/{id}` | Yes | Update topic (author/admin, 403 otherwise) |
| DELETE | `/api/topics/{id}` | Yes | Delete topic (author/admin, 403 otherwise) |
| POST | `/api/comments` | Yes | Post a comment (triggers notifications) |
| DELETE | `/api/comments/{id}` | Yes | Delete comment (author/admin) |
| POST | `/api/likes/{topic_id}` | Yes | Like a topic |
| DELETE | `/api/likes/{topic_id}` | Yes | Unlike a topic |
| GET | `/api/notifications` | Yes | Notification list (?page=&size=) |
| GET | `/api/notifications/unread-count` | Yes | Unread notification count |
| PUT | `/api/notifications/{id}/read` | Yes | Mark notification as read |
| PUT | `/api/notifications/read-all` | Yes | Mark all notifications as read |

## Frontend Architecture

```
frontend/src/
├── App.vue           # Navbar, notification bell, theme toggle, hamburger, mounts global components (AppToast, ConfirmDialog, BackToTop)
├── main.js           # App bootstrap: Pinia + Router
├── style.css         # Global styles: 26 CSS variables, light/dark theme
├── router/index.js   # 10 routes, lazy-loaded, beforeEach auth guard, scrollBehavior, afterEach title
├── stores/auth.js    # Pinia: user, token, localStorage persistence, login calls restoreUser()
├── api/
│   ├── client.js     # Axios instance, auth interceptor, 401 redirect with ?redirect=
│   ├── auth.js       # register(), login(), getMe(), updateMe()
│   ├── topic.js      # CRUD functions: getTopics(), getTopicById(), createTopic(), updateTopic(), deleteTopic()
│   ├── comment.js    # createComment(topicId, content, parentId?), deleteComment()
│   ├── like.js       # likeTopic(), unlikeTopic()
│   ├── notification.js # getNotifications(), getUnreadCount(), markRead(), markAllRead()
│   └── user.js       # getUserProfile()
├── components/
│   ├── AppToast.vue       # Toast notifications (success/error/info), auto-dismiss, slide-in animation
│   ├── BackToTop.vue      # Floating back-to-top button, appears at scroll >400px, smooth scroll
│   ├── CommentItem.vue    # Recursive nested comment (楼中楼), inline reply form, indented threading
│   └── ConfirmDialog.vue  # Modal confirmation dialog, ESC/overlay to cancel, Promise-based
├── composables/
│   ├── toast.js     # Module-level reactive toast state, showToast.success/error/info()
│   └── confirm.js   # Module-level reactive confirm state, showConfirm(msg) → Promise<boolean>
└── views/
    ├── HomeView.vue         # Topic list, pagination, full-text search
    ├── TopicDetailView.vue   # Markdown rendering (marked + highlight.js), nested comments, likes, author actions
    ├── TopicEditView.vue    # Markdown editor (textarea + live preview), new/edit modes
    ├── NotificationsView.vue # Notification list, click to visit topic, mark read/all read
    ├── LoginView.vue        # Login form with redirect support, autocomplete attrs
    ├── RegisterView.vue     # Registration form with validation, autocomplete attrs
    ├── UserProfile.vue      # User info (avatar, bio, github) + topic/comment stats + their topics
    ├── ProfileEdit.vue      # Edit avatar, bio, github_url
    └── NotFoundView.vue     # 404 page
```

### Key patterns

- **Auth guard**: `router.beforeEach` checks localStorage token for routes with `meta.requiresAuth`, redirects to `/login` with `?redirect=` param
- **Optional auth**: `get_optional_user` dependency returns User or None — used by topic detail for `is_liked`
- **Author/Admin actions**: `_author_or_admin` backend helper; frontend shows edit/delete buttons to both author and admin
- **Theme system**: 26 CSS custom properties (colors, shadows, fonts, spacing). Dark mode toggle in navbar, persisted to localStorage, auto-detects `prefers-color-scheme` on first visit
- **Responsive**: Hamburger menu at ≤640px, sticky navbar, outside-click to close
- **Loading states**: Skeleton shimmer animations on HomeView (topic list), TopicDetailView (content), TopicEditView (form fields)
- **Error states**: Retry buttons on load failure across all data-fetching views
- **Toast/Confirm**: Module-level reactive state (composables/toast.js, composables/confirm.js). Components mounted once in App.vue. Any view imports `showToast`/`showConfirm` directly.
- **Nested comments**: `Comment.parent_id` (self-referential FK). `build_comment_tree()` in crud.py converts flat list to nested dicts. `CommentItem.vue` renders recursively with depth-based indentation.
- **Search**: Full-width search input on HomeView; backend uses `or_(Topic.title.ilike(), Topic.content.ilike())` via `?q=` param
- **Likes**: `likes` table (user_id + topic_id composite PK); `like_topic()` handles IntegrityError for idempotency; `is_liked` resolved server-side via optional auth
- **Notifications**: Created on comment (topic author + parent comment author). Navbar polls `/api/notifications/unread-count` every 30s. Badge shows unread count.
- **Pagination**: Snake-case params (page, size); returns items, total, page, size, pages
- **Page titles**: `router.afterEach` sets `document.title` from route meta (format: "Page - Forum")
- **Login flow**: `login()` stores token + partial user, immediately calls `restoreUser()` to get full user with `id` and `is_admin`
- **Topic list**: Returns comment_count, likes_count, last_comment_at for each topic; relative time display

## Database

PostgreSQL for both dev and production. Default connection: `postgresql://blog:blog@localhost:5432/blog`.

**Local PG via Docker:** `docker compose up db -d` starts just the PostgreSQL 16 container. Override via `DATABASE_URL` env var if needed.

- **users**: id, username, password_hash, avatar, bio, github_url, is_admin, topic_count, comment_count, created_at
- **topics**: id, title, content, author_id (FK), view_count, created_at, updated_at
- **comments**: id, content, topic_id (FK), user_id (FK), parent_id (self-ref FK), created_at
- **likes**: user_id + topic_id (composite PK, many-to-many between users and topics)
- **notifications**: id, user_id (FK), type, topic_id (FK), comment_id (FK), is_read, created_at

## Security

- Passwords hashed with bcrypt (bcrypt library)
- JWT with 24h expiry (python-jose, HS256)
- SECRET_KEY read from `os.environ.get("SECRET_KEY", "dev-fallback")`
- HTML sanitization via bleach (whitelist tags/attributes only)
- Rate limiting via slowapi on auth and write endpoints
- CORS origin configurable via `CORS_ORIGIN` env var (default `localhost:5173`)
- JWT `sub` claim explicitly cast to `int` in `get_current_user` to avoid type mismatch
- Notification FK cascade delete at database level — deleting topics/comments auto-removes related notifications
