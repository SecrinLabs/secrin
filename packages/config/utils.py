"""
Configuration utilities and helpers.
"""

import os
import argparse
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from pathlib import Path
import json


# ============================================================================
# CLI Context Management
# ============================================================================

_CLI_CONTEXT = False


def set_cli_context(enabled: bool = True) -> None:
    """
    Set whether we're running in CLI context (vs web app).
    
    Args:
        enabled: True for CLI context, False for web app context
    """
    global _CLI_CONTEXT
    _CLI_CONTEXT = enabled


def is_cli_context() -> bool:
    """
    Check if running in CLI context.
    
    Returns:
        True if running in CLI context, False otherwise
    """
    return _CLI_CONTEXT


# ============================================================================
# WikiConfig Dataclass
# ============================================================================

@dataclass
class WikiConfig:
    """
    Configuration dataclass for Wiki/Documentation generation.
    
    This class provides a structured way to pass configuration through
    the wiki generation pipeline, supporting both CLI and web app contexts.
    """
    repo_path: str
    output_dir: str
    dependency_graph_dir: str
    docs_dir: str
    max_depth: int
    # LLM configuration
    llm_base_url: str
    llm_api_key: str
    main_model: str
    cluster_model: str
    fallback_model: str = "glm-4p5"
    
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'WikiConfig':
        """
        Create configuration from parsed arguments.
        
        Args:
            args: Parsed command line arguments with repo_path attribute
            
        Returns:
            WikiConfig instance configured from arguments
        """
        from packages.config.settings import Settings
        
        settings = Settings()
        repo_name = os.path.basename(os.path.normpath(args.repo_path))
        sanitized_repo_name = ''.join(c if c.isalnum() else '_' for c in repo_name)
        
        return cls(
            repo_path=args.repo_path,
            output_dir=settings.WIKI_OUTPUT_BASE_DIR,
            dependency_graph_dir=os.path.join(
                settings.WIKI_OUTPUT_BASE_DIR, 
                settings.WIKI_DEPENDENCY_GRAPHS_DIR
            ),
            docs_dir=os.path.join(
                settings.WIKI_OUTPUT_BASE_DIR, 
                settings.WIKI_DOCS_DIR, 
                f"{sanitized_repo_name}-docs"
            ),
            max_depth=settings.WIKI_MAX_DEPTH,
            llm_base_url=settings.WIKI_LLM_BASE_URL,
            llm_api_key=settings.WIKI_LLM_API_KEY,
            main_model=settings.WIKI_MAIN_MODEL,
            cluster_model=settings.get_wiki_cluster_model(),
            fallback_model=settings.WIKI_FALLBACK_MODEL
        )
    
    @classmethod
    def from_cli(
        cls,
        repo_path: str,
        output_dir: str,
        llm_base_url: str,
        llm_api_key: str,
        main_model: str,
        cluster_model: str,
        fallback_model: Optional[str] = None
    ) -> 'WikiConfig':
        """
        Create configuration for CLI context.
        
        In CLI mode, configuration is loaded from ~/.codewiki/config.json + keyring.
        
        Args:
            repo_path: Repository path to generate documentation for
            output_dir: Output directory for generated docs
            llm_base_url: LLM API base URL
            llm_api_key: LLM API key
            main_model: Primary model for generation
            cluster_model: Model for clustering operations
            fallback_model: Fallback model (optional)
            
        Returns:
            WikiConfig instance configured for CLI usage
        """
        from packages.config.settings import Settings
        
        settings = Settings()
        base_output_dir = os.path.join(output_dir, "temp")
        
        return cls(
            repo_path=repo_path,
            output_dir=base_output_dir,
            dependency_graph_dir=os.path.join(
                base_output_dir, 
                settings.WIKI_DEPENDENCY_GRAPHS_DIR
            ),
            docs_dir=output_dir,
            max_depth=settings.WIKI_MAX_DEPTH,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
            main_model=main_model,
            cluster_model=cluster_model,
            fallback_model=fallback_model or settings.WIKI_FALLBACK_MODEL
        )
    
    @classmethod
    def from_settings(cls, repo_path: str, settings: Optional[Any] = None) -> 'WikiConfig':
        """
        Create configuration from Settings (for web app context).
        
        Args:
            repo_path: Repository path to generate documentation for
            settings: Settings instance (creates new one if not provided)
            
        Returns:
            WikiConfig instance configured from settings
        """
        if settings is None:
            from packages.config.settings import Settings
            settings = Settings()
        
        repo_name = os.path.basename(os.path.normpath(repo_path))
        sanitized_repo_name = ''.join(c if c.isalnum() else '_' for c in repo_name)
        
        return cls(
            repo_path=repo_path,
            output_dir=settings.WIKI_OUTPUT_BASE_DIR,
            dependency_graph_dir=os.path.join(
                settings.WIKI_OUTPUT_BASE_DIR, 
                settings.WIKI_DEPENDENCY_GRAPHS_DIR
            ),
            docs_dir=os.path.join(
                settings.WIKI_OUTPUT_BASE_DIR, 
                settings.WIKI_DOCS_DIR, 
                f"{sanitized_repo_name}-docs"
            ),
            max_depth=settings.WIKI_MAX_DEPTH,
            llm_base_url=settings.WIKI_LLM_BASE_URL,
            llm_api_key=settings.WIKI_LLM_API_KEY,
            main_model=settings.WIKI_MAIN_MODEL,
            cluster_model=settings.get_wiki_cluster_model(),
            fallback_model=settings.WIKI_FALLBACK_MODEL
        )


