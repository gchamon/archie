import unittest
from unittest.mock import patch

from archie.applet import (
    ArchieStatusNotifier,
    format_shy_mode_status,
    format_tooltip,
    load_applet_snapshot,
    select_applet_icon,
)
from archie.privacy import DunstClient, ShyModeController, ShyModeViewState


class AppletTooltipTest(unittest.TestCase):
    def test_formats_all_settings_and_current_state(self) -> None:
        self.assertEqual(
            format_tooltip(
                {
                    "brightness": [{"name": "amdgpu_bl1", "percent": 71}],
                    "monitors": [{"name": "eDP-1", "label": "Built-in display", "enabled": True, "focused": True}],
                    "lid-close-behavior": "lock",
                    "notifications": "off",
                    "kdeconnect": "on",
                    "power-profile": "balanced",
                    "waybar-theme": "tokyonight",
                },
                ShyModeViewState(False, False, False, False, False),
            ),
            "Hardware\n"
            "  Brightness: amdgpu_bl1 71%\n"
            "  Monitors: eDP-1 Built-in display: enabled (focused)\n"
            "\n"
            "Desktop\n"
            "  Lid close: lock\n"
            "  KDE Connect: on\n"
            "  Power profile: balanced\n"
            "  Waybar theme: tokyonight\n"
            "\n"
            "Privacy\n"
            "  Notifications: off\n"
            "  Shy mode: off\n"
            "  Share: off",
        )

    def test_keeps_other_settings_when_some_are_unavailable_or_unknown(self) -> None:
        self.assertEqual(
            format_tooltip(
                {
                    "brightness": [],
                    "monitors": [],
                    "lid-close-behavior": "unknown",
                    "notifications": "on",
                    "kdeconnect": "off",
                    "power-profile": "",
                },
                ShyModeViewState(False, False, False, False, False),
            ),
            "Hardware\n"
            "  Brightness: unavailable\n"
            "  Monitors: unavailable\n"
            "\n"
            "Desktop\n"
            "  Lid close: unknown\n"
            "  KDE Connect: off\n"
            "  Power profile: unknown\n"
            "  Waybar theme: unknown\n"
            "\n"
            "Privacy\n"
            "  Notifications: on\n"
            "  Shy mode: off\n"
            "  Share: off",
        )


class AppletPrivacyStateTest(unittest.TestCase):
    @patch("archie.applet.collect_system_status")
    def test_loads_tooltip_values_in_process(self, collect) -> None:
        collect.return_value = ({"brightness": [], "share-state": "on"}, {})

        self.assertEqual(load_applet_snapshot(), {"brightness": [], "share-state": "on"})
        collect.assert_called_once_with()

    def test_startup_tooltip_does_not_read_privacy_configuration(self) -> None:
        with patch("archie.applet.load_shy_mode_settings") as settings:
            tooltip = format_tooltip(privacy_ready=False)

        settings.assert_not_called()
        self.assertIn("Shy mode: starting privacy monitor…", tooltip)

    def test_pending_state_selects_orange_icon_and_text(self) -> None:
        state = ShyModeViewState(
            enabled=True,
            sharing=True,
            owns_pause=True,
            pending=True,
            replaying=False,
        )

        self.assertEqual(select_applet_icon(state), "orange")
        self.assertEqual(
            format_shy_mode_status(state),
            "on, sharing; notifications pending",
        )

    def test_non_pending_states_use_base_icon_and_specific_text(self) -> None:
        guarding = ShyModeViewState(True, True, True, False, False)
        replaying = ShyModeViewState(True, False, False, False, True)
        disabled = ShyModeViewState(False, False, False, False, False)

        self.assertEqual(select_applet_icon(guarding), "base")
        self.assertEqual(format_shy_mode_status(guarding), "on, guarding active share")
        self.assertEqual(format_shy_mode_status(replaying), "on, replaying missed notifications")
        self.assertEqual(format_shy_mode_status(disabled), "off")

    @patch.object(ArchieStatusNotifier, "emit_state_changed")
    def test_privacy_state_idle_callback_runs_once(self, emit_state_changed) -> None:
        state = ShyModeViewState(True, True, True, False, False)
        notifier = ArchieStatusNotifier(object(), {}, ShyModeController(DunstClient()))

        self.assertFalse(notifier.apply_privacy_state(state))
        self.assertEqual(notifier.shy_state, state)
        self.assertTrue(notifier.privacy_ready)
        self.assertFalse(notifier.privacy_refresh_in_progress)
        emit_state_changed.assert_called_once_with()
