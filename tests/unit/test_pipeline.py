import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from src.rag.pipeline import RAGPipeline


class TestRAGPipeline:
    """Test end-to-end RAG pipeline."""
    
    @patch('src.rag.pipeline.DocumentProcessor')
    @patch('src.rag.pipeline.GeminiEmbeddings')
    @patch('src.rag.pipeline.ChromaVectorStore')
    def test_ingest_document_success(self, mock_store, mock_embeddings, mock_processor):
        """Test successful document ingestion."""
        # Setup mocks
        mock_processor.return_value.process_file.return_value = {
            'doc_id': '123',
            'filename': 'test.pdf',
            'chunks': ['chunk1', 'chunk2'],
            'upload_date': '2025-01-01T00:00:00'
        }
        mock_embeddings.return_value.embed_batch.return_value = [[0.1] * 768, [0.2] * 768]
        
        pipeline = RAGPipeline()
        file_content = BytesIO(b"test content")
        result = pipeline.ingest_document(file_content, "test.pdf")
        
        assert result['doc_id'] == '123'
        assert result['filename'] == 'test.pdf'
        assert result['chunks_created'] == 2
    
    @patch('src.rag.pipeline.DocumentRetriever')
    @patch('src.rag.pipeline.GeminiLLM')
    def test_query_success(self, mock_llm, mock_retriever):
        """Test successful query."""
        # Setup mocks
        mock_retriever.return_value.retrieve.return_value = [
            {
                'text': 'Test chunk',
                'metadata': {'doc_id': '123', 'filename': 'test.pdf'},
                'score': 0.95
            }
        ]
        mock_llm.return_value.generate_answer.return_value = "Test answer"
        
        pipeline = RAGPipeline()
        result = pipeline.query("test question")
        
        assert result['answer'] == "Test answer"
        assert len(result['sources']) == 1
        assert 'trace_id' in result
    
    @patch('src.rag.pipeline.DocumentRetriever')
    @patch('src.rag.pipeline.GeminiLLM')
    def test_query_no_results(self, mock_llm, mock_retriever):
        """Test query with no results."""
        mock_retriever.return_value.retrieve.return_value = []
        
        pipeline = RAGPipeline()
        result = pipeline.query("test question")
        
        assert "couldn't find" in result['answer'].lower()
        assert len(result['sources']) == 0
