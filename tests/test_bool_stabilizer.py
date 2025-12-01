"""Tests for BoolStabilizer class."""

import time
import unittest

from boolstabilizer import BoolStabilizer, BufferMode


class TestBoolStabilizerInit(unittest.TestCase):
    """Test BoolStabilizer initialization."""
    
    def test_default_initialization(self):
        """Test default initialization values."""
        stabilizer = BoolStabilizer()
        self.assertEqual(stabilizer.count_threshold, 1)
        self.assertEqual(stabilizer.duration_threshold, 0.0)
        self.assertEqual(stabilizer.buffer_mode, BufferMode.BOTH)
        self.assertEqual(len(stabilizer), 0)
    
    def test_custom_initialization(self):
        """Test custom initialization values."""
        stabilizer = BoolStabilizer(
            count_threshold=5,
            duration_threshold=2.0,
            buffer_mode=BufferMode.TRUE_TO_FALSE
        )
        self.assertEqual(stabilizer.count_threshold, 5)
        self.assertEqual(stabilizer.duration_threshold, 2.0)
        self.assertEqual(stabilizer.buffer_mode, BufferMode.TRUE_TO_FALSE)
    
    def test_invalid_count_threshold(self):
        """Test that invalid count_threshold raises ValueError."""
        with self.assertRaises(ValueError):
            BoolStabilizer(count_threshold=0)
    
    def test_invalid_duration_threshold(self):
        """Test that invalid duration_threshold raises ValueError."""
        with self.assertRaises(ValueError):
            BoolStabilizer(duration_threshold=-1.0)


class TestBoolStabilizerAttributes(unittest.TestCase):
    """Test BoolStabilizer attribute management."""
    
    def test_add_attribute(self):
        """Test adding an attribute."""
        stabilizer = BoolStabilizer()
        attr = stabilizer.add_attribute("test")
        
        self.assertIn("test", stabilizer)
        self.assertEqual(len(stabilizer), 1)
        self.assertFalse(attr.value)
    
    def test_add_attribute_with_custom_values(self):
        """Test adding an attribute with custom values."""
        stabilizer = BoolStabilizer(count_threshold=10, duration_threshold=5.0)
        attr = stabilizer.add_attribute("test", initial_value=True, count_threshold=3, duration_threshold=1.0)
        
        self.assertTrue(attr.value)
        self.assertEqual(attr.count_threshold, 3)
        self.assertEqual(attr.duration_threshold, 1.0)
    
    def test_add_attribute_uses_defaults(self):
        """Test that add_attribute uses stabilizer defaults when not specified."""
        stabilizer = BoolStabilizer(count_threshold=5, duration_threshold=2.0)
        attr = stabilizer.add_attribute("test")
        
        self.assertEqual(attr.count_threshold, 5)
        self.assertEqual(attr.duration_threshold, 2.0)
    
    def test_add_duplicate_attribute_raises(self):
        """Test that adding duplicate attribute raises ValueError."""
        stabilizer = BoolStabilizer()
        stabilizer.add_attribute("test")
        
        with self.assertRaises(ValueError):
            stabilizer.add_attribute("test")
    
    def test_remove_attribute(self):
        """Test removing an attribute."""
        stabilizer = BoolStabilizer()
        stabilizer.add_attribute("test")
        
        result = stabilizer.remove_attribute("test")
        self.assertTrue(result)
        self.assertNotIn("test", stabilizer)
        self.assertEqual(len(stabilizer), 0)
    
    def test_remove_nonexistent_attribute(self):
        """Test removing a nonexistent attribute returns False."""
        stabilizer = BoolStabilizer()
        result = stabilizer.remove_attribute("nonexistent")
        self.assertFalse(result)
    
    def test_get_attribute(self):
        """Test getting an attribute."""
        stabilizer = BoolStabilizer()
        added = stabilizer.add_attribute("test")
        retrieved = stabilizer.get_attribute("test")
        
        self.assertIs(retrieved, added)
    
    def test_get_nonexistent_attribute(self):
        """Test getting a nonexistent attribute returns None."""
        stabilizer = BoolStabilizer()
        result = stabilizer.get_attribute("nonexistent")
        self.assertIsNone(result)


