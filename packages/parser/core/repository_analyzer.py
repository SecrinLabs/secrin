"""Main repository analyzer that orchestrates the parsing process"""
from pathlib import Path
from typing import Optional, Dict
import subprocess

from packages.parser.models import GraphData, RepoNode
from packages.parser.core import BaseLanguageParser
from packages.parser.languages import PythonParser, JavaScriptParser
from packages.parser.utils import (
    detect_language,
    is_code_file,
    should_ignore_path,
    get_relative_path,
    language_registry,
    is_git_url,
    clone_repository,
    cleanup_temp_repo,
    extract_repo_info,
    is_git_installed,
)


class RepositoryAnalyzer:
    """
    Main class that orchestrates repository analysis
    Scans a repository, detects file languages, and routes to appropriate parsers
    """
    
    def __init__(self):
        self.parsers: Dict[str, BaseLanguageParser] = {}
        self._initialize_parsers()
    
    def _initialize_parsers(self):
        """Initialize all available language parsers"""
        # Python
        python_lang = language_registry.get_language("python")
        if python_lang:
            self.parsers["python"] = PythonParser(python_lang)
        
        # JavaScript
        js_lang = language_registry.get_language("javascript")
        if js_lang:
            self.parsers["javascript"] = JavaScriptParser(js_lang)
        
        # Add more parsers as they become available
        # TypeScript, Java, Go, etc.
    
    def analyze_repository(self, repo_path: str | Path, cleanup_after: bool = True) -> GraphData:
        """
        Analyze an entire repository and extract graph data
        
        Supports both local paths and Git URLs (GitHub, GitLab, Bitbucket, etc.)
        
        Args:
            repo_path: Path to the repository root OR a Git URL (e.g., https://github.com/user/repo)
            cleanup_after: If True, cleanup temporary cloned repos after analysis
        
        Returns:
            GraphData containing all nodes and relationships
        
        Examples:
            # Local path
            graph_data = analyzer.analyze_repository("/path/to/repo")
            
            # GitHub URL
            graph_data = analyzer.analyze_repository("https://github.com/user/repo")
            
            # Keep cloned repo after analysis
            graph_data = analyzer.analyze_repository("https://github.com/user/repo", cleanup_after=False)
        """
        repo_path_str = str(repo_path)
        is_temp_clone = False
        original_input = repo_path_str
        
        # Check if it's a Git URL
        if is_git_url(repo_path_str):
            if not is_git_installed():
                raise RuntimeError("Git is not installed. Please install git to clone repositories.")
            
            print(f"Detected Git URL: {repo_path_str}")
            
            # Clone the repository
            try:
                repo_path, is_temp_clone = clone_repository(repo_path_str)
            except Exception as e:
                raise RuntimeError(f"Failed to clone repository: {e}")
        else:
            repo_path = Path(repo_path).resolve()
            
            if not repo_path.exists():
                raise ValueError(f"Repository path does not exist: {repo_path}")
            
            if not repo_path.is_dir():
                raise ValueError(f"Repository path is not a directory: {repo_path}")
        
        # Initialize graph data
        graph_data = GraphData()
        
        # Get repository metadata
        repo_context = self._get_repo_context(repo_path)
        
        # Create Repo node
        repo_node = self._create_repo_node(repo_path, repo_context)
        graph_data.add_node(repo_node)
        
        # Extract README if exists
        self._extract_readme(repo_path, repo_node, graph_data, repo_context)
        
        # Scan and parse all files
        files_parsed = 0
        files_skipped = 0
        
        for file_path in self._walk_repository(repo_path):
            try:
                # Get relative path for cleaner IDs
                rel_path = get_relative_path(file_path, repo_path)
                
                # Detect language
                language = detect_language(file_path)
                
                if language is None:
                    files_skipped += 1
                    continue
                
                # Check if we have a parser for this language
                parser = self.parsers.get(language)
                
                if parser is None:
                    print(f"Skipping {rel_path}: No parser for language '{language}'")
                    files_skipped += 1
                    continue
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Parse the file
                print(f"Parsing {rel_path} ({language})...")
                file_graph_data = parser.parse_file(rel_path, content, repo_context)
                
                # Merge into main graph data
                for node in file_graph_data.nodes:
                    graph_data.add_node(node)
                
                for rel in file_graph_data.relationships:
                    graph_data.add_relationship(rel)
                
                # Add Repo -> File relationship
                file_nodes = [n for n in file_graph_data.nodes if hasattr(n, 'path')]
                for file_node in file_nodes:
                    from packages.parser.models import Relationship, RelationshipType
                    graph_data.add_relationship(Relationship(
                        source_id=repo_node.id,
                        target_id=file_node.id,
                        type=RelationshipType.HAS_FILE
                    ))
                
                files_parsed += 1
                
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
                files_skipped += 1
                continue
        
        print(f"\nAnalysis complete:")
        print(f"  Files parsed: {files_parsed}")
        print(f"  Files skipped: {files_skipped}")
        print(f"  Total nodes: {len(graph_data.nodes)}")
        print(f"  Total relationships: {len(graph_data.relationships)}")
        
        # Cleanup temporary clone if needed
        if is_temp_clone and cleanup_after:
            print(f"\nCleaning up temporary clone...")
            cleanup_temp_repo(repo_path)
        elif is_temp_clone:
            print(f"\nTemporary clone preserved at: {repo_path}")
        
        return graph_data
    
    def _walk_repository(self, repo_path: Path):
        """
        Walk through repository and yield code files
        
        Args:
            repo_path: Path to the repository root
        
        Yields:
            Path objects for code files
        """
        for path in repo_path.rglob("*"):
            # Skip if it's a directory
            if path.is_dir():
                continue
            
            # Skip ignored paths
            if should_ignore_path(path):
                continue
            
            # Only process code files
            if not is_code_file(path):
                continue
            
            yield path
    
    def _get_repo_context(self, repo_path: Path) -> dict:
        """
        Extract repository metadata (git info if available)
        
        Args:
            repo_path: Path to the repository root
        
        Returns:
            Dictionary with repo context
        """
        context = {
            "name": repo_path.name,
            "path": str(repo_path),
        }
        
        # Try to get git info
        try:
            # Get current commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                context["sha"] = result.stdout.strip()
                context["commit_hash"] = result.stdout.strip()
            
            # Get remote URL
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                context["url"] = result.stdout.strip()
            
            # Get default branch
            result = subprocess.run(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Extract branch name from refs/remotes/origin/main
                branch = result.stdout.strip().split('/')[-1]
                context["default_branch"] = branch
            else:
                context["default_branch"] = "main"
                
        except Exception as e:
            print(f"Warning: Could not get git info: {e}")
            context["default_branch"] = "main"
        
        return context
    
    def _create_repo_node(self, repo_path: Path, repo_context: dict) -> RepoNode:
        """
        Create a RepoNode for the repository
        
        Args:
            repo_path: Path to the repository
            repo_context: Repository metadata
        
        Returns:
            RepoNode object
        """
        return RepoNode(
            id=f"repo:{repo_context['name']}",
            name=repo_context["name"],
            url=repo_context.get("url", str(repo_path)),
            default_branch=repo_context.get("default_branch", "main"),
            source_path=str(repo_path),
            repo_sha=repo_context.get("sha"),
        )
    
    def _extract_readme(self, repo_path: Path, repo_node, graph_data: GraphData, repo_context: dict):
        """Extract README file and create DocNode"""
        from packages.parser.models import DocNode, Relationship, RelationshipType
        from packages.parser.models.nodes import DocType
        
        # Look for README files
        readme_patterns = ['README.md', 'README.rst', 'README.txt', 'README', 'readme.md']
        
        for pattern in readme_patterns:
            readme_path = repo_path / pattern
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Limit README size
                    if len(content) > 50000:  # Limit to 50KB
                        content = content[:50000] + "\n... (truncated)"
                    
                    doc_id = self._generate_id(repo_context["name"], "doc", "README")
                    
                    doc_node = DocNode(
                        id=doc_id,
                        type=DocType.README,
                        text=content,
                        source_path=str(readme_path),
                        repo_sha=repo_context.get("sha"),
                    )
                    
                    graph_data.add_node(doc_node)
                    
                    # Create relationship: Repo HAS_DOC Doc
                    graph_data.add_relationship(Relationship(
                        source_id=repo_node.id,
                        target_id=doc_id,
                        type=RelationshipType.HAS_DOC
                    ))
                    
                    print(f"✓ Extracted README: {pattern}")
                    break
                    
                except Exception as e:
                    print(f"Warning: Could not read README {pattern}: {e}")
    
    def _generate_id(self, *parts: str) -> str:
        """Generate a canonical ID"""
        return ":".join(str(p) for p in parts)
    
    def get_supported_languages(self) -> list[str]:
        """
        Get list of all supported languages
        
        Returns:
            List of language names
        """
        return list(self.parsers.keys())
