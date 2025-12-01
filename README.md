# BoolStabilizer

A Python library for stabilizing boolean values based on configurable count and duration thresholds.

## Overview

BoolStabilizer provides classes that prevent boolean values from changing until certain conditions are met:
- **Count threshold**: The number of times a new value must be reported before it takes effect
- **Duration threshold**: How long a new value must be consistently reported before it takes effect
- **Buffer mode**: Control which transitions are buffered (true→false, false→true, or both)

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

For more direct control, use `BoolAttribute` directly:

```python
from boolstabilizer import BoolAttribute, BufferMode

# Create an attribute with custom thresholds and buffer mode
attr = BoolAttribute(
    name="my_bool",
    initial_value=False,
    count_threshold=5,
    duration_threshold=1.0,
    buffer_mode=BufferMode.BOTH
)

# Report values
attr.report(True)  # Start tracking
print(attr.pending_count)     # Number of times True has been reported
print(attr.pending_duration)  # How long True has been pending
print(attr.buffer_mode)       # Current buffer mode

# Change buffer mode at runtime
attr.buffer_mode = BufferMode.NONE
attr.report(True)  # Now changes immediately

# Reset pending state
attr.reset()
```

## API Reference

### BoolStabilizer

| Method | Description |
|--------|-------------|
| `add_attribute(name, initial_value, count_threshold, duration_threshold, buffer_mode)` | Add a new boolean attribute |
| `remove_attribute(name)` | Remove an attribute |
| `get_attribute(name)` | Get the BoolAttribute object |
| `report(name, new_value)` | Report a new value for an attribute |
| `get_value(name)` | Get the current stabilized value |
| `get_all_values()` | Get all values as a dictionary |
| `reset_all()` | Reset all pending states |

| Property | Description |
|----------|-------------|
| `count_threshold` | Default count threshold for new attributes |
| `duration_threshold` | Default duration threshold for new attributes |
| `buffer_mode` | Default buffer mode for new attributes |

### BoolAttribute

| Property | Description |
|----------|-------------|
| `name` | The attribute name |
| `value` | Current stabilized value |
| `count_threshold` | Required report count |
| `duration_threshold` | Required duration in seconds |
| `buffer_mode` | Buffer mode for this attribute (can be changed at runtime) |
| `pending_count` | Current pending report count |
| `pending_duration` | Current pending duration |
| `pending_value` | The pending value (or None) |

| Method | Description |
|--------|-------------|
| `report(new_value)` | Report a new value (respects buffer_mode) |
| `reset(new_value)` | Reset pending state, optionally set new value |

## License

MIT License - see [LICENSE](LICENSE) for details.
