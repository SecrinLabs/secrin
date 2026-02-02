"""
Configuration data classes for arc42gen.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-5-20250929"
    api_key: str = ""
    max_tokens: int = 16000


@dataclass
class RepositoryConfig:
    """Repository analysis configuration."""
    include: List[str] = field(default_factory=lambda: ["**/*.py"])
    exclude: List[str] = field(default_factory=lambda: ["**/test/**", "**/__pycache__/**"])
    language: Optional[str] = "python"
    focus_modules: List[str] = field(default_factory=list)


@dataclass
class DecompositionConfig:
    """Hierarchical decomposition settings."""
    max_module_size: int = 5000  # LOC threshold
    max_depth: int = 3
    cluster_by: str = "directory"  # directory, namespace


@dataclass
class OutputConfig:
    """Output settings."""
    path: str = "./docs/arc42/"
    create_diagrams_folder: bool = True
    include_statistics: bool = True


@dataclass
class Arc42Config:
    """Arc42 generation settings."""
    sections: List[int] = field(default_factory=lambda: [5])
    diagram_style: str = "c4"  # c4, uml
    output_format: str = "markdown"


@dataclass
class Config:
    """Main configuration object."""
    llm: LLMConfig
    repository: RepositoryConfig
    arc42: Arc42Config
    decomposition: DecompositionConfig
    output: OutputConfig
    version: str = "1.0"

    @classmethod
    def from_yaml(cls, path: str) -> 'Config':
        """Load configuration from YAML file."""
        config_path = Path(path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(config_path) as f:
            data = yaml.safe_load(f)

        # Replace environment variables in strings
        data = cls._replace_env_vars(data)

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create Config from dictionary."""
        llm_data = data.get('llm', {})
        repo_data = data.get('repository', {})
        arc42_data = data.get('arc42', {})
        decomp_data = data.get('decomposition', {})
        output_data = data.get('output', {})

        return cls(
            llm=LLMConfig(**llm_data),
            repository=RepositoryConfig(**repo_data),
            arc42=Arc42Config(**arc42_data),
            decomposition=DecompositionConfig(**decomp_data),
            output=OutputConfig(**output_data),
            version=data.get('version', '1.0')
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create Config from dictionary (public interface)."""
        data = cls._replace_env_vars(data)
        return cls._from_dict(data)

    @staticmethod
    def _replace_env_vars(data: Any) -> Any:
        """Replace ${VAR} with environment variable values."""
        if isinstance(data, dict):
            return {k: Config._replace_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [Config._replace_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            var_name = data[2:-1]
            return os.getenv(var_name, "")
        else:
            return data

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'version': self.version,
            'llm': {
                'provider': self.llm.provider,
                'model': self.llm.model,
                'api_key': '***' if self.llm.api_key else '',  # Mask API key
                'max_tokens': self.llm.max_tokens,
            },
            'repository': {
                'include': self.repository.include,
                'exclude': self.repository.exclude,
                'language': self.repository.language,
                'focus_modules': self.repository.focus_modules,
            },
            'arc42': {
                'sections': self.arc42.sections,
                'diagram_style': self.arc42.diagram_style,
                'output_format': self.arc42.output_format,
            },
            'decomposition': {
                'max_module_size': self.decomposition.max_module_size,
                'max_depth': self.decomposition.max_depth,
                'cluster_by': self.decomposition.cluster_by,
            },
            'output': {
                'path': self.output.path,
                'create_diagrams_folder': self.output.create_diagrams_folder,
                'include_statistics': self.output.include_statistics,
            },
        }

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        # Validate LLM config
        if not self.llm.api_key:
            errors.append("LLM API key not set. Set ANTHROPIC_API_KEY environment variable.")

        if self.llm.provider not in ['anthropic']:
            errors.append(f"Unsupported LLM provider: {self.llm.provider}")

        # Validate repository config
        if not self.repository.include:
            errors.append("No include patterns specified for repository analysis.")

        if self.repository.language not in ['python', 'javascript', 'typescript', None]:
            errors.append(f"Unsupported language: {self.repository.language}")

        # Validate Arc42 config
        if 5 not in self.arc42.sections:
            errors.append("MVP only supports Section 5. Include 5 in sections list.")

        # Validate decomposition config
        if self.decomposition.max_module_size < 100:
            errors.append("max_module_size should be at least 100 LOC.")

        if self.decomposition.max_depth < 1 or self.decomposition.max_depth > 10:
            errors.append("max_depth should be between 1 and 10.")

        return errors


# Default configuration template
DEFAULT_CONFIG_YAML = """# Arc42-Gen Configuration
version: "1.0"

# LLM Settings
llm:
  provider: "anthropic"
  model: "claude-sonnet-4-5-20250929"
  api_key: "${ANTHROPIC_API_KEY}"  # Set via environment variable
  max_tokens: 16000

# Repository Analysis
repository:
  # Include patterns (glob)
  include:
    - "src/**/*.py"
    - "lib/**/*.py"
    - "app/**/*.py"
    - "**/*.py"

  # Exclude patterns (glob)
  exclude:
    - "**/test/**"
    - "**/tests/**"
    - "**/__pycache__/**"
    - "**/venv/**"
    - "**/.venv/**"
    - "**/node_modules/**"
    - "**/*.pyc"

  # Language (auto-detect if not specified)
  language: "python"  # python, javascript, typescript

  # Focus on specific modules (optional)
  focus_modules: []

# Arc42 Settings
arc42:
  sections: [5]  # MVP: Section 5 only
  diagram_style: "c4"  # c4, uml
  output_format: "markdown"

# Hierarchical Decomposition
decomposition:
  max_module_size: 5000  # LOC threshold
  max_depth: 3
  cluster_by: "directory"

# Output Settings
output:
  path: "./docs/arc42/"
  create_diagrams_folder: true
  include_statistics: true
"""
