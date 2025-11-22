"""
Configuration package providing settings, feature flags, and utilities.
"""

from packages.config.settings import Settings
from packages.config.feature_flags import (
    FeatureFlag,
    FeatureFlagConfig,
    FeatureFlagManager,
    get_feature_flag_manager,
    is_feature_enabled,
)
from packages.config.utils import (
    validate_required_settings,
    get_effective_config,
    print_config_summary,
)

__all__ = [
    # Settings
    "Settings",
    
    # Feature Flags
    "FeatureFlag",
    "FeatureFlagConfig",
    "FeatureFlagManager",
    "get_feature_flag_manager",
    "is_feature_enabled",
    
    # Utilities
    "validate_required_settings",
    "get_effective_config",
    "print_config_summary",
]
