from pydantic_ai import Agent
# import logfire
import logging
import os
from typing import Dict, List, Any, Optional

# Configure logging and monitoring

logger = logging.getLogger(__name__)

# Local imports
from packages.wiki.agent_tools.deps import CodeWikiDeps
from packages.wiki.agent_tools.read_code_components import read_code_components_tool
from packages.wiki.agent_tools.str_replace_editor import str_replace_editor_tool
from packages.wiki.agent_tools.generate_sub_module_documentations import generate_sub_module_documentation_tool
from packages.wiki.llm_services import create_fallback_models
from packages.wiki.prompt_template import (
    SYSTEM_PROMPT,
    LEAF_SYSTEM_PROMPT,
    format_user_prompt,
)
from packages.wiki.dependency_analyzer.models.core import Node

from packages.wiki.utils import is_complex_module
from packages.config import Settings, WikiConfig, file_manager

# Get settings for constants
_settings = Settings()


class AgentOrchestrator:
    """Orchestrates the AI agents for documentation generation."""
    
    def __init__(self, config: WikiConfig):
        self.config = config
        self.fallback_models = create_fallback_models(config)
    
    def create_agent(self, module_name: str, components: Dict[str, Any], 
                    core_component_ids: List[str]) -> Agent[CodeWikiDeps, str]:
        """Create an appropriate agent based on module complexity."""
        if is_complex_module(components, core_component_ids):
            return Agent(
                self.fallback_models,
                name=module_name,
                deps_type=CodeWikiDeps,
                tools=[
                    read_code_components_tool, 
                    str_replace_editor_tool, 
                    generate_sub_module_documentation_tool
                ],
                system_prompt=SYSTEM_PROMPT.format(module_name=module_name),
            )
        else:
            return Agent(
                self.fallback_models,
                name=module_name,
                deps_type=CodeWikiDeps,
                tools=[read_code_components_tool, str_replace_editor_tool],
                system_prompt=LEAF_SYSTEM_PROMPT.format(module_name=module_name),
            )
    
    async def process_module(self, module_name: str, components: Dict[str, Node], 
                           core_component_ids: List[str], module_path: List[str], working_dir: str) -> Dict[str, Any]:
        """Process a single module and generate its documentation."""
        logger.info(f"Processing module: {module_name}")
        
        # Load or create module tree
        module_tree_path = os.path.join(working_dir, _settings.WIKI_MODULE_TREE_FILENAME)
        module_tree = file_manager.load_json(module_tree_path) or {}
        
        # Create agent
        agent = self.create_agent(module_name, components, core_component_ids)
        
        # Create dependencies
        deps = CodeWikiDeps(
            absolute_docs_path=working_dir,
            absolute_repo_path=str(os.path.abspath(self.config.repo_path)),
            registry={},
            components=components,
            path_to_current_module=module_path,
            current_module_name=module_name,
            module_tree=module_tree,
            max_depth=self.config.max_depth,
            current_depth=1,
            config=self.config
        )

        # check if overview docs already exists
        overview_docs_path = os.path.join(working_dir, _settings.WIKI_OVERVIEW_FILENAME)
        if os.path.exists(overview_docs_path):
            logger.info(f"✓ Overview docs already exists at {overview_docs_path}")
            return module_tree

        # check if module docs already exists
        docs_path = os.path.join(working_dir, f"{module_name}.md")
        if os.path.exists(docs_path):
            logger.info(f"✓ Module docs already exists at {docs_path}")
            return module_tree
        
        # Run agent
        try:
            result = await agent.run(
                format_user_prompt(
                    module_name=module_name,
                    core_component_ids=core_component_ids,
                    components=components,
                    module_tree=deps.module_tree
                ),
                deps=deps
            )
            
            # Save updated module tree
            file_manager.save_json(deps.module_tree, module_tree_path)
            logger.debug(f"Successfully processed module: {module_name}")
            
            return deps.module_tree
            
        except Exception as e:
            logger.error(f"Error processing module {module_name}: {str(e)}")
            raise