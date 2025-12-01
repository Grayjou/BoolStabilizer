"""BoolStabilizer - A class that stabilizes booleans for a determined amount of time and/or checks."""

from .bool_attribute import BoolAttribute
from .bool_stabilizer import BoolStabilizer, BufferMode

__all__ = ["BoolAttribute", "BoolStabilizer", "BufferMode"]
__version__ = "0.1.0"
