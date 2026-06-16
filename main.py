from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api import attendance, audit_logs, auth, categories, dashboard, events, registrations, reports, roles, tickets
from app.core.config import get_settings
from app.core.exceptions import AppError, app_error_handler, validation_error_handler
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import *  # noqa: F401,F403 - imported so SQLAlchemy sees all tables.
from app.services.bootstrap import seed_roles


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_roles(db)
    yield


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="FastAPI backend for events, registrations, tickets, attendance, reports, and audit logs.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    app.include_router(auth.router)
    app.include_router(roles.router)
    app.include_router(categories.router)
    app.include_router(events.router)
    app.include_router(registrations.router)
    app.include_router(tickets.router)
    app.include_router(attendance.router)
    app.include_router(dashboard.router)
    app.include_router(reports.router)
    app.include_router(audit_logs.router)

    @app.get("/health", tags=["System"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
