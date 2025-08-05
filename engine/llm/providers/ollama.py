"""
Ollama LLM implementation for DevSecrin

This module provides an Ollama-based LLM implementation for text generation.
"""

import os
import time
from typing import Any, Dict, Optional
from ollama import generate

from ..base import LLM
from config import get_logger

# Setup logger for this module
logger = get_logger(__name__)


class OllamaLLM(LLM):
    """
    Ollama LLM implementation.
    
    Uses the Ollama API for text generation with local models.
    """
    
    def __init__(
        self, 
        model: Optional[str] = None,
        host: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Ollama LLM.
        
        Args:
            model: The Ollama model to use (defaults to OLLAMA_MODEL env var)
            host: The Ollama host URL (defaults to OLLAMA_HOST env var)
            **kwargs: Additional configuration options
        """
        self.model = model or os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.kwargs = kwargs
        
        logger.info(f"Initialized OllamaLLM with model: {self.model}, host: {self.host}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text response using Ollama.
        
        Args:
            prompt: The input prompt to generate a response for
            **kwargs: Additional parameters for generation (think, temperature, etc.)
            
        Returns:
            Generated text response as a string
            
        Raises:
            Exception: If generation fails
        """
        try:
            start_time = time.time()
            
            # Merge instance kwargs with method kwargs
            generation_params = {**self.kwargs, **kwargs}
            generation_params.setdefault('think', False)
            
            logger.debug(f"Generating response with Ollama model: {self.model}")
            
            response = generate(
                model=self.model,
                prompt=prompt,
                **generation_params
            )
            
            generation_time = time.time() - start_time
            logger.debug(f"Ollama generation took {generation_time:.2f} seconds")
            return response['response']
                
        except Exception as e:
            logger.error(f"Error generating response with Ollama: {str(e)}")
            raise Exception(f"Ollama generation failed: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current Ollama model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "provider": "ollama",
            "model": self.model,
            "host": self.host,
            "type": "local"
        }
