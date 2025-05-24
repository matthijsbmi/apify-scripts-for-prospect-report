"""
Exception handling and custom exceptions for the application.
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog

logger = structlog.get_logger(__name__)


class BaseAppException(Exception):
    """Base exception class for application-specific exceptions."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ApifyActorException(BaseAppException):
    """Exception raised when Apify actor operations fail."""
    
    def __init__(
        self,
        message: str,
        actor_id: Optional[str] = None,
        run_id: Optional[str] = None,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        details = details or {}
        if actor_id:
            details["actor_id"] = actor_id
        if run_id:
            details["run_id"] = run_id
        super().__init__(message, status_code, details)


class CostExceededException(BaseAppException):
    """Exception raised when cost limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        current_cost: float,
        max_budget: float,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        details = details or {}
        details.update({
            "current_cost": current_cost,
            "max_budget": max_budget,
            "cost_exceeded_by": current_cost - max_budget,
        })
        super().__init__(message, status.HTTP_402_PAYMENT_REQUIRED, details)


class ValidationException(BaseAppException):
    """Exception raised for data validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class RateLimitException(BaseAppException):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS, details)


class ProspectAnalysisException(BaseAppException):
    """Exception raised during prospect analysis operations."""
    
    def __init__(
        self,
        message: str,
        prospect_id: Optional[str] = None,
        stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        details = details or {}
        if prospect_id:
            details["prospect_id"] = prospect_id
        if stage:
            details["analysis_stage"] = stage
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


async def base_app_exception_handler(
    request: Request, exc: BaseAppException
) -> ORJSONResponse:
    """Handle application-specific exceptions."""
    logger.error(
        "Application exception occurred",
        exception_type=type(exc).__name__,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
        method=request.method,
    )
    
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": type(exc).__name__,
                "message": exc.message,
                "details": exc.details,
            },
            "path": request.url.path,
            "method": request.method,
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> ORJSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
    )
    
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code,
            },
            "path": request.url.path,
            "method": request.method,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> ORJSONResponse:
    """Handle request validation errors."""
    logger.warning(
        "Validation error occurred",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method,
    )
    
    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": {
                    "errors": exc.errors(),
                },
            },
            "path": request.url.path,
            "method": request.method,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    """Handle unexpected exceptions."""
    logger.error(
        "Unexpected exception occurred",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    
    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
                "details": {
                    "exception_type": type(exc).__name__,
                },
            },
            "path": request.url.path,
            "method": request.method,
        },
    )


def add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers to the FastAPI application."""
    app.add_exception_handler(BaseAppException, base_app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler) 