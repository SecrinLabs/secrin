import logging
import argparse
import asyncio
import os
import tempfile
import shutil
from urllib.parse import urlparse

# Configure logging and monitoring
from packages.wiki.dependency_analyzer.utils.logging_config import setup_logging

# Initialize colored logging
setup_logging(level=logging.INFO)

logger = logging.getLogger(__name__)

# Local imports
from packages.wiki.documentation_generator import DocumentationGenerator
from packages.config import WikiConfig, Settings


def is_git_url(path: str) -> bool:
    """Check if the path is a git URL."""
    if path.startswith(("http://", "https://", "git@", "ssh://")):
        return True
    if "github.com" in path or "gitlab.com" in path or "bitbucket.org" in path:
        return True
    return False


def clone_repository(url: str, target_dir: str) -> str:
    """
    Clone a git repository to the target directory.
    
    Args:
        url: Git repository URL
        target_dir: Directory to clone into
        
    Returns:
        Path to the cloned repository
    """
    import git
    
    # Extract repo name from URL
    parsed = urlparse(url)
    path_parts = parsed.path.rstrip("/").split("/")
    repo_name = path_parts[-1].replace(".git", "") if path_parts else "repo"
    
    clone_path = os.path.join(target_dir, repo_name)
    
    # If already cloned, pull latest
    if os.path.exists(clone_path):
        logger.info(f"📂 Repository already exists at {clone_path}, pulling latest...")
        try:
            repo = git.Repo(clone_path)
            repo.remotes.origin.pull()
            logger.info("✅ Repository updated successfully")
        except Exception as e:
            logger.warning(f"Could not pull latest changes: {e}")
        return clone_path
    
    logger.info(f"📥 Cloning repository from {url}...")
    git.Repo.clone_from(url, clone_path, depth=1)  # Shallow clone for speed
    logger.info(f"✅ Repository cloned to {clone_path}")
    
    return clone_path


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate comprehensive documentation for Python components in dependency order.'
    )
    parser.add_argument(
        '--repo-path',
        type=str,
        required=True,
        help='Path to the repository (local path or git URL)'
    )
    
    return parser.parse_args()


async def async_main() -> None:
    """Main entry point for the documentation generation process."""
    try:
        # Parse arguments and create configuration
        args = parse_arguments()
        settings = Settings()
        
        # Handle git URLs - clone to output directory
        repo_path = args.repo_path
        if is_git_url(repo_path):
            # Clone to a repos subdirectory in the output base
            repos_dir = os.path.join(settings.WIKI_OUTPUT_BASE_DIR, "repos")
            os.makedirs(repos_dir, exist_ok=True)
            repo_path = clone_repository(repo_path, repos_dir)
            # Update args with the local path
            args.repo_path = repo_path
        
        config = WikiConfig.from_args(args)
        
        # Create and run documentation generator
        doc_generator = DocumentationGenerator(config)
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