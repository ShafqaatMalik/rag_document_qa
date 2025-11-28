from typing import List, Dict, Any, Optional
from src.core.embeddings import GeminiEmbeddings
from src.database.vector_store import ChromaVectorStore
from src.core.config import get_settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


class DocumentRetriever:
    """Retrieve relevant documents based on semantic similarity."""
    
    def __init__(self):
        self.embeddings = GeminiEmbeddings()
        self.vector_store = ChromaVectorStore()
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        doc_ids: Optional[List[str]] = None,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve top-k relevant document chunks."""
        top_k = top_k if top_k is not None else settings.top_k_results
        min_score = min_score if min_score is not None else settings.min_similarity_score
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Add doc_id filter if specified
            if doc_ids:
                if filters is None:
                    filters = {}
                filters['doc_id'] = {'$in': doc_ids}
            
            # Query vector store
            results = self.vector_store.query(
                query_embedding=query_embedding,
                top_k=top_k,
                filter_dict=filters
            )
            
            # Filter by minimum similarity score
            filtered_results = [
                result for result in results['results']
                if result['score'] >= min_score
            ]

            # Extract similarity scores for logging
            similarity_scores = [round(result['score'], 4) for result in filtered_results]

            logger.info(
                f"Retrieved {len(filtered_results)} chunks for query (filtered from {len(results['results'])})",
                extra={"extra_fields": {
                    "query_length": len(query),
                    "top_k": top_k,
                    "results_count": len(filtered_results),
                    "min_score": min_score,
                    "similarity_scores": similarity_scores,
                    "filtered_doc_ids": doc_ids
                }}
            )

            return filtered_results
            
        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            raise
