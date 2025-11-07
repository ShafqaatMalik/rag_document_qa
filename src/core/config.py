from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Settings
    app_name: str = "RAG Document Q&A"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    debug: bool = False
    
    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "models/text-embedding-004"
    
    # ChromaDB
    chroma_persist_directory: str = "./chroma_data"
    chroma_collection_name: str = "documents"
    
    # RAG Settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5
    min_similarity_score: float = 0.3  # Minimum similarity score for retrieved chunks
    
    # API Settings
    max_upload_size: int = 10_000_000  # 10MB
    allowed_extensions: list = [".pdf", ".txt", ".docx", ".md"]
    
    # Retry Settings
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
