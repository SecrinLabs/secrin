from pydantic import BaseModel
from typing import Any, Optional
from enum import Enum


class RelationshipType(str, Enum):
    HAS_FILE = "HAS_FILE"
    CONTAINS_CLASS = "CONTAINS_CLASS"
    CONTAINS_FUNCTION = "CONTAINS_FUNCTION"
    CALLS = "CALLS"
    DEFINED_IN = "DEFINED_IN"
    TOUCHED = "TOUCHED"
    MENTIONS_FILE = "MENTIONS_FILE"
    HAS_METHOD = "HAS_METHOD"
    USES_VARIABLE = "USES_VARIABLE"
    IMPORTS = "IMPORTS"
    HAS_DOC = "HAS_DOC"
    DEPENDS_ON = "DEPENDS_ON"
    HAS_MODULE = "HAS_MODULE"
    HAS_TEST = "HAS_TEST"


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
