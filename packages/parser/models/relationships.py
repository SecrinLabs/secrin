from pydantic import BaseModel
from typing import Any, Optional
from enum import Enum


class RelationshipType(str, Enum):
    # File and structure relationships
    HAS_FILE = "HAS_FILE"
    CONTAINS_CLASS = "CONTAINS_CLASS"
    CONTAINS_FUNCTION = "CONTAINS_FUNCTION"
    DEFINED_IN = "DEFINED_IN"
    HAS_METHOD = "HAS_METHOD"
    HAS_MODULE = "HAS_MODULE"
    HAS_TEST = "HAS_TEST"
    
    # Function and data flow relationships
    CALLS = "CALLS"  # function -> function with call-site info
    READS = "READS"  # function -> variable (read access)
    WRITES = "WRITES"  # function -> variable (write access)
    USES_VARIABLE = "USES_VARIABLE"  # Generic usage
    
    # Import/export relationships
    IMPORTS = "IMPORTS"  # file -> package/module
    IMPORTS_FROM = "IMPORTS_FROM"  # more specific import with source
    EXPORTS = "EXPORTS"  # file -> exported symbol
    
    # Type relationships
    EXTENDS = "EXTENDS"  # class -> parent class
    IMPLEMENTS = "IMPLEMENTS"  # class -> interface
    HAS_TYPE = "HAS_TYPE"  # variable/param -> type
    
    # Documentation and metadata
    HAS_DOC = "HAS_DOC"
    DOCUMENTS = "DOCUMENTS"  # comment/doc -> code node
    
    # Version control relationships
    CHANGED_IN = "CHANGED_IN"  # node -> commit
    TOUCHED = "TOUCHED"  # commit -> file
    MENTIONS_FILE = "MENTIONS_FILE"
    
    # Test relationships
    TESTS = "TESTS"  # test -> function/class/module
    
    # Dependencies
    DEPENDS_ON = "DEPENDS_ON"


class Relationship(BaseModel):
    """Represents a relationship between two nodes"""
    source_id: str
    target_id: str
    type: RelationshipType
    properties: dict[str, Any] = {}
    
    def __hash__(self):
        return hash((self.source_id, self.target_id, self.type))
    
    def __eq__(self, other):
        if not isinstance(other, Relationship):
            return False
        return (
            self.source_id == other.source_id
            and self.target_id == other.target_id
            and self.type == other.type
        )
