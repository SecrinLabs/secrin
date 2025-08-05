"""
Base LLM interface for DevSecrin

This module defines the base interface for Large Language Models (LLMs)
that can be used for text generation in the DevSecrin system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class LLM(ABC):
    """
    Abstract base class for all LLM implementations.
    
    This class defines the interface that all LLM implementations must follow.
    """
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text response from the given prompt.
        
        Args:
            prompt: The input prompt to generate a response for
            **kwargs: Additional parameters specific to the LLM implementation
            
        Returns:
            Generated text response as a string
            
        Raises:
            Exception: If generation fails
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary containing model information like name, version, etc.
        """
        pass
