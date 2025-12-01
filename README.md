# BoolStabilizer

A Python library for stabilizing boolean values based on configurable count and duration thresholds.

## Overview

BoolStabilizer provides classes that prevent boolean values from changing until certain conditions are met.
Thresholds can be symmetric or asymmetric:

- **Count threshold**: How many consecutive reports are required before a transition is accepted  
- **Duration threshold**: How long a new value must be continuously reported before being accepted  
- **Asymmetric thresholds**: You may use different thresholds for true→false vs false→true transitions  
- **Buffer mode**: Control which transitions are stabilized (true→false, false→true, or both)


This is useful for debouncing, filtering noise from sensor data, or any scenario where you want to prevent rapid boolean state changes.

## Installation

```bash
pip install boolstabilizer
```

Or install from source:

```bash
git clone https://github.com/Grayjou/BoolStabilizer.git
cd BoolStabilizer
pip install -e .
```

## Quick Start

```python
from boolstabilizer import BoolStabilizer, BufferMode

# Create a stabilizer with default thresholds
stabilizer = BoolStabilizer(count_threshold=3, duration_threshold=0.5)

# Add boolean attributes (they inherit default thresholds and buffer_mode)
stabilizer.add_attribute("sensor1", initial_value=False)
stabilizer.add_attribute("sensor2", initial_value=True)

# Report new values - the value won't change until thresholds are met
stabilizer.report("sensor1", True)  # Count: 1/3 - still False
stabilizer.report("sensor1", True)  # Count: 2/3 - still False
stabilizer.report("sensor1", True)  # Count: 3/3 - now True (if duration met)

# Get the current stabilized value
print(stabilizer.get_value("sensor1"))
```

## Asymmetric Thresholds

BoolStabilizer supports asymmetric stabilization:
you can specify different thresholds for **true→false** and **false→true** transitions.

If a per-direction threshold is not provided, it falls back to the base
`count_threshold` or `duration_threshold`.

### Example

```python
from boolstabilizer import BoolStabilizer

# Quick to turn on, slow to turn off
stabilizer = BoolStabilizer(
    count_threshold_false_to_true=2,
    count_threshold_true_to_false=5,
)

stabilizer.add_attribute("sensor", initial_value=False)

# Turns True after 2 reports
stabilizer.report("sensor", True)
stabilizer.report("sensor", True)
assert stabilizer.get_value("sensor") == True

# Turns False after 5 reports
for _ in range(5):
    stabilizer.report("sensor", False)
assert stabilizer.get_value("sensor") == False
```

## Buffer Modes

Each attribute can have its own buffer mode, controlling when stabilization is applied:

```python
from boolstabilizer import BoolStabilizer, BoolAttribute, BufferMode

# Create a stabilizer with a default buffer mode
stabilizer = BoolStabilizer(count_threshold=3, buffer_mode=BufferMode.BOTH)

# Add attributes with different buffer modes
stabilizer.add_attribute("sensor1", buffer_mode=BufferMode.BOTH)        # Buffer both directions
stabilizer.add_attribute("sensor2", buffer_mode=BufferMode.TRUE_TO_FALSE)  # Only buffer True→False
stabilizer.add_attribute("sensor3", buffer_mode=BufferMode.FALSE_TO_TRUE)  # Only buffer False→True
stabilizer.add_attribute("sensor4", buffer_mode=BufferMode.NONE)        # No buffering (immediate)

# Or use BoolAttribute directly with a specific buffer mode
attr = BoolAttribute("my_bool", count_threshold=3, buffer_mode=BufferMode.TRUE_TO_FALSE)

# Change buffer mode at runtime
attr.buffer_mode = BufferMode.NONE
```

### Buffer Mode Options

| Mode | Description |
|------|-------------|
| `BufferMode.BOTH` | Buffer both true→false and false→true transitions (default) |
| `BufferMode.TRUE_TO_FALSE` | Only buffer when changing from True to False |
| `BufferMode.FALSE_TO_TRUE` | Only buffer when changing from False to True |
| `BufferMode.NONE` | No buffering - all changes are immediate |

## BoolAttribute Class

`BoolAttribute` supports both symmetric and asymmetric thresholds.

You may specify:

- `count_threshold` / `duration_threshold` (symmetric)
- `count_threshold_true_to_false`
- `count_threshold_false_to_true`
- `duration_threshold_true_to_false`
- `duration_threshold_false_to_true`

If a per-direction threshold is omitted, the symmetric threshold is used.

### Example

```python
from boolstabilizer import BoolAttribute, BufferMode

attr = BoolAttribute(
    name="my_bool",
    initial_value=False,
    count_threshold=3,
    count_threshold_false_to_true=1,   # faster to turn on
    count_threshold_true_to_false=5,   # slower to turn off
    duration_threshold=0.5,
    buffer_mode=BufferMode.BOTH
)

attr.report(True)
print(attr.pending_count)
print(attr.pending_duration)
print(attr.buffer_mode)

# Update buffer mode dynamically
attr.buffer_mode = BufferMode.NONE
attr.report(True)  # immediate

```

## API Reference

### BoolStabilizer

| Method | Description |
|--------|-------------|
| `add_attribute(name, initial_value, ..., count_threshold_false_to_true, count_threshold_true_to_false, duration_threshold_false_to_true, duration_threshold_true_to_false)` | Add a new boolean attribute |
| `remove_attribute(name)` | Remove an attribute |
| `get_attribute(name)` | Get the BoolAttribute |
| `report(name, new_value)` | Report a new value |
| `get_value(name)` | Current stabilized value |
| `get_all_values()` | Dictionary of all values |
| `reset_all()` | Reset all attributes |

#### Default Threshold Properties

The following defaults apply to newly added attributes:

| Property | Description |
|----------|-------------|
| `count_threshold` | Symmetric count threshold |
| `duration_threshold` | Symmetric duration threshold |
| `count_threshold_false_to_true` | Per-direction threshold (optional) |
| `count_threshold_true_to_false` | Per-direction threshold (optional) |
| `duration_threshold_false_to_true` | Per-direction threshold (optional) |
| `duration_threshold_true_to_false` | Per-direction threshold (optional) |
| `buffer_mode` | Default buffer mode |

### BoolAttribute

| Property | Description |
|----------|-------------|
| `name` | Attribute name |
| `value` | Current stabilized value |
| `pending_value` | Pending transition value |
| `pending_count` | Count of repeated reports |
| `pending_duration` | Duration in seconds of consistent reports |
| `count_threshold` | Symmetric count threshold |
| `duration_threshold` | Symmetric duration threshold |
| `count_threshold_false_to_true` | Optional per-direction threshold |
| `count_threshold_true_to_false` | Optional per-direction threshold |
| `duration_threshold_false_to_true` | Optional per-direction duration |
| `duration_threshold_true_to_false` | Optional per-direction duration |
| `buffer_mode` | Buffer mode (can be changed dynamically) |

| Method | Description |
|--------|-------------|
| `report(value)` | Report a new boolean value |
| `reset(new_value=None)` | Reset pending state (and optionally force value) |

## License

MIT License - see [LICENSE](LICENSE) for details.
