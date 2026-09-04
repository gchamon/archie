import subprocess
import unittest
from unittest.mock import Mock, patch

from archie.applet import (
    MENU_ITEM_LID_HIBERNATE,
    MENU_ITEM_LID_LOCK,
    MENU_ITEM_NOTIFICATION_SOUNDS,
    MENU_ITEM_NOTIFICATIONS,
    ArchieStatusNotifier,
    format_shy_mode_status,
    format_tooltip,
    format_tooltip_title,
    load_applet_snapshot,
    menu_action_value,
    menu_toggle_state,
    select_applet_icon,
)
from archie.gui_state import GUI_SETTINGS_SNAPSHOT_ENV, GuiSettingsSnapshot
from archie.monitor import MonitorOutput
from archie.privacy import (
    DunstClient,
    ShyModeController,
    ShyModeSettings,
    ShyModeViewState,
)


class AppletTooltipTest(unittest.TestCase):
    def test_formats_all_settings_and_current_state(self) -> None:
        self.assertEqual(
            format_tooltip(
                {
                    "brightness": [{"name": "amdgpu_bl1", "percent": 71}],
                    "monitors": [{"name": "eDP-1", "label": "Built-in display", "enabled": True, "focused": True}],
                    "lid-close-behavior": "lock",
                    "notifications": "off",
                    "notification-sounds": "on",
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
            "  Notification sounds: on\n"
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
                    "notification-sounds": "unknown",
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
            "  Notification sounds: unknown\n"
            "  Shy mode: off\n"
            "  Share: off",
        )

    def test_formats_versioned_tooltip_title(self) -> None:
        self.assertEqual(format_tooltip_title("0.1.0"), "Archie Controls v0.1.0")
        self.assertNotIn(
            "Archie Controls",
            format_tooltip({}, ShyModeViewState(False, False, False, False, False)),
        )


class AppletPrivacyStateTest(unittest.TestCase):
    def test_menu_switches_emit_native_toggle_properties(self) -> None:
        notifier = ArchieStatusNotifier(object(), {}, Mock())
        notifier.snapshot = {
            "lid-close-behavior": "lock",
            "notifications": "on",
            "notification-sounds": "off",
        }

        expected = {
            MENU_ITEM_LID_HIBERNATE: ("radio", 0),
            MENU_ITEM_LID_LOCK: ("radio", 1),
            MENU_ITEM_NOTIFICATIONS: ("checkmark", 1),
            MENU_ITEM_NOTIFICATION_SOUNDS: ("checkmark", 0),
        }
        for item_id, (toggle_type, toggle_state) in expected.items():
            with self.subTest(item_id=item_id):
                properties = notifier._item_props(item_id)

                self.assertIsNotNone(properties)
                assert properties is not None
                self.assertEqual(properties["toggle-type"].unpack(), toggle_type)
                self.assertEqual(properties["toggle-state"].unpack(), toggle_state)

    def test_menu_switches_follow_snapshot_values(self) -> None:
        snapshot = {
            "lid-close-behavior": "lock",
            "notifications": "on",
            "notification-sounds": "off",
        }

        self.assertEqual(menu_toggle_state(MENU_ITEM_LID_HIBERNATE, snapshot), 0)
        self.assertEqual(menu_toggle_state(MENU_ITEM_LID_LOCK, snapshot), 1)
        self.assertEqual(menu_toggle_state(MENU_ITEM_NOTIFICATIONS, snapshot), 1)
        self.assertEqual(menu_toggle_state(MENU_ITEM_NOTIFICATION_SOUNDS, snapshot), 0)

    def test_menu_switches_invert_or_set_expected_values(self) -> None:
        snapshot = {
            "lid-close-behavior": "hibernate",
            "notifications": "on",
            "notification-sounds": "off",
        }

        self.assertEqual(menu_action_value(MENU_ITEM_LID_LOCK, snapshot), "lock")
        self.assertEqual(menu_action_value(MENU_ITEM_NOTIFICATIONS, snapshot), "off")
        self.assertEqual(menu_action_value(MENU_ITEM_NOTIFICATION_SOUNDS, snapshot), "on")

    def test_menu_switches_are_unavailable_for_unknown_values(self) -> None:
        snapshot = {
            "lid-close-behavior": "unknown",
            "notifications": "unknown",
            "notification-sounds": "unknown",
        }

        self.assertIsNone(menu_toggle_state(MENU_ITEM_LID_HIBERNATE, snapshot))
        self.assertIsNone(menu_action_value(MENU_ITEM_LID_HIBERNATE, snapshot))
        self.assertIsNone(menu_toggle_state(MENU_ITEM_LID_LOCK, snapshot))
        self.assertIsNone(menu_action_value(MENU_ITEM_LID_LOCK, snapshot))
        self.assertIsNone(menu_toggle_state(MENU_ITEM_NOTIFICATIONS, snapshot))
        self.assertIsNone(menu_action_value(MENU_ITEM_NOTIFICATIONS, snapshot))
        self.assertIsNone(menu_toggle_state(MENU_ITEM_NOTIFICATION_SOUNDS, snapshot))
        self.assertIsNone(menu_action_value(MENU_ITEM_NOTIFICATION_SOUNDS, snapshot))

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


class AppletTooltipRefreshTest(unittest.TestCase):
    @patch.object(ArchieStatusNotifier, "emit_state_changed")
    def test_changed_refresh_emits_a_tooltip_update(self, emit_state_changed) -> None:
        notifier = ArchieStatusNotifier(object(), {}, Mock())
        refreshed_state = ShyModeViewState(True, True, True, False, False)
        notifier.tooltip_refresh_in_progress = True

        self.assertFalse(notifier.apply_tooltip_refresh({"notifications": "off"}, refreshed_state))

        self.assertEqual(notifier.snapshot, {"notifications": "off"})
        self.assertEqual(notifier.shy_state, refreshed_state)
        self.assertTrue(notifier.privacy_ready)
        self.assertFalse(notifier.tooltip_refresh_in_progress)
        emit_state_changed.assert_called_once_with()

    @patch.object(ArchieStatusNotifier, "emit_state_changed")
    def test_unchanged_refresh_preserves_last_good_values_without_a_signal(self, emit_state_changed) -> None:
        previous_snapshot: dict[str, object] = {"notifications": "on"}
        previous_state = ShyModeViewState(True, False, False, True, False)
        notifier = ArchieStatusNotifier(
            object(),
            {},
            Mock(),
            shy_state=previous_state,
            snapshot=previous_snapshot,
            privacy_ready=True,
        )
        notifier.tooltip_refresh_in_progress = True

        self.assertFalse(notifier.apply_tooltip_refresh(None, None))

        self.assertIs(notifier.snapshot, previous_snapshot)
        self.assertIs(notifier.shy_state, previous_state)
        self.assertTrue(notifier.privacy_ready)
        self.assertFalse(notifier.tooltip_refresh_in_progress)
        emit_state_changed.assert_not_called()

    def test_settings_changed_requests_a_background_tooltip_refresh(self) -> None:
        notifier = ArchieStatusNotifier(object(), {}, Mock())
        invocation = Mock()

        with patch.object(notifier, "request_tooltip_refresh") as refresh:
            notifier.applet_method_call(None, "", "", "", "SettingsChanged", None, invocation)

        refresh.assert_called_once_with()
        invocation.return_value.assert_called_once_with(None)

    def test_restart_requests_a_deferred_applet_restart(self) -> None:
        notifier = ArchieStatusNotifier(object(), {}, Mock())
        invocation = Mock()

        with patch.object(notifier, "request_restart") as restart:
            notifier.applet_method_call(None, "", "", "", "Restart", None, invocation)

        restart.assert_called_once_with()
        invocation.return_value.assert_called_once_with(None)


class AppletGuiSnapshotTest(unittest.TestCase):
    def test_startup_requests_a_gui_snapshot(self) -> None:
        notifier = ArchieStatusNotifier(object(), {}, ShyModeController(DunstClient()))

        with (
            patch("archie.applet.threading.Thread"),
            patch.object(notifier, "request_privacy_refresh"),
            patch.object(notifier, "request_gui_snapshot_refresh") as refresh_gui_snapshot,
        ):
            self.assertFalse(notifier.start_privacy_monitor())

        refresh_gui_snapshot.assert_called_once_with()

    def test_applies_gui_snapshot_in_memory(self) -> None:
        notifier = ArchieStatusNotifier(object(), {}, ShyModeController(DunstClient()))
        snapshot = make_gui_snapshot()
        notifier.gui_snapshot_refresh_in_progress = True

        self.assertFalse(notifier.apply_gui_snapshot(snapshot))
        self.assertIs(notifier.gui_snapshot, snapshot)
        self.assertFalse(notifier.gui_snapshot_refresh_in_progress)

    def test_open_gui_passes_the_cached_snapshot_through_its_environment(self) -> None:
        notifier = ArchieStatusNotifier(object(), {}, ShyModeController(DunstClient()))
        snapshot = make_gui_snapshot()
        notifier.gui_snapshot = snapshot

        with patch("archie.applet._open_gui") as open_gui:
            notifier.open_gui()

        open_gui.assert_called_once_with(snapshot)

    def test_launch_serializes_the_snapshot_only_for_the_gui_child(self) -> None:
        snapshot = make_gui_snapshot()

        with patch("archie.applet.subprocess.Popen") as popen:
            from archie.applet import _open_gui

            _open_gui(snapshot)

        command, = popen.call_args.args
        environment = popen.call_args.kwargs["env"]
        self.assertEqual(command, ["archie", "gui"])
        self.assertIn(GUI_SETTINGS_SNAPSHOT_ENV, environment)


def make_gui_snapshot() -> GuiSettingsSnapshot:
    return GuiSettingsSnapshot(
        brightness_result=subprocess.CompletedProcess([], 0, "", ""),
        monitors=[MonitorOutput("eDP-1", "", 1920, 1080, 60.0, 0, 0, 1.0, 0, False, True)],
        monitor_error=None,
        lid_behavior="lock",
        notifications="on",
        notification_sounds="on",
        notification_sound="default",
        shy_mode=ShyModeSettings(),
        kdeconnect="on",
        power_profile="balanced",
        waybar_theme="tokyonight",
        waybar_font_family="MesloLGM Nerd Font",
        waybar_font_size=20,
        waybar_menu_font_family="MesloLGM Nerd Font",
        waybar_menu_font_size=20,
        waybar_tooltip_font_family="MesloLGM Nerd Font",
        waybar_tooltip_font_size=20,
    )
