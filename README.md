# User Management Service

A FastAPI-based user management service for registration, authentication, profile management, password reset workflows, and administrative user listing.

## Overview

This project provides a backend API for managing users in a multi-service environment. It includes JWT-based authentication, Redis token handling, PostgreSQL persistence, RabbitMQ messaging for password-reset workflows, and S3-backed profile image support.

The application is designed to run locally with Docker Compose and can also be started directly with Poetry for development.

## Features

- User signup and login
- JWT access and refresh tokens
- Redis-based token invalidation for refresh flow
- User profile retrieval and updates
- Profile image upload and deletion with S3-compatible storage
- Password reset request flow using RabbitMQ
- Role-based access control for admin/moderator operations
- Pagination, filtering, and sorting for user list queries
- Health check endpoint for service monitoring

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Redis
- RabbitMQ
- Alembic
- Pydantic & Pydantic Settings
- JWT (PyJWT)
- AWS SDK for S3 integration
- Pytest
- Docker / Docker Compose

## Project Structure

```text
.
├── .github/
├── scripts/
│   └── entrypoint.sh
├── src/
│   ├── api/
│   │   ├── dependencies/
│   │   └── routes/
│   ├── aws/
│   ├── db/
│   │   ├── migration/
│   │   └── models/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   ├── logger.py
│   ├── main.py
│   └── settings.py
├── tests/
│   ├── integration/
│   └── unit/
├── .dockerignore
├── .gitignore
├── .pre-commit-config.yaml
├── Dockerfile
├── README.md
├── alembic.ini
├── compose.yml
├── poetry.lock
├── pyproject.toml
├── pytest.ini
└── .env / .env.test (local environment files)
```

## Prerequisites

Before running the project, ensure you have:

- Python 3.11+
- Poetry
- Docker and Docker Compose
- PostgreSQL client access (optional, for manual verification)

## Environment Configuration

Create a `.env` file in the project root with the required variables. The application reads settings from `.env` using `pydantic-settings`.

Example:

```env
JWT_SECRET_KEY=your-super-secret-key

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_NAME=user_management

TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/postgres

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672

FRONTEND_URL=http://localhost

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=eu-central-1
AWS_S3_BUCKET=
```

For tests, the project also expects a `.env.test` file, which is used by the Docker Compose test database service.

## Installation

Install dependencies with Poetry:

```bash
poetry install
```

Activate the environment:

```bash
poetry shell
```

## Running the Application

### Option 1: Docker Compose (recommended)

```bash
docker compose up --build
```

This starts:

- FastAPI app on `http://localhost:8000`
- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`
- RabbitMQ management UI on `http://localhost:15672`

The app uses the startup script in `scripts/entrypoint.sh` and runs Uvicorn with auto-reload enabled.

### Option 2: Local development

```bash
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger UI is available at:

```text
http://localhost:8000/docs
```

## Database Migrations

This project uses Alembic for schema management.

Apply migrations:

```bash
poetry run alembic upgrade head
```

If you are using Docker Compose, the application container already boots with the project runtime and can be configured to work with the database services defined in `compose.yml`.

## API Endpoints

### Authentication

- `POST /auth/signup` — register a new user
- `POST /auth/login` — authenticate and receive JWT tokens
- `POST /auth/refresh-token` — refresh access token
- `POST /auth/reset-password` — request a password reset

### User

- `GET /user/me` — current user profile
- `PATCH /user/me` — update current user profile
- `DELETE /user/me` — delete current user
- `GET /user/{user_id}` — fetch a user by ID
- `PATCH /user/{user_id}` — update user by ID (admin-level access)
- `POST /me/image` — upload profile image
- `GET /{user_id}/image-url` — get presigned image URL
- `DELETE /me/image` — delete profile image

### Users listing

- `GET /users/` — list users with pagination, filtering, and sorting

### Health

- `GET /healthcheck` — service health status
- `GET /` — root endpoint

## Testing

Run the test suite:

```bash
poetry run pytest
```

For more focused runs:

```bash
poetry run pytest tests/unit -q
poetry run pytest tests/integration -q
```

## Linting and Formatting

The project includes formatting and quality tools configured in `pyproject.toml`.

```bash
poetry run black .
poetry run isort .
poetry run ruff check .
poetry run mypy src
```

## Notes

- The application is built around a modular FastAPI structure with route, service, and schema separation.
- Redis is used for token/session-related operations.
- RabbitMQ is used for asynchronous password-reset event processing.
- S3 storage is integrated for user profile image handling.

## License

This project does not currently include a license file. If needed, add one based on your project requirements.

## Contributing

Contributions are welcome. Please create a feature branch, make your changes, and open a pull request with a clear summary of the update.
