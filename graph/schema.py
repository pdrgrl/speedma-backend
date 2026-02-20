from enum import Enum

class NodeType(str, Enum):
    COMPONENT  = "Component"
    SCENARIO   = "Scenario"
    PHASE      = "Phase"
    PROCEDURE  = "Procedure"
    RISK       = "Risk"

class EdgeType(str, Enum):
    ACTIVE_IN  = "ACTIVE_IN"
    PART_OF    = "PART_OF"
    EVOLVES_TO = "EVOLVES_TO"
    REQUIRES   = "REQUIRES"
    CAUSES     = "CAUSES"
    MITIGATES  = "MITIGATES"
    USED_IN    = "USED_IN"