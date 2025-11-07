import functools
import time
from typing import Callable, Type, Tuple, Any
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """Decorator for retrying functions with exponential backoff."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Max retries ({max_retries}) reached for {func.__name__}",
                            extra={"extra_fields": {"error": str(e)}}
                        )
                        raise
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {delay}s",
                        extra={"extra_fields": {"error": str(e)}}
                    )
                    time.sleep(delay)
                    delay *= exponential_base
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
