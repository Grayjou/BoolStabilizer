"""BoolStabilizer - A class that stabilizes booleans for a determined amount of time and/or checks."""

from .bool_attribute import BoolAttribute
from .bool_attribute_types import BufferMode, EffectiveThresholds, PendingTransition, TransitionResult
from .bool_stabilizer import BoolStabilizer

__all__ = [
    "BoolAttribute",
    "BoolStabilizer",
    "BufferMode",
    "EffectiveThresholds",
    "PendingTransition",
    "TransitionResult",
]
__version__ = "0.2.0"
