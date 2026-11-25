"""Stateful, report-driven boolean transition stabilization."""

import time
from typing import Callable, Optional

from ._validation import (
    validate_bool,
    validate_buffer_mode,
    validate_clock,
    validate_clock_value,
    validate_count,
    validate_duration,
)
from .bool_attribute_types import (
    BufferMode,
    EffectiveThresholds,
    PendingTransition,
    TransitionResult,
)


class BoolAttribute:
    """Stabilize one boolean value using count and duration requirements.

    A transition is accepted only when both requirements are satisfied. Duration
    starts at the first pending report and is evaluated on later ``report()``
    calls, or explicitly by ``update()``. Silence never creates an observation.
    """

    __slots__ = (
        "_name",
        "_value",
        "_count_threshold",
        "_duration_threshold",
        "_buffer_mode",
        "_count_threshold_true_to_false",
        "_count_threshold_false_to_true",
        "_duration_threshold_true_to_false",
        "_duration_threshold_false_to_true",
        "_clock",
        "_last_time",
        "_pending_value",
        "_pending_count",
        "_pending_start_time",
    )

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
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._name = name
        self._value = validate_bool(initial_value, "initial_value")
        configured_count = validate_count(count_threshold, "count_threshold")
        configured_duration = validate_duration(duration_threshold, "duration_threshold")
        assert configured_count is not None
        assert configured_duration is not None
        self._count_threshold = configured_count
        self._duration_threshold = configured_duration
        self._buffer_mode = validate_buffer_mode(buffer_mode)
        self._count_threshold_true_to_false = validate_count(
            count_threshold_true_to_false, "count_threshold_true_to_false", allow_none=True
        )
        self._count_threshold_false_to_true = validate_count(
            count_threshold_false_to_true, "count_threshold_false_to_true", allow_none=True
        )
        self._duration_threshold_true_to_false = validate_duration(
            duration_threshold_true_to_false, "duration_threshold_true_to_false", allow_none=True
        )
        self._duration_threshold_false_to_true = validate_duration(
            duration_threshold_false_to_true, "duration_threshold_false_to_true", allow_none=True
        )
        self._clock = validate_clock(clock)
        self._last_time: Optional[float] = None
        self._pending_value: Optional[bool] = None
        self._pending_count = 0
        self._pending_start_time: Optional[float] = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> bool:
        """The accepted, stabilized value, not the most recent raw report."""
        return self._value

    @property
    def count_threshold(self) -> int:
        """The configured symmetric count threshold."""
        return self._count_threshold

    @property
    def duration_threshold(self) -> float:
        """The configured symmetric duration threshold in seconds."""
        return self._duration_threshold

    @property
    def count_threshold_true_to_false(self) -> Optional[int]:
        """Configured true-to-false override, or ``None`` to use the base."""
        return self._count_threshold_true_to_false

    @property
    def count_threshold_false_to_true(self) -> Optional[int]:
        """Configured false-to-true override, or ``None`` to use the base."""
        return self._count_threshold_false_to_true

    @property
    def duration_threshold_true_to_false(self) -> Optional[float]:
        """Configured true-to-false override, or ``None`` to use the base."""
        return self._duration_threshold_true_to_false

    @property
    def duration_threshold_false_to_true(self) -> Optional[float]:
        """Configured false-to-true override, or ``None`` to use the base."""
        return self._duration_threshold_false_to_true

    @property
    def buffer_mode(self) -> BufferMode:
        return self._buffer_mode

    @buffer_mode.setter
    def buffer_mode(self, mode: BufferMode) -> None:
        mode = validate_buffer_mode(mode)
        if mode != self._buffer_mode:
            self._buffer_mode = mode
            self._reset_pending()

    @property
    def pending_count(self) -> int:
        return self._pending_count

    @property
    def pending_duration(self) -> float:
        """Elapsed pending duration without committing or changing state."""
        if self._pending_start_time is None:
            return 0.0
        return self._pending_duration_at(self._inspection_time())

    @property
    def pending_value(self) -> Optional[bool]:
        return self._pending_value

    @property
    def pending_transition(self) -> PendingTransition:
        """Return an immutable snapshot of pending evidence and progress."""
        if self._pending_value is None:
            return PendingTransition(
                self._value, None, 0, 0.0, None, None, False, False, False, 0.0, 0.0, 0.0
            )
        now = self._inspection_time()
        duration = self._pending_duration_at(now)
        thresholds = self.get_effective_thresholds(self._value, self._pending_value)
        count_satisfied = self._pending_count >= thresholds.count_threshold
        duration_satisfied = duration >= thresholds.duration_threshold
        count_progress = min(1.0, self._pending_count / thresholds.count_threshold)
        duration_progress = (
            1.0
            if thresholds.duration_threshold == 0
            else min(1.0, duration / thresholds.duration_threshold)
        )
        return PendingTransition(
            self._value,
            self._pending_value,
            self._pending_count,
            duration,
            thresholds.count_threshold,
            thresholds.duration_threshold,
            count_satisfied,
            duration_satisfied,
            count_satisfied and duration_satisfied,
            count_progress,
            duration_progress,
            min(count_progress, duration_progress),
        )

    def get_effective_thresholds(self, from_value: bool, to_value: bool) -> EffectiveThresholds:
        """Resolve directional overrides for a specific state transition."""
        from_value = validate_bool(from_value, "from_value")
        to_value = validate_bool(to_value, "to_value")
        if from_value == to_value:
            raise ValueError("from_value and to_value must differ")
        if from_value:
            count = self._count_threshold_true_to_false
            duration = self._duration_threshold_true_to_false
        else:
            count = self._count_threshold_false_to_true
            duration = self._duration_threshold_false_to_true
        return EffectiveThresholds(
            self._count_threshold if count is None else count,
            self._duration_threshold if duration is None else duration,
        )

    def report(self, new_value: bool) -> bool:
        """Record a raw boolean observation and return the stabilized value."""
        return self.report_with_result(new_value).value

    def report_with_result(self, new_value: bool) -> TransitionResult:
        """Record an observation and return its stabilized transition outcome."""
        new_value = validate_bool(new_value, "new_value")
        now = self._operation_time()
        previous = self._value

        if not self._should_apply_buffer(new_value):
            self._value = new_value
            self._reset_pending()
            return self._result(previous)

        if new_value == self._value:
            self._reset_pending()
            return self._result(previous)

        if self._pending_value != new_value:
            self._pending_value = new_value
            self._pending_count = 1
            self._pending_start_time = now
        else:
            self._pending_count += 1

        if self._is_eligible_at(now):
            self._value = new_value
            self._reset_pending()
        return self._result(previous)

    def update(self) -> bool:
        """Evaluate pending evidence without adding an observation."""
        return self.update_with_result().value

    def update_with_result(self) -> TransitionResult:
        """Evaluate pending evidence without incrementing its report count."""
        previous = self._value
        if self._pending_value is not None:
            now = self._operation_time()
            if self._is_eligible_at(now):
                self._value = self._pending_value
                self._reset_pending()
        return self._result(previous)

    def reset(self, new_value: Optional[bool] = None) -> None:
        """Clear pending evidence and optionally explicitly set the value."""
        if new_value is not None:
            new_value = validate_bool(new_value, "new_value")
            self._value = new_value
        self._reset_pending()

    def _operation_time(self) -> float:
        now = validate_clock_value(self._clock())
        if self._last_time is not None and now < self._last_time:
            now = self._last_time
        self._last_time = now
        return now

    def _inspection_time(self) -> float:
        now = validate_clock_value(self._clock())
        if self._last_time is not None and now < self._last_time:
            return self._last_time
        return now

    def _pending_duration_at(self, now: float) -> float:
        assert self._pending_start_time is not None
        return max(0.0, now - self._pending_start_time)

    def _should_apply_buffer(self, new_value: bool) -> bool:
        if self._buffer_mode == BufferMode.NONE:
            return False
        if self._buffer_mode == BufferMode.BOTH:
            return True
        if self._buffer_mode == BufferMode.TRUE_TO_FALSE:
            return self._value and not new_value
        return not self._value and new_value

    def _is_eligible_at(self, now: float) -> bool:
        assert self._pending_value is not None
        thresholds = self.get_effective_thresholds(self._value, self._pending_value)
        return (
            self._pending_count >= thresholds.count_threshold
            and self._pending_duration_at(now) >= thresholds.duration_threshold
        )

    def _result(self, previous: bool) -> TransitionResult:
        changed = previous != self._value
        return TransitionResult(previous, self._value, changed, changed and self._value, changed and not self._value)

    def _reset_pending(self) -> None:
        self._pending_value = None
        self._pending_count = 0
        self._pending_start_time = None

    def __repr__(self) -> str:
        return (
            "BoolAttribute(name={!r}, value={}, count_threshold={}, "
            "duration_threshold={}, buffer_mode={})"
        ).format(
            self._name,
            self._value,
            self._count_threshold,
            self._duration_threshold,
            self._buffer_mode,
        )
