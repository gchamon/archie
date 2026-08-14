import io
import os
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from archie.cli import main
from archie.gui import (
    filter_documentation_rows,
    filter_shortcut_rows,
    get_notification_sounds_state,
    load_gui_settings_snapshot,
    load_gui_settings_snapshot_from_environment,
    parse_brightness_devices,
    parse_markdown_table,
    snap_brightness_percent,
)
from archie.gui_state import (
    GuiSettingsSnapshot,
    deserialize_gui_settings_snapshot,
    serialize_gui_settings_snapshot,
)
from archie.monitor import MonitorOutput
from archie.privacy import ShyModeSettings


class CliExposureTest(unittest.TestCase):
    def test_help_all_includes_gui_and_applet_commands(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as error, redirect_stdout(stdout), redirect_stderr(stderr):
            main(["--help-all"])

        self.assertEqual(error.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("  applet - Run the Archie tray applet.", stdout.getvalue())
        self.assertIn("  gui - Open Archie graphical controls.", stdout.getvalue())


class KeyboardShortcutMarkdownTest(unittest.TestCase):
    def test_parse_markdown_table_removes_separator_and_code_ticks(self) -> None:
        rows = parse_markdown_table([
            "| Shortcut | Command/Action | Description |",
            "| :------- | :------------- | :---------- |",
            "| `SUPER + L` | `exec, hyprlock` | Locks the screen. |",
        ])

        self.assertEqual(rows, [
            ["Shortcut", "Command/Action", "Description"],
            ["SUPER + L", "exec, hyprlock", "Locks the screen."],
        ])

    def test_filter_shortcut_rows_matches_any_column_case_insensitively(self) -> None:
        rows = [
            ["SUPER + L", "exec, hyprlock", "Locks the screen."],
            ["SUPER + R", "exec, $menu", "Opens Rofi."],
        ]

        self.assertEqual(filter_shortcut_rows(rows, "ROFI"), [rows[1]])
        self.assertEqual(filter_shortcut_rows(rows, ""), rows)


class ShellCommandMarkdownTest(unittest.TestCase):
    def test_parse_zsh_command_table_removes_separator_and_code_ticks(self) -> None:
        rows = parse_markdown_table([
            "| Name | Kind | Description |",
            "| --- | --- | --- |",
            "| `gp` | Alias | Uses `ggpush` as the default push command. |",
        ])

        self.assertEqual(rows, [
            ["Name", "Kind", "Description"],
            ["gp", "Alias", "Uses ggpush as the default push command."],
        ])

    def test_filter_documentation_rows_matches_zsh_command_columns(self) -> None:
        rows = [
            ["gp", "Alias", "Uses ggpush as the default push command."],
            ["git:stash-commit", "Function", "Turns commits into a stash entry."],
        ]

        self.assertEqual(filter_documentation_rows(rows, "function"), [rows[1]])
        self.assertEqual(filter_documentation_rows(rows, "GGPUSH"), [rows[0]])


class BrightnessGuiStateTest(unittest.TestCase):
    def test_parse_brightness_devices_uses_tab_separated_cli_output(self) -> None:
        devices = parse_brightness_devices("amdgpu_bl1\t71\t181\t255\n")

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].name, "amdgpu_bl1")
        self.assertEqual(devices[0].percent, 71)
        self.assertEqual(devices[0].current, 181)
        self.assertEqual(devices[0].maximum, 255)

    def test_snap_brightness_percent_uses_ten_percent_steps(self) -> None:
        self.assertEqual(snap_brightness_percent(-1), 0)
        self.assertEqual(snap_brightness_percent(14), 10)
        self.assertEqual(snap_brightness_percent(15), 20)
        self.assertEqual(snap_brightness_percent(25), 30)
        self.assertEqual(snap_brightness_percent(103), 100)


class NotificationSoundsGuiStateTest(unittest.TestCase):
    def test_reads_notification_sounds_from_the_system_cli(self) -> None:
        with patch("archie.gui.run_cli") as run_cli:
            run_cli.return_value = subprocess.CompletedProcess([], 0, "off\n", "")

            self.assertEqual(get_notification_sounds_state(), "off")
            run_cli.assert_called_once_with(
                ["archie", "system", "get", "notification-sounds"]
            )


