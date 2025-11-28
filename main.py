from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from src.api.routes import router
from src.api.middleware import (
    TraceIDMiddleware,
    rag_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from src.core.config import get_settings
from src.utils.exceptions import RAGException
from src.utils.logger import setup_logger

# Setup
settings = get_settings()
logger = setup_logger(__name__, level=settings.log_level)

# Create FastAPI app
app = FastAPI(
    title="RAG-Powered Document Q&A",
    version=settings.app_version,
    docs_url=None,  # Disable Swagger UI
    redoc_url=None,  # Disable ReDoc
    description="A Retrieval-Augmented Generation system for document Q&A using Gemini AI"
)

# Add middlewares
app.add_middleware(TraceIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        # Add your production domains here:
        # "https://yourdomain.com",
        # "https://app.yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Trace-ID"],
)

# Add exception handlers
app.add_exception_handler(RAGException, rag_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(router, prefix=settings.api_prefix, tags=["RAG"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint - Serve Chat UI
@app.get("/", include_in_schema=False)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# API info endpoint
@app.get("/api/info")
async def api_info():
    return {
        "message": "RAG Document Q&A API",
        "version": settings.app_version,
        "documentation": "/docs"
    }


# RapiDoc - API Documentation
@app.get("/docs", include_in_schema=False)
async def rapidoc():
    return HTMLResponse("""
    <!doctype html>
    <html>
        <head>
            <meta charset="utf-8">
            <title>RAG-Powered Document Q&A</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script type="module" src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"></script>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                }
                rapi-doc {
                    width: 100%;
                    height: 100vh;
                    --font-size-regular: 20px;
                    --font-size-mono: 18px;
                    --font-size-small: 16px;
                }
                /* Custom header styling */
                .custom-header {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 30px 20px;
                    background: #2d2d2d;
                    border-bottom: 2px solid #C9989F;
                }
                .custom-header h1 {
                    margin: 0;
                    color: #C9989F;
                    font-size: 32px;
                    font-weight: 600;
                    font-family: 'Segoe UI', system-ui, sans-serif;
                }
                /* Make response areas scrollable and wrap text */
                rapi-doc::part(section-response-body) {
                    max-height: 600px;
                    overflow: auto !important;
                }
                rapi-doc::part(code-block) {
                    white-space: pre-wrap !important;
                    word-wrap: break-word !important;
                    overflow-wrap: break-word !important;
                    max-width: 100% !important;
                }
            </style>
        </head>
        <body>
            <div class="custom-header">
                <h1>RAG-Powered Document Q&A</h1>
            </div>
            <rapi-doc
                spec-url="/openapi.json"
                theme="dark"
                bg-color="#1a1a1a"
                text-color="#f0f0f0"
                primary-color="#C9989F"
                nav-bg-color="#2d2d2d"
                nav-text-color="#ffffff"
                nav-hover-bg-color="#3d3d3d"
                nav-accent-color="#C9989F"
                render-style="focused"
                show-header="false"
                show-info="false"
                allow-authentication="false"
                allow-server-selection="false"
                allow-api-list-style-selection="false"
                allow-try="true"
                allow-spec-url-load="false"
                allow-spec-file-load="false"
                api-key-name="Authorization"
                api-key-location="header"
                font-size="large"
                regular-font="Segoe UI, system-ui"
                mono-font="'Fira Code', monospace"
                response-area-height="600px"
            >
            </rapi-doc>
        </body>
    </html>
    """)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
