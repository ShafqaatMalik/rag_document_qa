import pytest
from unittest.mock import Mock, patch
from src.rag.retriever import DocumentRetriever


class TestDocumentRetriever:
    """Test document retrieval functionality."""
    
    @patch('src.rag.retriever.GeminiEmbeddings')
    @patch('src.rag.retriever.ChromaVectorStore')
    def test_retrieve_success(self, mock_store, mock_embeddings):
        """Test successful document retrieval."""
        # Setup mocks
        mock_embeddings.return_value.embed_query.return_value = [0.1] * 768
        mock_store.return_value.query.return_value = {
            'results': [
                {
                    'text': 'Test chunk',
                    'metadata': {'doc_id': '123', 'filename': 'test.pdf'},
                    'score': 0.95
                }
            ]
        }
        
        retriever = DocumentRetriever()
        results = retriever.retrieve("test query", top_k=5)
        
        assert len(results) == 1
        assert results[0]['text'] == 'Test chunk'
        assert results[0]['score'] == 0.95
    
    @patch('src.rag.retriever.GeminiEmbeddings')
    @patch('src.rag.retriever.ChromaVectorStore')
    def test_retrieve_with_filters(self, mock_store, mock_embeddings):
        """Test retrieval with filters."""
        mock_embeddings.return_value.embed_query.return_value = [0.1] * 768
        mock_store.return_value.query.return_value = {'results': []}
        
        retriever = DocumentRetriever()
        filters = {'doc_id': '123'}
        results = retriever.retrieve("test query", top_k=3, filters=filters)
        
        assert isinstance(results, list)
        mock_store.return_value.query.assert_called_once()
