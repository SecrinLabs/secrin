import os
import time
from google import genai
from typing import List, Union

from ..base import Embedder

class GeminiEmbedder(Embedder):
    def __init__(self, model: str = "gemini-embedding-001"):
        self.model = model
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        self.client = genai.Client(api_key=api_key)
    
    def embed(self, text: str, max_retries: int = 3, base_delay: float = 10.0) -> List[float]:
        """
        Given a string, return a list of embeddings as floats.
        Implements retry logic for rate limiting (403 errors).
        
        Args:
            text: The text to embed
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Base delay in seconds before retrying (default: 10.0)
            
        Returns:
            List of embedding values as floats
            
        Raises:
            ValueError: If no embeddings are returned or after max retries
            Exception: For non-retryable errors
        """
        for attempt in range(max_retries + 1):
            try:
                result = self.client.models.embed_content(
                    model=self.model,
                    contents=[text]
                )
                
                if not result.embeddings or len(result.embeddings) == 0:
                    raise ValueError("No embeddings returned from Gemini API")
                
                # Extract the values from the first (and only) embedding
                embedding_values = result.embeddings[0].values
                return list(embedding_values)
                
            except Exception as e:
                # Check if this is a rate limiting error (403)
                error_message = str(e).lower()
                is_rate_limit_error = (
                    "403" in error_message or 
                    "rate limit" in error_message or
                    "quota" in error_message or
                    "resource" in error_message
                )
                
                if is_rate_limit_error and attempt < max_retries:
                    # Calculate delay with exponential backoff
                    delay = base_delay * (2 ** attempt)
                    print(f"Rate limit exceeded. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(delay)
                    continue
                else:
                    # Re-raise the exception if it's not retryable or we've exhausted retries
                    if is_rate_limit_error:
                        raise ValueError(f"Rate limit exceeded after {max_retries} retries. Original error: {e}")
                    else:
                        raise e
        
        # This should never be reached, but just in case
        raise ValueError(f"Failed to get embeddings after {max_retries} retries")
    
    def embed_with_retry(self, text: str) -> List[float]:
        """
        Convenience method that calls embed with default retry settings.
        This maintains backward compatibility while providing retry functionality.
        """
        return self.embed(text)
