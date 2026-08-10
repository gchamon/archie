import subprocess
import tempfile
import unittest
from pathlib import Path

from archie.privacy import (
    DunstClient,
    ShyModeController,
    ShyModeSettings,
    format_shy_mode_settings,
    load_shy_mode_settings,
    parse_share_active,
    save_shy_mode_settings,
)


class ShyModeSettingsTest(unittest.TestCase):
    def test_missing_configuration_uses_disabled_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = load_shy_mode_settings(Path(temp_dir) / "shy-mode.json")

        self.assertEqual(settings, ShyModeSettings())
        self.assertEqual(
            format_shy_mode_settings(settings),
            "enabled: off\nreplay-count: 10\nreplay-interval: 5s",
        )

    def test_round_trips_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "archie/shy-mode.json"
            expected = ShyModeSettings(True, replay_count=7, replay_interval=2.5)

            save_shy_mode_settings(expected, path)

            self.assertEqual(load_shy_mode_settings(path), expected)
            self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))

    def test_invalid_configuration_falls_back_safely(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "shy-mode.json"
            path.write_text("not json", encoding="utf-8")

            self.assertEqual(load_shy_mode_settings(path), ShyModeSettings())


class ShareDetectionTest(unittest.TestCase):
    def test_detects_only_the_managed_portal_node(self) -> None:
        self.assertTrue(
            parse_share_active(
                '[{"info":{"props":{"node.name":"xdg-desktop-portal-hyprland"}}}]'
            )
        )
        self.assertFalse(
            parse_share_active('[{"info":{"props":{"node.name":"OBS Studio"}}}]')
        )
        self.assertFalse(parse_share_active("invalid"))


class FakeDunst:
    def __init__(
        self,
        *,
        paused: bool = False,
        waiting: int = 0,
        history: int = 0,
        pop_results: list[bool] | None = None,
    ) -> None:
        self.paused = paused
        self.waiting = waiting
        self.history = history
        self.pop_results = list(pop_results or [])
        self.calls: list[tuple[str, bool | None]] = []

    def is_paused(self) -> bool:
        self.calls.append(("is_paused", None))
        return self.paused

    def set_paused(self, paused: bool) -> bool:
        self.calls.append(("set_paused", paused))
        self.paused = paused
        return True

    def waiting_count(self) -> int:
        self.calls.append(("waiting_count", None))
        return self.waiting

    def history_count(self) -> int:
        self.calls.append(("history_count", None))
        return self.history

    def history_pop(self) -> bool:
        self.calls.append(("history_pop", None))
        if self.pop_results:
            return self.pop_results.pop(0)
        return self.history > 0


class ShyModeControllerTest(unittest.TestCase):
    def make_controller(
        self,
        dunst: FakeDunst,
        settings: ShyModeSettings | None = None,
    ) -> ShyModeController:
        configured = settings or ShyModeSettings(enabled=True)
        return ShyModeController(dunst, settings_loader=lambda: configured)  # type: ignore[arg-type]

    def test_pauses_active_dunst_and_replays_missed_notifications_on_schedule(self) -> None:
        dunst = FakeDunst(history=3, pop_results=[True, True, True])
        controller = self.make_controller(
            dunst,
            ShyModeSettings(True, replay_count=2, replay_interval=5),
        )

        started = controller.poll(sharing=True, now=0)
        dunst.waiting = 3
        during = controller.poll(sharing=True, now=1)
        ended = controller.poll(sharing=False, now=2)
        waiting = controller.poll(sharing=False, now=6)
        finished = controller.poll(sharing=False, now=7)

        self.assertTrue(started.owns_pause)
        self.assertTrue(during.pending)
        self.assertTrue(ended.replaying)
        self.assertTrue(waiting.pending)
        self.assertFalse(finished.pending)
        self.assertEqual(
            [call for call in dunst.calls if call[0] == "set_paused"],
            [("set_paused", True), ("set_paused", False)],
        )
        self.assertEqual(
            [call for call in dunst.calls if call[0] == "history_pop"],
            [("history_pop", None), ("history_pop", None)],
        )

    def test_does_not_own_or_replay_a_preexisting_pause(self) -> None:
        dunst = FakeDunst(paused=True, waiting=2, history=2)
        controller = self.make_controller(dunst)

        started = controller.poll(sharing=True, now=0)
        dunst.waiting = 4
        ended = controller.poll(sharing=False, now=1)

        self.assertFalse(started.owns_pause)
        self.assertFalse(ended.pending)
        self.assertNotIn(("set_paused", False), dunst.calls)
        self.assertNotIn(("history_pop", None), dunst.calls)

    def test_replay_is_bounded_by_missed_count_and_available_history(self) -> None:
        dunst = FakeDunst(history=1, pop_results=[True])
        controller = self.make_controller(
            dunst,
            ShyModeSettings(True, replay_count=10, replay_interval=1),
        )

        controller.poll(sharing=True, now=0)
        dunst.waiting = 6
        state = controller.poll(sharing=False, now=1)

        self.assertFalse(state.pending)
        self.assertEqual(dunst.calls.count(("history_pop", None)), 1)

    def test_empty_or_failing_history_stops_replay_safely(self) -> None:
        for history, pop_results in ((0, []), (2, [False])):
            with self.subTest(history=history, pop_results=pop_results):
                dunst = FakeDunst(history=history, pop_results=pop_results)
                controller = self.make_controller(dunst)
                controller.poll(sharing=True, now=0)
                dunst.waiting = 2

                state = controller.poll(sharing=False, now=1)

                self.assertFalse(state.pending)
                self.assertFalse(state.replaying)

    def test_disabling_mode_releases_only_an_owned_pause_without_replay(self) -> None:
        enabled = True
        dunst = FakeDunst()
        controller = ShyModeController(
            dunst,  # type: ignore[arg-type]
            settings_loader=lambda: ShyModeSettings(enabled=enabled),
        )
        controller.poll(sharing=True, now=0)
        dunst.waiting = 2
        controller.poll(sharing=True, now=1)

        enabled = False
        state = controller.poll(sharing=True, now=2)

        self.assertFalse(state.enabled)
        self.assertFalse(state.pending)
        self.assertFalse(dunst.paused)
        self.assertNotIn(("history_pop", None), dunst.calls)

    def test_manual_resume_during_share_relinquishes_ownership(self) -> None:
        dunst = FakeDunst()
        controller = self.make_controller(dunst)
        controller.poll(sharing=True, now=0)

        dunst.paused = False
        state = controller.poll(sharing=True, now=1)
        controller.poll(sharing=False, now=2)

        self.assertFalse(state.owns_pause)
        self.assertNotIn(("history_pop", None), dunst.calls)

    def test_enabling_mode_during_an_active_share_starts_protection(self) -> None:
        enabled = False
        dunst = FakeDunst()
        controller = ShyModeController(
            dunst,  # type: ignore[arg-type]
            settings_loader=lambda: ShyModeSettings(enabled=enabled),
        )

        controller.poll(sharing=True, now=0)
        enabled = True
        state = controller.poll(sharing=True, now=1)

        self.assertTrue(state.owns_pause)
        self.assertIn(("set_paused", True), dunst.calls)


class DunstClientTest(unittest.TestCase):
    def test_handles_invalid_counts_and_failed_history_pop(self) -> None:
        responses = {
            ("dunstctl", "count", "waiting"): subprocess.CompletedProcess([], 0, "bad", ""),
            ("dunstctl", "count", "history"): subprocess.CompletedProcess([], 1, "", "failed"),
            ("dunstctl", "history-pop"): subprocess.CompletedProcess([], 1, "", "empty"),
        }
        client = DunstClient(lambda command: responses[tuple(command)])

        self.assertIsNone(client.waiting_count())
        self.assertIsNone(client.history_count())
        self.assertFalse(client.history_pop())
