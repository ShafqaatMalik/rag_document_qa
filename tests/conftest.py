import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_embeddings():
    """Mock Gemini embeddings."""
    with patch('src.core.embeddings.GeminiEmbeddings') as mock:
        instance = mock.return_value
        instance.embed_text.return_value = [0.1] * 768
        instance.embed_query.return_value = [0.1] * 768
        yield instance


@pytest.fixture
def mock_llm():
    """Mock Gemini LLM."""
    with patch('src.core.llm.GeminiLLM') as mock:
        instance = mock.return_value
        instance.generate_answer.return_value = "This is a test answer."
        yield instance


@pytest.fixture
def mock_vector_store():
    """Mock ChromaDB vector store."""
    with patch('src.database.vector_store.ChromaVectorStore') as mock:
        instance = mock.return_value
        instance.query.return_value = {'results': []}
        yield instance


@pytest.fixture
def sample_text_file():
    """Sample text file for testing."""
    from io import BytesIO
    content = b"This is a test document content."
    file = BytesIO(content)
    file.name = "test.txt"
    return file
