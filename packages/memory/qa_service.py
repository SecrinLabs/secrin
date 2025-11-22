"""
Question-Answering service that combines search and LLM.
Provides natural language answers to code-related questions.
"""

from typing import Optional, Dict, Any, List
import logging
from packages.memory.services.graph_service import GraphService
from packages.memory.llm import BaseLLMProvider
from packages.memory.factories.llm_factory import create_llm_provider
from packages.config import Settings, is_feature_enabled, FeatureFlag

settings = Settings()
logger = logging.getLogger(__name__)


class QAService:
    """Question-Answering service combining search and LLM."""
    
    def __init__(
        self,
        graph_service: GraphService,
        llm_provider: Optional[BaseLLMProvider] = None
    ):
        """
        Initialize QA service.
        
        Args:
            graph_service: Graph service for context retrieval
            llm_provider: Optional LLM provider (creates default if not provided)
        """
        self.graph_service = graph_service
        self.llm_provider = llm_provider or create_llm_provider()
        logger.info(
            f"QA Service initialized with {self.llm_provider.get_provider_name()} "
            f"(model: {self.llm_provider.model})"
        )
    
    def ask(
        self,
        question: str,
        search_type: str = "hybrid",
        node_type: str = "Function",
        context_limit: int = 5,
        max_answer_tokens: int = 1000,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ask a question and get a natural language answer with context.
        
        Args:
            question: The question to answer
            search_type: Type of search ('vector' or 'hybrid')
            node_type: Type of nodes to search
            context_limit: Maximum number of context items to retrieve
            max_answer_tokens: Maximum tokens for LLM response
            system_prompt: Optional custom system prompt
            
        Returns:
            Dictionary containing answer, context, and metadata
        """
        logger.info(f"Processing question: '{question[:50]}...'")
        
        # Step 1: Retrieve relevant context
        if search_type == "hybrid":
            if not is_feature_enabled(FeatureFlag.ENABLE_HYBRID_SEARCH):
                logger.warning("Hybrid search disabled, falling back to vector search")
                search_type = "vector"
        
        if search_type == "vector":
            context_items = self.graph_service.vector_search(
                query_text=question,
                node_type=node_type,
                limit=context_limit
            )
        elif search_type == "hybrid":
            context_items = self.graph_service.hybrid_search(
                query_text=question,
                node_type=node_type,
                limit=context_limit
            )
        else:
            raise ValueError(f"Unknown search type: {search_type}")
        
        logger.info(f"Retrieved {len(context_items)} context items")
        
        # Check if we have context
        if not context_items:
            return {
                "answer": "I couldn't find any relevant context in the codebase to answer your question. Please try rephrasing or ensure the code has been indexed.",
                "question": question,
                "context": [],
                "context_count": 0,
                "search_type": search_type,
                "node_type": node_type,
                "model": self.llm_provider.model,
                "provider": self.llm_provider.get_provider_name()
            }
        
        # Step 2: Generate answer with LLM
        answer = self.llm_provider.generate_answer(
            question=question,
            context_items=context_items,
            search_type=search_type
        )
        
        # Step 3: Format and return response
        context_summary = self._format_context_summary(context_items)
        
        return {
            "answer": answer,
            "question": question,
            "context": context_summary,
            "context_count": len(context_items),
            "search_type": search_type,
            "node_type": node_type,
            "model": self.llm_provider.model,
            "provider": self.llm_provider.get_provider_name()
        }
    
    def ask_multiple_types(
        self,
        question: str,
        node_types: List[str] = ["Function", "Class", "File"],
        search_type: str = "hybrid",
        context_per_type: int = 2,
        max_answer_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Ask a question and search across multiple node types.
        
        Args:
            question: The question to answer
            node_types: List of node types to search
            search_type: Type of search
            context_per_type: Max context items per type
            max_answer_tokens: Maximum tokens for LLM response
            
        Returns:
            Dictionary containing answer and aggregated context
        """
        logger.info(f"Processing multi-type question: '{question[:50]}...'")
        
        # Collect context from all node types
        all_context = []
        
        for node_type in node_types:
            try:
                if search_type == "hybrid":
                    items = self.graph_service.hybrid_search(
                        query_text=question,
                        node_type=node_type,
                        limit=context_per_type
                    )
                else:
                    items = self.graph_service.vector_search(
                        query_text=question,
                        node_type=node_type,
                        limit=context_per_type
                    )
                
                all_context.extend(items)
            except Exception as e:
                logger.warning(f"Error searching {node_type}: {e}")
        
        if not all_context:
            return {
                "answer": "I couldn't find any relevant context in the codebase to answer your question.",
                "question": question,
                "context": [],
                "context_count": 0,
                "search_type": search_type,
                "node_types": node_types,
                "model": self.llm_provider.model,
                "provider": self.llm_provider.get_provider_name()
            }
        
        # Generate answer
        answer = self.llm_provider.generate_answer(
            question=question,
            context_items=all_context,
            search_type=search_type
        )
        
        # Format context
        context_summary = self._format_context_summary(all_context)
        
        return {
            "answer": answer,
            "question": question,
            "context": context_summary,
            "context_count": len(all_context),
            "search_type": search_type,
            "node_types": node_types,
            "model": self.llm_provider.model,
            "provider": self.llm_provider.get_provider_name()
        }
    
    def _format_context_summary(
        self,
        context_items: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Format context items into serializable dictionaries.
        
        Args:
            context_items: List of search results
        
        Returns:
            List of context summaries
        """
        context_summary = []
        for item in context_items:
            summary = {
                "type": getattr(item, 'type', 'Unknown'),
                "name": getattr(item, 'name', 'N/A'),
                "content": getattr(item, 'content', '')[:500],  # Truncate for response
                "score": getattr(item, 'score', None)
            }
            context_summary.append(summary)
        
        return context_summary
