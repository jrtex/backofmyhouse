# Claude Code Instructions

## Project Overview

Self-hosted recipe management application with user authentication and role-based access control. See `PRD.md` for full requirements and roadmap.

## Public Repository Notice

This codebase is intended for publication on a public repository. Never commit sensitive information including:
- Passwords, API keys, or tokens
- Personal emails or individual names
- Database credentials or connection strings
- Any other secrets or PII

Use environment variables and `.env` files (excluded via `.gitignore`) for configuration.

## Tech Stack

- **Backend**: FastAPI (Python) with SQLAlchemy ORM and Alembic migrations
- **Database**: PostgreSQL
- **Frontend**: React or Svelte SPA
- **Deployment**: Docker with docker-compose

## Development Guidelines

### Backend
- Use Pydantic models for request/response validation
- Create Alembic migrations for all schema changes
- Follow REST conventions for API endpoints
- Implement proper error handling with appropriate HTTP status codes
- Keep business logic in service layers, not route handlers

### Database
- Use UUIDs for primary keys
- Always create migrations rather than modifying models directly
- Test migrations both up and down before committing

### Frontend
- Keep components small and focused
- Store auth tokens securely (prefer HTTP-only cookies)
- Implement proper loading and error states
- Use TypeScript if using React

### Docker
- Do not modify `docker-compose.override.yml` - this is user-customizable
- Keep images minimal and production-ready
- Use multi-stage builds where appropriate

### Testing
- Use test-driven development (TDD) for all new features and refactoring
- Write tests before implementing functionality
- Ensure all tests pass before considering work complete

## File Structure Reference

```
/backend        - FastAPI application
/frontend       - SPA application
/docker         - Docker configuration files
PRD.md          - Product requirements and roadmap
```

## Before Making Changes

1. Read `PRD.md` for feature context and requirements
2. Check existing code patterns before introducing new ones
3. Create database migrations for any schema changes
4. Ensure changes work in Docker environment
