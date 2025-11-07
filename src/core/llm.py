import google.generativeai as genai
from typing import List, Dict, Any
from src.core.config import get_settings
from src.utils.logger import setup_logger
from src.utils.exceptions import GenerationError
from src.utils.retry import retry_with_exponential_backoff

logger = setup_logger(__name__)
settings = get_settings()


class GeminiLLM:
    """Gemini API client for text generation."""
    
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        logger.info(f"Initialized Gemini LLM with model: {settings.gemini_model}")
    
    @retry_with_exponential_backoff(
        max_retries=settings.max_retries,
        initial_delay=settings.retry_delay,
        exceptions=(Exception,)
    )
    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        temperature: float = 0.3
    ) -> str:
        """Generate an answer based on query and context."""
        try:
            # Build context from chunks
            context = self._build_context(context_chunks)
            
            # Create prompt
            prompt = self._create_prompt(query, context)
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': temperature,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 2048,
                }
            )
            
            answer = response.text
            logger.info(f"Generated answer of length {len(answer)}")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            raise GenerationError(f"Answer generation failed: {str(e)}")
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Source {i}]")
            context_parts.append(f"Document: {chunk['metadata']['filename']}")
            context_parts.append(f"Content: {chunk['text']}")
            context_parts.append("")
        return "\n".join(context_parts)
    
    def _create_prompt(self, query: str, context: str) -> str:
        """Create prompt for answer generation."""
        return f"""You are a helpful AI assistant that answers questions based on provided context. Provide clear, natural, and conversational responses.

Context:
{context}

Question: {query}

Instructions:
- Answer the question using the information from the context above
- Write in a natural, conversational tone similar to how you would explain something to a colleague
- Use complete, flowing sentences rather than bullet points or short fragments
- Organize your response into clear paragraphs (separated by double line breaks) when covering multiple points
- If the context doesn't contain enough information, explain what you can answer and what's missing
- Cite sources naturally in your response using [Source N] notation where appropriate
- Be thorough but concise - aim for clarity over brevity
- If you're unsure about something, acknowledge it naturally in your response

Answer:"""
