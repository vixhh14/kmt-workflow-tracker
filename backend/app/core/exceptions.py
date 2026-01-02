from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from sqlalchemy.exc import IntegrityError, DataError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation errors (422) during REQUEST"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Validation error in request data",
            "detail": str(exc.errors()),
            "details": exc.errors()
        }
    )

async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
    """Handles Pydantic validation errors (500) during RESPONSE serialization"""
    print(f"⚠️ RESPONSE VALIDATION ERROR: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "RESPONSE_VALIDATION_ERROR",
            "message": "The server failed to serialize the response.",
            "detail": str(exc.errors())
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handles Database Integrity Constraints (409 Conflict)"""
    error_msg = str(exc.orig) if exc.orig else str(exc)
    
    if "unique constraint" in error_msg.lower():
        msg = "A record with this unique value already exists."
        code = "UNIQUE_VIOLATION"
    elif "foreign key constraint" in error_msg.lower():
        msg = "Operation failed due to referenced data. Check related fields."
        code = "FOREIGN_KEY_VIOLATION"
    else:
        msg = "Database integrity error."
        code = "INTEGRITY_ERROR"

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error_code": code,
            "message": msg,
            "detail": error_msg
        }
    )

async def data_error_handler(request: Request, exc: DataError):
    """Handles Data format errors (400 Bad Request)"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error_code": "DATA_ERROR",
            "message": "Invalid data format provided.",
            "detail": str(exc.orig) if exc.orig else str(exc)
        }
    )

async def operational_error_handler(request: Request, exc: OperationalError):
    """Handles Connection/Operational errors (503 Service Unavailable)"""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error_code": "DB_CONNECTION_ERROR",
            "message": "Database connection failed. Please try again later.",
            "detail": "Database connection failed."
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handles normal HTTPExceptions (404, 401, 403, etc)"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "detail": exc.detail
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*"
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for 500 errors"""
    error_msg = str(exc)
    trace = traceback.format_exc()
    print(f"❌ UNHANDLED EXCEPTION: {trace}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred.",
            "detail": error_msg 
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )
