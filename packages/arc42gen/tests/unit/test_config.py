"""
Unit tests for configuration module.
"""

import os
import tempfile
from pathlib import Path

import pytest

from packages.arc42gen.models.config import (
    Config,
    LLMConfig,
    RepositoryConfig,
    DEFAULT_CONFIG_YAML,
)


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = LLMConfig()

        assert config.provider == "anthropic"
        assert config.model == "claude-sonnet-4-5-20250929"
        assert config.api_key == ""
        assert config.max_tokens == 16000

    def test_custom_values(self):
        """Test custom configuration values."""
        config = LLMConfig(
            provider="anthropic",
            model="claude-3-opus",
            api_key="test_key",
            max_tokens=8000
        )

        assert config.model == "claude-3-opus"
        assert config.api_key == "test_key"
        assert config.max_tokens == 8000


class TestRepositoryConfig:
    """Tests for RepositoryConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RepositoryConfig()

        assert "**/*.py" in config.include
        assert "**/*.js" in config.include  # Now includes JS/TS
        assert "**/*.ts" in config.include
        assert "**/test/**" in config.exclude
        assert config.language == "auto"  # Changed from "python" to "auto"
        assert config.focus_modules == []

    def test_custom_patterns(self):
        """Test custom include/exclude patterns."""
        config = RepositoryConfig(
            include=["src/**/*.py"],
            exclude=["**/test/**", "**/docs/**"],
            language="python"
        )

        assert config.include == ["src/**/*.py"]
        assert "**/docs/**" in config.exclude


class TestConfig:
    """Tests for main Config class."""

    def test_from_yaml(self):
        """Test loading config from YAML file."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
version: "1.0"
llm:
  provider: "anthropic"
  model: "claude-sonnet-4-5-20250929"
  api_key: "test_api_key"
  max_tokens: 8000
repository:
  include:
    - "src/**/*.py"
  exclude:
    - "**/test/**"
  language: "python"
arc42:
  sections: [5]
  diagram_style: "c4"
  output_format: "markdown"
decomposition:
  max_module_size: 3000
  max_depth: 2
  cluster_by: "directory"
output:
  path: "./output/"
  create_diagrams_folder: true
  include_statistics: true
""")
            temp_path = f.name

        try:
            config = Config.from_yaml(temp_path)

            assert config.llm.api_key == "test_api_key"
            assert config.llm.max_tokens == 8000
            assert config.repository.include == ["src/**/*.py"]
            assert config.arc42.sections == [5]
            assert config.decomposition.max_module_size == 3000
            assert config.output.path == "./output/"
        finally:
            os.unlink(temp_path)

    def test_env_var_replacement(self):
        """Test environment variable replacement."""
        os.environ['TEST_API_KEY'] = 'env_test_key'

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write("""
version: "1.0"
llm:
  provider: "anthropic"
  model: "claude-sonnet-4-5-20250929"
  api_key: "${TEST_API_KEY}"
  max_tokens: 16000
repository:
  include: ["**/*.py"]
  exclude: []
  language: "python"
arc42:
  sections: [5]
decomposition:
  max_module_size: 5000
  max_depth: 3
output:
  path: "./docs/"
""")
                temp_path = f.name

            config = Config.from_yaml(temp_path)
            assert config.llm.api_key == "env_test_key"
        finally:
            os.unlink(temp_path)
            del os.environ['TEST_API_KEY']

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            'llm': {
                'provider': 'anthropic',
                'model': 'test-model',
                'api_key': 'dict_key',
                'max_tokens': 4000
            },
            'repository': {
                'include': ['*.py'],
                'exclude': [],
                'language': 'python'
            },
            'arc42': {
                'sections': [5],
                'diagram_style': 'c4',
                'output_format': 'markdown'
            },
            'decomposition': {
                'max_module_size': 5000,
                'max_depth': 3,
                'cluster_by': 'directory'
            },
            'output': {
                'path': './test/',
                'create_diagrams_folder': True,
                'include_statistics': True
            }
        }

        config = Config.from_dict(data)

        assert config.llm.api_key == "dict_key"
        assert config.llm.max_tokens == 4000
        assert config.repository.language == "python"

    def test_validate_missing_api_key(self):
        """Test validation catches missing API key."""
        config = Config(
            llm=LLMConfig(api_key=""),
            repository=RepositoryConfig(),
            arc42=Config._from_dict({
                'llm': {},
                'repository': {},
                'arc42': {'sections': [5]},
                'decomposition': {},
                'output': {}
            }).arc42,
            decomposition=Config._from_dict({
                'llm': {},
                'repository': {},
                'arc42': {},
                'decomposition': {},
                'output': {}
            }).decomposition,
            output=Config._from_dict({
                'llm': {},
                'repository': {},
                'arc42': {},
                'decomposition': {},
                'output': {}
            }).output,
        )

        errors = config.validate()
        assert any("API key" in e for e in errors)

    def test_validate_unsupported_language(self):
        """Test validation catches unsupported language."""
        config = Config.from_dict({
            'llm': {'api_key': 'test'},
            'repository': {'language': 'cobol'},
            'arc42': {'sections': [5]},
            'decomposition': {},
            'output': {}
        })

        errors = config.validate()
        assert any("Unsupported language" in e for e in errors)

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = Config.from_dict({
            'llm': {'api_key': 'secret_key'},
            'repository': {'language': 'python'},
            'arc42': {'sections': [5]},
            'decomposition': {},
            'output': {}
        })

        result = config.to_dict()

        # API key should be masked
        assert result['llm']['api_key'] == '***'
        assert result['repository']['language'] == 'python'

    def test_file_not_found(self):
        """Test FileNotFoundError for missing config."""
        with pytest.raises(FileNotFoundError):
            Config.from_yaml("/nonexistent/path/config.yaml")


class TestDefaultConfig:
    """Tests for default configuration template."""

    def test_default_config_is_valid_yaml(self):
        """Test that default config template is valid YAML."""
        import yaml

        data = yaml.safe_load(DEFAULT_CONFIG_YAML)

        assert 'version' in data
        assert 'llm' in data
        assert 'repository' in data
        assert 'arc42' in data

    def test_default_config_has_env_var_placeholder(self):
        """Test that default config uses environment variable."""
        # Default now uses Gemini
        assert "${GEMINI_API_KEY}" in DEFAULT_CONFIG_YAML
