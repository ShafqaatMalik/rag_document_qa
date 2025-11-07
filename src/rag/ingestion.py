import uuid
from datetime import datetime
from typing import List, Dict, Any, BinaryIO
from pathlib import Path
from pypdf import PdfReader
from docx import Document
from src.core.config import get_settings
from src.utils.logger import setup_logger
from src.utils.exceptions import DocumentProcessingError

logger = setup_logger(__name__)
settings = get_settings()


class DocumentProcessor:
    """Process and chunk documents for ingestion."""
    
    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def process_file(
        self,
        file_content: BinaryIO,
        filename: str
    ) -> Dict[str, Any]:
        """Process uploaded file and extract text."""
        try:
            file_ext = Path(filename).suffix.lower()
            
            # Extract text based on file type
            if file_ext == '.pdf':
                text = self._extract_pdf(file_content)
            elif file_ext == '.txt':
                text = file_content.read().decode('utf-8')
            elif file_ext == '.docx':
                text = self._extract_docx(file_content)
            elif file_ext == '.md':
                text = file_content.read().decode('utf-8')
            else:
                raise DocumentProcessingError(
                    f"Unsupported file type: {file_ext}",
                    details={'filename': filename}
                )
            
            if not text or len(text.strip()) == 0:
                raise DocumentProcessingError(
                    "No text content extracted from document",
                    details={'filename': filename}
                )
            
            # Chunk text
            chunks = self._chunk_text(text)
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            logger.info(
                f"Processed document: {filename}",
                extra={"extra_fields": {
                    "doc_id": doc_id,
                    "chunks": len(chunks),
                    "text_length": len(text)
                }}
            )
            
            return {
                'doc_id': doc_id,
                'filename': filename,
                'text': text,
                'chunks': chunks,
                'upload_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            raise DocumentProcessingError(
                f"Failed to process document: {str(e)}",
                details={'filename': filename}
            )
    
    def _extract_pdf(self, file_content: BinaryIO) -> str:
        """Extract text from PDF file."""
        try:
            pdf_reader = PdfReader(file_content)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            raise DocumentProcessingError(f"PDF extraction failed: {str(e)}")
    
    def _extract_docx(self, file_content: BinaryIO) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_content)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            raise DocumentProcessingError(f"DOCX extraction failed: {str(e)}")
    
    def _chunk_text(self, text: str) -> List[str]:
        """Chunk text with overlap for better context."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = " ".join(words[i:i + self.chunk_size])
            chunks.append(chunk)
        
        return chunks if chunks else [text]
