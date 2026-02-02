"""
Integration tests for Orchestrator.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from packages.arc42gen.core.orchestrator import Orchestrator
from packages.arc42gen.models.config import Config


class TestOrchestrator:
    """Integration tests for Orchestrator class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config.from_dict({
            'llm': {
                'api_key': 'test_api_key',
                'model': 'claude-sonnet-4-5-20250929',
            },
            'repository': {
                'include': ['**/*.py'],
                'exclude': ['**/test/**'],
                'language': 'python'
            },
            'arc42': {'sections': [5]},
            'decomposition': {
                'max_module_size': 5000,
                'max_depth': 3,
            },
            'output': {
                'path': './docs/',
                'create_diagrams_folder': True,
                'include_statistics': True,
            }
        })

    @pytest.fixture
    def sample_repo(self, tmp_path):
        """Create a sample repository."""
        src = tmp_path / "src"
        src.mkdir()

        (src / "main.py").write_text('''"""Main module."""

class Application:
    """Main application class."""

    def run(self):
        pass

def main():
    app = Application()
    app.run()
''')

        (src / "utils.py").write_text('''"""Utilities."""

def helper():
    return 42
''')

        return tmp_path

    @pytest.fixture
    def mock_claude(self):
        """Mock Claude API responses."""
        with patch('packages.arc42gen.core.generator.anthropic.Anthropic') as mock:
            client = Mock()
            mock.return_value = client

            # Mock response for Level 1
            level_1_response = Mock()
            level_1_response.content = [Mock(text="""OVERVIEW:
A simple application with utilities.

COMPONENTS:
- main: Main application entry point
- utils: Helper utilities

INTERFACES:
Main calls utils for helper functions.

RATIONALE:
Simple modular structure.""")]

            # Mock response for Level 2
            level_2_response = Mock()
            level_2_response.content = [Mock(text="""PURPOSE:
Main application module.

INTERNAL_STRUCTURE:
- Application: Main app class

DEPENDENCIES:
- utils""")]

            # Mock response for diagram
            diagram_response = Mock()
            diagram_response.content = [Mock(text="""```mermaid
flowchart TB
    main --> utils
```""")]

            # Return different responses for each call
            client.messages.create.side_effect = [
                level_1_response,
                level_2_response,
                diagram_response,
            ]

            yield client

    def test_full_workflow(self, config, sample_repo, mock_claude, tmp_path):
        """Test complete documentation generation workflow."""
        output_path = tmp_path / "output"

        orchestrator = Orchestrator(config)

        progress_values = []
        def progress_callback(value):
            progress_values.append(value)

        success = orchestrator.run(
            repo_path=str(sample_repo),
            output_path=str(output_path),
            progress_callback=progress_callback
        )

        assert success is True
        assert (output_path / "arc42_section_5.md").exists()

        # Check progress was reported
        assert len(progress_values) > 0
        assert 100 in progress_values

    def test_output_file_content(self, config, sample_repo, mock_claude, tmp_path):
        """Test that output file has expected content."""
        output_path = tmp_path / "output"

        orchestrator = Orchestrator(config)
        orchestrator.run(
            repo_path=str(sample_repo),
            output_path=str(output_path)
        )

        md_content = (output_path / "arc42_section_5.md").read_text()

        # Check for expected sections
        assert "# 5. Building Block View" in md_content
        assert "## 5.1 Level 1" in md_content
        assert "Overview" in md_content
        assert "mermaid" in md_content

    def test_diagram_file_created(self, config, sample_repo, mock_claude, tmp_path):
        """Test that diagram file is created."""
        output_path = tmp_path / "output"

        orchestrator = Orchestrator(config)
        orchestrator.run(
            repo_path=str(sample_repo),
            output_path=str(output_path)
        )

        diagram_path = output_path / "diagrams" / "architecture.mmd"
        assert diagram_path.exists()

        diagram_content = diagram_path.read_text()
        assert "flowchart" in diagram_content

    def test_invalid_repo_path(self, config, tmp_path):
        """Test handling of invalid repository path."""
        orchestrator = Orchestrator(config)

        success = orchestrator.run(
            repo_path="/nonexistent/path",
            output_path=str(tmp_path / "output")
        )

        assert success is False

    def test_missing_api_key(self, sample_repo, tmp_path):
        """Test handling of missing API key."""
        config = Config.from_dict({
            'llm': {'api_key': ''},  # Empty API key
            'repository': {'language': 'python'},
            'arc42': {'sections': [5]},
            'decomposition': {},
            'output': {}
        })

        orchestrator = Orchestrator(config)

        success = orchestrator.run(
            repo_path=str(sample_repo),
            output_path=str(tmp_path / "output")
        )

        assert success is False

    def test_empty_repository(self, config, mock_claude, tmp_path):
        """Test handling of empty repository."""
        empty_repo = tmp_path / "empty_repo"
        empty_repo.mkdir()

        output_path = tmp_path / "output"

        orchestrator = Orchestrator(config)
        success = orchestrator.run(
            repo_path=str(empty_repo),
            output_path=str(output_path)
        )

        # Should complete but with minimal output
        assert success is True

    def test_validation_errors_reported(self, sample_repo, tmp_path):
        """Test that validation errors are properly handled."""
        config = Config.from_dict({
            'llm': {'api_key': 'test'},
            'repository': {
                'language': 'invalid_language'  # Invalid
            },
            'arc42': {'sections': [5]},
            'decomposition': {
                'max_module_size': 50  # Too small
            },
            'output': {}
        })

        orchestrator = Orchestrator(config)

        # Should fail due to validation errors
        success = orchestrator.run(
            repo_path=str(sample_repo),
            output_path=str(tmp_path / "output")
        )

        assert success is False