class GuiSettingsSnapshotTest(unittest.TestCase):
    def test_collects_settings_without_constructing_gtk_widgets(self) -> None:
        brightness = subprocess.CompletedProcess([], 0, "amdgpu_bl1\t71\t181\t255\n", "")
        shy_mode = ShyModeSettings(enabled=True, replay_count=4, replay_interval=2.5)
        monitors = [object()]

        with (
            patch("archie.gui.get_brightness_devices", return_value=brightness),
            patch("archie.gui.list_monitors", return_value=monitors),
            patch("archie.gui.get_lid_behavior", return_value="lock"),
            patch("archie.gui.get_notifications_state", return_value="on"),
            patch("archie.gui.get_notification_sounds_state", return_value="off"),
            patch("archie.gui.get_shy_mode_settings", return_value=shy_mode),
            patch("archie.gui.get_kdeconnect_state", return_value="on"),
            patch("archie.gui.get_power_profile", return_value="balanced"),
            patch("archie.gui.get_waybar_theme", return_value="tokyonight"),
        ):
            snapshot = load_gui_settings_snapshot()

        self.assertIs(snapshot.brightness_result, brightness)
        self.assertEqual(snapshot.monitors, monitors)
        self.assertIsNone(snapshot.monitor_error)
        self.assertEqual(snapshot.lid_behavior, "lock")
        self.assertEqual(snapshot.notifications, "on")
        self.assertEqual(snapshot.notification_sounds, "off")
        self.assertEqual(snapshot.shy_mode, shy_mode)
        self.assertEqual(snapshot.kdeconnect, "on")
        self.assertEqual(snapshot.power_profile, "balanced")
        self.assertEqual(snapshot.waybar_theme, "tokyonight")

    def test_keeps_other_settings_when_monitor_discovery_fails(self) -> None:
        with (
            patch("archie.gui.get_brightness_devices", return_value=subprocess.CompletedProcess([], 0, "", "")),
            patch("archie.gui.list_monitors", side_effect=RuntimeError("Hyprland unavailable")),
            patch("archie.gui.get_lid_behavior", return_value="unknown"),
            patch("archie.gui.get_notifications_state", return_value="unknown"),
            patch("archie.gui.get_notification_sounds_state", return_value="unknown"),
            patch("archie.gui.get_shy_mode_settings", return_value=ShyModeSettings()),
            patch("archie.gui.get_kdeconnect_state", return_value="unknown"),
            patch("archie.gui.get_power_profile", return_value="unknown"),
            patch("archie.gui.get_waybar_theme", return_value="unknown"),
        ):
            snapshot = load_gui_settings_snapshot()

        self.assertEqual(snapshot.monitors, [])
        self.assertEqual(snapshot.monitor_error, "Hyprland unavailable")
        self.assertEqual(snapshot.notifications, "unknown")

    def test_serializes_and_restores_an_applet_snapshot(self) -> None:
        snapshot = GuiSettingsSnapshot(
            brightness_result=subprocess.CompletedProcess([], 0, "amdgpu_bl1\t71\t181\t255\n", ""),
            monitors=[
                MonitorOutput("eDP-1", "Built-in", 1920, 1080, 60.0, 0, 0, 1.0, 0, False, True),
            ],
            monitor_error=None,
            lid_behavior="lock",
            notifications="on",
            notification_sounds="off",
            shy_mode=ShyModeSettings(enabled=True, replay_count=4, replay_interval=2.5),
            kdeconnect="on",
            power_profile="balanced",
            waybar_theme="tokyonight",
        )

        restored = deserialize_gui_settings_snapshot(serialize_gui_settings_snapshot(snapshot))

        assert restored is not None
        self.assertEqual(restored.brightness_result.returncode, snapshot.brightness_result.returncode)
        self.assertEqual(restored.brightness_result.stdout, snapshot.brightness_result.stdout)
        self.assertEqual(restored.brightness_result.stderr, snapshot.brightness_result.stderr)
        self.assertEqual(restored.monitors, snapshot.monitors)
        self.assertEqual(restored.monitor_error, snapshot.monitor_error)
        self.assertEqual(restored.lid_behavior, snapshot.lid_behavior)
        self.assertEqual(restored.notifications, snapshot.notifications)
        self.assertEqual(restored.notification_sounds, snapshot.notification_sounds)
        self.assertEqual(restored.shy_mode, snapshot.shy_mode)
        self.assertEqual(restored.kdeconnect, snapshot.kdeconnect)
        self.assertEqual(restored.power_profile, snapshot.power_profile)
        self.assertEqual(restored.waybar_theme, snapshot.waybar_theme)

    def test_ignores_malformed_applet_snapshot_environment(self) -> None:
        with patch.dict(os.environ, {"ARCHIE_GUI_SETTINGS_SNAPSHOT": "not json"}, clear=False):
            self.assertIsNone(load_gui_settings_snapshot_from_environment())
