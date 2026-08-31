from enum import Enum

class AutonomyMode(str, Enum):
    STRICT = "strict"
    SUPERVISED = "supervised"
    FULL_AUTONOMOUS = "autonomous"
