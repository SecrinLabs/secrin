"""
Feature flags for controlling application behavior at runtime.
Production-grade flag system with hierarchical configuration.
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class FeatureFlag(str, Enum):
    """Available feature flags."""
    
    # Embedding Features
    ENABLE_EMBEDDINGS = "enable_embeddings"
    ENABLE_BATCH_EMBEDDINGS = "enable_batch_embeddings"
    ENABLE_EMBEDDING_CACHE = "enable_embedding_cache"
    
    # Search Features
    ENABLE_VECTOR_SEARCH = "enable_vector_search"
    ENABLE_HYBRID_SEARCH = "enable_hybrid_search"
    ENABLE_SEMANTIC_SEARCH = "enable_semantic_search"
    
    # Performance Features
    ENABLE_QUERY_CACHE = "enable_query_cache"
    ENABLE_CONNECTION_POOLING = "enable_connection_pooling"
    ENABLE_LAZY_LOADING = "enable_lazy_loading"
    
    # Observability Features
    ENABLE_METRICS = "enable_metrics"
    ENABLE_TRACING = "enable_tracing"
    ENABLE_DETAILED_LOGGING = "enable_detailed_logging"
    
    # Security Features
    ENABLE_API_AUTH = "enable_api_auth"
    ENABLE_RATE_LIMITING = "enable_rate_limiting"
    ENABLE_REQUEST_VALIDATION = "enable_request_validation"
    
    # Experimental Features
    ENABLE_AUTO_INDEXING = "enable_auto_indexing"
    ENABLE_SMART_RETRY = "enable_smart_retry"
    ENABLE_MULTIMODAL_EMBEDDINGS = "enable_multimodal_embeddings"


class FeatureFlagConfig(BaseModel):
    """Feature flag configuration with metadata."""
    
    enabled: bool = Field(default=False, description="Whether the feature is enabled")
    rollout_percentage: int = Field(default=100, ge=0, le=100, description="Percentage of traffic to enable (0-100)")
    environments: list[str] = Field(default_factory=lambda: ["development", "staging", "production"], description="Environments where feature is available")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def is_enabled_for_environment(self, environment: str) -> bool:
        """Check if feature is enabled for given environment."""
        return self.enabled and environment in self.environments


class FeatureFlagManager:
    """Manages feature flags with environment-specific overrides."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self._flags: Dict[FeatureFlag, FeatureFlagConfig] = self._initialize_defaults()
    
    def _initialize_defaults(self) -> Dict[FeatureFlag, FeatureFlagConfig]:
        """Initialize default feature flag configurations."""
        return {
            # Embedding Features - Essential, always on
            FeatureFlag.ENABLE_EMBEDDINGS: FeatureFlagConfig(
                enabled=True,
                environments=["development", "staging", "production"]
            ),
            FeatureFlag.ENABLE_BATCH_EMBEDDINGS: FeatureFlagConfig(
                enabled=True,
                environments=["development", "staging", "production"]
            ),
            FeatureFlag.ENABLE_EMBEDDING_CACHE: FeatureFlagConfig(
                enabled=False,  # Opt-in for performance
                environments=["staging", "production"]
            ),
            
            # Search Features - Core functionality
            FeatureFlag.ENABLE_VECTOR_SEARCH: FeatureFlagConfig(
                enabled=True,
                environments=["development", "staging", "production"]
            ),
            FeatureFlag.ENABLE_HYBRID_SEARCH: FeatureFlagConfig(
                enabled=True,
                environments=["development", "staging", "production"]
            ),
            FeatureFlag.ENABLE_SEMANTIC_SEARCH: FeatureFlagConfig(
                enabled=True,
                environments=["development", "staging", "production"]
            ),
            
            # Performance Features
            FeatureFlag.ENABLE_QUERY_CACHE: FeatureFlagConfig(
                enabled=False,
                environments=["production"]
            ),
            FeatureFlag.ENABLE_CONNECTION_POOLING: FeatureFlagConfig(
                enabled=True,
                environments=["staging", "production"]
            ),
            FeatureFlag.ENABLE_LAZY_LOADING: FeatureFlagConfig(
                enabled=False,
                environments=["development", "staging", "production"]
            ),
            
            # Observability Features
            FeatureFlag.ENABLE_METRICS: FeatureFlagConfig(
                enabled=True,
                environments=["staging", "production"]
            ),
            FeatureFlag.ENABLE_TRACING: FeatureFlagConfig(
                enabled=False,
                environments=["development", "staging", "production"],
                metadata={"tracing_backend": "jaeger"}
            ),
            FeatureFlag.ENABLE_DETAILED_LOGGING: FeatureFlagConfig(
                enabled=True,
                environments=["development"],
            ),
            
            # Security Features
            FeatureFlag.ENABLE_API_AUTH: FeatureFlagConfig(
                enabled=False,
                environments=["staging", "production"]
            ),
            FeatureFlag.ENABLE_RATE_LIMITING: FeatureFlagConfig(
                enabled=True,
                environments=["production"]
            ),
            FeatureFlag.ENABLE_REQUEST_VALIDATION: FeatureFlagConfig(
                enabled=True,
                environments=["development", "staging", "production"]
            ),
            
            # Experimental Features
            FeatureFlag.ENABLE_AUTO_INDEXING: FeatureFlagConfig(
                enabled=False,
                rollout_percentage=10,
                environments=["development"]
            ),
            FeatureFlag.ENABLE_SMART_RETRY: FeatureFlagConfig(
                enabled=False,
                environments=["development"]
            ),
            FeatureFlag.ENABLE_MULTIMODAL_EMBEDDINGS: FeatureFlagConfig(
                enabled=False,
                environments=["development"]
            ),
        }
    
    def is_enabled(self, flag: FeatureFlag) -> bool:
        """
        Check if a feature flag is enabled for current environment.
        
        Args:
            flag: The feature flag to check
            
        Returns:
            True if enabled, False otherwise
        """
        config = self._flags.get(flag)
        if not config:
            return False
        
        return config.is_enabled_for_environment(self.environment)
    
    def get_config(self, flag: FeatureFlag) -> Optional[FeatureFlagConfig]:
        """Get the full configuration for a feature flag."""
        return self._flags.get(flag)
    
    def set_flag(self, flag: FeatureFlag, config: FeatureFlagConfig) -> None:
        """
        Override a feature flag configuration.
        
        Args:
            flag: The feature flag to set
            config: The new configuration
        """
        self._flags[flag] = config
    
    def enable(self, flag: FeatureFlag, environments: Optional[list[str]] = None) -> None:
        """
        Enable a feature flag.
        
        Args:
            flag: The feature flag to enable
            environments: Optional list of environments (defaults to all)
        """
        config = self._flags.get(flag, FeatureFlagConfig())
        config.enabled = True
        if environments:
            config.environments = environments
        self._flags[flag] = config
    
    def disable(self, flag: FeatureFlag) -> None:
        """
        Disable a feature flag.
        
        Args:
            flag: The feature flag to disable
        """
        config = self._flags.get(flag, FeatureFlagConfig())
        config.enabled = False
        self._flags[flag] = config
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get status of all flags for current environment."""
        return {
            flag.value: self.is_enabled(flag)
            for flag in FeatureFlag
        }


# Global feature flag manager instance
_feature_flag_manager: Optional[FeatureFlagManager] = None


def get_feature_flag_manager(environment: Optional[str] = None) -> FeatureFlagManager:
    """
    Get or create the global feature flag manager.
    
    Args:
        environment: Optional environment override
        
    Returns:
        FeatureFlagManager instance
    """
    global _feature_flag_manager
    
    if _feature_flag_manager is None or environment is not None:
        from packages.config.settings import Settings
        settings = Settings()
        env = environment or settings.ENVIRONMENT
        _feature_flag_manager = FeatureFlagManager(environment=env)
    
    return _feature_flag_manager


def is_feature_enabled(flag: FeatureFlag) -> bool:
    """
    Convenience function to check if a feature is enabled.
    
    Args:
        flag: The feature flag to check
        
    Returns:
        True if enabled, False otherwise
    """
    manager = get_feature_flag_manager()
    return manager.is_enabled(flag)
