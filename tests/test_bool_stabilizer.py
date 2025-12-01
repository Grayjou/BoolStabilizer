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
        self.assertEqual(attr.buffer_mode, BufferMode.BOTH)
    
    def test_add_attribute_with_custom_values(self):
        """Test adding an attribute with custom values."""
        stabilizer = BoolStabilizer(count_threshold=10, duration_threshold=5.0)
        attr = stabilizer.add_attribute(
            "test",
            initial_value=True,
            count_threshold=3,
            duration_threshold=1.0,
            buffer_mode=BufferMode.TRUE_TO_FALSE
        )
        
        self.assertTrue(attr.value)
        self.assertEqual(attr.count_threshold, 3)
        self.assertEqual(attr.duration_threshold, 1.0)
        self.assertEqual(attr.buffer_mode, BufferMode.TRUE_TO_FALSE)
    
    def test_add_attribute_uses_defaults(self):
        """Test that add_attribute uses stabilizer defaults when not specified."""
        stabilizer = BoolStabilizer(
            count_threshold=5,
            duration_threshold=2.0,
            buffer_mode=BufferMode.FALSE_TO_TRUE
        )
        attr = stabilizer.add_attribute("test")
        
        self.assertEqual(attr.count_threshold, 5)
        self.assertEqual(attr.duration_threshold, 2.0)
        self.assertEqual(attr.buffer_mode, BufferMode.FALSE_TO_TRUE)
    
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


class TestBoolStabilizerBufferModePerAttribute(unittest.TestCase):
    """Test BoolStabilizer with per-attribute buffer modes."""
    
    def test_different_buffer_modes_per_attribute(self):
        """Test that different attributes can have different buffer modes."""
        stabilizer = BoolStabilizer(count_threshold=3)
        
        # Add attributes with different buffer modes
        stabilizer.add_attribute("buffered", initial_value=False, buffer_mode=BufferMode.BOTH)
        stabilizer.add_attribute("unbuffered", initial_value=False, buffer_mode=BufferMode.NONE)
        stabilizer.add_attribute("only_t2f", initial_value=False, buffer_mode=BufferMode.TRUE_TO_FALSE)
        
        # Buffered attribute needs 3 reports
        stabilizer.report("buffered", True)
        stabilizer.report("buffered", True)
        self.assertFalse(stabilizer.get_value("buffered"))
        stabilizer.report("buffered", True)
        self.assertTrue(stabilizer.get_value("buffered"))
        
        # Unbuffered attribute changes immediately
        result = stabilizer.report("unbuffered", True)
        self.assertTrue(result)
        
        # Only_t2f: False to True is immediate, True to False is buffered
        result = stabilizer.report("only_t2f", True)
        self.assertTrue(result)  # Immediate change
        
        stabilizer.report("only_t2f", False)
        stabilizer.report("only_t2f", False)
        self.assertTrue(stabilizer.get_value("only_t2f"))  # Not changed yet
        stabilizer.report("only_t2f", False)
        self.assertFalse(stabilizer.get_value("only_t2f"))  # Changed after 3 reports
    
    def test_attribute_buffer_mode_override(self):
        """Test that attribute buffer_mode can be changed after creation."""
        stabilizer = BoolStabilizer(count_threshold=3, buffer_mode=BufferMode.BOTH)
        attr = stabilizer.add_attribute("test", initial_value=False)
        
        # Initially uses stabilizer default (BOTH)
        self.assertEqual(attr.buffer_mode, BufferMode.BOTH)
        
        # Change to NONE - reports should now be immediate
        attr.buffer_mode = BufferMode.NONE
        result = stabilizer.report("test", True)
        self.assertTrue(result)  # Immediate change
    
    def test_buffer_mode_default_inheritance(self):
        """Test that new attributes inherit the stabilizer's default buffer_mode."""
        stabilizer = BoolStabilizer(buffer_mode=BufferMode.TRUE_TO_FALSE)
        attr = stabilizer.add_attribute("test")
        
        self.assertEqual(attr.buffer_mode, BufferMode.TRUE_TO_FALSE)
    
    def test_buffer_mode_setter_changes_default(self):
        """Test that changing stabilizer's buffer_mode affects new attributes."""
        stabilizer = BoolStabilizer(buffer_mode=BufferMode.BOTH)
        
        attr1 = stabilizer.add_attribute("attr1")
        self.assertEqual(attr1.buffer_mode, BufferMode.BOTH)
        
        stabilizer.buffer_mode = BufferMode.NONE
        attr2 = stabilizer.add_attribute("attr2")
        self.assertEqual(attr2.buffer_mode, BufferMode.NONE)
        
        # attr1 should still have its original buffer_mode
        self.assertEqual(attr1.buffer_mode, BufferMode.BOTH)


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


