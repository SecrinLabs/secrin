"""
Base abstract class for LLM providers.
Defines the interface that all LLM implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 1000):
        """
        Initialize the LLM provider.
        
        Args:
            model: Model name/identifier
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    def generate_answer(
        self,
        question: str,
        context_items: List[Any],
        search_type: str
    ) -> str:
        """
        Generate an answer to the question using provided context.
        
        Args:
            question: User's question
            context_items: List of search results to use as context
            search_type: Type of search performed (vector/hybrid)
        
        Returns:
            Generated answer as string
        
        Raises:
            Exception: If generation fails
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'ollama', 'openai')."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and properly configured.
        
        Returns:
            True if provider can be used, False otherwise
        """
        pass
    
    def _build_prompt(
        self,
        question: str,
        context_items: List[Any],
        search_type: str
    ) -> str:
        """
        Build the prompt for the LLM.
        
        Args:
            question: User's question
            context_items: Context from search
            search_type: Type of search used
        
        Returns:
            Formatted prompt string
        """
        # Format context
        context_text = self._format_context(context_items)
        
        # Build prompt
        prompt = f"""You are a helpful code assistant. Answer the user's question based on the provided code context.

Context from codebase (found using {search_type} search):
{context_text}

Question: {question}

Instructions:
- Provide a clear, concise answer based on the context above
- Reference specific functions, classes, or files when relevant
- If the context doesn't contain enough information, say so
- Use technical accuracy but keep explanations accessible
- Format code snippets with proper syntax highlighting

Answer:"""
        
        return prompt
    
    def _format_context(
        self,
        context_items: List[Any]
    ) -> str:
        """
        Format context items into a readable string.
        
        Args:
            context_items: List of search results
        
        Returns:
            Formatted context string
        """
        if not context_items:
            return "No relevant context found."
        
        formatted = []
        for idx, item in enumerate(context_items, 1):
            # Extract node data from SearchResult objects
            node = getattr(item, 'node', item) if hasattr(item, 'node') else item
            
            # Get node properties
            if isinstance(node, dict):
                node_type = node.get('labels', ['Unknown'])[0] if node.get('labels') else 'Unknown'
                # For commits, use short SHA as name; otherwise use name field
                if node_type == 'Commit':
                    name = node.get('sha', 'Unknown')[:8]
                else:
                    name = node.get('name', 'Unnamed')
                content = node.get('content', '')
            else:
                node_type = 'Unknown'
                name = 'Unnamed'
                content = ''
            
            score = getattr(item, 'score', None)
            
            # Build context entry
            entry = f"\n--- Context {idx}: {node_type} '{name}'"
            if score is not None:
                entry += f" (relevance: {score:.3f})"
            entry += " ---\n"
            entry += content[:1000]  # Limit content length
            if len(content) > 1000:
                entry += "\n... (truncated)"
            
            formatted.append(entry)
        
        return "\n".join(formatted)
