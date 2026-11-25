"""Shared input validation for the public API."""

import math
from numbers import Integral, Real
from typing import Callable, Optional

from .bool_attribute_types import BufferMode


def validate_bool(value: object, parameter: str) -> bool:
    """Return a genuine bool or raise a consistent error."""
    if type(value) is not bool:
        raise TypeError("{} must be a bool".format(parameter))
    return value


def validate_count(value: object, parameter: str, allow_none: bool = False) -> Optional[int]:
    """Validate a count threshold."""
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("{} must be an integer greater than or equal to 1".format(parameter))
    if value < 1:
        raise ValueError("{} must be greater than or equal to 1".format(parameter))
    return int(value)


def validate_duration(
    value: object, parameter: str, allow_none: bool = False
) -> Optional[float]:
    """Validate a finite, nonnegative duration threshold."""
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{} must be a finite nonnegative number".format(parameter))
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("{} must be a finite nonnegative number".format(parameter))
    return result


def validate_buffer_mode(value: object, parameter: str = "buffer_mode") -> BufferMode:
    """Validate a BufferMode instance rather than accepting lookalikes."""
    if not isinstance(value, BufferMode):
        raise TypeError("{} must be a BufferMode".format(parameter))
    return value


def validate_clock(value: object) -> Callable[[], float]:
    """Validate a clock callable."""
    if not callable(value):
        raise TypeError("clock must be callable")
    return value  # type: ignore[return-value]


def validate_clock_value(value: object) -> float:
    """Validate a value returned by a clock."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("clock result must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("clock result must be a finite number")
    return result
