# Testing Logging and Error Handling

This guide explains how to test the logging and error handling features implemented in the RAG system.

## Overview

The RAG system implements:

1. **Structured JSON Logging** - All logs in JSON format for easy parsing
2. **Trace IDs** - Unique IDs to track requests across the system
3. **Custom Exceptions** - Specific exception types for different error scenarios
4. **Retry Mechanism** - Exponential backoff for transient failures
5. **Error Details** - Rich error context for debugging

---

## Components

### 1. Structured Logging (`src/utils/logger.py`)

**Features:**
- JSON-formatted log output
- Trace ID for request correlation
- Timestamp, level, logger name, message
- Exception stack traces
- Extra fields for metrics

**Example Log Entry:**
```json
{
  "timestamp": "2025-11-24T10:30:15.123456",
  "level": "INFO",
  "logger": "src.rag.pipeline",
  "message": "Query completed in 2.45s",
  "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "question_length": 42,
  "sources_count": 5,
  "answer_length": 1234,
  "elapsed_seconds": 2.45
}
```

### 2. Custom Exceptions (`src/utils/exceptions.py`)

**Exception Types:**
- `RAGException` - Base exception
- `DocumentProcessingError` - File processing failures (422)
- `EmbeddingError` - Embedding generation failures (500)
- `RetrievalError` - Retrieval failures (500)
- `GenerationError` - LLM generation failures (500)
- `ValidationError` - Input validation failures (400)

**Features:**
- HTTP status codes
- Error details dictionary
- Message + context

### 3. Retry Mechanism (`src/utils/retry.py`)

**Features:**
- Exponential backoff (1s, 2s, 4s, etc.)
- Configurable max retries
- Logs each retry attempt
- Used in LLM and embedding calls

---

## How to Test

### Automated Test Script (Recommended)

**Step 1:** Start the API server (if not already running)
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Step 2:** In a new terminal, run the test script
```bash
python test_logging_errors.py
```

**Step 3:** Watch both windows:
- Test script window: Shows test progress
- Server window: Shows structured logs

The script tests:
1. ✓ Normal logging (health check)
2. ✓ Validation errors (empty query)
3. ✓ File validation errors (wrong type)
4. ✓ Missing documents scenario
5. ✓ Invalid parameters
6. ✓ Successful operations with metrics
7. ✓ Trace ID propagation

---


The system uses appropriate log levels:

| Level | When Used | Examples |
|-------|-----------|----------|
| INFO | Normal operations | Query received, document uploaded |
| WARNING | Recoverable issues | Retry attempts, no documents found |
| ERROR | Failures | Max retries exceeded, exceptions |

---