class TestBoolStabilizerReport(unittest.TestCase):
    """Test BoolStabilizer report functionality."""
    
    def test_report_basic(self):
        """Test basic report functionality."""
        stabilizer = BoolStabilizer(count_threshold=1)
        stabilizer.add_attribute("test", initial_value=False)
        
        result = stabilizer.report("test", True)
        self.assertTrue(result)
        self.assertTrue(stabilizer.get_value("test"))
    
    def test_report_nonexistent_attribute_raises(self):
        """Test reporting to nonexistent attribute raises KeyError."""
        stabilizer = BoolStabilizer()
        
        with self.assertRaises(KeyError):
            stabilizer.report("nonexistent", True)
    
    def test_report_with_count_threshold(self):
        """Test report respects count threshold."""
        stabilizer = BoolStabilizer(count_threshold=3)
        stabilizer.add_attribute("test", initial_value=False)
        
        # First two reports should not change
        self.assertFalse(stabilizer.report("test", True))
        self.assertFalse(stabilizer.report("test", True))
        
        # Third report should change
        self.assertTrue(stabilizer.report("test", True))


class TestBoolStabilizerBufferMode(unittest.TestCase):
    """Test BoolStabilizer buffer mode functionality."""
    
    def test_buffer_mode_both(self):
        """Test BufferMode.BOTH applies buffering in both directions."""
        stabilizer = BoolStabilizer(count_threshold=3, buffer_mode=BufferMode.BOTH)
        stabilizer.add_attribute("test", initial_value=False)
        
        # False to True - should be buffered
        stabilizer.report("test", True)
        stabilizer.report("test", True)
        self.assertFalse(stabilizer.get_value("test"))  # Not changed yet
        stabilizer.report("test", True)
        self.assertTrue(stabilizer.get_value("test"))  # Changed after 3 reports
        
        # True to False - should also be buffered
        stabilizer.report("test", False)
        stabilizer.report("test", False)
        self.assertTrue(stabilizer.get_value("test"))  # Not changed yet
        stabilizer.report("test", False)
        self.assertFalse(stabilizer.get_value("test"))  # Changed after 3 reports
    
    def test_buffer_mode_true_to_false(self):
        """Test BufferMode.TRUE_TO_FALSE only buffers true→false transitions."""
        stabilizer = BoolStabilizer(count_threshold=3, buffer_mode=BufferMode.TRUE_TO_FALSE)
        stabilizer.add_attribute("test", initial_value=False)
        
        # False to True - should NOT be buffered (immediate change)
        result = stabilizer.report("test", True)
        self.assertTrue(result)  # Changed immediately
        
        # True to False - should be buffered
        stabilizer.report("test", False)
        stabilizer.report("test", False)
        self.assertTrue(stabilizer.get_value("test"))  # Not changed yet
        stabilizer.report("test", False)
        self.assertFalse(stabilizer.get_value("test"))  # Changed after 3 reports
    
    def test_buffer_mode_false_to_true(self):
        """Test BufferMode.FALSE_TO_TRUE only buffers false→true transitions."""
        stabilizer = BoolStabilizer(count_threshold=3, buffer_mode=BufferMode.FALSE_TO_TRUE)
        stabilizer.add_attribute("test", initial_value=True)
        
        # True to False - should NOT be buffered (immediate change)
        result = stabilizer.report("test", False)
        self.assertFalse(result)  # Changed immediately
        
        # False to True - should be buffered
        stabilizer.report("test", True)
        stabilizer.report("test", True)
        self.assertFalse(stabilizer.get_value("test"))  # Not changed yet
        stabilizer.report("test", True)
        self.assertTrue(stabilizer.get_value("test"))  # Changed after 3 reports
    
    def test_buffer_mode_none(self):
        """Test BufferMode.NONE never applies buffering."""
        stabilizer = BoolStabilizer(count_threshold=3, buffer_mode=BufferMode.NONE)
        stabilizer.add_attribute("test", initial_value=False)
        
        # False to True - immediate change
        result = stabilizer.report("test", True)
        self.assertTrue(result)
        
        # True to False - immediate change
        result = stabilizer.report("test", False)
        self.assertFalse(result)
    
    def test_buffer_mode_setter(self):
        """Test setting buffer_mode after initialization."""
        stabilizer = BoolStabilizer(buffer_mode=BufferMode.BOTH)
        self.assertEqual(stabilizer.buffer_mode, BufferMode.BOTH)
        
        stabilizer.buffer_mode = BufferMode.NONE
        self.assertEqual(stabilizer.buffer_mode, BufferMode.NONE)