class TestBoolStabilizerPerDirectionThresholds(unittest.TestCase):
    """Test BoolStabilizer per-direction threshold functionality."""

    def test_init_with_per_direction_count_thresholds(self):
        """Test initialization with per-direction count thresholds."""
        stabilizer = BoolStabilizer(
            count_threshold=5,
            count_threshold_true_to_false=3,
            count_threshold_false_to_true=7,
        )
        self.assertEqual(stabilizer.count_threshold_true_to_false, 3)
        self.assertEqual(stabilizer.count_threshold_false_to_true, 7)

    def test_init_with_per_direction_duration_thresholds(self):
        """Test initialization with per-direction duration thresholds."""
        stabilizer = BoolStabilizer(
            duration_threshold=1.0,
            duration_threshold_true_to_false=0.5,
            duration_threshold_false_to_true=2.0,
        )
        self.assertEqual(stabilizer.duration_threshold_true_to_false, 0.5)
        self.assertEqual(stabilizer.duration_threshold_false_to_true, 2.0)

    def test_per_direction_properties_return_none_when_not_set(self):
        """Test that per-direction properties return None when not set."""
        stabilizer = BoolStabilizer()
        self.assertIsNone(stabilizer.count_threshold_true_to_false)
        self.assertIsNone(stabilizer.count_threshold_false_to_true)
        self.assertIsNone(stabilizer.duration_threshold_true_to_false)
        self.assertIsNone(stabilizer.duration_threshold_false_to_true)

    def test_add_attribute_inherits_per_direction_thresholds(self):
        """Test that add_attribute inherits per-direction thresholds from stabilizer."""
        stabilizer = BoolStabilizer(
            count_threshold=5,
            count_threshold_true_to_false=3,
            count_threshold_false_to_true=7,
            duration_threshold_true_to_false=0.5,
            duration_threshold_false_to_true=1.5,
        )
        attr = stabilizer.add_attribute("test")
        
        self.assertEqual(attr.count_threshold_true_to_false, 3)
        self.assertEqual(attr.count_threshold_false_to_true, 7)
        self.assertEqual(attr.duration_threshold_true_to_false, 0.5)
        self.assertEqual(attr.duration_threshold_false_to_true, 1.5)

    def test_add_attribute_can_override_per_direction_thresholds(self):
        """Test that add_attribute can override per-direction thresholds."""
        stabilizer = BoolStabilizer(
            count_threshold=5,
            count_threshold_true_to_false=3,
            count_threshold_false_to_true=7,
        )
        attr = stabilizer.add_attribute(
            "test",
            count_threshold_true_to_false=10,
            count_threshold_false_to_true=20,
        )
        
        self.assertEqual(attr.count_threshold_true_to_false, 10)
        self.assertEqual(attr.count_threshold_false_to_true, 20)

    def test_per_direction_thresholds_used_in_report(self):
        """Test that per-direction thresholds are actually used when reporting values."""
        stabilizer = BoolStabilizer(
            count_threshold=10,  # Default not used
            count_threshold_true_to_false=2,
            count_threshold_false_to_true=3,
        )
        stabilizer.add_attribute("test", initial_value=False)
        
        # False to True: needs 3 reports
        stabilizer.report("test", True)
        stabilizer.report("test", True)
        self.assertFalse(stabilizer.get_value("test"))  # Not changed (2 < 3)
        stabilizer.report("test", True)
        self.assertTrue(stabilizer.get_value("test"))  # Changed after 3

        # True to False: needs 2 reports
        stabilizer.report("test", False)
        self.assertTrue(stabilizer.get_value("test"))  # Not changed (1 < 2)
        stabilizer.report("test", False)
        self.assertFalse(stabilizer.get_value("test"))  # Changed after 2

    def test_mixed_per_direction_and_default_thresholds(self):
        """Test mixing per-direction thresholds with defaults."""
        stabilizer = BoolStabilizer(
            count_threshold=4,
            count_threshold_false_to_true=2,  # Override for false→true only
        )
        stabilizer.add_attribute("test", initial_value=False)
        
        # False to True: uses specific (2)
        stabilizer.report("test", True)
        self.assertFalse(stabilizer.get_value("test"))  # Not changed (1 < 2)
        stabilizer.report("test", True)
        self.assertTrue(stabilizer.get_value("test"))  # Changed after 2

        # True to False: uses default (4)
        stabilizer.report("test", False)
        stabilizer.report("test", False)
        stabilizer.report("test", False)
        self.assertTrue(stabilizer.get_value("test"))  # Not changed (3 < 4)
        stabilizer.report("test", False)
        self.assertFalse(stabilizer.get_value("test"))  # Changed after 4

    def test_attribute_override_with_none_uses_stabilizer_default(self):
        """Test that None override in add_attribute uses stabilizer default."""
        stabilizer = BoolStabilizer(
            count_threshold=5,
            count_threshold_true_to_false=3,
        )
        # Explicitly pass None - should use stabilizer default (3)
        attr = stabilizer.add_attribute(
            "test",
            count_threshold_true_to_false=None,
        )
        
        self.assertEqual(attr.count_threshold_true_to_false, 3)


if __name__ == "__main__":
    unittest.main()
