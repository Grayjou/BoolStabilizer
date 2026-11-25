# BoolStabilizer

`boolstabilizer` is a small, standard-library-only, stateful boolean transition filter. It separates raw observations from an accepted stabilized value. It is useful for debounce logic, noisy sensors, online/offline monitors, game transitions, and deterministic simulations.

## Install

```bash
pip install boolstabilizer
```

Requires Python 3.8 or newer.

## Core model

A `BoolAttribute` has a stabilized `value` and, while evidence is accumulating, a pending candidate value, count, and start time.

- `report(value)` records a raw observation and returns the stabilized value.
- A buffered transition is accepted only when both the count and duration thresholds are met.
- A report equal to the stabilized value cancels pending evidence.
- An unbuffered transition is accepted immediately.
- Pending evidence is cleared when it is cancelled or accepted.

Duration is **report-driven** by default. It starts with the first report for a candidate; time between reports counts, but silence alone does not accept a transition. The next matching `report()` evaluates the thresholds. This does not prove the source remained in that state while no observations arrived.

`update()` is an explicit, optional evaluation operation for callers that intentionally treat the last observation as valid until replaced. It never increments the pending report count and creates no observations. There are no threads, timers, callbacks, or background work.

## Deterministic quick start

```python
from boolstabilizer import BoolAttribute


class ManualClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


clock = ManualClock()
sensor = BoolAttribute("door", count_threshold=2, duration_threshold=5, clock=clock)

assert sensor.report(True) is False       # Pending: 1 report, 0 seconds
clock.now = 5
assert sensor.report(True) is True        # 2 reports AND 5 seconds
assert sensor.value is True
```

The default clock is `time.monotonic()`. A custom clock must return finite numeric seconds. If it moves backwards, the value used for an operation is clamped to the last operation time, so elapsed pending duration cannot move backwards or become negative. Inspection does not update this clamp.

## Stream-monitoring example

For a Twitch-like stream, turn online immediately but require an offline observation to persist for 60 seconds. A recovered stream cancels the pending offline transition, so it does not produce a duplicate online notification.

```python
from boolstabilizer import BoolAttribute, BufferMode

stream = BoolAttribute(
    "stream",
    buffer_mode=BufferMode.TRUE_TO_FALSE,
    duration_threshold_true_to_false=60,
)

result = stream.report_with_result(is_online)
if result.rose:
    notify_stream_online()
```

`report_with_result()` returns immutable `TransitionResult` data with `previous_value`, `value`, `changed`, `rose`, and `fell`. A transition indication is true exactly once: on the operation that accepts it. `BoolStabilizer.report_with_result(name, value)` provides the same API for managed attributes.

## Thresholds and buffer modes

Base thresholds are symmetric:

- `count_threshold`: integer at least `1`.
- `duration_threshold`: finite, nonnegative seconds.

Directional overrides can be supplied for `true_to_false` and `false_to_true`. A directional override of `None` falls back to the base threshold. `count_threshold` and `duration_threshold` always expose their configured base values, even when directional overrides differ. Use `get_effective_thresholds(from_value, to_value)` to inspect the resolved requirements for a direction.

```python
attribute = BoolAttribute(
    "connection",
    count_threshold=3,
    duration_threshold=0,
    count_threshold_false_to_true=1,
    count_threshold_true_to_false=5,
)

assert attribute.count_threshold == 3
assert attribute.get_effective_thresholds(False, True).count_threshold == 1
assert attribute.get_effective_thresholds(True, False).count_threshold == 5
```

`BufferMode.BOTH` buffers both directions. `TRUE_TO_FALSE` buffers only outages, `FALSE_TO_TRUE` buffers only recoveries, and `NONE` accepts every change immediately. Setting a different `buffer_mode` clears pending evidence but preserves the stabilized value; assigning the existing mode does not clear it.

## Manager defaults and inheritance

`BoolStabilizer` supplies defaults when `add_attribute()` creates an attribute. Attributes are independent after creation; later manager changes affect only future attributes.

For each direction, precedence is:

1. An explicit attribute directional override.
2. A manager directional default when the attribute directional argument is omitted.
3. The attribute symmetric threshold.
4. The manager symmetric default.

Passing `None` explicitly to a directional argument of `add_attribute()` disables a manager directional default for that direction and uses the attribute base threshold. Omitting the argument inherits the manager directional default. This distinction permits an attribute to opt out without adding another public option.

The manager clock is inherited by new attributes unless `clock=` is passed to `add_attribute()`.

## Pending inspection and progress

`pending_value`, `pending_count`, and `pending_duration` remain available. `pending_transition` returns an immutable `PendingTransition` snapshot with effective thresholds, satisfaction flags, and progress.

For an active pending transition, count progress is `min(1, pending_count / count_threshold)` and duration progress is `min(1, pending_duration / duration_threshold)`. A zero duration threshold has duration progress `1`. Overall progress is the smaller component because both requirements are required. Progress is zero with no pending transition. Progress of one means the requirements are satisfied; in report-driven use it does not mean the transition has been committed until a report or explicit `update()` performs evaluation.

Inspection never commits a transition or changes pending evidence.

## API

```python
from boolstabilizer import (
    BoolAttribute,
    BoolStabilizer,
    BufferMode,
    EffectiveThresholds,
    PendingTransition,
    TransitionResult,
)
```

- `BoolAttribute.report(value)` and `BoolStabilizer.report(name, value)` return the stabilized boolean for compatibility.
- `report_with_result(...)` provides transition observability.
- `update()` / `update_with_result()` evaluate existing pending evidence without a report.
- `reset(new_value=None)` clears pending evidence and can explicitly set a boolean stabilized value.
- `BoolStabilizer.reset_all()` clears pending evidence for all attributes.

Inputs are strict: initial values, reports, and explicit reset values must be actual `bool` instances. Thresholds reject booleans, fractional counts, negatives, NaN, and infinity. Buffer modes must be `BufferMode` members.

## Thread safety

Instances are not thread-safe. Serialize access to an attribute or manager when multiple threads may report or reset the same state.

## Migration from 0.1

- `BoolAttribute.count_threshold` and `duration_threshold` no longer raise when directional thresholds differ; they always return the configured base threshold. Use `get_effective_thresholds()` for direction-specific values.
- The default timing source changed from wall-clock time to `time.monotonic()`.
- Inputs that were previously accepted incidentally, such as `1` for a report or `True` for a count threshold, now raise `TypeError`.
- In `BoolStabilizer.add_attribute()`, an explicitly passed directional `None` now opts out of a manager directional default. Omit the argument to retain the previous inheritance behavior.

## Deliberately deferred

Maximum report-gap expiry, mutable thresholds, and additional stabilization strategies are intentionally not included. They introduce evidence-expiration and reconfiguration semantics that overlap with the small report-driven model. Callers needing time-driven commitment can use `update()` explicitly; callers needing freshness can track observation timestamps separately.

## License

MIT. See [LICENSE](LICENSE).
