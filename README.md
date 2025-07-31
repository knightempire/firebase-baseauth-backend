# FastAPI Backend - Bio Auth App

## Features
- FastAPI with modular MVC-like structure
- JWT authentication and refresh tokens
- Google sign-in via Firebase Admin SDK
- MySQL (CloudSQL) database
- Environment-based configuration (all secrets in `.env`)
- Docker and docker-compose support
- Health check with database status

## Project Structure
```
backend/
  app/
    core/      # Config, DB, auth helpers
    models/    # Pydantic models
    routes/    # API endpoints (auth, bio, refresh, health)
    main.py    # FastAPI entrypoint
  requirements.txt
  .env         # All secrets and config (never commit to git)
  Dockerfile
  docker-compose.yml
  README.md
```

## Setup

### 1. Environment Variables
Copy `.env.example` to `.env` and fill in all required values. **All variables are required.**

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Locally
```bash
uvicorn app.main:app --reload
```

### 4. Run with Docker
```bash
docker-compose up --build
```

## Endpoints
- `POST /login` - Google sign-in, returns JWT
- `GET /bio` - Get user bio (JWT required)
- `POST /bio` - Update user bio (JWT required)
- `POST /refresh` - Refresh JWT using refresh token
- `GET /` - Health check (shows DB status)

## Notes
- All config/secrets must be set in `.env` (see `.env.example`).
- `.env` is ignored by git for security.
- Database must be available and schema must include a `users` table with `email`, `name`, and `bio` columns.
- For production, use secure values and proper secret management.

---

**Questions?** Open an issue or contact the maintainer.
