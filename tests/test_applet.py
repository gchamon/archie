import subprocess
import unittest
from unittest.mock import patch

from archie.applet import format_tooltip
from archie.monitor import MonitorOutput


class AppletTooltipTest(unittest.TestCase):
    @patch("archie.applet.get_waybar_theme", return_value="tokyonight")
    @patch("archie.applet.get_power_profile", return_value="balanced")
    @patch("archie.applet.get_kdeconnect_state", return_value="on")
    @patch("archie.applet.get_notifications_state", return_value="off")
    @patch("archie.applet.get_lid_behavior", return_value="lock")
    @patch("archie.applet.list_monitors")
    @patch("archie.applet.get_brightness_devices")
    def test_formats_all_settings_and_current_state(
        self,
        brightness,
        monitors,
        _lid,
        _notifications,
        _kdeconnect,
        _power_profile,
        _waybar_theme,
    ) -> None:
        brightness.return_value = subprocess.CompletedProcess(
            [], 0, stdout="amdgpu_bl1\t71\t181\t255\n", stderr=""
        )
        monitors.return_value = [
            MonitorOutput(
                name="eDP-1",
                description="Built-in display",
                width=1920,
                height=1080,
                refresh_rate=60.0,
                x=0,
                y=0,
                scale=1.0,
                transform=0,
                disabled=False,
                focused=True,
            )
        ]

        self.assertEqual(
            format_tooltip(),
            "Brightness: amdgpu_bl1 71%\n"
            "Monitors: eDP-1 Built-in display: enabled (focused)\n"
            "Lid close: lock\n"
            "Notifications: off\n"
            "KDE Connect: on\n"
            "Power profile: balanced\n"
            "Waybar theme: tokyonight",
        )

    @patch("archie.applet.get_waybar_theme", side_effect=RuntimeError("missing"))
    @patch("archie.applet.get_power_profile", return_value="")
    @patch("archie.applet.get_kdeconnect_state", return_value="off")
    @patch("archie.applet.get_notifications_state", return_value="on")
    @patch("archie.applet.get_lid_behavior", return_value="unknown")
    @patch("archie.applet.list_monitors", return_value=[])
    @patch("archie.applet.get_brightness_devices")
    def test_keeps_other_settings_when_some_are_unavailable_or_unknown(
        self,
        brightness,
        _monitors,
        _lid,
        _notifications,
        _kdeconnect,
        _power_profile,
        _waybar_theme,
    ) -> None:
        brightness.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")

        self.assertEqual(
            format_tooltip(),
            "Brightness: unavailable\n"
            "Monitors: unavailable\n"
            "Lid close: unknown\n"
            "Notifications: on\n"
            "KDE Connect: off\n"
            "Power profile: unknown\n"
            "Waybar theme: unknown",
        )
