# Recipe Management Application

![Tests](https://github.com/jrtex/backofmyhouse/actions/workflows/test.yml/badge.svg)

A full-stack application for managing recipes, built with FastAPI, SvelteKit, and PostgreSQL.

## Features

- User authentication with JWT tokens (HTTP-only cookies)
- Role-based access control (admin/standard users)
- Recipe CRUD with ingredients and instructions
- Categories and tags for organization
- Search and filtering
- Admin panel for user and content management
- Rate limiting on authentication endpoints
- Docker deployment

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **Frontend**: SvelteKit, Tailwind CSS
- **Infrastructure**: Docker, Nginx

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Running with Docker

1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set a secure JWT secret:
   ```
   JWT_SECRET=your-secure-random-string
   ```

3. Start the application:
   ```bash
   docker-compose up --build
   ```

4. Access the application at http://localhost

### Local Development

#### Backend

1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy and configure environment:
   ```bash
   cp .env.example .env
   ```

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

#### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Access at http://localhost:5173

## First User

The first user to register automatically receives the `admin` role. Subsequent users are assigned the `standard` role.

## API Documentation

When running the backend, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backofmyhouse/
├── backend/
│   ├── app/
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── routers/     # API routes
│   │   ├── services/    # Business logic
│   │   └── middleware/  # Rate limiting
│   ├── alembic/         # Database migrations
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── routes/      # SvelteKit pages
│   │   └── lib/         # Stores, API client, components
│   └── Dockerfile
├── docker-compose.yml
└── nginx.conf
```

## API Endpoints

| Method | Endpoint | Auth | Role | Description |
|--------|----------|------|------|-------------|
| POST | /api/auth/register | No | - | Register new user |
| POST | /api/auth/login | No | - | Login |
| POST | /api/auth/logout | Yes | Any | Logout |
| POST | /api/auth/refresh | Yes | Any | Refresh token |
| GET | /api/auth/me | Yes | Any | Current user |
| GET | /api/recipes | Yes | Any | List recipes |
| GET | /api/recipes/{id} | Yes | Any | Get recipe |
| POST | /api/recipes | Yes | Any | Create recipe |
| PUT | /api/recipes/{id} | Yes | Owner/Admin | Update recipe |
| DELETE | /api/recipes/{id} | Yes | Owner/Admin | Delete recipe |
| GET | /api/categories | Yes | Any | List categories |
| POST | /api/categories | Yes | Admin | Create category |
| PUT | /api/categories/{id} | Yes | Admin | Update category |
| DELETE | /api/categories/{id} | Yes | Admin | Delete category |
| GET | /api/tags | Yes | Any | List tags |
| POST | /api/tags | Yes | Admin | Create tag |
| DELETE | /api/tags/{id} | Yes | Admin | Delete tag |
| GET | /api/users | Yes | Admin | List users |
| POST | /api/users | Yes | Admin | Create user |
| PUT | /api/users/{id} | Yes | Admin | Update user |
| DELETE | /api/users/{id} | Yes | Admin | Delete user |

## Security

- Passwords hashed with bcrypt
- JWT tokens stored in HTTP-only cookies
- Rate limiting on auth endpoints (5 requests/minute)
- CORS configured for frontend origin
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy ORM
