# Event Management System API

Production-style FastAPI backend for events, registrations, tickets, attendance, dashboards, reports, audit logs, JWT auth, and role-based access control.

## Official References Used

- FastAPI security with OAuth2, password hashing, and JWT: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- FastAPI database dependencies: https://fastapi.tiangolo.com/tutorial/sql-databases/
- SQLAlchemy typed declarative ORM: https://docs.sqlalchemy.org/en/latest/orm/declarative_tables.html
- Alembic autogenerate migrations: https://alembic.sqlalchemy.org/en/latest/autogenerate.html

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

For MySQL, update `.env`:

```env
DATABASE_URL=mysql+pymysql://event_user:event_password@127.0.0.1:3306/event_management
JWT_SECRET_KEY=replace-with-a-long-random-secret
```

To start only MySQL with Docker:

```powershell
docker compose up -d mysql
```

If you want to create the MySQL database manually instead of using Alembic, run:

```powershell
mysql -u root -p < database/mysql_schema.sql
```

To check the Python-to-MySQL connection:

```powershell
.\.venv\Scripts\python scripts\check_mysql_connection.py
```

## Run

```powershell
alembic upgrade head
uvicorn main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Database Migrations

```powershell
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

The app also creates tables on startup for local development convenience. Use Alembic migrations for real deployments.

## Tests

```powershell
pytest
```

## Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## Roles

The startup process seeds these roles:

- `Admin`
- `Organizer`
- `Participant`

New users register as `Participant`. Admins can assign roles through `POST /roles/assign`.

## Main Modules

- `app/api`: FastAPI routers
- `app/models`: SQLAlchemy models
- `app/schemas`: Pydantic request/response schemas
- `app/core`: config, security, dependencies, exception handling
- `app/services`: audit, bootstrap, email, ticket helpers
- `alembic`: migration setup and versions
