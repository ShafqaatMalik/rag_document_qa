from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from typing import List
from datetime import datetime
from pathlib import Path
from src.api.schemas import (
    QueryRequest, QueryResponse, DocumentUploadResponse,
    DocumentListResponse, DocumentDeleteResponse, HealthResponse
)
from src.rag.pipeline import RAGPipeline
from src.core.config import get_settings, Settings
from src.utils.logger import setup_logger, get_trace_id
from src.utils.exceptions import ValidationError

logger = setup_logger(__name__)

# Create router
router = APIRouter()

# Initialize RAG pipeline (singleton)
_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Dependency to get RAG pipeline instance."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


def get_settings_dep() -> Settings:
    """Dependency to get settings."""
    return get_settings()


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description="Upload and process a document (PDF, TXT, DOCX, MD)"
)
async def upload_document(
    file: UploadFile = File(...),
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
    settings: Settings = Depends(get_settings_dep)
):
    """Upload and ingest a document."""
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.allowed_extensions:
        raise ValidationError(
            f"File type not supported. Allowed: {', '.join(settings.allowed_extensions)}",
            details={'filename': file.filename, 'extension': file_ext}
        )
    
    # Validate file size
    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise ValidationError(
            f"File too large. Max size: {settings.max_upload_size} bytes",
            details={'filename': file.filename, 'size': len(content)}
        )
    
    # Reset file pointer
    await file.seek(0)
    
    # Ingest document
    result = pipeline.ingest_document(file.file, file.filename)
    result['trace_id'] = get_trace_id()
    
    return result


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query documents",
    description="Ask a question and get an AI-generated answer with sources"
)
async def query_documents(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """Query the document collection."""
    
    result = pipeline.query(
        question=request.question,
        top_k=request.top_k,
        filters=request.filters,
        doc_ids=request.doc_ids
    )
    
    return result


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List documents",
    description="Get a list of all uploaded documents"
)
async def list_documents(
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """List all documents."""
    
    documents = pipeline.list_documents()
    
    return {
        'documents': documents,
        'total': len(documents),
        'trace_id': get_trace_id()
    }


@router.delete(
    "/documents/{doc_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete document",
    description="Delete a document and all its chunks"
)
async def delete_document(
    doc_id: str,
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """Delete a document by ID."""
    
    result = pipeline.delete_document(doc_id)
    
    return result


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the service is running"
)
async def health_check(settings: Settings = Depends(get_settings_dep)):
    """Health check endpoint."""
    
    return {
        'status': 'healthy',
        'version': settings.app_version,
        'timestamp': datetime.utcnow().isoformat()
    }
