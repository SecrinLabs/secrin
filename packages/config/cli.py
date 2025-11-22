#!/usr/bin/env python3
"""
Configuration management CLI tool.
Provides utilities for validating, inspecting, and managing application configuration.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from packages.config.utils import (
    validate_required_settings,
    print_config_summary,
    export_config_template,
    get_effective_config
)
from packages.config.feature_flags import get_feature_flag_manager, FeatureFlag


def cmd_validate(args):
    """Validate configuration and check for missing required settings."""
    print("Validating configuration...\n")
    
    is_valid, missing = validate_required_settings()
    
    if is_valid:
        print("✅ Configuration is valid!")
        print("All required settings are configured.")
    else:
        print("❌ Configuration is invalid!")
        print("\nMissing required settings:")
        for setting in missing:
            print(f"  • {setting}")
        print("\nPlease configure these in your .env file")
        sys.exit(1)


def cmd_summary(args):
    """Print configuration summary."""
    print_config_summary()


def cmd_export(args):
    """Export configuration template."""
    output_path = Path(args.output) if args.output else None
    export_config_template(output_path)


def cmd_flags(args):
    """List feature flags and their status."""
    manager = get_feature_flag_manager()
    flags = manager.get_all_flags()
    
    print("=" * 80)
    print("FEATURE FLAGS")
    print("=" * 80)
    
    enabled = [f for f, status in flags.items() if status]
    disabled = [f for f, status in flags.items() if not status]
    
    if enabled:
        print("\n✅ ENABLED:")
        for flag in sorted(enabled):
            print(f"  • {flag}")
    
    if disabled:
        print("\n❌ DISABLED:")
        for flag in sorted(disabled):
            print(f"  • {flag}")
    
    print(f"\nTotal: {len(enabled)} enabled, {len(disabled)} disabled")
    print("=" * 80)


def cmd_env(args):
    """Show environment-specific configuration."""
    from packages.config.settings import Settings
    
    settings = Settings()
    
    print("=" * 80)
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    print("=" * 80)
    
    print(f"\nDebug Mode: {settings.DEBUG}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    
    if settings.is_production():
        print("\n⚠️  RUNNING IN PRODUCTION MODE")
        print("  • Debug mode should be OFF")
        print("  • Sensitive logging should be disabled")
        print("  • Security features should be enabled")
    elif settings.is_development():
        print("\n🔧 RUNNING IN DEVELOPMENT MODE")
        print("  • Enhanced logging available")
        print("  • Experimental features can be tested")
    else:
        print(f"\n📦 RUNNING IN {settings.ENVIRONMENT.upper()} MODE")
    
    print("=" * 80)


def cmd_check_provider(args):
    """Check embedding provider configuration."""
    from packages.config.settings import Settings
    
    settings = Settings()
    provider = settings.EMBEDDING_PROVIDER
    
    print("=" * 80)
    print(f"EMBEDDING PROVIDER: {provider.upper()}")
    print("=" * 80)
    
    if provider == "openai":
        print("\nOpenAI Configuration:")
        print(f"  Model: {settings.OPENAI_EMBEDDING_MODEL}")
        print(f"  API Key: {'✅ Set' if settings.OPENAI_API_KEY else '❌ Not Set'}")
        print(f"  Max Retries: {settings.OPENAI_MAX_RETRIES}")
        print(f"  Timeout: {settings.OPENAI_TIMEOUT}s")
        
        if not settings.OPENAI_API_KEY:
            print("\n⚠️  WARNING: OPENAI_API_KEY is not set!")
            
    elif provider == "ollama":
        print("\nOllama Configuration:")
        print(f"  Base URL: {settings.OLLAMA_BASE_URL}")
        print(f"  Model: {settings.OLLAMA_EMBEDDING_MODEL}")
        print(f"  Timeout: {settings.OLLAMA_TIMEOUT}s")
        print(f"  Dimension: {settings.EMBEDDING_DIMENSION}")
        
    elif provider == "sentence_transformer":
        print("\nSentence Transformer Configuration:")
        print(f"  Model: {settings.SENTENCE_TRANSFORMER_MODEL}")
        print(f"  Device: {settings.SENTENCE_TRANSFORMER_DEVICE}")
        print(f"  Dimension: {settings.EMBEDDING_DIMENSION}")
    
    print("\nGeneral Settings:")
    print(f"  Batch Size: {settings.EMBEDDING_BATCH_SIZE}")
    print(f"  Cache TTL: {settings.EMBEDDING_CACHE_TTL}s")
    
    print("=" * 80)


def cmd_test_connection(args):
    """Test Neo4j database connection."""
    from packages.config.settings import Settings
    from packages.database.graph.graph import Neo4jClient
    
    settings = Settings()
    
    print("Testing Neo4j connection...\n")
    print(f"URI: {settings.NEO4J_URI}")
    print(f"Database: {settings.NEO4J_DB}")
    
    try:
        client = Neo4jClient()
        result = client.run_query("RETURN 1 as test")
        
        if result and result[0]["test"] == 1:
            print("\n✅ Connection successful!")
        else:
            print("\n❌ Connection failed: Unexpected response")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Secrin Configuration Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate configuration
  python -m packages.config.cli validate
  
  # Show configuration summary
  python -m packages.config.cli summary
  
  # List feature flags
  python -m packages.config.cli flags
  
  # Check embedding provider
  python -m packages.config.cli provider
  
  # Test database connection
  python -m packages.config.cli test-connection
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Validate command
    parser_validate = subparsers.add_parser(
        "validate",
        help="Validate configuration and check for missing settings"
    )
    parser_validate.set_defaults(func=cmd_validate)
    
    # Summary command
    parser_summary = subparsers.add_parser(
        "summary",
        help="Print configuration summary"
    )
    parser_summary.set_defaults(func=cmd_summary)
    
    # Export command
    parser_export = subparsers.add_parser(
        "export",
        help="Export configuration template"
    )
    parser_export.add_argument(
        "-o", "--output",
        help="Output file path (default: config.template.json)"
    )
    parser_export.set_defaults(func=cmd_export)
    
    # Flags command
    parser_flags = subparsers.add_parser(
        "flags",
        help="List feature flags and their status"
    )
    parser_flags.set_defaults(func=cmd_flags)
    
    # Environment command
    parser_env = subparsers.add_parser(
        "env",
        help="Show environment-specific configuration"
    )
    parser_env.set_defaults(func=cmd_env)
    
    # Provider command
    parser_provider = subparsers.add_parser(
        "provider",
        help="Check embedding provider configuration"
    )
    parser_provider.set_defaults(func=cmd_check_provider)
    
    # Test connection command
    parser_test = subparsers.add_parser(
        "test-connection",
        help="Test Neo4j database connection"
    )
    parser_test.set_defaults(func=cmd_test_connection)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
