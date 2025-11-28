import time
from typing import Dict, Any, List, BinaryIO
from src.rag.ingestion import DocumentProcessor
from src.rag.retriever import DocumentRetriever
from src.core.embeddings import GeminiEmbeddings
from src.core.llm import GeminiLLM
from src.database.vector_store import ChromaVectorStore
from src.utils.logger import setup_logger, get_trace_id
from src.utils.exceptions import RAGException

logger = setup_logger(__name__)


class RAGPipeline:
    """End-to-end RAG pipeline orchestrator."""
    
    def __init__(self):
        self.processor = DocumentProcessor()
        self.embeddings = GeminiEmbeddings()
        self.vector_store = ChromaVectorStore()
        self.retriever = DocumentRetriever()
        self.llm = GeminiLLM()
        logger.info("RAG Pipeline initialized")
    
    def ingest_document(
        self,
        file_content: BinaryIO,
        filename: str
    ) -> Dict[str, Any]:
        """
        Ingest a document: process, chunk, embed, and store.
        
        Returns:
            Document metadata with doc_id
        """
        try:
            start_time = time.time()
            
            # Process document
            doc_data = self.processor.process_file(file_content, filename)

            # Generate embeddings for chunks
            embeddings = self.embeddings.embed_batch(doc_data['chunks'])

            # Prepare metadata for each chunk
            metadatas = [
                {
                    'doc_id': doc_data['doc_id'],
                    'filename': filename,
                    'chunk_index': i,
                    'upload_date': doc_data['upload_date']
                }
                for i in range(len(doc_data['chunks']))
            ]

            # Generate IDs for each chunk
            ids = [f"{doc_data['doc_id']}_chunk_{i}" for i in range(len(doc_data['chunks']))]

            # Store in vector database
            self.vector_store.add_documents(
                texts=doc_data['chunks'],
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            elapsed_time = time.time() - start_time
            
            logger.info(
                f"Document ingestion completed in {elapsed_time:.2f}s",
                extra={"extra_fields": {
                    "doc_id": doc_data['doc_id'],
                    "chunks": len(doc_data['chunks']),
                    "elapsed_seconds": elapsed_time
                }}
            )
            
            return {
                'doc_id': doc_data['doc_id'],
                'filename': filename,
                'chunks_created': len(doc_data['chunks']),
                'upload_date': doc_data['upload_date']
            }
            
        except RAGException:
            raise
        except Exception as e:
            logger.error(f"Document ingestion failed: {str(e)}")
            raise RAGException(f"Document ingestion failed: {str(e)}")
    
    def query(
        self,
        question: str,
        top_k: int = 5,
        filters: Dict[str, Any] = None,
        doc_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG system: retrieve context and generate answer.
        
        Returns:
            Answer with sources and metadata
        """
        try:
            start_time = time.time()
            
            # Retrieve relevant chunks
            retrieved_chunks = self.retriever.retrieve(
                query=question,
                top_k=top_k,
                filters=filters,
                doc_ids=doc_ids
            )
            
            if not retrieved_chunks:
                logger.warning("No relevant documents found for query")
                return {
                    'answer': "I couldn't find any relevant information to answer your question. This could be because:\n- No documents match your query with sufficient confidence\n- The similarity score is below the threshold (0.3)\n- The specified documents don't contain relevant information",
                    'sources': [],
                    'trace_id': get_trace_id(),
                    'latency_seconds': time.time() - start_time
                }
            
            # Generate answer
            answer = self.llm.generate_answer(
                query=question,
                context_chunks=retrieved_chunks
            )
            
            # Format sources
            sources = [
                {
                    'doc_id': chunk['metadata']['doc_id'],
                    'filename': chunk['metadata']['filename'],
                    'text_snippet': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text'],
                    'score': round(chunk['score'], 3)
                }
                for chunk in retrieved_chunks
            ]
            
            elapsed_time = time.time() - start_time
            
            logger.info(
                f"Query completed in {elapsed_time:.2f}s",
                extra={"extra_fields": {
                    "question_length": len(question),
                    "sources_count": len(sources),
                    "answer_length": len(answer),
                    "elapsed_seconds": elapsed_time
                }}
            )
            
            return {
                'answer': answer,
                'sources': sources,
                'trace_id': get_trace_id(),
                'latency_seconds': round(elapsed_time, 2)
            }
            
        except RAGException:
            raise
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            raise RAGException(f"Query failed: {str(e)}")

    def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """Delete a document and all its chunks."""
        try:
            self.vector_store.delete_document(doc_id)
            return {
                'doc_id': doc_id,
                'deleted': True,
                'trace_id': get_trace_id()
            }
        except Exception as e:
            logger.error(f"Document deletion failed: {str(e)}")
            raise RAGException(f"Document deletion failed: {str(e)}")
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the system."""
        try:
            documents = self.vector_store.list_documents()
            return documents
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            raise RAGException(f"Failed to list documents: {str(e)}")
