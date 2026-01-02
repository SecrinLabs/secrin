import logging
import argparse
import asyncio

# Configure logging and monitoring
from packages.wiki.dependency_analyzer.utils.logging_config import setup_logging

# Initialize colored logging
setup_logging(level=logging.INFO)

logger = logging.getLogger(__name__)

# Local imports
from packages.wiki.documentation_generator import DocumentationGenerator
from packages.wiki.fumadocs_generator import FumadocsGenerator
from packages.config import WikiConfig, Settings


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate comprehensive documentation for Python components in dependency order.'
    )
    parser.add_argument(
        '--repo-path',
        type=str,
        required=True,
        help='Path to the repository'
    )
    parser.add_argument(
        '--no-fumadocs',
        action='store_true',
        default=False,
        help='Skip Fumadocs static site generation'
    )
    parser.add_argument(
        '--fumadocs-only',
        action='store_true',
        default=False,
        help='Only generate Fumadocs site from existing docs (skip doc generation)'
    )
    
    return parser.parse_args()


async def async_main() -> None:
    """Main entry point for the documentation generation process."""
    try:
        # Parse arguments and create configuration
        args = parse_arguments()
        config = WikiConfig.from_args(args)
        settings = Settings()
        
        # Handle fumadocs-only mode
        if args.fumadocs_only:
            import os
            docs_dir = os.path.join(
                settings.WIKI_OUTPUT_BASE_DIR,
                os.path.basename(os.path.normpath(config.repo_path)),
                settings.WIKI_DOCS_DIR
            )
            logger.info(f"📚 Generating Fumadocs site from existing docs at: {docs_dir}")
            fumadocs_generator = FumadocsGenerator(docs_dir)
            site_dir = fumadocs_generator.generate()
            logger.info(f"✅ Fumadocs site generated at: {site_dir}")
            return
        
        # Create and run documentation generator
        doc_generator = DocumentationGenerator(config)
        doc_generator.skip_fumadocs = getattr(args, 'no_fumadocs', False)
        await doc_generator.run()
        
    except KeyboardInterrupt:
        logger.debug("Documentation generation interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise


def main() -> None:
    """Synchronous wrapper for poetry script entry point."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()