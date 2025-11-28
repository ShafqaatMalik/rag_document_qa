# RAG Document Q&A System

## Try the Demo!

**Recruiters:** Test this system in 5 minutes! See **[RECRUITER_SETUP.md](RECRUITER_SETUP.md)** for quick setup instructions.

```batch
# Windows - Quick Start
demo_setup.bat    # One-time setup
start_demo.bat    # Launch demo (opens browser automatically)
```

**Sample Documents:** Ready-to-use test documents are included in the `demo_samples/` folder.

## Overview
RAG Document Q&A System is a production-grade Retrieval-Augmented Generation (RAG) platform for semantic document search and question answering. It ingests unstructured documents, generates vector embeddings, retrieves the most relevant context, and produces grounded answers with source attribution. The system emphasizes reliability, observability, and deployment flexibility.

## Quick Start
1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure API key**: Set `GEMINI_API_KEY` in `.env` file
3. **Start server**: `uvicorn main:app --reload`
4. **Open chat UI**: http://localhost:8000
5. **View API docs**: http://localhost:8000/docs

## Features
- Multi-format document ingestion: PDF, TXT, DOCX, Markdown
- Vector storage and semantic search using ChromaDB
- Contextual and accurate answer generation via Google Gemini (embeddings + LLM)
- Similarity score thresholding and multi-document filtering
- Source citation with confidence scoring
- Structured logging (trace IDs) and error handling via custom exceptions and retries
- Containerized (Dockerfile + docker-compose) for reproducible deployments
- Automated testing (unit + integration) with coverage reporting
- CI/CD pipelines (GitHub Actions) for build, test, and deploy automation

## Architecture
FastAPI application providing REST endpoints:
1. Ingestion: File upload, validation, chunking
2. Embedding: Gemini embedding generation
3. Indexing: Vectors stored in ChromaDB (persistent directory)
4. Query: Retrieve top-k relevant chunks (threshold + filters)
5. Synthesis: Assemble context and generate answer via LLM
6. Response: Return answer, cited sources, and metadata

Key Modules:
- `api/`: Routing, request/response schemas, middleware
- `rag/`: Ingestion, pipeline orchestration, retrieval logic
- `core/`: Configuration management, LLM + embedding clients
- `database/`: Vector store abstraction (ChromaDB)
- `utils/`: Logging, retry strategy, custom exceptions

## Data Flow
Upload → Validation → Chunking → Embedding → Vector Store → Query → Retrieval → Answer Generation → Response

## Installation
Prerequisites: Python 3.11+, Google Gemini API key

```powershell
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
copy .env.example .env  # Set GEMINI_API_KEY in .env
```

## Configuration
Environment variables (in `.env`):

| Variable | Purpose | Default |
|----------|---------|---------|
| GEMINI_API_KEY | LLM + embedding access | Required |
| CHUNK_SIZE | Text chunk token size | 500 |
| CHUNK_OVERLAP | Overlap between chunks | 50 |
| TOP_K_RESULTS | Max retrieved chunks | 5 |
| MIN_SIMILARITY_SCORE | Similarity filter threshold | 0.3 |
| MAX_UPLOAD_SIZE | Max file size (bytes) | 10000000 |
| LOG_LEVEL | Log verbosity | INFO |

## Running Locally

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload and ingest a document |
| GET | `/api/v1/documents` | List ingested documents |
| DELETE | `/api/v1/documents/{doc_id}` | Delete a document |
| POST | `/api/v1/query` | Submit a question and get answer |
| GET | `/api/v1/health` | Health check endpoint |


## Testing

### Unit and Integration Tests
```powershell
# Run all tests
pytest tests -v

# Run with coverage report
pytest tests -v --cov=src --cov-report=html
# View report
start htmlcov/index.html
```

### Logging and Error Handling Tests
Test the structured JSON logging, trace IDs, custom exceptions, and retry mechanisms:

```powershell
# Automated test suite (recommended)
python test_logging_errors.py
```

For comprehensive testing guide, see [TESTING_LOGGING_ERRORS.md](TESTING_LOGGING_ERRORS.md)

## Evaluation

Run comprehensive evaluation to benchmark system performance:
```powershell
python evaluate.py
```

This generates `evaluation_report.json` with metrics:
- **NDCG@5**: Retrieval ranking quality (Normalized Discounted Cumulative Gain)
- **Similarity scores**: Average relevance of retrieved documents
- **Response time**: End-to-end latency analysis
- **Topic coverage**: How well answers address expected topics
- **SLA compliance**: Percentage of queries meeting the 15-second threshold

## Deployment
### Docker Compose
```bash
docker-compose -f deployment/docker/docker-compose.yml up -d
```
### Docker Image
```bash
docker build -f deployment/docker/Dockerfile -t rag-qa:latest .
docker run -p 8000:8000 --env-file .env rag-qa:latest
```

### Cloud (AWS EC2)
- Launch an Ubuntu 22.04 EC2 instance
- Clone the repository and run `deployment/aws/ec2-setup.sh`
- CI/CD: Use GitHub Actions for build/test/deploy

## Directory Structure
```
src/
  api/          # Routes, schemas, middleware
  core/         # Settings, embeddings, LLM client
  rag/          # Pipeline, ingestion, retrieval
  database/     # Vector store wrapper (ChromaDB)
  utils/        # Logging, exceptions, retry
tests/          # Unit and integration tests
deployment/     # Docker and AWS assets
static/         # Front-end assets (chat UI)
main.py         # FastAPI entry point
requirements.txt
```


