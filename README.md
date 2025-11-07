# RAG-Powered Document Q&A

Production-grade Retrieval-Augmented Generation (RAG) system for semantic document search and AI-powered question answering.

## 🚀 Features

- **Document Processing**: Upload PDF, TXT, DOCX, and Markdown files
- **Semantic Search**: Vector similarity search using ChromaDB
- **AI-Powered Answers**: Context-aware responses via Google Gemini
- **Smart Filtering**: 
  - **Similarity Score Threshold**: Automatic filtering of low-confidence results (>0.3)
  - **Multi-Document Query**: Target specific documents for more accurate answers
- **Source Citations**: Answers include relevant source references with confidence scores
- **Production-Ready**: Structured logging, error handling, health checks
- **Containerized**: Docker support with docker-compose
- **Cloud-Ready**: Deploy to Render or AWS EC2
- **CI/CD**: Automated testing and deployment via GitHub Actions

## 📋 Prerequisites

- Python 3.11+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Docker (optional, for containerized deployment)

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Run Locally

```bash
# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access the API
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
# - API: http://localhost:8000/api/v1/
```

### 4. Test the API

```bash
# Upload a document
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf"

# Query the document
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this document about?",
  "top_k": 5
  }'

# Query specific documents only (multi-document filtering)
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key features?",
  "top_k": 5,
    "doc_ids": ["550e8400-e29b-41d4-a716-446655440000"]
  }'

# List all documents
curl -X GET "http://localhost:8000/api/v1/documents"

# Health check
curl -X GET "http://localhost:8000/api/v1/health"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           Client (REST API)             │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         FastAPI Application             │
│  ┌────────────────────────────────────┐ │
│  │      RAG Pipeline                  │ │
│  │  • Document Ingestion & Chunking   │ │
│  │  • Semantic Search (top-k)         │ │
│  │  • Context Assembly                │ │
│  │  • Answer Generation               │ │
│  └─────┬──────────────────────┬───────┘ │
└────────┼──────────────────────┼─────────┘
         │                      │
    ┌────▼──────┐         ┌────▼──────────┐
    │ ChromaDB  │         │  Gemini API   │
    │ (Vectors) │         │  (Embeddings  │
    │           │         │  + Generation)│
    └───────────┘         └───────────────┘
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# View coverage report
htmlcov/index.html
```

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and run

docker-compose -f deployment/docker/docker-compose.yml up -d

# View logs
docker-compose -f deployment/docker/docker-compose.yml logs -f

# Stop
docker-compose -f deployment/docker/docker-compose.yml down
```

### Build Docker Image

```bash
docker build -f deployment/docker/Dockerfile -t rag-qa:latest .
docker run -p 8000:8000 --env-file .env rag-qa:latest
```

## ☁️ Cloud Deployment

### Deploy to Render (Free Tier)

1. Push code to GitHub
2. In Render Dashboard:
   - New Web Service
   - Connect GitHub repository
   - Select branch: main
   - Environment: Docker
   - Add environment variable: GEMINI_API_KEY
   - Deploy

### Deploy to AWS EC2

1. Launch EC2 Instance (t3.micro, Ubuntu 22.04)
2. SSH into instance and run:

```bash
git clone https://github.com/yourusername/rag-document-qa.git
cd rag-document-qa
chmod +x deployment/aws/ec2-setup.sh
./deployment/aws/ec2-setup.sh
```

## 📁 Project Structure

```
rag-document-qa/
├── src/
│   ├── api/              # FastAPI routes and schemas
│   ├── core/             # Embeddings and LLM clients
│   ├── rag/              # RAG pipeline components
│   ├── database/         # Vector store wrapper
│   └── utils/            # Logging, exceptions, retry logic
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── deployment/
│   ├── docker/           # Docker configuration
│   ├── render/           # Render deployment config
│   └── aws/              # AWS EC2 setup scripts
├── .github/workflows/    # CI/CD pipelines
├── main.py               # Application entry point
└── requirements.txt      # Python dependencies
```

## 🔧 Configuration

Key configuration options in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `CHUNK_SIZE` | Token size for text chunks | 500 |
| `CHUNK_OVERLAP` | Overlap between chunks | 50 |
| `TOP_K_RESULTS` | Number of results to retrieve | 5 |
| `MIN_SIMILARITY_SCORE` | Minimum similarity threshold (0-1) | 0.3 |
| `MAX_UPLOAD_SIZE` | Max file size (bytes) | 10000000 |
| `LOG_LEVEL` | Logging level | INFO |


