# Secrin Auditor

**AI-powered documentation drift detection** - Ensure your docs stay in sync with your code.

[![PyPI version](https://badge.fury.io/py/secrin-auditor.svg)](https://pypi.org/project/secrin-auditor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install secrin-auditor
```

## Quick Start

```bash
# Set your Gemini API key
export GEMINI_API_KEY="your-key-from-aistudio.google.com"

# Run the audit
secrin-audit ./docs ./src
```

## Features

- 🔍 **Drift Detection** - Find where docs say X but code does Y
- 🏷️ **CodeWiki Tags** - Link docs to specific code files
- 🤖 **AI-Powered** - Uses Gemini 2.0 Flash for intelligent comparison
- 📊 **Rich Output** - Beautiful terminal tables with issue details
- 🚀 **CI/CD Ready** - Exit code 1 on failures for pipeline integration

## Usage

### Basic Audit

```bash
secrin-audit <docs_folder> <repo_folder>
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `docs_folder` | Path to your documentation folder |
| `repo_folder` | Path to your codebase |

**Options:**
| Option | Description |
|--------|-------------|
| `-v, --verbose` | Show verbose output |

### Example Output

```
╭─────────────────────────────╮
│ Secrin Auditor V1           │
│ Powered by Gemini 2.0 Flash │
╰─────────────────────────────╯

                    Audit Results
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Document      ┃ Linked Code      ┃ Status ┃ AI Feedback               ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ api-routes.md │ routes/api.py    │ FAIL   │ • [WRONG_ENDPOINT] Doc    │
│               │                  │        │   says /api/users but     │
│               │                  │        │   code has /api/v1/users  │
├───────────────┼──────────────────┼────────┼───────────────────────────┤
│ auth.md       │ auth/handler.py  │ PASS   │ ✅ Accurate               │
└───────────────┴──────────────────┴────────┴───────────────────────────┘

Summary: 2 docs audited

✖ Audit Failed: 1 document(s) have drifted from code.
```

## Linking Docs to Code

### Explicit Links (Recommended)

Add CodeWiki tags to link documentation to specific code files:

```markdown
<!-- codewiki:src/auth/jwt_handler.py -->

# JWT Authentication

This module handles JWT token generation and validation...
```

### Multiple Files

```markdown
<!-- codewiki:src/auth/jwt_handler.py -->
<!-- codewiki:src/auth/middleware.py -->

# Authentication System

This document covers the complete auth system...
```

### Implicit Matching

If no tags are present, the auditor tries to match by filename:

- `auth.md` → looks for `auth.py`, `auth.ts`, etc.

For overview docs without matches, the entire codebase context is used.

## Issue Types

| Type              | Description                           |
| ----------------- | ------------------------------------- |
| `MISSING_ROUTE`   | Route documented but not in code      |
| `WRONG_ENDPOINT`  | Endpoint path or method mismatch      |
| `OUTDATED_PARAM`  | Parameter no longer exists or changed |
| `NOT_IMPLEMENTED` | Feature documented but not coded      |
| `WRONG_PATH`      | File or module path incorrect         |
| `CONFIG_DRIFT`    | Environment variable mismatch         |

## CI/CD Integration

### GitHub Actions

```yaml
name: Documentation Audit

on:
  push:
    branches: [main]
  pull_request:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Secrin Auditor
        run: pip install secrin-auditor

      - name: Run Documentation Audit
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: secrin-audit ./docs ./src
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: docs-audit
        name: Documentation Audit
        entry: secrin-audit ./docs ./src
        language: system
        pass_filenames: false
        always_run: true
```

## Python API

```python
from secrin_auditor import run_audit, audit_with_gemini

# Run full audit
issues = run_audit("./docs", "./src", verbose=True)

# Audit single doc
result = audit_with_gemini(
    doc_text="# API Routes\nGET /users - List users",
    code_text="@app.get('/api/v1/users')\ndef list_users(): ...",
    filename="api.md"
)
print(result)  # "• [WRONG_ENDPOINT] Doc says /users but code has /api/v1/users"
```

## Requirements

- Python 3.11+
- Gemini API key ([Get one free](https://aistudio.google.com/))

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

---

**Part of the [Secrin](https://github.com/SecrinLabs/secrin) project** - The memory layer for engineering teams.
