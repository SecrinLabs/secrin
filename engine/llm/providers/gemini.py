"""
Gemini LLM implementation for DevSecrin

This module provides a Gemini-based LLM implementation for text generation.
"""

import os
import time
from typing import Any, Dict, Optional
from google import genai

from ..base import LLM
from config import get_logger

# Setup logger for this module
logger = get_logger(__name__)


class GeminiLLM(LLM):
    """
    Gemini LLM implementation.
    
    Uses the Gemini API for text generation with Google's Gemini models.
    """
    
    def __init__(
        self, 
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Gemini LLM.
        
        Args:
            model: The Gemini model to use (defaults to gemini-1.5-pro)
            api_key: The Gemini API key (defaults to GEMINI_API_KEY env var)
            **kwargs: Additional configuration options
        """
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.client = genai.Client(api_key=api_key)
        self.kwargs = kwargs
        
        logger.info(f"Initialized GeminiLLM with model: {self.model}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text response using Gemini.
        
        Args:
            prompt: The input prompt to generate a response for
            **kwargs: Additional parameters for generation (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response as a string
            
        Raises:
            Exception: If generation fails
        """
        try:
            start_time = time.time()
            
            # Merge instance kwargs with method kwargs
            generation_params = {**self.kwargs, **kwargs}
            
            # Remove parameters that don't apply to Gemini
            generation_params.pop('think', None)
            
            # Map common parameters to Gemini's expected format
            temperature = generation_params.pop('temperature', 0.7)
            max_tokens = generation_params.pop('max_tokens', 2048)
            
            logger.debug(f"Generating response with Gemini model: {self.model}")
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt],
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    **generation_params
                }
            )
            
            generation_time = time.time() - start_time
            logger.debug(f"Gemini generation took {generation_time:.2f} seconds")
            
            if response.text:
                return response.text
            else:
                raise Exception("No text response from Gemini")
                
        except Exception as e:
            logger.error(f"Error generating response with Gemini: {str(e)}")
            raise Exception(f"Gemini generation failed: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current Gemini model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "provider": "gemini",
            "model": self.model,
            "type": "cloud"
        }
