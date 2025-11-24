from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class NodeType(str, Enum):
    REPO = "Repo"
    FILE = "File"
    COMMIT = "Commit"
    MODULE = "Module"
    CLASS = "Class"
    FUNCTION = "Function"
    VARIABLE = "Variable"
    TEST = "Test"
    DOC = "Doc"
    ISSUE = "Issue"
    PACKAGE = "Package"
    IMPORT = "Import"
    EXPORT = "Export"
    TYPE = "Type"
    INTERFACE = "Interface"
    COMMENT = "Comment"
    PR = "PullRequest"
    TODO = "Todo"


class BaseNode(BaseModel):
    """Base class for all nodes with common provenance properties"""
    id: str
    source_path: Optional[str] = None
    repo_sha: Optional[str] = None
    commit_hash: Optional[str] = None
    snippet: Optional[str] = None
    hash_id: Optional[str] = None
    embedding_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RepoNode(BaseNode):
    name: str
    url: str
    default_branch: str


class FileNode(BaseNode):
    path: str
    language: str
    sha: str
    lines: int


class CommitNode(BaseNode):
    hash: str
    author: str
    email: str
    date: datetime
    message: str


class ModuleNode(BaseNode):
    name: str
    package: Optional[str] = None


class ClassNode(BaseNode):
    name: str
    visibility: Optional[str] = None
    start_line: int
    end_line: int


class FunctionNode(BaseNode):
    name: str
    signature: str
    start_line: int
    end_line: int
    is_method: bool = False
    cyclomatic_complexity: Optional[int] = None  # Code complexity metric
    documentation: Optional[str] = None  # Docstring/JSDoc


class VariableNode(BaseNode):
    name: str
    kind: str  # e.g., 'parameter', 'local', 'global', 'attribute'
    start_line: int


class TestNode(BaseNode):
    name: str
    kind: str  # e.g., 'unit', 'integration', 'e2e'


class DocType(str, Enum):
    README = "README"
    DOCSTRING = "docstring"
    COMMENT = "comment"


class DocNode(BaseNode):
    type: DocType
    text: str
    start_line: Optional[int] = None


class IssueNode(BaseNode):
    title: str
    body: str
    labels: list[str] = Field(default_factory=list)
    state: str  # e.g., 'open', 'closed'


class PackageNode(BaseNode):
    name: str
    version: str


class ImportNode(BaseNode):
    """Represents an import statement"""
    name: str  # The name being imported
    source: str  # The module/package source
    alias: Optional[str] = None  # Import alias (e.g., 'as np')
    is_wildcard: bool = False  # True for 'import *'
    start_line: int


class ExportNode(BaseNode):
    """Represents an export statement (primarily for JS/TS)"""
    name: str  # The name being exported
    kind: str  # 'default', 'named', 're-export'
    source: Optional[str] = None  # Re-export source if applicable
    start_line: int


class TypeNode(BaseNode):
    """Represents a type definition (TypeScript, Python type hints)"""
    name: str
    definition: str  # The type definition itself
    kind: str  # 'alias', 'union', 'generic', etc.
    start_line: int
    end_line: int


class InterfaceNode(BaseNode):
    """Represents an interface (TypeScript, protocols in Python)"""
    name: str
    members: list[str] = Field(default_factory=list)  # Member names
    start_line: int
    end_line: int


class CommentNode(BaseNode):
    """Represents inline comments and TODOs"""
    text: str
    kind: str  # 'comment', 'todo', 'fixme', 'note'
    author: Optional[str] = None  # From git blame
    line: int


class PRNode(BaseNode):
    """Represents a Pull Request"""
    number: int
    title: str
    body: str
    author: str
    state: str  # 'open', 'closed', 'merged'
    created_at: datetime
    merged_at: Optional[datetime] = None
    labels: list[str] = Field(default_factory=list)
    url: str
