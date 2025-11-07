import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from src.core.config import get_settings
from src.utils.logger import setup_logger
from src.utils.exceptions import RetrievalError

logger = setup_logger(__name__)
settings = get_settings()


class ChromaVectorStore:
    """ChromaDB wrapper for vector storage and retrieval."""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(
            f"Initialized ChromaDB collection: {settings.chroma_collection_name}"
        )
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Add documents to the vector store."""
        try:
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(texts)} documents to vector store")
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise RetrievalError(f"Failed to add documents: {str(e)}")
    
    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query the vector store for similar documents."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_dict
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'score': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'id': results['ids'][0][i]
                    })
            
            logger.info(f"Retrieved {len(formatted_results)} documents")
            return {'results': formatted_results}
            
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            raise RetrievalError(f"Query failed: {str(e)}")
    
    def delete_document(self, doc_id: str) -> None:
        """Delete a document by ID."""
        try:
            # Get all chunks with this doc_id
            results = self.collection.get(
                where={"doc_id": doc_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted document {doc_id} ({len(results['ids'])} chunks)")
            else:
                logger.warning(f"No document found with id {doc_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete document: {str(e)}")
            raise RetrievalError(f"Failed to delete document: {str(e)}")
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all unique documents in the store."""
        try:
            # Get all documents
            results = self.collection.get()
            
            # Extract unique documents
            unique_docs = {}
            for metadata in results['metadatas']:
                doc_id = metadata.get('doc_id')
                if doc_id and doc_id not in unique_docs:
                    unique_docs[doc_id] = {
                        'doc_id': doc_id,
                        'filename': metadata.get('filename'),
                        'upload_date': metadata.get('upload_date')
                    }
            
            return list(unique_docs.values())
            
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            raise RetrievalError(f"Failed to list documents: {str(e)}")
