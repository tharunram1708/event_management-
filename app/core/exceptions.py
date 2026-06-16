from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status


class AppError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    message = "Request could not be processed"

    def __init__(self, message: str | None = None, status_code: int | None = None) -> None:
        self.message = message or self.message
        self.status_code = status_code or self.status_code


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Resource not found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    message = "Resource already exists"


class PermissionDeniedError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    message = "You do not have permission to perform this action"


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


def serialize_validation_errors(exc: RequestValidationError) -> list[dict]:
    errors = []
    for error in exc.errors():
        serialized_error = dict(error)
        context = serialized_error.get("ctx")
        if isinstance(context, dict):
            serialized_error["ctx"] = {key: str(value) for key, value in context.items()}
        errors.append(serialized_error)
    return errors


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": "Validation failed", "errors": serialize_validation_errors(exc)}),
    )
