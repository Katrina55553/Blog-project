# Blog Project

A minimalist, high-performance personal technical blog system powered by **Vue 3** + **FastAPI**.

## Tech Stack

| Layer    | Technology                          |
| -------- | ----------------------------------- |
| Frontend | Vue 3 · Vite · Vue Router · Pinia · Axios |
| Backend  | FastAPI · SQLAlchemy · JWT          |
| Database | SQLite (dev) / PostgreSQL (prod)    |
| Auth     | JWT (24h expiry, bcrypt hashing)    |

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 24+

### Backend

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows: venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API available at: `http://localhost:8000`  
Swagger docs at: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at: `http://localhost:5173`  
API requests are proxied to `http://localhost:8000`

### Seed Data

```bash
cd backend
venv/Scripts/python seed.py
```

Creates test user `admin / admin123` with a sample post.

## API Overview

### Public

| Method | Path               | Description              |
| ------ | ------------------ | ------------------------ |
| GET    | `/api/posts`       | Paginated article list (?page=&size=&tag=&q=) |
| GET    | `/api/posts/{slug}`| Article detail + comments + likes |
| GET    | `/api/tags`        | All tags                 |
| GET    | `/api/users/{username}` | User profile + their posts |
| POST   | `/api/auth/register`| Register                |
| POST   | `/api/auth/login`  | Login (returns JWT)      |

### Authenticated

| Method | Path                     | Description       |
| ------ | ------------------------ | ----------------- |
| GET    | `/api/auth/me`           | Current user info |
| PUT    | `/api/auth/me`           | Update profile (avatar, bio, github) |
| GET    | `/api/admin/posts`       | My articles (paginated) |
| POST   | `/api/admin/posts`       | Create article    |
| GET    | `/api/admin/posts/{id}`  | Get article for editing |
| PUT    | `/api/admin/posts/{id}`  | Update article (author or admin) |
| DELETE | `/api/admin/posts/{id}`  | Delete article (author or admin) |
| POST   | `/api/comments`          | Post a comment    |
| POST   | `/api/likes/{post_id}`   | Like a post       |
| DELETE | `/api/likes/{post_id}`   | Unlike a post     |

## Project Structure

```
blog-project/
├── backend/
│   ├── main.py          # FastAPI app & routes
│   ├── models.py        # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── crud.py          # Database CRUD functions
│   ├── auth.py          # JWT & password utilities
│   ├── database.py      # SQLAlchemy engine & session
│   └── seed.py          # Test data seeder
└── frontend/
    └── src/
        ├── App.vue           # Navbar, theme toggle, search
        ├── style.css         # Global CSS variables & themes
        ├── router/index.js   # Vue Router config
        ├── stores/auth.js    # Pinia auth store
        ├── api/              # Axios client & API modules
        │   ├── client.js     # Axios instance, auth interceptor
        │   ├── auth.js       # Login, register, profile
        │   ├── post.js       # Post CRUD
        │   ├── comment.js    # Comment creation
        │   ├── like.js       # Like/unlike
        │   └── user.js       # User profile
        └── views/            # Page components
            ├── HomeView.vue         # Article list, search, tag filter
            ├── PostDetailView.vue   # Article detail, comments, likes
            ├── LoginView.vue        # Login form
            ├── RegisterView.vue     # Registration form
            ├── AdminDashboard.vue   # My articles management
            ├── AdminPostEdit.vue    # Markdown editor (new/edit)
            ├── UserProfile.vue      # User profile & their posts
            ├── ProfileEdit.vue      # Edit own profile
            └── NotFoundView.vue     # 404 page
```

## Features

- Article CRUD with Markdown rendering (highlight.js)
- Tag-based filtering
- Full-text search (title + content)
- Comment system
- Like/unlike posts
- User profiles with avatar, bio, GitHub link
- Profile editing
- Admin dashboard (personal article management)
- Admin permission control (admins can manage all posts)
- JWT authentication (24h expiry, bcrypt)
- Responsive layout with hamburger menu
- Dark mode (auto-detects system preference)
- Skeleton loading states
- Rate limiting on auth and write endpoints
- HTML sanitization (bleach whitelist)
