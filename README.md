# Secrin

A powerful code analysis tool that parses repositories and builds a comprehensive knowledge graph of code structure, relationships, and metadata using Neo4j.

## Overview

Secrin analyzes source code repositories (both local and remote) to extract structural information about files, modules, classes, functions, variables, and their relationships. It creates a graph database representation that enables deep code analysis, dependency tracking, and insights into your codebase.

### Key Features

- **Multi-Language Support**: Currently supports Python and JavaScript, with extensible architecture for additional languages
- **Git Integration**: Analyze both local repositories and remote Git URLs (GitHub, GitLab, Bitbucket)
- **Graph Database Storage**: Stores code structure in Neo4j for powerful querying and visualization
- **AST-Based Parsing**: Uses Tree-sitter for accurate syntax parsing
- **Commit History Analysis**: Tracks file modifications and commit metadata
- **Comprehensive Relationships**: Captures imports, inheritance, calls, and other code relationships

## Requirements

- Python >= 3.13
- Neo4j database instance
- Git (for cloning remote repositories)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Authors

- Jenil Savani (jenil@secrinlabs.com)

## Support

For issues and questions, please visit the [GitHub repository](https://github.com/SecrinLabs/secrin).
