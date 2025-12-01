"""Tests for BoolAttribute class."""

import time
import unittest

from boolstabilizer import BoolAttribute


class TestBoolAttributeInit(unittest.TestCase):
    """Test BoolAttribute initialization."""
    
    def test_default_initialization(self):
        """Test default initialization values."""
        attr = BoolAttribute("test")
        self.assertEqual(attr.name, "test")
        self.assertFalse(attr.value)
        self.assertEqual(attr.count_threshold, 1)
        self.assertEqual(attr.duration_threshold, 0.0)
    
    def test_custom_initialization(self):
        """Test custom initialization values."""
        attr = BoolAttribute("custom", initial_value=True, count_threshold=5, duration_threshold=2.0)
        self.assertEqual(attr.name, "custom")
        self.assertTrue(attr.value)
        self.assertEqual(attr.count_threshold, 5)
        self.assertEqual(attr.duration_threshold, 2.0)
    
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
    
    def test_report_without_buffer(self):
        """Test reporting without buffer changes immediately."""
        attr = BoolAttribute("test", initial_value=False, count_threshold=10)
        result = attr.report(True, apply_buffer=False)
        self.assertTrue(result)
        self.assertTrue(attr.value)


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


if __name__ == "__main__":
    unittest.main()
