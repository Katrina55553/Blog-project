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
| GET    | `/api/posts`       | Paginated article list   |
| GET    | `/api/posts/{slug}`| Article detail + comments|
| GET    | `/api/tags`        | All tags                 |
| POST   | `/api/auth/register`| Register                |
| POST   | `/api/auth/login`  | Login (returns JWT)      |

### Authenticated

| Method | Path                     | Description       |
| ------ | ------------------------ | ----------------- |
| POST   | `/api/admin/posts`       | Create article    |
| PUT    | `/api/admin/posts/{id}`  | Update article    |
| DELETE | `/api/admin/posts/{id}`  | Delete article    |
| GET    | `/api/auth/me`           | Current user info |
| POST   | `/api/comments`          | Post a comment    |

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
        ├── views/        # Page components
        ├── components/   # Reusable UI
        ├── router/       # Vue Router config
        ├── stores/       # Pinia stores
        └── api/          # Axios client & API functions
```

## Features

- Article CRUD with Markdown support
- Tag-based filtering
- Comment system
- JWT authentication
- Responsive layout
- Dark mode
