import pytest
from unittest.mock import patch, Mock
from src.core.embeddings import GeminiEmbeddings
from src.utils.exceptions import EmbeddingError


class TestGeminiEmbeddings:
    """Test Gemini embeddings functionality."""
    
    @patch('src.core.embeddings.genai')
    def test_embed_text_success(self, mock_genai):
        """Test successful text embedding."""
        mock_genai.embed_content.return_value = {'embedding': [0.1] * 768}
        
        embeddings = GeminiEmbeddings()
        result = embeddings.embed_text("test text")
        
        assert len(result) == 768
        assert isinstance(result, list)
    
    @patch('src.core.embeddings.genai')
    def test_embed_query_success(self, mock_genai):
        """Test successful query embedding."""
        mock_genai.embed_content.return_value = {'embedding': [0.2] * 768}
        
        embeddings = GeminiEmbeddings()
        result = embeddings.embed_query("test query")
        
        assert len(result) == 768
        assert isinstance(result, list)
    
    @patch('src.core.embeddings.genai')
    def test_embed_batch_success(self, mock_genai):
        """Test batch embedding."""
        mock_genai.embed_content.return_value = {'embedding': [0.1] * 768}
        
        embeddings = GeminiEmbeddings()
        texts = ["text1", "text2", "text3"]
        results = embeddings.embed_batch(texts)
        
        assert len(results) == 3
        assert all(len(r) == 768 for r in results)
    
    @patch('src.core.embeddings.genai')
    def test_embed_text_failure(self, mock_genai):
        """Test embedding failure handling."""
        mock_genai.embed_content.side_effect = Exception("API Error")
        
        embeddings = GeminiEmbeddings()
        
        with pytest.raises(EmbeddingError):
            embeddings.embed_text("test text")
