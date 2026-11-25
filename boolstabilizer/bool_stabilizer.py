"""Container for BoolAttribute instances sharing configuration defaults."""

import time
from typing import Callable, Dict, Final, Iterator, Optional, Union

from ._validation import (
    validate_bool,
    validate_buffer_mode,
    validate_clock,
    validate_count,
    validate_duration,
)
from .bool_attribute import BoolAttribute
from .bool_attribute_types import BufferMode, TransitionResult


class _InheritanceSentinel:
    """Private marker that distinguishes omission from an explicit None."""

    __slots__ = ()


_INHERIT: Final = _InheritanceSentinel()
DirectionalCount = Union[Optional[int], _InheritanceSentinel]
DirectionalDuration = Union[Optional[float], _InheritanceSentinel]


class BoolStabilizer:
    """Manage named boolean stabilizers with defaults for newly added attributes.

    Defaults are copied into an attribute when it is created; subsequent manager
    configuration changes do not alter existing attributes.
    """

    __slots__ = (
        "_count_threshold",
        "_duration_threshold",
        "_buffer_mode",
        "_count_threshold_true_to_false",
        "_count_threshold_false_to_true",
        "_duration_threshold_true_to_false",
        "_duration_threshold_false_to_true",
        "_clock",
        "_attributes",
    )

    def __init__(
        self,
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
        self._attributes: Dict[str, BoolAttribute] = {}

    @property
    def count_threshold(self) -> int:
        """Configured symmetric count default."""
        return self._count_threshold

    @property
    def duration_threshold(self) -> float:
        """Configured symmetric duration default."""
        return self._duration_threshold

    @property
    def count_threshold_true_to_false(self) -> Optional[int]:
        return self._count_threshold_true_to_false

    @property
    def count_threshold_false_to_true(self) -> Optional[int]:
        return self._count_threshold_false_to_true

    @property
    def duration_threshold_true_to_false(self) -> Optional[float]:
        return self._duration_threshold_true_to_false

    @property
    def duration_threshold_false_to_true(self) -> Optional[float]:
        return self._duration_threshold_false_to_true

    @property
    def buffer_mode(self) -> BufferMode:
        """Default buffer mode for attributes added in the future."""
        return self._buffer_mode

    @buffer_mode.setter
    def buffer_mode(self, mode: BufferMode) -> None:
        self._buffer_mode = validate_buffer_mode(mode)

    def add_attribute(
        self,
        name: str,
        initial_value: bool = False,
        count_threshold: Optional[int] = None,
        duration_threshold: Optional[float] = None,
        buffer_mode: Optional[BufferMode] = None,
        *,
        count_threshold_true_to_false: DirectionalCount = _INHERIT,
        count_threshold_false_to_true: DirectionalCount = _INHERIT,
        duration_threshold_true_to_false: DirectionalDuration = _INHERIT,
        duration_threshold_false_to_true: DirectionalDuration = _INHERIT,
        clock: Optional[Callable[[], float]] = None,
    ) -> BoolAttribute:
        """Create and register an attribute.

        Directional arguments omitted here inherit the manager directional
        defaults. Passing ``None`` explicitly disables that inherited directional
        default so the attribute's symmetric threshold is used instead.
        """
        if name in self._attributes:
            raise ValueError("Attribute {!r} already exists".format(name))
        initial_value = validate_bool(initial_value, "initial_value")

        resolved_count = self._count_threshold if count_threshold is None else validate_count(
            count_threshold, "count_threshold"
        )
        resolved_duration = (
            self._duration_threshold
            if duration_threshold is None
            else validate_duration(duration_threshold, "duration_threshold")
        )
        assert resolved_count is not None
        assert resolved_duration is not None
        resolved_mode = self._buffer_mode if buffer_mode is None else validate_buffer_mode(buffer_mode)
        resolved_clock = self._clock if clock is None else validate_clock(clock)

        resolved_count_t2f = self._resolve_directional_count(
            count_threshold_true_to_false,
            self._count_threshold_true_to_false,
            "count_threshold_true_to_false",
        )
        resolved_count_f2t = self._resolve_directional_count(
            count_threshold_false_to_true,
            self._count_threshold_false_to_true,
            "count_threshold_false_to_true",
        )
        resolved_duration_t2f = self._resolve_directional_duration(
            duration_threshold_true_to_false,
            self._duration_threshold_true_to_false,
            "duration_threshold_true_to_false",
        )
        resolved_duration_f2t = self._resolve_directional_duration(
            duration_threshold_false_to_true,
            self._duration_threshold_false_to_true,
            "duration_threshold_false_to_true",
        )

        attribute = BoolAttribute(
            name,
            initial_value,
            resolved_count,
            resolved_duration,
            resolved_mode,
            count_threshold_true_to_false=resolved_count_t2f,
            count_threshold_false_to_true=resolved_count_f2t,
            duration_threshold_true_to_false=resolved_duration_t2f,
            duration_threshold_false_to_true=resolved_duration_f2t,
            clock=resolved_clock,
        )
        self._attributes[name] = attribute
        return attribute

    @staticmethod
    def _resolve_directional_count(
        value: DirectionalCount, inherited: Optional[int], parameter: str
    ) -> Optional[int]:
        if value is _INHERIT:
            return inherited
        return validate_count(value, parameter, allow_none=True)

    @staticmethod
    def _resolve_directional_duration(
        value: DirectionalDuration, inherited: Optional[float], parameter: str
    ) -> Optional[float]:
        if value is _INHERIT:
            return inherited
        return validate_duration(value, parameter, allow_none=True)

    def remove_attribute(self, name: str) -> bool:
        if name in self._attributes:
            del self._attributes[name]
            return True
        return False

    def get_attribute(self, name: str) -> Optional[BoolAttribute]:
        return self._attributes.get(name)

    def report(self, name: str, new_value: bool) -> bool:
        """Report an observation and return the named stabilized value."""
        return self._get_required(name).report(new_value)

    def report_with_result(self, name: str, new_value: bool) -> TransitionResult:
        """Report an observation and return its transition outcome."""
        return self._get_required(name).report_with_result(new_value)

    def update(self, name: str) -> bool:
        """Evaluate pending evidence for one attribute without a new report."""
        return self._get_required(name).update()

    def update_with_result(self, name: str) -> TransitionResult:
        """Evaluate pending evidence and return its transition outcome."""
        return self._get_required(name).update_with_result()

    def get_value(self, name: str) -> bool:
        return self._get_required(name).value

    def _get_required(self, name: str) -> BoolAttribute:
        try:
            return self._attributes[name]
        except KeyError:
            raise KeyError("Attribute {!r} does not exist".format(name)) from None

    def get_all_values(self) -> Dict[str, bool]:
        return {name: attribute.value for name, attribute in self._attributes.items()}

    def reset_all(self) -> None:
        for attribute in self._attributes.values():
            attribute.reset()

    def __len__(self) -> int:
        return len(self._attributes)

    def __contains__(self, name: str) -> bool:
        return name in self._attributes

    def __iter__(self) -> Iterator[str]:
        return iter(self._attributes)

    def __getitem__(self, name: str) -> bool:
        return self.get_value(name)

    def __repr__(self) -> str:
        return (
            "BoolStabilizer(count_threshold={}, duration_threshold={}, "
            "buffer_mode={}, attributes={})"
        ).format(
            self._count_threshold,
            self._duration_threshold,
            self._buffer_mode,
            list(self._attributes),
        )
