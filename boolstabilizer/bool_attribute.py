"""BoolAttribute class for tracking stabilized boolean values."""

import time
from enum import Enum, auto
from typing import Optional


class BufferMode(Enum):
    """
    Enum defining when to apply buffering/stabilization.
    
    BOTH: Apply buffering for both true→false and false→true transitions.
    TRUE_TO_FALSE: Only apply buffering when transitioning from True to False.
    FALSE_TO_TRUE: Only apply buffering when transitioning from False to True.
    NONE: No buffering - all changes are immediate.
    """
    BOTH = auto()
    TRUE_TO_FALSE = auto()
    FALSE_TO_TRUE = auto()
    NONE = auto()


class BoolAttribute:
    """
    A boolean attribute that stabilizes its value based on count and duration thresholds.
    
    The attribute maintains an internal stabilized value that only changes when:
    1. A new value is reported a sufficient number of times (count threshold)
    2. The new value has been reported consistently for a sufficient duration (duration threshold)
    
    Attributes:
        name: The name identifier for this attribute.
        value: The current stabilized boolean value.
        count_threshold: Number of times a value must be reported before it can change.
        duration_threshold: Duration (in seconds) a value must be reported before it can change.
        buffer_mode: The mode determining when buffering is applied.
    """
    
    def __init__(
        self,
        name: str,
        initial_value: bool = False,
        count_threshold: int = 1,
        duration_threshold: float = 0.0,
        buffer_mode: BufferMode = BufferMode.BOTH,
        *,
        count_threshold_true_to_false: Optional[int] = None,
        count_threshold_false_to_true: Optional[int] = None,
        duration_threshold_true_to_false: Optional[float] = None,
        duration_threshold_false_to_true: Optional[float] = None,
    ):
        """
        Initialize a BoolAttribute.
        
        Args:
            name: The name identifier for this attribute.
            initial_value: The initial boolean value. Defaults to False.
            count_threshold: Number of consecutive reports needed to change the value.
                            Must be at least 1. Defaults to 1.
            duration_threshold: Duration in seconds the value must be consistently
                               reported before changing. Defaults to 0.0.
            buffer_mode: When to apply buffering. Defaults to BufferMode.BOTH.
        
        Raises:
            ValueError: If count_threshold is less than 1 or duration_threshold is negative.
        """
        if count_threshold < 1:
            raise ValueError("count_threshold must be at least 1")
        if duration_threshold < 0:
            raise ValueError("duration_threshold cannot be negative")
        
        self._name = name
        self._value = initial_value
        self._count_threshold = count_threshold
        self._duration_threshold = duration_threshold
        self._buffer_mode = buffer_mode
        
        self._count_threshold_true_to_false = count_threshold_true_to_false
        self._count_threshold_false_to_true = count_threshold_false_to_true
        self._duration_threshold_true_to_false = duration_threshold_true_to_false
        self._duration_threshold_false_to_true = duration_threshold_false_to_true

        # Tracking state for pending value changes
        self._pending_value: Optional[bool] = None
        self._pending_count: int = 0
        self._pending_start_time: Optional[float] = None
    
    @property
    def name(self) -> str:
        """Get the name of this attribute."""
        return self._name
    
    @property
    def value(self) -> bool:
        """Get the current stabilized boolean value."""
        return self._value
    
    @property
    def count_threshold(self) -> int:
        """Get the count threshold."""
        false_to_true = self._count_threshold_false_to_true if self._count_threshold_false_to_true is not None else self._count_threshold
        true_to_false = self._count_threshold_true_to_false if self._count_threshold_true_to_false is not None else self._count_threshold
        if true_to_false != false_to_true:
            raise ValueError("Count thresholds differ for true→false and false→true transitions")
        return self._count_threshold
    
    @property
    def duration_threshold(self) -> float:
        """Get the duration threshold in seconds."""
        false_to_true = self._duration_threshold_false_to_true if self._duration_threshold_false_to_true is not None else self._duration_threshold
        true_to_false = self._duration_threshold_true_to_false if self._duration_threshold_true_to_false is not None else self._duration_threshold
        if true_to_false != false_to_true:
            raise ValueError("Duration thresholds differ for true→false and false→true transitions")
        return self._duration_threshold
    
    @property
    def buffer_mode(self) -> BufferMode:
        """Get the current buffer mode."""

        return self._buffer_mode
    
    @buffer_mode.setter
    def buffer_mode(self, mode: BufferMode) -> None:
        """Set the buffer mode."""
        self._buffer_mode = mode
    
    @property
    def pending_count(self) -> int:
        """Get the current count of pending value reports."""
        return self._pending_count
    
    @property
    def pending_duration(self) -> float:
        """Get the duration the pending value has been reported (in seconds)."""
        if self._pending_start_time is None:
            return 0.0
        return time.time() - self._pending_start_time
    
    @property
    def pending_value(self) -> Optional[bool]:
        """Get the pending value, if any."""
        return self._pending_value
    
    def report(self, new_value: bool) -> bool:
        """
        Report a new value for this attribute.
        
        The buffering behavior depends on the buffer_mode setting:
        - BOTH: Always apply buffering
        - TRUE_TO_FALSE: Only buffer when transitioning from True to False
        - FALSE_TO_TRUE: Only buffer when transitioning from False to True
        - NONE: Never buffer (immediate changes)
        
        Args:
            new_value: The new boolean value being reported.
        
        Returns:
            The current stabilized value after processing the report.
        """
        # Determine if buffering should be applied for this transition
        apply_buffer = self._should_apply_buffer(new_value)
        
        if not apply_buffer:
            # Bypass buffering - change immediately
            self._value = new_value
            self._reset_pending()
            return self._value
        
        if new_value == self._value:
            # Reported value matches current value - reset pending state
            self._reset_pending()
            return self._value
        
        # Value is different from current - track for potential change
        if self._pending_value != new_value:
            # Different pending value - start fresh tracking
            self._pending_value = new_value
            self._pending_count = 1
            self._pending_start_time = time.time()
        else:
            # Same pending value - increment count
            self._pending_count += 1
        
        # Check if thresholds are met
        if self._check_thresholds():
            self._value = new_value
            self._reset_pending()
        
        return self._value
    
    def _should_apply_buffer(self, new_value: bool) -> bool:
        """
        Determine if buffering should be applied for a transition.
        
        Args:
            new_value: The new value being reported.
        
        Returns:
            True if buffering should be applied, False otherwise.
        """
        if self._buffer_mode == BufferMode.NONE:
            return False
        
        if self._buffer_mode == BufferMode.BOTH:
            return True
        
        if self._buffer_mode == BufferMode.TRUE_TO_FALSE:
            # Only buffer when going from True to False
            return self._value and not new_value
        
        if self._buffer_mode == BufferMode.FALSE_TO_TRUE:
            # Only buffer when going from False to True
            return not self._value and new_value
        
        return True
    
    def _check_thresholds(self) -> bool:
        """Check if both count and duration thresholds are met."""
        count_met = self._pending_count >= self._count_threshold
        duration_met = self.pending_duration >= self._duration_threshold
        return count_met and duration_met
    
    def _reset_pending(self) -> None:
        """Reset the pending state."""
        self._pending_value = None
        self._pending_count = 0
        self._pending_start_time = None
    
    def reset(self, new_value: Optional[bool] = None) -> None:
        """
        Reset the attribute to a clean state.
        
        Args:
            new_value: If provided, sets the stabilized value to this.
                      If None, keeps the current stabilized value.
        """
        if new_value is not None:
            self._value = new_value
        self._reset_pending()
    
    def __repr__(self) -> str:
        """Return a string representation of the attribute."""
        return (
            f"BoolAttribute(name={self._name!r}, value={self._value}, "
            f"count_threshold={self._count_threshold}, "
            f"duration_threshold={self._duration_threshold}, "
            f"buffer_mode={self._buffer_mode})"
        )
