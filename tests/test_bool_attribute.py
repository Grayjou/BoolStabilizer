"""Tests for BoolAttribute class."""

import time
import unittest

from boolstabilizer import BoolAttribute, BufferMode


class TestBoolAttributeInit(unittest.TestCase):
    """Test BoolAttribute initialization."""
    
    def test_default_initialization(self):
        """Test default initialization values."""
        attr = BoolAttribute("test")
        self.assertEqual(attr.name, "test")
        self.assertFalse(attr.value)
        self.assertEqual(attr.count_threshold, 1)
        self.assertEqual(attr.duration_threshold, 0.0)
        self.assertEqual(attr.buffer_mode, BufferMode.BOTH)
    
    def test_custom_initialization(self):
        """Test custom initialization values."""
        attr = BoolAttribute(
            "custom",
            initial_value=True,
            count_threshold=5,
            duration_threshold=2.0,
            buffer_mode=BufferMode.TRUE_TO_FALSE
        )
        self.assertEqual(attr.name, "custom")
        self.assertTrue(attr.value)
        self.assertEqual(attr.count_threshold, 5)
        self.assertEqual(attr.duration_threshold, 2.0)
        self.assertEqual(attr.buffer_mode, BufferMode.TRUE_TO_FALSE)
    
    def test_invalid_count_threshold(self):
        """Test that invalid count_threshold raises ValueError."""
        with self.assertRaises(ValueError):
            BoolAttribute("test", count_threshold=0)
        with self.assertRaises(ValueError):
            BoolAttribute("test", count_threshold=-1)
    
    def test_invalid_duration_threshold(self):
        """Test that invalid duration_threshold raises ValueError."""
        with self.assertRaises(ValueError):
            BoolAttribute("test", duration_threshold=-1.0)


class TestBoolAttributeReport(unittest.TestCase):
    """Test BoolAttribute report functionality."""
    
    def test_report_same_value(self):
        """Test reporting the same value doesn't change anything."""
        attr = BoolAttribute("test", initial_value=False)
        result = attr.report(False)
        self.assertFalse(result)
        self.assertEqual(attr.pending_count, 0)
    
    def test_report_different_value_count_threshold_1(self):
        """Test reporting different value with count_threshold=1 changes immediately."""
        attr = BoolAttribute("test", initial_value=False, count_threshold=1)
        result = attr.report(True)
        self.assertTrue(result)
        self.assertTrue(attr.value)
    
    def test_report_different_value_count_threshold_greater_than_1(self):
        """Test reporting different value with higher count_threshold requires multiple reports."""
        attr = BoolAttribute("test", initial_value=False, count_threshold=3)
        
        # First report - should not change yet
        result = attr.report(True)
        self.assertFalse(result)
        self.assertEqual(attr.pending_count, 1)
        
        # Second report - should not change yet
        result = attr.report(True)
        self.assertFalse(result)
        self.assertEqual(attr.pending_count, 2)
        
        # Third report - should change now
        result = attr.report(True)
        self.assertTrue(result)
        self.assertTrue(attr.value)
        self.assertEqual(attr.pending_count, 0)
    
    def test_report_resets_pending_on_original_value(self):
        """Test that reporting the original value resets pending state."""
        attr = BoolAttribute("test", initial_value=False, count_threshold=5)
        
        # Report True twice
        attr.report(True)
        attr.report(True)
        self.assertEqual(attr.pending_count, 2)
        
        # Report False (original) - should reset
        attr.report(False)
        self.assertEqual(attr.pending_count, 0)
        self.assertIsNone(attr.pending_value)


