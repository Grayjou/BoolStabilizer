"""Public value types used by BoolAttribute."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class BufferMode(Enum):
    """Select the transition directions to stabilize."""

    BOTH = auto()
    TRUE_TO_FALSE = auto()
    FALSE_TO_TRUE = auto()
    NONE = auto()


@dataclass(frozen=True)
class EffectiveThresholds:
    """Resolved requirements for one transition direction."""

    count_threshold: int
    duration_threshold: float


@dataclass(frozen=True)
class TransitionResult:
    """The stabilized-state outcome of one report or update operation."""

    previous_value: bool
    value: bool
    changed: bool
    rose: bool
    fell: bool


@dataclass(frozen=True)
class PendingTransition:
    """A non-mutating snapshot of pending transition evidence."""

    stabilized_value: bool
    pending_value: Optional[bool]
    pending_count: int
    pending_duration: float
    count_threshold: Optional[int]
    duration_threshold: Optional[float]
    count_satisfied: bool
    duration_satisfied: bool
    eligible: bool
    count_progress: float
    duration_progress: float
    progress: float
