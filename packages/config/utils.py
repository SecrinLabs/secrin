"""
Configuration utilities and helpers.
"""

import os
from typing import Any, Dict, Optional
from pathlib import Path
import json


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
