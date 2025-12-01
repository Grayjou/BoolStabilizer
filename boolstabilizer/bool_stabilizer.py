"""BoolStabilizer class for managing multiple BoolAttributes."""

from typing import Dict, Iterator, Optional

from .bool_attribute import BoolAttribute, BufferMode


class BoolStabilizer:
    """
    A container class for managing multiple BoolAttributes with configurable stabilization.
    
    This class provides a way to manage multiple boolean attributes that stabilize
    their values based on count and duration thresholds. Each attribute can have its
    own buffer_mode to control when stabilization is applied for that specific attribute.
    
    Attributes:
        count_threshold: Default count threshold for new attributes.
        duration_threshold: Default duration threshold for new attributes.
        buffer_mode: Default buffer mode for new attributes.
    """
    
    def __init__(
        self,
        count_threshold: int = 1,
        duration_threshold: float = 0.0,
        buffer_mode: BufferMode = BufferMode.BOTH
    ):
        """
        Initialize a BoolStabilizer.
        
        Args:
            count_threshold: Default number of reports needed before a value changes.
                           Must be at least 1. Defaults to 1.
            duration_threshold: Default duration in seconds before a value changes.
                              Defaults to 0.0.
            buffer_mode: Default buffer mode for new attributes. Defaults to BufferMode.BOTH.
        
        Raises:
            ValueError: If count_threshold is less than 1 or duration_threshold is negative.
        """
        if count_threshold < 1:
            raise ValueError("count_threshold must be at least 1")
        if duration_threshold < 0:
            raise ValueError("duration_threshold cannot be negative")
        
        self._count_threshold = count_threshold
        self._duration_threshold = duration_threshold
        self._buffer_mode = buffer_mode
        self._attributes: Dict[str, BoolAttribute] = {}
    
    @property
    def count_threshold(self) -> int:
        """Get the default count threshold."""
        return self._count_threshold
    
    @property
    def duration_threshold(self) -> float:
        """Get the default duration threshold."""
        return self._duration_threshold
    
    @property
    def buffer_mode(self) -> BufferMode:
        """Get the default buffer mode for new attributes."""
        return self._buffer_mode
    
    @buffer_mode.setter
    def buffer_mode(self, mode: BufferMode) -> None:
        """Set the default buffer mode for new attributes."""
        self._buffer_mode = mode
    
    def add_attribute(
        self,
        name: str,
        initial_value: bool = False,
        count_threshold: Optional[int] = None,
        duration_threshold: Optional[float] = None,
        buffer_mode: Optional[BufferMode] = None
    ) -> BoolAttribute:
        """
        Add a new BoolAttribute to the stabilizer.
        
        Args:
            name: The name identifier for the attribute.
            initial_value: The initial boolean value. Defaults to False.
            count_threshold: Count threshold for this attribute.
                           Uses stabilizer default if None.
            duration_threshold: Duration threshold for this attribute.
                              Uses stabilizer default if None.
            buffer_mode: Buffer mode for this attribute.
                        Uses stabilizer default if None.
        
        Returns:
            The created BoolAttribute.
        
        Raises:
            ValueError: If an attribute with the given name already exists.
        """
        if name in self._attributes:
            raise ValueError(f"Attribute '{name}' already exists")
        
        attr = BoolAttribute(
            name=name,
            initial_value=initial_value,
            count_threshold=count_threshold if count_threshold is not None else self._count_threshold,
            duration_threshold=duration_threshold if duration_threshold is not None else self._duration_threshold,
            buffer_mode=buffer_mode if buffer_mode is not None else self._buffer_mode
        )
        self._attributes[name] = attr
        return attr
    
    def remove_attribute(self, name: str) -> bool:
        """
        Remove an attribute from the stabilizer.
        
        Args:
            name: The name of the attribute to remove.
        
        Returns:
            True if the attribute was removed, False if it didn't exist.
        """
        if name in self._attributes:
            del self._attributes[name]
            return True
        return False
    
    def get_attribute(self, name: str) -> Optional[BoolAttribute]:
        """
        Get an attribute by name.
        
        Args:
            name: The name of the attribute.
        
        Returns:
            The BoolAttribute if found, None otherwise.
        """
        return self._attributes.get(name)
    
    def report(self, name: str, new_value: bool) -> bool:
        """
        Report a new value for an attribute.
        
        The buffering behavior depends on the attribute's buffer_mode setting:
        - BOTH: Always apply buffering
        - TRUE_TO_FALSE: Only buffer when transitioning from True to False
        - FALSE_TO_TRUE: Only buffer when transitioning from False to True
        - NONE: Never buffer (immediate changes)
        
        Args:
            name: The name of the attribute to update.
            new_value: The new boolean value being reported.
        
        Returns:
            The current stabilized value after processing the report.
        
        Raises:
            KeyError: If no attribute with the given name exists.
        """
        if name not in self._attributes:
            raise KeyError(f"Attribute '{name}' does not exist")
        
        return self._attributes[name].report(new_value)
    
    def get_value(self, name: str) -> bool:
        """
        Get the current stabilized value of an attribute.
        
        Args:
            name: The name of the attribute.
        
        Returns:
            The current stabilized boolean value.
        
        Raises:
            KeyError: If no attribute with the given name exists.
        """
        if name not in self._attributes:
            raise KeyError(f"Attribute '{name}' does not exist")
        return self._attributes[name].value
    
    def get_all_values(self) -> Dict[str, bool]:
        """
        Get all attribute values as a dictionary.
        
        Returns:
            A dictionary mapping attribute names to their current stabilized values.
        """
        return {name: attr.value for name, attr in self._attributes.items()}
    
    def reset_all(self) -> None:
        """Reset all attributes' pending states without changing their values."""
        for attr in self._attributes.values():
            attr.reset()
    
    def __len__(self) -> int:
        """Return the number of attributes in the stabilizer."""
        return len(self._attributes)
    
    def __contains__(self, name: str) -> bool:
        """Check if an attribute exists."""
        return name in self._attributes
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over attribute names."""
        return iter(self._attributes)
    
    def __getitem__(self, name: str) -> bool:
        """Get an attribute's value using indexing syntax."""
        return self.get_value(name)
    
    def __repr__(self) -> str:
        """Return a string representation of the stabilizer."""
        return (
            f"BoolStabilizer(count_threshold={self._count_threshold}, "
            f"duration_threshold={self._duration_threshold}, "
            f"buffer_mode={self._buffer_mode}, "
            f"attributes={list(self._attributes.keys())})"
        )
