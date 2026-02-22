"""
Configuration data classes for arc42gen.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml

from ..constants import (
    DEFAULT_INCLUDE_PATTERNS,
    DEFAULT_EXCLUDE_PATTERNS,
    VALID_LANGUAGE_CONFIG,
)


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str = "anthropic"  # 'anthropic', 'gemini', or 'ollama'
    model: str = "claude-sonnet-4-5-20250929"
    api_key: str = ""
    max_tokens: int = 16000
    base_url: str = ""  # Used by Ollama provider
    timeout: int = 0  # Request timeout in seconds. 0 = no timeout (recommended for local Ollama)

    # Provider-specific default models
    DEFAULT_MODELS = {
        "anthropic": "claude-sonnet-4-5-20250929",
        "gemini": "gemini-2.0-flash",
        "ollama": "qwen2.5-coder:0.5b",
    }

    # Environment variable names for API keys
    API_KEY_ENV_VARS = {
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "ollama": "OLLAMA_BASE_URL",
    }

    def get_api_key_env_var(self) -> str:
        """Get the environment variable name for this provider's API key."""
        return self.API_KEY_ENV_VARS.get(self.provider, "LLM_API_KEY")

    @classmethod
    def get_default_model(cls, provider: str) -> str:
        """Get the default model for a provider."""
        return cls.DEFAULT_MODELS.get(provider, "")


@dataclass
class RepositoryConfig:
    """Repository analysis configuration."""
    include: List[str] = field(default_factory=lambda: list(DEFAULT_INCLUDE_PATTERNS))
    exclude: List[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDE_PATTERNS))
    language: Optional[str] = "auto"  # python, javascript, typescript, auto
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
class CitationConfig:
    """Citation and grounding settings."""
    require_citations: bool = False  # When True, enables citation grounding
    allow_hallucinations: bool = True  # When False, rejects ungrounded claims
    validation_mode: str = "warn"  # "strict", "warn", "off"
    max_facts_per_prompt: int = 50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "require_citations": self.require_citations,
            "allow_hallucinations": self.allow_hallucinations,
            "validation_mode": self.validation_mode,
            "max_facts_per_prompt": self.max_facts_per_prompt,
        }


@dataclass
class QualityConfig:
    """Quality metrics settings."""
    readability_target: float = 0.6  # Target readability score (0-1)
    citation_coverage_min: float = 0.5  # Minimum citation coverage
    run_validation: bool = False  # Run multi-pass validation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "readability_target": self.readability_target,
            "citation_coverage_min": self.citation_coverage_min,
            "run_validation": self.run_validation,
        }


@dataclass
class MaintenanceConfig:
    """Documentation maintenance settings."""
    auto_drift_detection: bool = False  # Run drift detection on generate
    freshness_check_interval: str = "7d"  # How often to check staleness
    include_provenance: bool = False  # Add provenance footer to docs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "auto_drift_detection": self.auto_drift_detection,
            "freshness_check_interval": self.freshness_check_interval,
            "include_provenance": self.include_provenance,
        }


@dataclass
class Config:
    """Main configuration object."""
    llm: LLMConfig
    repository: RepositoryConfig
    arc42: Arc42Config
    decomposition: DecompositionConfig
    output: OutputConfig
    citation: CitationConfig = None
    quality: QualityConfig = None
    maintenance: MaintenanceConfig = None
    version: str = "1.0"

    def __post_init__(self):
        if self.citation is None:
            self.citation = CitationConfig()
        if self.quality is None:
            self.quality = QualityConfig()
        if self.maintenance is None:
            self.maintenance = MaintenanceConfig()

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
        citation_data = data.get('citation', {})
        quality_data = data.get('quality', {})
        maintenance_data = data.get('maintenance', {})

        return cls(
            llm=LLMConfig(**llm_data),
            repository=RepositoryConfig(**repo_data),
            arc42=Arc42Config(**arc42_data),
            decomposition=DecompositionConfig(**decomp_data),
            output=OutputConfig(**output_data),
            citation=CitationConfig(**citation_data) if citation_data else CitationConfig(),
            quality=QualityConfig(**quality_data) if quality_data else QualityConfig(),
            maintenance=MaintenanceConfig(**maintenance_data) if maintenance_data else MaintenanceConfig(),
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
            'citation': self.citation.to_dict() if self.citation else {},
            'quality': self.quality.to_dict() if self.quality else {},
            'maintenance': self.maintenance.to_dict() if self.maintenance else {},
        }

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        # Validate LLM config
        if self.llm.provider != 'ollama' and not self.llm.api_key:
            env_var = self.llm.get_api_key_env_var()
            errors.append(f"LLM API key not set. Set {env_var} environment variable.")

        if self.llm.provider not in ['anthropic', 'gemini', 'ollama']:
            errors.append(f"Unsupported LLM provider: {self.llm.provider}. Supported: anthropic, gemini, ollama")

        # Validate repository config
        if not self.repository.include:
            errors.append("No include patterns specified for repository analysis.")

        valid_langs = VALID_LANGUAGE_CONFIG + [None]
        if self.repository.language not in valid_langs:
            errors.append(
                f"Unsupported language: {self.repository.language}. "
                f"Supported: {', '.join(VALID_LANGUAGE_CONFIG)}"
            )

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
# Supported providers: "anthropic" (Claude), "gemini" (Google), "ollama" (local)
llm:
  provider: "gemini"  # Options: "anthropic", "gemini", or "ollama"
  model: "gemini-2.0-flash"  # Gemini: gemini-2.0-flash | Anthropic: claude-sonnet-4-5-20250929 | Ollama: qwen2.5-coder:0.5b
  api_key: "${GEMINI_API_KEY}"  # Set via environment variable (not needed for ollama)
  max_tokens: 16000
  # base_url: "http://localhost:11434"  # Only needed for ollama (default: http://localhost:11434)
  # timeout: 0  # Request timeout in seconds. 0 = no timeout (recommended for local Ollama)

# Repository Analysis
repository:
  # Include patterns (glob)
  # Supports Python, JavaScript, and TypeScript
  include:
    - "src/**/*.py"
    - "lib/**/*.py"
    - "app/**/*.py"
    - "**/*.py"
    - "src/**/*.js"
    - "src/**/*.ts"
    - "src/**/*.jsx"
    - "src/**/*.tsx"
    - "lib/**/*.js"
    - "lib/**/*.ts"
    - "**/*.js"
    - "**/*.ts"

  # Exclude patterns (glob)
  exclude:
    - "**/test/**"
    - "**/tests/**"
    - "**/__pycache__/**"
    - "**/venv/**"
    - "**/.venv/**"
    - "**/node_modules/**"
    - "**/dist/**"
    - "**/build/**"
    - "**/*.pyc"
    - "**/*.min.js"
    - "**/*.bundle.js"

  # Language (auto-detect if not specified)
  # Options: python, javascript, typescript, auto
  language: "auto"  # Set to specific language or "auto" to detect

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
