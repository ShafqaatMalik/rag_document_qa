from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Any, Optional


class QueryRequest(BaseModel):
    """Request schema for document queries."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "What are vector embeddings?",
                "top_k": 5,
                "filters": None,
                "doc_ids": ["string"]
            }
        }
    )

    question: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Optional[Dict[str, Any]] = None
    doc_ids: Optional[List[str]] = Field(default=None, description="Filter by specific document IDs")

    @field_validator('question')
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Question cannot be empty')
        return v.strip()


class SourceInfo(BaseModel):
    """Source information for citations."""
    doc_id: str
    filename: str
    text_snippet: str
    score: float


class QueryResponse(BaseModel):
    """Response schema for document queries."""
    answer: str
    sources: List[SourceInfo]
    trace_id: str
    latency_seconds: float


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload."""
    doc_id: str
    filename: str
    chunks_created: int
    upload_date: str
    trace_id: str


class DocumentInfo(BaseModel):
    """Document information schema."""
    doc_id: str
    filename: str
    upload_date: str


class DocumentListResponse(BaseModel):
    """Response schema for document listing."""
    documents: List[DocumentInfo]
    total: int
    trace_id: str


class DocumentDeleteResponse(BaseModel):
    """Response schema for document deletion."""
    doc_id: str
    deleted: bool
    trace_id: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    trace_id: Optional[str] = None
