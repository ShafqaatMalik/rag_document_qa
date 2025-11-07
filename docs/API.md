# API Documentation

Complete API reference for the RAG Document Q&A system.

## Base URL

- Local: `http://localhost:8000/api/v1`
- Production: `https://your-app.onrender.com/api/v1`

## Endpoints

### 1. Upload Document

Upload and process a document for Q&A.

**Endpoint**: `POST /documents/upload`

**Request**:
- Content-Type: `multipart/form-data`
- Body: File upload

**Response** (201 Created):
```json
{
  "doc_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "chunks_created": 15,
  "upload_date": "2025-01-15T10:30:00Z",
  "trace_id": "abc123-def456"
}
```

### 2. Query Documents

Ask a question and get an AI-generated answer.

**Endpoint**: `POST /query`

**Request**:
```json
{
  "question": "What is the main topic?",
  "top_k": 5,
  "filters": {
    "doc_id": "optional-filter-by-document"
  },
  "doc_ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

**Parameters**:
- `question` (string, required): The question to ask
- `top_k` (integer, optional): Number of chunks to retrieve (1-20, default: 5)
- `filters` (object, optional): Additional metadata filters
- `doc_ids` (array, optional): List of specific document IDs to query

**Features**:
- **Similarity Threshold**: Results below 0.3 similarity are automatically filtered out
- **Multi-Document Filtering**: Use `doc_ids` to query only specific documents for more accurate results

**Response** (200 OK):
```json
{
  "answer": "Based on the documents, the return policy allows...",
  "sources": [
    {
      "doc_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "policy.pdf",
      "text_snippet": "Returns are accepted within 30 days...",
      "score": 0.95
    }
  ],
  "trace_id": "abc123-def456",
  "latency_seconds": 2.15
}
```

**Note**: If no results meet the similarity threshold (0.3), you'll receive an informative message explaining why no relevant information was found.

### 3. List Documents

Get all uploaded documents.

**Endpoint**: `GET /documents`

**Response** (200 OK):
```json
{
  "documents": [
    {
      "doc_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "policy.pdf",
      "upload_date": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "trace_id": "abc123-def456"
}
```

**Usage Tip**: Use the `doc_id` from this response in the `doc_ids` parameter when querying to filter results to specific documents.

### 4. Delete Document

Delete a document and all its chunks.

**Endpoint**: `DELETE /documents/{doc_id}`

### 5. Health Check

Check service health.

**Endpoint**: `GET /health`

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "detail": "Additional details",
  "trace_id": "abc123-def456"
}
```

## Rate Limiting

- 10 requests per second per IP
- Configurable in Nginx configuration
