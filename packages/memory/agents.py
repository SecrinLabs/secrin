from enum import Enum
from typing import List


class AgentType(str, Enum):    
    PATHFINDER = "pathfinder"       # Code structure & navigation
    CHRONICLE = "chronicle"         # Commit history & evolution
    DIAGNOSTICIAN = "diagnostician" # Debugging & error analysis
    BLUEPRINT = "blueprint"         # Architecture reasoning
    SENTINEL = "sentinel"           # Code review & quality checks
    
    @classmethod
    def list_values(cls) -> list[str]:
        return [agent.value for agent in cls]
    
    @classmethod
    def get_description(cls, agent_type: "AgentType") -> str:
        descriptions = {
            cls.PATHFINDER: "Code structure & navigation",
            cls.CHRONICLE: "Commit history & evolution",
            cls.DIAGNOSTICIAN: "Debugging & error analysis",
            cls.BLUEPRINT: "Architecture reasoning",
            cls.SENTINEL: "Code review & quality checks",
        }
        return descriptions.get(agent_type, "Unknown agent type")

    @classmethod
    def get_node_types(cls, agent_type: str) -> List[str]:
        """
        Get the relevant node types to search for each agent.
        Returns a list of node types ordered by priority.
        """
        node_types_map = {
            cls.PATHFINDER.value: ["Function", "Class", "File"],
            cls.CHRONICLE.value: ["Commit", "File"],
            cls.DIAGNOSTICIAN.value: ["Function", "Class", "Commit", "File"],
            cls.BLUEPRINT.value: ["Class", "File", "Function"],
            cls.SENTINEL.value: ["Function", "Class", "File", "Commit"],
        }
        return node_types_map.get(agent_type, ["Function", "Class", "File"])