# ============================================================================
# Configuration File Utilities
# ============================================================================


def get_config_path(filename: str = ".env") -> Path:
    """
    Get the path to a configuration file.
    
    Args:
        filename: Name of the configuration file
        
    Returns:
        Path object pointing to the configuration file
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    return project_root / filename


def load_env_file(filepath: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        filepath: Optional path to .env file (defaults to project root)
        
    Returns:
        Dictionary of environment variables
    """
    if filepath is None:
        filepath = get_config_path(".env")
    
    env_vars = {}
    
    if not filepath.exists():
        return env_vars
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse key=value
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                env_vars[key] = value
    
    return env_vars


def export_config_template(output_path: Optional[Path] = None) -> None:
    """
    Export current configuration as a template file.
    
    Args:
        output_path: Optional path for output file (defaults to config.template.json)
    """
    from packages.config.settings import Settings
    
    if output_path is None:
        output_path = get_config_path("config.template.json")
    
    settings = Settings()
    
    # Extract all settings as a dictionary
    config_dict = settings.model_dump()
    
    # Remove sensitive data
    sensitive_keys = ['NEO4J_PASS', 'OPENAI_API_KEY', 'API_KEY']
    for key in sensitive_keys:
        if key in config_dict:
            config_dict[key] = "***REDACTED***"
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2, default=str)
    
    print(f"Configuration template exported to: {output_path}")


def validate_required_settings() -> tuple[bool, list[str]]:
    """
    Validate that all required settings are configured.
    
    Returns:
        Tuple of (is_valid, missing_settings)
    """
    from packages.config.settings import Settings
    
    settings = Settings()
    missing = []
    
    # Check required settings
    required = {
        'NEO4J_URI': settings.NEO4J_URI,
        'NEO4J_USER': settings.NEO4J_USER,
        'NEO4J_PASS': settings.NEO4J_PASS,
    }
    
    # Check provider-specific requirements
    if settings.EMBEDDING_PROVIDER == "openai":
        required['OPENAI_API_KEY'] = settings.OPENAI_API_KEY
    
    for key, value in required.items():
        if not value or value == "":
            missing.append(key)
    
    return len(missing) == 0, missing


def get_effective_config() -> Dict[str, Any]:
    """
    Get the effective configuration (after all overrides applied).
    
    Returns:
        Dictionary of current configuration values
    """
    from packages.config.settings import Settings
    from packages.config.feature_flags import get_feature_flag_manager
    
    settings = Settings()
    flag_manager = get_feature_flag_manager()
    
    return {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "log_level": settings.LOG_LEVEL,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_dimension": settings.EMBEDDING_DIMENSION,
        "feature_flags": flag_manager.get_all_flags(),
        "neo4j": {
            "uri": settings.NEO4J_URI,
            "database": settings.NEO4J_DB,
            "pool_size": settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
        },
        "api": {
            "host": settings.API_HOST,
            "port": settings.API_PORT,
            "version": settings.API_VERSION,
        }
    }


def print_config_summary() -> None:
    """Print a summary of the current configuration."""
    config = get_effective_config()
    
    print("=" * 80)
    print("SECRIN CONFIGURATION SUMMARY")
    print("=" * 80)
    print(f"\nEnvironment: {config['environment']}")
    print(f"Debug Mode: {config['debug']}")
    print(f"Log Level: {config['log_level']}")
    
    print("\n--- Embedding Configuration ---")
    print(f"Provider: {config['embedding_provider']}")
    print(f"Dimension: {config['embedding_dimension']}")
    
    print("\n--- Neo4j Configuration ---")
    print(f"URI: {config['neo4j']['uri']}")
    print(f"Database: {config['neo4j']['database']}")
    print(f"Pool Size: {config['neo4j']['pool_size']}")
    
    print("\n--- API Configuration ---")
    print(f"Host: {config['api']['host']}")
    print(f"Port: {config['api']['port']}")
    print(f"Version: {config['api']['version']}")
    
    print("\n--- Feature Flags ---")
    for flag, enabled in config['feature_flags'].items():
        status = "✓ ENABLED" if enabled else "✗ DISABLED"
        print(f"{flag}: {status}")
    
    print("\n" + "=" * 80)


# ============================================================================
# File Manager
# ============================================================================

class FileManager:
    """Handles file I/O operations."""
    
    @staticmethod
    def ensure_directory(path: str) -> None:
        """Create directory if it doesn't exist."""
        os.makedirs(path, exist_ok=True)
    
    @staticmethod
    def save_json(data: Any, filepath: str) -> None:
        """Save data as JSON to file."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
    
    @staticmethod
    def load_json(filepath: str) -> Optional[Dict[str, Any]]:
        """Load JSON from file, return None if file doesn't exist."""
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def save_text(content: str, filepath: str) -> None:
        """Save text content to file."""
        with open(filepath, 'w') as f:
            f.write(content)
    
    @staticmethod
    def load_text(filepath: str) -> str:
        """Load text content from file."""
        with open(filepath, 'r') as f:
            return f.read()


# Singleton instance for convenience
file_manager = FileManager()


if __name__ == "__main__":
    # Run configuration validation and print summary
    is_valid, missing = validate_required_settings()
    
    if not is_valid:
        print("⚠️  WARNING: Missing required settings:")
        for setting in missing:
            print(f"  - {setting}")
        print("\nPlease configure these in your .env file")
        print()
    
    print_config_summary()