class TestBoolStabilizerValues(unittest.TestCase):
    """Test BoolStabilizer value retrieval."""
    
    def test_get_value(self):
        """Test get_value method."""
        stabilizer = BoolStabilizer()
        stabilizer.add_attribute("test", initial_value=True)
        
        self.assertTrue(stabilizer.get_value("test"))
    
    def test_get_value_nonexistent_raises(self):
        """Test get_value for nonexistent attribute raises KeyError."""
        stabilizer = BoolStabilizer()
        
        with self.assertRaises(KeyError):
            stabilizer.get_value("nonexistent")
    
    def test_get_all_values(self):
        """Test get_all_values method."""
        stabilizer = BoolStabilizer()
        stabilizer.add_attribute("a", initial_value=True)
        stabilizer.add_attribute("b", initial_value=False)
        stabilizer.add_attribute("c", initial_value=True)
        
        values = stabilizer.get_all_values()
        self.assertEqual(values, {"a": True, "b": False, "c": True})
    
    def test_indexing(self):
        """Test __getitem__ method."""
        stabilizer = BoolStabilizer()
        stabilizer.add_attribute("test", initial_value=True)
        
        self.assertTrue(stabilizer["test"])


class TestBoolStabilizerIterator(unittest.TestCase):
    """Test BoolStabilizer iteration."""
    
    def test_iteration(self):
        """Test iterating over stabilizer yields attribute names."""
        stabilizer = BoolStabilizer()
        stabilizer.add_attribute("a")
        stabilizer.add_attribute("b")
        stabilizer.add_attribute("c")
        
        names = list(stabilizer)
        self.assertEqual(set(names), {"a", "b", "c"})
    
    def test_contains(self):
        """Test __contains__ method."""
        stabilizer = BoolStabilizer()
        stabilizer.add_attribute("test")
        
        self.assertIn("test", stabilizer)
        self.assertNotIn("other", stabilizer)


class TestBoolStabilizerReset(unittest.TestCase):
    """Test BoolStabilizer reset functionality."""
    
    def test_reset_all(self):
        """Test reset_all clears all pending states."""
        stabilizer = BoolStabilizer(count_threshold=5)
        stabilizer.add_attribute("a", initial_value=False)
        stabilizer.add_attribute("b", initial_value=True)
        
        # Build up some pending state
        stabilizer.report("a", True)
        stabilizer.report("a", True)
        stabilizer.report("b", False)
        
        attr_a = stabilizer.get_attribute("a")
        attr_b = stabilizer.get_attribute("b")
        
        self.assertEqual(attr_a.pending_count, 2)
        self.assertEqual(attr_b.pending_count, 1)
        
        stabilizer.reset_all()
        
        self.assertEqual(attr_a.pending_count, 0)
        self.assertEqual(attr_b.pending_count, 0)


class TestBoolStabilizerRepr(unittest.TestCase):
    """Test BoolStabilizer string representation."""
    
    def test_repr(self):
        """Test __repr__ method."""
        stabilizer = BoolStabilizer(count_threshold=3, duration_threshold=1.5)
        stabilizer.add_attribute("test")
        
        repr_str = repr(stabilizer)
        self.assertIn("3", repr_str)
        self.assertIn("1.5", repr_str)
        self.assertIn("test", repr_str)


if __name__ == "__main__":
    unittest.main()
