# Architecture Documentation

## System Overview

The RAG Document Q&A system is built with a modular architecture that separates concerns into distinct layers:

## Components

### 1. API Layer (`src/api/`)

- **routes.py**: FastAPI endpoints for document management and querying
- **schemas.py**: Pydantic models for request/response validation
- **middleware.py**: Request tracing and error handling

### 2. Core Layer (`src/core/`)

- **config.py**: Application configuration and settings
- **embeddings.py**: Gemini embeddings client
- **llm.py**: Gemini LLM client for answer generation

### 3. RAG Pipeline (`src/rag/`)

- **ingestion.py**: Document processing and chunking
- **retriever.py**: Semantic similarity search
- **pipeline.py**: End-to-end RAG orchestration

### 4. Database Layer (`src/database/`)

- **vector_store.py**: ChromaDB wrapper for vector storage

### 5. Utilities (`src/utils/`)

- **logger.py**: Structured JSON logging
- **exceptions.py**: Custom exception classes
- **retry.py**: Exponential backoff retry logic

## Data Flow

1. **Document Ingestion**:
   - User uploads document → Document processor extracts text
   - Text chunked with overlap → Embeddings generated
   - Vectors stored in ChromaDB with metadata

2. **Query Processing**:
   - User submits question → Query embedding generated
   - Vector similarity search retrieves top-k chunks
   - Context assembled → LLM generates answer
   - Answer returned with source citations

## Design Decisions

### Chunking Strategy

- Fixed-size chunks with overlap to maintain context
- Configurable chunk size (default: 500 tokens)
- Overlap prevents information loss at boundaries

### Vector Database

- ChromaDB chosen for simplicity and local persistence
- Cosine similarity for semantic search
- Metadata filtering support

### LLM Integration

- Google Gemini for both embeddings and generation
- Retry logic for API resilience
- Temperature control for answer consistency

## Scalability Considerations

- Stateless API design enables horizontal scaling
- Vector database can be replaced with cloud solutions
- Async operations for concurrent request handling
- Docker containerization for easy deployment

## Error Handling

- Custom exception hierarchy
- Trace IDs for request tracking
- Structured logging for debugging
- Graceful degradation

## Security

- Input validation via Pydantic
- File type and size restrictions
- Rate limiting in production
- Environment-based configuration
