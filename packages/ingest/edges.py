from enum import Enum

class Edge(Enum):
    # Github / Commits
    AUTHORED_BY = "AUTHORED_BY"
    BELONGS_TO = "BELONGS_TO"
    TOUCHED = "TOUCHED"

    # Code structure
    HAS_CLASS = "HAS_CLASS"
    HAS_FUNCTION = "HAS_FUNCTION"
    HAS_VARIABLE = "HAS_VARIABLE"
    HAS_TEST = "HAS_TEST"
    HAS_DOC = "HAS_DOC"

    # Architecture / Dependencies
    IMPORTS = "IMPORTS"
    DEPENDS_ON = "DEPENDS_ON"

    # Issues / PRs / context
    REFERENCES = "REFERENCES"
    RELATED_TO = "RELATED_TO"
    CREATED_BY = "CREATED_BY"
    MERGED_TO = "MERGED_TO"
    INCLUDES = "INCLUDES"
