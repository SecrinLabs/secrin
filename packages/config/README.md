# Configuration Package

Settings and feature flags for Secrin.

## Quick Start

```python
from packages.config import Settings, is_feature_enabled, FeatureFlag

# Get settings
settings = Settings()
print(settings.NEO4J_URI)
print(settings.EMBEDDING_PROVIDER)

# Check feature flags
if is_feature_enabled(FeatureFlag.ENABLE_VECTOR_SEARCH):
    results = search(query)
```

## Files

- **`settings.py`** - All application settings with Pydantic validation
- **`feature_flags.py`** - Runtime feature flag system
- **`cli.py`** - Configuration management CLI
- **`utils.py`** - Helper functions

## CLI Commands

```bash
# Validate configuration
python -m packages.config.cli validate

# View settings
python -m packages.config.cli summary

# Check feature flags
python -m packages.config.cli flags

# Test database
python -m packages.config.cli test-connection
```

## Configuration Priority

1. Environment variables (highest)
2. `.env` file
3. Default values in `settings.py` (lowest)

## Adding Settings

Add to `settings.py`:
```python
MY_SETTING: str = Field(
    default="default",
    description="What this setting does"
)
```

Add to `.env.example`:
```bash
MY_SETTING=example_value
```

## Adding Feature Flags

1. Add to `FeatureFlag` enum in `feature_flags.py`
2. Add default config in `_initialize_defaults()`
3. Use: `if is_feature_enabled(FeatureFlag.MY_FLAG):`

See `/CONFIGURATION.md` in project root for complete setup guide.
