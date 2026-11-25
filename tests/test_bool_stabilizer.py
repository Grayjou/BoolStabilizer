"""Deterministic integration tests for BoolStabilizer."""

import math
import unittest

from boolstabilizer import BoolStabilizer, BufferMode

from .test_bool_attribute import ManualClock


class TestManagerValidationAndInheritance(unittest.TestCase):
    def test_manager_validates_all_thresholds_and_modes(self):
        for keyword, value in (
            ("count_threshold", True),
            ("count_threshold_true_to_false", 0),
            ("duration_threshold", math.inf),
            ("duration_threshold_false_to_true", True),
            ("buffer_mode", "both"),
        ):
            with self.subTest(keyword=keyword), self.assertRaises((TypeError, ValueError)):
                BoolStabilizer(**{keyword: value})

    def test_directional_precedence_and_explicit_none(self):
        stabilizer = BoolStabilizer(
            count_threshold=5,
            count_threshold_true_to_false=3,
            duration_threshold=9,
            duration_threshold_true_to_false=7,
        )
        inherited = stabilizer.add_attribute("inherited", count_threshold=2, duration_threshold=1)
        disabled = stabilizer.add_attribute(
            "disabled",
            count_threshold=2,
            duration_threshold=1,
            count_threshold_true_to_false=None,
            duration_threshold_true_to_false=None,
        )
        overridden = stabilizer.add_attribute(
            "overridden",
            count_threshold_true_to_false=4,
            duration_threshold_true_to_false=6,
        )
        self.assertEqual(inherited.get_effective_thresholds(True, False).count_threshold, 3)
        self.assertEqual(inherited.get_effective_thresholds(True, False).duration_threshold, 7)
        self.assertEqual(disabled.get_effective_thresholds(True, False).count_threshold, 2)
        self.assertEqual(disabled.get_effective_thresholds(True, False).duration_threshold, 1)
        self.assertEqual(overridden.get_effective_thresholds(True, False).count_threshold, 4)
        self.assertEqual(overridden.get_effective_thresholds(True, False).duration_threshold, 6)

    def test_manager_clock_is_inherited_unless_attribute_overrides_it(self):
        manager_clock = ManualClock()
        attribute_clock = ManualClock()
        stabilizer = BoolStabilizer(duration_threshold=2, clock=manager_clock)
        inherited = stabilizer.add_attribute("inherited")
        overridden = stabilizer.add_attribute("overridden", clock=attribute_clock)
        inherited.report(True)
        overridden.report(True)
        manager_clock.advance(2)
        attribute_clock.advance(1)
        self.assertTrue(inherited.report(True))
        self.assertFalse(overridden.report(True))

    def test_defaults_are_copied_when_attribute_is_created(self):
        stabilizer = BoolStabilizer(buffer_mode=BufferMode.BOTH)
        existing = stabilizer.add_attribute("existing")
        stabilizer.buffer_mode = BufferMode.NONE
        self.assertEqual(existing.buffer_mode, BufferMode.BOTH)
        self.assertEqual(stabilizer.add_attribute("new").buffer_mode, BufferMode.NONE)


class TestManagerOperations(unittest.TestCase):
    def test_result_and_update_are_available_through_manager(self):
        clock = ManualClock()
        stabilizer = BoolStabilizer(count_threshold=2, duration_threshold=5, clock=clock)
        stabilizer.add_attribute("a")
        self.assertFalse(stabilizer.report_with_result("a", True).changed)
        clock.advance(5)
        self.assertFalse(stabilizer.update_with_result("a").changed)
        self.assertTrue(stabilizer.report_with_result("a", True).rose)

    def test_attributes_are_independent_and_reset_all_only_clears_pending(self):
        stabilizer = BoolStabilizer(count_threshold=2)
        a = stabilizer.add_attribute("a")
        b = stabilizer.add_attribute("b", initial_value=True)
        stabilizer.report("a", True)
        stabilizer.report("b", False)
        stabilizer.reset_all()
        self.assertEqual((a.value, a.pending_count), (False, 0))
        self.assertEqual((b.value, b.pending_count), (True, 0))

    def test_missing_name_errors_remain_key_errors(self):
        stabilizer = BoolStabilizer()
        with self.assertRaises(KeyError):
            stabilizer.report("missing", True)
        with self.assertRaises(KeyError):
            stabilizer.update("missing")


class TestTwitchRegression(unittest.TestCase):
    def test_temporary_outage_does_not_start_a_new_stream_session(self):
        clock = ManualClock()
        stream = BoolStabilizer(
            buffer_mode=BufferMode.TRUE_TO_FALSE,
            duration_threshold_true_to_false=60,
            clock=clock,
        )
        stream.add_attribute("stream", initial_value=False)
        notifications = []

        def report(at, online):
            clock.now = at
            result = stream.report_with_result("stream", online)
            if result.rose:
                notifications.append(at)
            return result.value

        self.assertTrue(report(0, True))
        self.assertTrue(report(100, False))
        self.assertTrue(report(110, True))
        self.assertTrue(report(200, False))
        self.assertTrue(report(230, False))
        self.assertFalse(report(260, False))
        self.assertTrue(report(300, True))
        self.assertEqual(notifications, [0, 300])

    def test_separate_short_outages_do_not_accumulate_duration(self):
        clock = ManualClock()
        stream = BoolStabilizer(
            buffer_mode=BufferMode.TRUE_TO_FALSE,
            duration_threshold_true_to_false=60,
            clock=clock,
        )
        attribute = stream.add_attribute("stream", initial_value=True)
        for start in (0, 100, 200):
            clock.now = start
            stream.report("stream", False)
            clock.advance(59)
            self.assertTrue(stream.report("stream", True))
            self.assertIsNone(attribute.pending_value)
        self.assertTrue(attribute.value)


if __name__ == "__main__":
    unittest.main()
