"""
Question-Answering service that combines search and LLM.
Provides natural language answers to code-related questions.
"""

from typing import Optional, Dict, Any, List, Iterator
import logging
from packages.memory.services.graph_service import GraphService
from packages.memory.llm import BaseLLMProvider
from packages.memory.factories.llm_factory import create_llm_provider
from packages.memory.prompts import PromptFactory
from packages.memory.agents import AgentType
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
        agent_type: str = AgentType.PATHFINDER.value,
        search_type: str = "hybrid",
        context_limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Ask a question and get a natural language answer with context.
        
        Args:
            question: The question to answer
            agent_type: Type of agent to use (determines node types and prompt)
            search_type: Type of search ('vector' or 'hybrid')
            context_limit: Maximum number of context items to retrieve
            
        Returns:
            Dictionary containing answer, context, and metadata
        """
        logger.info(f"Processing question with {agent_type} agent: '{question[:50]}...'")
        
        # Step 1: Retrieve relevant context
        if search_type == "hybrid":
            if not is_feature_enabled(FeatureFlag.ENABLE_HYBRID_SEARCH):
                logger.warning("Hybrid search disabled, falling back to vector search")
                search_type = "vector"
        
        node_types = AgentType.get_node_types(agent_type)
        context_per_type = max(1, context_limit // len(node_types))
        
        context_items = []
        for node_type in node_types:
            try:
                if search_type == "vector":
                    items = self.graph_service.vector_search(
                        query_text=question,
                        node_type=node_type,
                        limit=context_per_type
                    )
                else:
                    items = self.graph_service.hybrid_search(
                        query_text=question,
                        node_type=node_type,
                        limit=context_per_type
                    )
                context_items.extend(items)
            except Exception as e:
                logger.warning(f"Error searching {node_type}: {e}")
        
        logger.info(f"Retrieved {len(context_items)} context items across {node_types}")
        
        # Check if we have context
        if not context_items:
            return {
                "answer": "I couldn't find any relevant context in the codebase to answer your question. Please try rephrasing or ensure the code has been indexed.",
                "question": question,
                "context": [],
                "context_count": 0,
                "search_type": search_type,
                "node_types": node_types,
                "agent_type": agent_type,
                "model": self.llm_provider.model,
                "provider": self.llm_provider.get_provider_name()
            }
        
        system_prompt = PromptFactory.get_prompt(agent_type)
        context_str = self._format_context_for_llm(context_items)
        prompt = f"""
            QUESTION: {question}

            RELEVANT CONTEXT FROM KNOWLEDGE GRAPH:
            {context_str}

            Please provide your answer based on the context above."""
                    
        answer = self.llm_provider.generate_text(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Step 3: Format and return response
        context_summary = self._format_context_summary(context_items)
        
        return {
            "answer": answer,
            "question": question,
            "context": context_summary,
            "context_count": len(context_items),
            "search_type": search_type,
            "node_types": node_types,
            "agent_type": agent_type,
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
            # Extract node data (SearchResult objects have a 'node' attribute)
            node = getattr(item, 'node', item) if hasattr(item, 'node') else item
            
            # Get node properties
            if isinstance(node, dict):
                node_type = node.get('labels', ['Unknown'])[0] if node.get('labels') else 'Unknown'
                name = node.get('name') or node.get('sha', 'N/A')[:8] if node.get('sha') else 'N/A'
                content = node.get('content', '')
            else:
                node_type = 'Unknown'
                name = 'N/A'
                content = ''
            
            summary = {
                "type": node_type,
                "name": name,
                "content": content[:500],  # Truncate for response
                "score": getattr(item, 'score', None)
            }
            context_summary.append(summary)
        
        return context_summary

    def ask_stream(
        self,
        question: str,
        agent_type: str = AgentType.PATHFINDER.value,
        search_type: str = "hybrid",
        context_limit: int = 5,
    ) -> Iterator[Dict[str, Any]]:
        logger.info(f"Processing streaming question with {agent_type} agent: '{question[:50]}...'")
        
        if search_type == "hybrid":
            if not is_feature_enabled(FeatureFlag.ENABLE_HYBRID_SEARCH):
                logger.warning("Hybrid search disabled, falling back to vector search")
                search_type = "vector"
        
        node_types = AgentType.get_node_types(agent_type)
        context_per_type = max(1, context_limit // len(node_types))
        
        # Search across multiple node types
        context_items = []
        for nt in node_types:
            try:
                if search_type == "vector":
                    items = self.graph_service.vector_search(
                        query_text=question,
                        node_type=nt,
                        limit=context_per_type
                    )
                else:
                    items = self.graph_service.hybrid_search(
                        query_text=question,
                        node_type=nt,
                        limit=context_per_type
                    )
                context_items.extend(items)
            except Exception as e:
                logger.warning(f"Error searching {nt}: {e}")
        
        logger.info(f"Retrieved {len(context_items)} context items across {node_types}")
        
        context_summary = self._format_context_summary(context_items)
        yield {
            "context": context_summary,
            "context_count": len(context_items),
            "search_type": search_type,
            "node_types": node_types,
            "agent_type": agent_type,
            "model": self.llm_provider.model,
            "provider": self.llm_provider.get_provider_name()
        }
        
        if not context_items:
            yield {
                "chunk": "I couldn't find any relevant context in the codebase to answer your question. Please try rephrasing or ensure the code has been indexed.",
                "done": True
            }
            return
        
        context_str = self._format_context_for_llm(context_items)
        
        system_prompt = PromptFactory.get_prompt(agent_type)
        
        prompt = f"""
            QUESTION: {question}

            RELEVANT CONTEXT FROM KNOWLEDGE GRAPH:
            {context_str}

            Please provide your answer based on the context above.
            """
        
        for chunk in self.llm_provider.stream_text(prompt=prompt, system_prompt=system_prompt):
            yield {"chunk": chunk}
        yield {"done": True}

    def _format_context_for_llm(self, context_items: List[Any]) -> str:
        output = []
        for item in context_items:
            node = getattr(item, 'node', item) if hasattr(item, 'node') else item
            
            if isinstance(node, dict):
                node_type = node.get('labels', ['Unknown'])[0] if node.get('labels') else 'Unknown'
                name = node.get('name') or node.get('sha', 'N/A')
                content = node.get('content') or node.get('snippet') or node.get('message') or ''
                output.append(f"--- [{node_type}] {name} ---\n{content}\n")
        return "\n".join(output)

