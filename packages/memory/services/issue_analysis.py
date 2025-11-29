from typing import Dict, Any, List, Optional
import logging
from packages.memory.services.graph_service import GraphService
from packages.memory.llm import BaseLLMProvider
from packages.memory.factories.llm_factory import create_llm_provider
from packages.database.graph.graph import neo4j_client

logger = logging.getLogger(__name__)

class IssueAnalyzer:
    """
    Analyzes GitHub issues to identify causes and solutions based on the Knowledge Graph.
    """
    
    def __init__(
        self,
        graph_service: Optional[GraphService] = None,
        llm_provider: Optional[BaseLLMProvider] = None
    ):
        self.graph_service = graph_service or GraphService(neo4j_client=neo4j_client)
        self.llm_provider = llm_provider or create_llm_provider()
        
    def analyze_issue(self, title: str, body: str) -> Dict[str, Any]:
        """
        Analyze an issue and return a report.
        
        Args:
            title: Issue title
            body: Issue body/description
            
        Returns:
            Analysis report
        """
        issue_text = f"{title}\n\n{body}"
        logger.info(f"Analyzing issue: {title}")
        
        # 1. Search for relevant code (Functions, Classes, Files)
        # We search for keywords from the issue in the code
        code_context = self.graph_service.hybrid_search(
            query_text=issue_text,
            node_type="Function", # Start with functions as they are most granular
            limit=5
        )
        
        # Also search for Files directly
        file_context = self.graph_service.hybrid_search(
            query_text=issue_text,
            node_type="File",
            limit=3
        )
        
        # 2. Search for relevant history (Commits)
        # Maybe the issue was introduced recently?
        commit_context = self.graph_service.hybrid_search(
            query_text=issue_text,
            node_type="Commit",
            limit=5
        )
        
        # Combine context
        all_context = code_context + file_context + commit_context
        
        if not all_context:
            return {
                "error": "No relevant context found in the knowledge graph."
            }
            
        # 3. Generate Report using LLM
        system_prompt = """
        You are an expert software engineer and debugger. 
        You are given a GitHub issue description and a set of relevant code snippets and commit history from the project's Knowledge Graph.
        
        Your task is to analyze the issue and provide a detailed report containing:
        1. **Root Cause Analysis**: What is likely causing the issue based on the code and history?
        2. **Affected Areas**: Which files, classes, or functions are involved?
        3. **Suggested Fix**: How can this be fixed? Provide code snippets if possible.
        4. **Relevant History**: Are there recent commits that might have introduced this?
        
        Be specific. Reference the filenames and function names provided in the context.
        """
        
        # Format context for LLM
        context_str = self._format_context(all_context)
        
        prompt = f"""
        ISSUE TITLE: {title}
        
        ISSUE BODY:
        {body}
        
        RELEVANT CONTEXT FROM KNOWLEDGE GRAPH:
        {context_str}
        
        Please provide your analysis report.
        """
        
        response = self.llm_provider.generate_text(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        return {
            "report": response,
            "context_used": [self._format_item_summary(item) for item in all_context]
        }

    def _format_context(self, items: List[Any]) -> str:
        output = []
        for item in items:
            node = getattr(item, 'node', item)
            if isinstance(node, dict):
                node_type = node.get('labels', ['Unknown'])[0] if node.get('labels') else 'Unknown'
                name = node.get('name') or node.get('sha', 'N/A')
                content = node.get('content') or node.get('snippet') or node.get('message') or ''
                
                output.append(f"--- [{node_type}] {name} ---\n{content}\n")
        return "\n".join(output)

    def _format_item_summary(self, item: Any) -> Dict[str, Any]:
        node = getattr(item, 'node', item)
        if isinstance(node, dict):
            return {
                "type": node.get('labels', ['Unknown'])[0] if node.get('labels') else 'Unknown',
                "name": node.get('name') or node.get('sha', 'N/A'),
                "score": getattr(item, 'score', 0.0)
            }
        return {"type": "Unknown", "name": "Unknown"}
