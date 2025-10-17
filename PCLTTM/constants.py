from enum import IntEnum

# ============================================================================
# CONSTANTS AND ENUMERATIONS
# ============================================================================

class StateFlag(IntEnum):
    """States during the conquest process."""
    Free = 0        # Not yet processed
    Conquered = 1   # Processed (part of coarse mesh)
    ToRemove = 2   # Will be removed (part of a patch)


class VertexTag(IntEnum):
    """Tags for boundary vertices to enable deterministic retriangulation."""
    Default = 0
    Plus = 1   # '+' tag
    Minus = 2  # '-' tag

class PCLTTMConstants:
    # Valence constraints for decimation and cleaning passes
    MIN_VALENCE_DECIMATION = 3
    MAX_VALENCE_DECIMATION = 6
    VALENCE_CLEANING = 3