import unittest

from archie.monitor import (
    MonitorOutput,
    can_disable,
    disable_monitor_command,
    enable_monitor_command,
    monitor_layout_value,
    parse_monitors_json,
    restore_monitor_commands,
)


class MonitorParsingTest(unittest.TestCase):
    def test_parses_enabled_and_disabled_outputs(self) -> None:
        monitors = parse_monitors_json(
            """[
  {
    "name": "eDP-1",
    "description": "Built-in",
    "width": 1920,
    "height": 1080,
    "refreshRate": 60.0,
    "x": 0,
    "y": 0,
    "scale": 1.0,
    "transform": 0,
    "disabled": false,
    "focused": true
  },
  {
    "name": "HDMI-A-1",
    "description": "External",
    "disabled": true
  }
]"""
        )

        self.assertEqual(monitors[0].name, "eDP-1")
        self.assertTrue(monitors[0].enabled)
        self.assertFalse(monitors[1].enabled)

    def test_rejects_disabling_last_enabled_output(self) -> None:
        monitors = [
            MonitorOutput("eDP-1", "", 1920, 1080, 60.0, 0, 0, 1.0, 0, False, True),
            MonitorOutput("HDMI-A-1", "", 0, 0, 0.0, 0, 0, 1.0, 0, True, False),
        ]

        self.assertFalse(can_disable(monitors, "eDP-1"))
        self.assertFalse(can_disable(monitors, "HDMI-A-1"))

    def test_allows_disabling_one_of_multiple_enabled_outputs(self) -> None:
        monitors = [
            MonitorOutput("eDP-1", "", 1920, 1080, 60.0, 0, 0, 1.0, 0, False, True),
            MonitorOutput("HDMI-A-1", "", 2560, 1440, 144.0, 1920, 0, 1.25, 0, False, False),
        ]

        self.assertTrue(can_disable(monitors, "HDMI-A-1"))


class MonitorCommandTest(unittest.TestCase):
    def test_builds_toggle_commands(self) -> None:
        self.assertEqual(disable_monitor_command("eDP-1"), ["hyprctl", "keyword", "monitor", "eDP-1,disable"])
        self.assertEqual(
            enable_monitor_command("HDMI-A-1"),
            ["hyprctl", "keyword", "monitor", "HDMI-A-1,preferred,auto,1"],
        )

    def test_builds_restore_commands(self) -> None:
        monitors = [
            MonitorOutput("eDP-1", "", 1920, 1080, 60.0, 0, 0, 1.0, 0, False, True),
            MonitorOutput("HDMI-A-1", "", 0, 0, 0.0, 0, 0, 1.0, 0, True, False),
        ]

        self.assertEqual(
            restore_monitor_commands(monitors),
            [
                ["hyprctl", "keyword", "monitor", "eDP-1,1920x1080@60,0x0,1"],
                ["hyprctl", "keyword", "monitor", "HDMI-A-1,disable"],
            ],
        )

    def test_includes_transform_in_layout_value(self) -> None:
        monitor = MonitorOutput("DP-1", "", 1200, 1920, 59.95, 0, 0, 1.5, 1, False, False)

        self.assertEqual(monitor_layout_value(monitor), "DP-1,1200x1920@59.95,0x0,1.5,transform,1")
