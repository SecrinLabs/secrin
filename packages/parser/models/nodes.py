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
