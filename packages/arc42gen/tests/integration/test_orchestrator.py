"""
Integration tests for Orchestrator.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from packages.arc42gen.core.orchestrator import Orchestrator
from packages.arc42gen.models.config import Config
from packages.arc42gen.providers.base import BaseLLMProvider, LLMResponse


class MockProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, api_key="test", model="test"):
        super().__init__(api_key, model)
        self.responses = []
        self.call_count = 0

    @property
    def provider_name(self):
        return "mock"

    def set_responses(self, responses):
        """Set list of responses to return in order."""
        self.responses = responses
        self.call_count = 0

    def generate(self, prompt, max_tokens=4000, temperature=0.7, system_prompt=None):
        if self.call_count < len(self.responses):
            content = self.responses[self.call_count]
        else:
            content = "Mock response"
        self.call_count += 1
        return LLMResponse(content=content, model=self.model)

    def generate_chat(self, messages, max_tokens=4000, temperature=0.7, system_prompt=None):
        return self.generate("", max_tokens, temperature, system_prompt)


class TestOrchestrator:
    """Integration tests for Orchestrator class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config.from_dict({
            'llm': {
                'provider': 'anthropic',
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
    def mock_provider(self):
        """Create mock provider with responses."""
        provider = MockProvider()
        provider.set_responses([
            # Level 1 response
            """OVERVIEW:
A simple application with utilities.

COMPONENTS:
- main: Main application entry point
- utils: Helper utilities

INTERFACES:
Main calls utils for helper functions.

RATIONALE:
Simple modular structure.""",
            # Level 2 response
            """PURPOSE:
Main application module.

INTERNAL_STRUCTURE:
- Application: Main app class

DEPENDENCIES:
- utils""",
            # Diagram response
            """```mermaid
flowchart TB
    main --> utils
```""",
        ])
        return provider

    @pytest.fixture
    def mock_provider_factory(self, mock_provider):
        """Mock the provider factory to return our mock provider."""
        with patch('packages.arc42gen.core.generator.create_llm_provider') as mock:
            mock.return_value = mock_provider
            yield mock_provider

    def test_full_workflow(self, config, sample_repo, mock_provider_factory, tmp_path):
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

    def test_output_file_content(self, config, sample_repo, mock_provider_factory, tmp_path):
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

    def test_diagram_file_created(self, config, sample_repo, mock_provider_factory, tmp_path):
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

    def test_empty_repository(self, config, mock_provider_factory, tmp_path):
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
