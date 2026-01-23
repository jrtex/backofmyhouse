# Product Requirements Document: Recipe Management Application

## Overview

A self-hosted recipe management web application with user authentication and role-based access control. Designed for personal or small-team use with a focus on simplicity, privacy, and extensibility.

---

## Goals

- Provide a private, self-hosted solution for storing and organizing recipes
- Support multiple users with role-based permissions
- Enable easy deployment via Docker
- Maintain a clean, responsive UI for browsing and managing recipes
- Build a foundation for future AI-powered features (e.g., photo-to-recipe import)

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| ORM | SQLAlchemy + Alembic (migrations) |
| Frontend | React or Svelte SPA |
| Deployment | Docker + docker-compose |
| Authentication | JWT tokens + bcrypt password hashing |

---

## User Roles & Permissions

### Admin
- Full CRUD on all recipes
- Manage categories and tags
- Create and manage users
- Configure API keys for external services
- Access all API endpoints

### Standard User
- View all recipes (read-only for others' recipes)
- Create, edit, and delete own recipes
- Use shared categories and tags

### Unauthenticated
- No access (all routes require authentication)

---

## MVP Features (v1.0)

### 1. User Authentication
- User registration (first registered user becomes admin automatically)
- Login/logout with JWT tokens
- Password hashing with bcrypt
- Role assignment (admin/standard)
- Token refresh mechanism

### 2. Recipe Management
Each recipe includes:
- Title
- Description
- Ingredients (with quantities)
- Instructions (ordered steps)
- Prep time
- Cook time
- Servings
- Notes
- Creator reference (user_id)
- Category (single)
- Tags (multiple)

**Access Control:**
- All authenticated users can view all recipes
- Only the creator or an admin can edit/delete a recipe

### 3. Organization & Categorization
- **Categories**: Mutually exclusive groupings (e.g., Breakfast, Dinner, Desserts)
- **Tags**: Flexible labels (e.g., vegetarian, quick, italian)
- Only admins can create/modify categories and tags

### 4. Admin Panel
- User management (create, view, modify roles)
- Category management
- Tag management
- Future: API key configuration for LLM services

---

## API Endpoints

### Authentication
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/auth/register` | Public | Register new user |
| POST | `/api/auth/login` | Public | Authenticate and receive JWT |
| GET | `/api/auth/me` | Authenticated | Get current user info |

### Recipes
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/recipes` | Authenticated | List recipes (filterable by category/tags) |
| GET | `/api/recipes/{id}` | Authenticated | Get single recipe |
| POST | `/api/recipes` | Authenticated | Create recipe |
| PUT | `/api/recipes/{id}` | Owner/Admin | Update recipe |
| DELETE | `/api/recipes/{id}` | Owner/Admin | Delete recipe |

### Categories & Tags
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/categories` | Authenticated | List categories |
| POST | `/api/categories` | Admin | Create category |
| GET | `/api/tags` | Authenticated | List tags |
| POST | `/api/tags` | Admin | Create tag |

### Users (Admin)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/users` | Admin | List all users |
| POST | `/api/users` | Admin | Create new user |

---

## Database Schema

### User
| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | Primary key |
| username | String | Unique, required |
| email | String | Unique, required |
| hashed_password | String | Required |
| role | Enum | admin/standard |
| created_at | DateTime | Auto-generated |

### Recipe
| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | Primary key |
| title | String | Required |
| description | Text | Optional |
| ingredients | JSON | Required |
| instructions | JSON | Required (ordered steps) |
| prep_time | Integer | Minutes, optional |
| cook_time | Integer | Minutes, optional |
| servings | Integer | Optional |
| notes | Text | Optional |
| user_id | UUID | Foreign key (User) |
| category_id | UUID | Foreign key (Category), optional |
| created_at | DateTime | Auto-generated |
| updated_at | DateTime | Auto-updated |

### Category
| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Unique, required |
| description | Text | Optional |

### Tag
| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Unique, required |

### RecipeTag (Junction)
| Field | Type | Constraints |
|-------|------|-------------|
| recipe_id | UUID | Foreign key |
| tag_id | UUID | Foreign key |

---

## Docker Configuration

### Services
- **backend**: FastAPI application
- **frontend**: Static SPA served via nginx or node
- **db**: PostgreSQL database

### Files
- `Dockerfile` - Backend container
- `docker-compose.yml` - Main orchestration
- `docker-compose.override.yml` - Local development overrides (user-editable, not overwritten on updates)

### Volumes
- PostgreSQL data persistence
- Uploaded files (future feature)

### Environment Variables
| Variable | Description |
|----------|-------------|
| `JWT_SECRET_KEY` | Secret for signing tokens |
| `DATABASE_URL` | PostgreSQL connection string |
| `CORS_ORIGINS` | Allowed frontend origins |

---

## Frontend Structure

### Pages
- `/login` - Login form
- `/register` - Registration form
- `/` - Recipe list (home)
- `/recipes/{id}` - Recipe detail view
- `/recipes/new` - Create recipe form
- `/recipes/{id}/edit` - Edit recipe form
- `/admin` - Admin panel (admin only)
- `/admin/users` - User management
- `/admin/categories` - Category management
- `/admin/tags` - Tag management

### Features
- Protected routes with auth redirect
- Role-based navigation display
- Recipe filtering by category and tags
- Responsive design

---

## Security Considerations

- JWT secret stored in environment variables
- Tokens stored in HTTP-only cookies (preferred) or localStorage
- Token refresh mechanism to extend sessions
- Rate limiting on authentication endpoints
- Input validation and sanitization on all endpoints
- SQL injection prevention via ORM
- XSS prevention via proper frontend escaping

---

## Future Roadmap

### v1.1 - Enhanced Organization
- Recipe search (full-text)
- Sorting options (date, name, cook time)
- Recipe favoriting/bookmarking

### v1.2 - Media Support
- Recipe photo uploads
- Multiple images per recipe
- Image optimization and thumbnails

### v1.3 - AI Integration
- Photo-to-recipe import using LLM vision APIs
- Recipe text extraction from images
- Configurable API keys for different LLM providers

### v1.4 - Sharing & Export
- Public recipe sharing links (optional)
- Recipe export (PDF, print-friendly)
- Import from common formats

### v1.5 - Meal Planning
- Weekly meal planner
- Shopping list generation from selected recipes
- Ingredient aggregation

### v2.0 - Advanced Features
- Recipe scaling (adjust servings)
- Nutritional information (manual or API-based)
- Recipe versioning/history
- Comments and ratings (for multi-user households)

---

## Success Metrics

- Application deploys successfully via single `docker-compose up` command
- First user registration creates admin account automatically
- All CRUD operations function correctly with proper access control
- Frontend displays appropriate UI based on user role
- Database migrations run without data loss

---

## Open Questions

*None currently - document will be updated as questions arise during implementation.*
