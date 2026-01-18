# Secrin Auditor

**AI-powered documentation drift detection** - Ensure your docs stay in sync with your code.

[![npm version](https://badge.fury.io/js/secrin-auditor.svg)](https://www.npmjs.com/package/secrin-auditor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
npm install -g secrin-auditor
# or
pnpm add -g secrin-auditor
# or use directly with npx
npx secrin-auditor ./docs ./src
```

## Quick Start

```bash
# Set your Gemini API key
export GEMINI_API_KEY="your-key-from-aistudio.google.com"

# Run the audit
secrin-audit ./docs ./src
```

## Requirements

- Node.js 18+
- Python 3.11+ (installed automatically via pip)
- Gemini API key ([Get one free](https://aistudio.google.com/))

## Usage

```bash
secrin-audit <docs_folder> <repo_folder> [options]
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
| `-h, --help` | Show help |

## Example

```bash
# Audit docs in a Next.js project
secrin-audit ./docs .

# Audit with verbose output
secrin-audit ./documentation ./src --verbose
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Documentation Audit

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Run Documentation Audit
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: npx secrin-auditor ./docs .
```

### package.json script

```json
{
  "scripts": {
    "docs:audit": "secrin-audit ./docs ./src"
  }
}
```

Then run:

```bash
GEMINI_API_KEY=your-key npm run docs:audit
```

## Linking Docs to Code

Add CodeWiki tags to link docs to specific files:

```markdown
<!-- codewiki:src/api/routes.ts -->

# API Routes

This document describes the API endpoints...
```

## License

MIT

---

**Part of the [Secrin](https://github.com/SecrinLabs/secrin) project**
