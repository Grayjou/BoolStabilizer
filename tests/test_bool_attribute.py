"""Deterministic tests for BoolAttribute."""

import math
import unittest

from boolstabilizer import BoolAttribute, BufferMode


class ManualClock:
    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class TestValidation(unittest.TestCase):
    def test_all_thresholds_validate_type_range_and_finiteness(self):
        invalid_counts = [0, -1, 1.5, True]
        invalid_durations = [-1, math.nan, math.inf, -math.inf, True, "1"]
        for value in invalid_counts:
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                BoolAttribute("a", count_threshold=value)
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                BoolAttribute("a", count_threshold_true_to_false=value)
        for value in invalid_durations:
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                BoolAttribute("a", duration_threshold=value)
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                BoolAttribute("a", duration_threshold_false_to_true=value)

    def test_boolean_and_mode_validation_does_not_modify_pending_state(self):
        clock = ManualClock()
        attr = BoolAttribute("a", count_threshold=2, clock=clock)
        attr.report(True)
        with self.assertRaises(TypeError):
            attr.report(1)
        self.assertEqual(attr.value, False)
        self.assertEqual(attr.pending_value, True)
        self.assertEqual(attr.pending_count, 1)
        with self.assertRaises(TypeError):
            attr.reset("true")
        self.assertEqual(attr.pending_count, 1)
        with self.assertRaises(TypeError):
            attr.buffer_mode = "none"
        self.assertEqual(attr.buffer_mode, BufferMode.BOTH)
        with self.assertRaises(TypeError):
            BoolAttribute("a", initial_value=0)

    def test_clock_must_be_callable_and_return_finite_number(self):
        with self.assertRaises(TypeError):
            BoolAttribute("a", clock=None)
        attr = BoolAttribute("a", clock=lambda: math.nan)
        with self.assertRaises(ValueError):
            attr.report(True)
        clock = ManualClock(-2)
        attr = BoolAttribute("a", duration_threshold=1, clock=clock)
        attr.report(True)
        clock.advance(1)
        self.assertTrue(attr.report(True))


class TestReportSemantics(unittest.TestCase):
    def test_count_and_duration_are_both_required_at_exact_boundaries(self):
        clock = ManualClock()
        attr = BoolAttribute("a", count_threshold=2, duration_threshold=5, clock=clock)
        self.assertFalse(attr.report(True))
        clock.advance(4.999)
        self.assertFalse(attr.report(True))  # Count is met, duration is not.
        self.assertEqual(attr.pending_count, 2)
        clock.advance(0.001)
        self.assertTrue(attr.report(True))  # Both are met exactly at five seconds.
        self.assertIsNone(attr.pending_value)

    def test_report_driven_duration_needs_another_observation(self):
        clock = ManualClock()
        attr = BoolAttribute("a", duration_threshold=10, clock=clock)
        attr.report(True)
        clock.advance(10)
        self.assertFalse(attr.value)
        self.assertTrue(attr.report(True))

    def test_update_evaluates_without_incrementing_count(self):
        clock = ManualClock()
        attr = BoolAttribute("a", count_threshold=2, duration_threshold=5, clock=clock)
        attr.report(True)
        clock.advance(5)
        result = attr.update_with_result()
        self.assertFalse(result.changed)
        self.assertEqual(attr.pending_count, 1)
        attr.report(True)
        self.assertTrue(attr.value)

    def test_matching_stabilized_report_cancels_pending_evidence(self):
        clock = ManualClock()
        attr = BoolAttribute("a", count_threshold=3, clock=clock)
        attr.report(True)
        attr.report(True)
        attr.report(False)
        self.assertIsNone(attr.pending_value)
        self.assertEqual(attr.pending_count, 0)
        self.assertEqual(attr.pending_duration, 0)

    def test_unbuffered_transition_is_immediate_and_has_no_pending_state(self):
        attr = BoolAttribute("a", count_threshold=9, buffer_mode=BufferMode.NONE)
        result = attr.report_with_result(True)
        self.assertTrue(result.changed)
        self.assertTrue(result.rose)
        self.assertFalse(result.fell)
        self.assertTrue(result.value)
        self.assertEqual(attr.pending_count, 0)

    def test_transition_result_is_emitted_once(self):
        attr = BoolAttribute("a")
        first = attr.report_with_result(True)
        second = attr.report_with_result(True)
        self.assertEqual((first.changed, first.rose, first.fell), (True, True, False))
        self.assertEqual((second.changed, second.rose, second.fell), (False, False, False))

    def test_multiple_reports_at_one_timestamp_satisfy_count_only(self):
        clock = ManualClock()
        attr = BoolAttribute("a", count_threshold=3, duration_threshold=1, clock=clock)
        attr.report(True)
        attr.report(True)
        self.assertFalse(attr.report(True))
        self.assertEqual(attr.pending_count, 3)
        clock.advance(1)
        self.assertTrue(attr.report(True))

    def test_backward_clock_is_clamped_to_last_operation_time(self):
        clock = ManualClock(10)
        attr = BoolAttribute("a", count_threshold=3, duration_threshold=3, clock=clock)
        attr.report(True)
        clock.advance(2)
        attr.report(True)
        clock.now = 7
        self.assertFalse(attr.report(True))
        self.assertEqual(attr.pending_duration, 2)
        clock.now = 13
        self.assertTrue(attr.report(True))


class TestConfigurationAndInspection(unittest.TestCase):
    def test_symmetric_properties_remain_configured_base_with_overrides(self):
        attr = BoolAttribute(
            "a",
            count_threshold=5,
            duration_threshold=4,
            count_threshold_false_to_true=2,
            duration_threshold_true_to_false=1,
        )
        self.assertEqual(attr.count_threshold, 5)
        self.assertEqual(attr.duration_threshold, 4)
        self.assertEqual(attr.get_effective_thresholds(False, True).count_threshold, 2)
        self.assertEqual(attr.get_effective_thresholds(True, False).duration_threshold, 1)
        with self.assertRaises(ValueError):
            attr.get_effective_thresholds(True, True)

    def test_snapshot_reports_progress_without_mutating_pending_evidence(self):
        clock = ManualClock()
        attr = BoolAttribute("a", count_threshold=4, duration_threshold=10, clock=clock)
        attr.report(True)
        clock.advance(5)
        snapshot = attr.pending_transition
        self.assertEqual(snapshot.pending_value, True)
        self.assertEqual(snapshot.pending_count, 1)
        self.assertEqual(snapshot.pending_duration, 5)
        self.assertEqual(snapshot.count_progress, 0.25)
        self.assertEqual(snapshot.duration_progress, 0.5)
        self.assertEqual(snapshot.progress, 0.25)
        self.assertEqual(attr.pending_count, 1)
        self.assertFalse(snapshot.eligible)

    def test_mode_change_clears_pending_only_when_changed(self):
        attr = BoolAttribute("a", count_threshold=3)
        attr.report(True)
        attr.buffer_mode = BufferMode.BOTH
        self.assertEqual(attr.pending_count, 1)
        attr.buffer_mode = BufferMode.NONE
        self.assertEqual(attr.pending_count, 0)
        self.assertFalse(attr.value)

    def test_reset_with_explicit_boolean_clears_pending(self):
        attr = BoolAttribute("a", count_threshold=3)
        attr.report(True)
        attr.reset(True)
        self.assertTrue(attr.value)
        self.assertIsNone(attr.pending_value)


if __name__ == "__main__":
    unittest.main()
