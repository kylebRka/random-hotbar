"""Behavior checks that never send real keyboard events."""
import random
import threading
import unittest
from unittest.mock import Mock, patch

from random_hotbar.config import RunConfig
from random_hotbar.runner import HotbarRunner
from random_hotbar.selection import choose_key


class SelectionTests(unittest.TestCase):
    def test_only_nine_minecraft_slots(self):
        self.assertEqual(RunConfig().keys, tuple("123456789"))
        for kwargs in ({"slots": 10}, {"priority_key": "0"}, {"priority_key": "10"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                RunConfig(**kwargs)

    def test_priority_must_be_in_range(self):
        with self.assertRaises(ValueError):
            RunConfig(slots=3, bias=True, priority_key="9")

    def test_probability_extremes(self):
        rng = random.Random(123)
        for chance in (0, 100):
            config = RunConfig(bias=True, priority_chance=chance)
            result = [choose_key(config, rng) for _ in range(100)]
            self.assertEqual("1" in result, chance == 100)
            if chance == 100:
                self.assertEqual(set(result), {"1"})

    def test_distribution_and_range(self):
        rng = random.Random(31)
        config = RunConfig(slots=4, bias=True, priority_key="3", priority_chance=40)
        result = [choose_key(config, rng) for _ in range(20000)]
        self.assertEqual(set(result), set("1234"))
        self.assertAlmostEqual(result.count("3") / len(result), .4, delta=.015)
        for key in "124":
            self.assertAlmostEqual(result.count(key) / len(result), .2, delta=.015)

    def test_invalid_settings(self):
        for kwargs in ({"slots": 1}, {"slots": 11}, {"priority_chance": -1},
                       {"priority_chance": 101}, {"start_delay": -1},
                       {"speed": "unknown"}, {"priority_key": "11"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                RunConfig(**kwargs)


class RunnerTests(unittest.TestCase):
    def wait_for_stop(self, runner):
        while True:
            event, value = runner.events.get(timeout=2)
            if event == "stopped":
                runner._thread.join(timeout=2)
                self.assertFalse(runner.running)
                return

    def test_cancel_countdown_without_press(self):
        backend = Mock()
        runner = HotbarRunner()
        self.assertTrue(runner.start(RunConfig(start_delay=30), backend))
        self.assertFalse(runner.start(RunConfig(), backend))
        runner.stop()
        self.wait_for_stop(runner)
        backend.press.assert_not_called()
        self.assertTrue(runner.start(RunConfig(start_delay=30), backend))
        runner.stop()
        self.wait_for_stop(runner)

    def test_stop_cannot_restart_held_key(self):
        entered = threading.Event()
        release = threading.Event()
        backend = Mock()

        def press(key):
            entered.set()
            release.wait(2)

        backend.press.side_effect = press
        runner = HotbarRunner()
        runner.start(RunConfig(start_delay=0), backend)
        self.assertTrue(entered.wait(2))
        runner.stop()
        try:
            self.assertFalse(runner.start(RunConfig(start_delay=0), backend))
        finally:
            release.set()
        self.wait_for_stop(runner)
        self.assertEqual(backend.press.call_count, 1)

    def test_backend_error_is_reported_and_worker_stops(self):
        runner = HotbarRunner()
        backend = Mock()
        backend.press.side_effect = RuntimeError("test failure")
        runner.start(RunConfig(start_delay=0), backend)
        runner._thread.join(timeout=2)
        events = []
        while not runner.events.empty():
            events.append(runner.events.get_nowait())
        self.assertIn(("error", "test failure"), events)
        self.assertIn(("stopped", None), events)
        self.assertFalse(runner.running)


class MacBackendTests(unittest.TestCase):
    def test_permission_denial_is_explained(self):
        from random_hotbar.backends.macos import MacOSKeyboard
        quartz = Mock()
        quartz.CGPreflightPostEventAccess.return_value = False
        with patch.dict("sys.modules", {"Quartz": quartz}):
            with self.assertRaisesRegex(RuntimeError, "Универсальный доступ"):
                MacOSKeyboard()

    def test_key_is_released_if_hold_fails(self):
        from random_hotbar.backends.macos import MacOSKeyboard
        quartz = Mock()
        keyboard = object.__new__(MacOSKeyboard)
        keyboard.quartz = quartz
        quartz.CGEventCreateKeyboardEvent.side_effect = ["down", "up"]
        with patch("random_hotbar.backends.macos.time.sleep", side_effect=RuntimeError("interrupted")):
            with self.assertRaises(RuntimeError):
                keyboard.press("9")
        self.assertEqual(quartz.CGEventPost.call_args.args[1], "up")
        self.assertEqual(quartz.CGEventCreateKeyboardEvent.call_args.args, (None, 25, False))


if __name__ == "__main__":
    unittest.main()
