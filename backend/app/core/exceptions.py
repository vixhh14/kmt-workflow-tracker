from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
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