class TestBoolAttributeBufferMode(unittest.TestCase):
    """Test BoolAttribute buffer mode functionality."""
    
    def test_buffer_mode_both(self):
        """Test BufferMode.BOTH applies buffering in both directions."""
        attr = BoolAttribute("test", initial_value=False, count_threshold=3, buffer_mode=BufferMode.BOTH)
        
        # False to True - should be buffered
        attr.report(True)
        attr.report(True)
        self.assertFalse(attr.value)  # Not changed yet
        attr.report(True)
        self.assertTrue(attr.value)  # Changed after 3 reports
        
        # True to False - should also be buffered
        attr.report(False)
        attr.report(False)
        self.assertTrue(attr.value)  # Not changed yet
        attr.report(False)
        self.assertFalse(attr.value)  # Changed after 3 reports
    
    def test_buffer_mode_true_to_false(self):
        """Test BufferMode.TRUE_TO_FALSE only buffers true→false transitions."""
        attr = BoolAttribute("test", initial_value=False, count_threshold=3, buffer_mode=BufferMode.TRUE_TO_FALSE)
        
        # False to True - should NOT be buffered (immediate change)
        result = attr.report(True)
        self.assertTrue(result)  # Changed immediately
        
        # True to False - should be buffered
        attr.report(False)
        attr.report(False)
        self.assertTrue(attr.value)  # Not changed yet
        attr.report(False)
        self.assertFalse(attr.value)  # Changed after 3 reports
    
    def test_buffer_mode_false_to_true(self):
        """Test BufferMode.FALSE_TO_TRUE only buffers false→true transitions."""
        attr = BoolAttribute("test", initial_value=True, count_threshold=3, buffer_mode=BufferMode.FALSE_TO_TRUE)
        
        # True to False - should NOT be buffered (immediate change)
        result = attr.report(False)
        self.assertFalse(result)  # Changed immediately
        
        # False to True - should be buffered
        attr.report(True)
        attr.report(True)
        self.assertFalse(attr.value)  # Not changed yet
        attr.report(True)
        self.assertTrue(attr.value)  # Changed after 3 reports
    
    def test_buffer_mode_none(self):
        """Test BufferMode.NONE never applies buffering."""
        attr = BoolAttribute("test", initial_value=False, count_threshold=3, buffer_mode=BufferMode.NONE)
        
        # False to True - immediate change
        result = attr.report(True)
        self.assertTrue(result)
        
        # True to False - immediate change
        result = attr.report(False)
        self.assertFalse(result)
    
    def test_buffer_mode_setter(self):
        """Test setting buffer_mode after initialization."""
        attr = BoolAttribute("test", buffer_mode=BufferMode.BOTH)
        self.assertEqual(attr.buffer_mode, BufferMode.BOTH)
        
        attr.buffer_mode = BufferMode.NONE
        self.assertEqual(attr.buffer_mode, BufferMode.NONE)


class TestBoolAttributeDurationThreshold(unittest.TestCase):
    """Test BoolAttribute duration threshold functionality."""
    
    def test_duration_threshold_not_met(self):
        """Test that value doesn't change if duration threshold not met."""
        attr = BoolAttribute("test", initial_value=False, count_threshold=1, duration_threshold=0.5)
        
        # Report True - count is met but duration is not
        result = attr.report(True)
        self.assertFalse(result)
        self.assertTrue(attr.pending_duration < 0.5)
    
    def test_duration_threshold_met(self):
        """Test that value changes when duration threshold is met."""
        attr = BoolAttribute("test", initial_value=False, count_threshold=1, duration_threshold=0.1)
        
        # First report - starts the timer
        attr.report(True)
        self.assertFalse(attr.value)
        
        # Wait for duration threshold
        time.sleep(0.15)
        
        # Second report - should now meet both thresholds
        result = attr.report(True)
        self.assertTrue(result)
        self.assertTrue(attr.value)


class TestBoolAttributeReset(unittest.TestCase):
    """Test BoolAttribute reset functionality."""
    
    def test_reset_clears_pending(self):
        """Test that reset clears pending state."""
        attr = BoolAttribute("test", initial_value=False, count_threshold=5)
        attr.report(True)
        attr.report(True)
        
        attr.reset()
        self.assertEqual(attr.pending_count, 0)
        self.assertIsNone(attr.pending_value)
        self.assertFalse(attr.value)  # Value unchanged
    
    def test_reset_with_new_value(self):
        """Test that reset with new_value changes the value."""
        attr = BoolAttribute("test", initial_value=False)
        attr.reset(new_value=True)
        self.assertTrue(attr.value)


class TestBoolAttributeRepr(unittest.TestCase):
    """Test BoolAttribute string representation."""
    
    def test_repr(self):
        """Test __repr__ method."""
        attr = BoolAttribute("test", initial_value=True, count_threshold=3, duration_threshold=1.5)
        repr_str = repr(attr)
        self.assertIn("test", repr_str)
        self.assertIn("True", repr_str)
        self.assertIn("3", repr_str)
        self.assertIn("1.5", repr_str)
        self.assertIn("buffer_mode", repr_str)


if __name__ == "__main__":
    unittest.main()
