"""
Unit tests for CodebaseAnalyzer.
"""

import tempfile
from pathlib import Path

import pytest

from packages.arc42gen.core.analyzer import CodebaseAnalyzer
from packages.arc42gen.models.config import Config


class TestCodebaseAnalyzer:
    """Tests for CodebaseAnalyzer class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config.from_dict({
            'llm': {'api_key': 'test'},
            'repository': {
                'include': ['**/*.py'],
                'exclude': ['**/test/**', '**/__pycache__/**'],
                'language': 'python'
            },
            'arc42': {'sections': [5]},
            'decomposition': {
                'max_module_size': 5000,
                'max_depth': 3,
                'cluster_by': 'directory'
            },
            'output': {}
        })

    @pytest.fixture
    def sample_repo(self, tmp_path):
        """Create a sample repository structure."""
        # Create src directory
        src = tmp_path / "src"
        src.mkdir()

        # Create main.py
        (src / "main.py").write_text('''"""Main application module."""

from src.utils import helper

class App:
    """Main application class."""

    def __init__(self):
        self.name = "TestApp"

    def run(self):
        """Run the application."""
        pass

def main():
    app = App()
    app.run()
''')

        # Create utils.py
        (src / "utils.py").write_text('''"""Utility functions."""

def helper(value):
    """Helper function."""
    return value * 2

def format_string(s):
    """Format a string."""
    return s.strip().lower()

class Logger:
    """Simple logger class."""

    def log(self, message):
        print(message)
''')

        # Create services directory
        services = src / "services"
        services.mkdir()

        (services / "__init__.py").write_text('"""Services package."""')

        (services / "user_service.py").write_text('''"""User service module."""

from src.utils import Logger

class UserService:
    """Handles user operations."""

    def __init__(self):
        self.logger = Logger()

    def get_user(self, user_id):
        """Get user by ID."""
        self.logger.log(f"Getting user {user_id}")
        return {"id": user_id}

    def create_user(self, data):
        """Create a new user."""
        pass
''')

        return tmp_path

    def test_analyze_basic(self, config, sample_repo):
        """Test basic analysis of sample repository."""
        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(str(sample_repo))

        assert result.repo_name == sample_repo.name
        assert result.language == "python"
        assert result.statistics.total_files > 0
        assert result.statistics.total_loc > 0

    def test_analyze_finds_classes(self, config, sample_repo):
        """Test that analysis finds classes."""
        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(str(sample_repo))

        # Should find: App, Logger, UserService
        assert result.statistics.total_classes >= 3

    def test_analyze_finds_functions(self, config, sample_repo):
        """Test that analysis finds functions."""
        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(str(sample_repo))

        # Should find module-level functions: main, helper, format_string
        assert result.statistics.total_functions >= 3

    def test_analyze_builds_module_tree(self, config, sample_repo):
        """Test that analysis builds module tree."""
        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(str(sample_repo))

        # Root should have children
        assert result.module_tree.root is not None
        assert len(result.module_tree.root.children) > 0

    def test_analyze_builds_dependency_graph(self, config, sample_repo):
        """Test that analysis builds dependency graph."""
        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(str(sample_repo))

        # Should have nodes and edges
        assert len(result.dependency_graph.nodes) > 0

    def test_analyze_respects_exclude_patterns(self, config, tmp_path):
        """Test that exclude patterns are respected."""
        # Create files
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("x = 1")

        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_main.py").write_text("y = 2")

        # Update config to exclude tests
        config.repository.exclude = ["**/tests/**"]

        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(str(tmp_path))

        # Should only find main.py, not test_main.py
        assert result.statistics.total_files == 1

    def test_analyze_nonexistent_path(self, config):
        """Test analyzing nonexistent path raises error."""
        analyzer = CodebaseAnalyzer(config)

        with pytest.raises(FileNotFoundError):
            analyzer.analyze("/nonexistent/path")

    def test_analyze_empty_repo(self, config, tmp_path):
        """Test analyzing empty repository."""
        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(str(tmp_path))

        assert result.statistics.total_files == 0
        assert result.statistics.total_loc == 0

    def test_module_tree_serialization(self, config, sample_repo):
        """Test that module tree can be serialized."""
        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(str(sample_repo))

        # Should not raise
        data = result.to_dict()

        assert "module_tree" in data
        assert "statistics" in data
        assert "dependency_graph" in data

    def test_get_all_modules(self, config, sample_repo):
        """Test getting all modules from tree."""
        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(str(sample_repo))

        all_modules = result.module_tree.get_all_modules()

        # Should return list of modules
        assert isinstance(all_modules, list)
        assert len(all_modules) > 0

    def test_statistics_accuracy(self, config, tmp_path):
        """Test that statistics are accurate."""
        # Create single file with known content
        (tmp_path / "test.py").write_text('''# Comment
class Foo:
    def bar(self):
        pass

def baz():
    pass

x = 1
y = 2
''')

        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(str(tmp_path))

        assert result.statistics.total_files == 1
        assert result.statistics.total_classes == 1
        assert result.statistics.total_functions == 1  # Module-level only
        # LOC should exclude comment and blank lines
        assert result.statistics.total_loc == 7
