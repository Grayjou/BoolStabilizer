"""BoolAttribute class for tracking stabilized boolean values."""

import time
from typing import Optional


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
    """
    
    def __init__(
        self,
        name: str,
        initial_value: bool = False,
        count_threshold: int = 1,
        duration_threshold: float = 0.0
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
        return self._count_threshold
    
    @property
    def duration_threshold(self) -> float:
        """Get the duration threshold in seconds."""
        return self._duration_threshold
    
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
    
    def report(self, new_value: bool, apply_buffer: bool = True) -> bool:
        """
        Report a new value for this attribute.
        
        If apply_buffer is True, the value will only change when thresholds are met.
        If apply_buffer is False, the value changes immediately.
        
        Args:
            new_value: The new boolean value being reported.
            apply_buffer: Whether to apply the buffering/stabilization logic.
                         If False, the value changes immediately.
        
        Returns:
            The current stabilized value after processing the report.
        """
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
            f"duration_threshold={self._duration_threshold})"
        )
