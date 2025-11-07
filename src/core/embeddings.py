import google.generativeai as genai
from typing import List
from src.core.config import get_settings
from src.utils.logger import setup_logger
from src.utils.exceptions import EmbeddingError
from src.utils.retry import retry_with_exponential_backoff

logger = setup_logger(__name__)
settings = get_settings()


class GeminiEmbeddings:
    """Gemini API client for generating embeddings."""
    
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = settings.gemini_embedding_model
        logger.info(f"Initialized Gemini embeddings with model: {self.model}")
    
    @retry_with_exponential_backoff(
        max_retries=settings.max_retries,
        initial_delay=settings.retry_delay,
        exceptions=(Exception,)
    )
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise EmbeddingError(f"Embedding generation failed: {str(e)}")
    
    @retry_with_exponential_backoff(
        max_retries=settings.max_retries,
        initial_delay=settings.retry_delay,
        exceptions=(Exception,)
    )
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query."""
        try:
            result = genai.embed_content(
                model=self.model,
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {str(e)}")
            raise EmbeddingError(f"Query embedding generation failed: {str(e)}")
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for i, text in enumerate(texts):
            try:
                embedding = self.embed_text(text)
                embeddings.append(embedding)
                logger.debug(f"Generated embedding {i+1}/{len(texts)}")
            except Exception as e:
                logger.error(f"Failed to embed text {i+1}: {str(e)}")
                raise
        return embeddings
