from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.utils.logger import setup_logger, generate_trace_id, set_trace_id, get_trace_id
from src.utils.exceptions import RAGException
from datetime import datetime

logger = setup_logger(__name__)


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add trace ID to all requests."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate and set trace ID
        trace_id = generate_trace_id()
        set_trace_id(trace_id)
        
        # Add to request state
        request.state.trace_id = trace_id
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "trace_id": trace_id
            }}
        )
        
        # Process request
        response = await call_next(request)
        
        # Add trace ID to response headers
        response.headers["X-Trace-ID"] = trace_id
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={"extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "trace_id": trace_id
            }}
        )
        
        return response


async def rag_exception_handler(request: Request, exc: RAGException):
    """Handle custom RAG exceptions."""
    logger.error(
        f"RAG Exception: {exc.message}",
        extra={"extra_fields": {
            "status_code": exc.status_code,
            "details": exc.details,
            "trace_id": get_trace_id()
        }}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "detail": exc.details,
            "trace_id": get_trace_id()
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={"extra_fields": {
            "exception_type": type(exc).__name__,
            "trace_id": get_trace_id()
        }},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if logger.level <= 10 else None,  # Show details in debug
            "trace_id": get_trace_id()
        }
    )
