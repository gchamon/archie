import argparse
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from archie.cli import main
from archie.system import (
    HIBERNATE_MODE,
    LOCK_MODE,
    NONE_MODE,
    OFF_VALUE,
    ON_VALUE,
    UNKNOWN_MODE,
    BrightnessDevice,
    clamp_brightness_percent,
    detect_kdeconnect_state,
    detect_lid_close_behavior,
    format_brightness_device,
    format_system_status,
    format_system_status_json,
    install_lid_close_behavior,
    list_backlight_device_names,
    load_notification_sound_path,
    load_notification_sounds_enabled,
    reload_logind_if_active,
    run_system_get,
    run_system_set,
    save_notification_sound_path,
    set_brightness,
    set_kdeconnect,
)


class NotificationSoundsCommandTest(unittest.TestCase):
    def test_defaults_to_enabled_when_configuration_is_missing_or_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "notification-sounds.json"

            self.assertTrue(load_notification_sounds_enabled(path))
            path.write_text("not json", encoding="utf-8")
            self.assertTrue(load_notification_sounds_enabled(path))

    def test_get_and_set_persist_sound_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "notification-sounds.json"
            args = argparse.Namespace(setting="notification-sounds", value="off")

            self.assertEqual(run_system_set(args, notification_sounds_path=path), 0)
            self.assertEqual(path.read_text(encoding="utf-8"), '{\n  "enabled": false\n}\n')

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(
                    run_system_get(
                        argparse.Namespace(setting="notification-sounds"),
                        notification_sounds_path=path,
                    ),
                    0,
                )
            self.assertEqual(stdout.getvalue(), "off\n")

    def test_custom_sound_path_is_persisted_and_requires_a_readable_absolute_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "notification-sounds.json"
            sound_path = Path(temp_dir) / "sound.ogg"
            sound_path.write_text("sound", encoding="utf-8")
            save_notification_sound_path(str(sound_path), config_path)
            self.assertEqual(load_notification_sound_path(config_path), str(sound_path))
            with self.assertRaises(ValueError):
                save_notification_sound_path("relative.ogg", config_path)


class ShyModeCommandTest(unittest.TestCase):
    def test_get_and_set_persist_replay_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "shy-mode.json"
            args = argparse.Namespace(
                setting="shy-mode",
                value="on",
                replay_count=6,
                replay_interval=2.5,
            )

            self.assertEqual(run_system_set(args, shy_mode_path=path), 0)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(
                    run_system_get(argparse.Namespace(setting="shy-mode"), shy_mode_path=path),
                    0,
                )

            self.assertEqual(
                stdout.getvalue(),
                "enabled: on\nreplay-count: 6\nreplay-interval: 2.5s\n",
            )

    def test_set_off_preserves_replay_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "shy-mode.json"
            run_system_set(
                argparse.Namespace(
                    setting="shy-mode",
                    value="on",
                    replay_count=4,
                    replay_interval=3.0,
                ),
                shy_mode_path=path,
            )

            self.assertEqual(
                run_system_set(
                    argparse.Namespace(
                        setting="shy-mode",
                        value="off",
                        replay_count=None,
                        replay_interval=None,
                    ),
                    shy_mode_path=path,
                ),
                0,
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                run_system_get(argparse.Namespace(setting="shy-mode"), shy_mode_path=path)

            self.assertEqual(
                stdout.getvalue(),
                "enabled: off\nreplay-count: 4\nreplay-interval: 3s\n",
            )

    def test_cli_validates_replay_bounds_and_interval(self) -> None:
        for arguments in (
            ["system", "set", "shy-mode", "on", "--replay-count", "21"],
            ["system", "set", "shy-mode", "on", "--replay-interval", "0"],
        ):
            with self.subTest(arguments=arguments):
                stderr = io.StringIO()
                with self.assertRaises(SystemExit) as error, redirect_stderr(stderr):
                    main(arguments)
                self.assertEqual(error.exception.code, 2)


class SystemStatusTest(unittest.TestCase):
    @patch("archie.system.collect_system_status")
    def test_cli_prints_status_without_the_applet(self, collect) -> None:
        collect.return_value = (
            {
                "notifications": "on",
                "notification-sounds": "on",
                "shy-mode": "off",
                "share-state": "off",
            },
            {},
        )
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            self.assertEqual(main(["system", "status"]), 0)

        self.assertIn("Notifications: on", stdout.getvalue())
        self.assertIn("Notification sounds: on", stdout.getvalue())
        self.assertIn("Shy mode: off", stdout.getvalue())
        self.assertIn("Share: off", stdout.getvalue())

    @patch("archie.system.collect_system_status")
    def test_cli_accepts_short_json_format_option(self, collect) -> None:
        collect.return_value = ({"notifications": "on"}, {})
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            self.assertEqual(main(["system", "status", "-f", "json"]), 0)

        status = json.loads(stdout.getvalue())
        self.assertEqual(status["notifications"], "on")
        self.assertEqual(status["notification-sounds"], "unknown")
        self.assertEqual(status["lid-close-behavior"], "unknown")
        self.assertEqual(list(status), [
            "lid-close-behavior",
            "notifications",
            "notification-sounds",
            "notification-sound",
            "shy-mode",
            "share-state",
            "kdeconnect",
            "power-profile",
            "waybar-theme",
            "brightness",
            "monitors",
        ])

    @patch("archie.system.collect_system_status")
    def test_cli_accepts_json_aliases(self, collect) -> None:
        collect.return_value = ({"notifications": "on"}, {})

        for option in ("-j", "--json"):
            with self.subTest(option=option):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(main(["system", "status", option]), 0)
                self.assertEqual(json.loads(stdout.getvalue())["notifications"], "on")

    def test_formats_the_applet_summary(self) -> None:
        values = {
            "notifications": "on",
            "notification-sounds": "off",
            "brightness": [{"name": "amdgpu_bl1", "percent": 71}],
            "monitors": [
                {
                    "name": "eDP-1",
                    "label": "Built-in display",
                    "enabled": True,
                    "focused": True,
                }
            ],
            "lid-close-behavior": "lock",
            "kdeconnect": "on",
            "power-profile": "balanced",
            "waybar-theme": "tokyonight",
            "shy-mode": "on",
            "share-state": "off",
        }

        self.assertEqual(
            format_system_status(values),
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
            "  Notifications: on\n"
            "  Notification sounds: off\n"
            "  Shy mode: on\n"
            "  Share: off",
        )

    def test_json_uses_system_get_and_set_property_names(self) -> None:
        rendered = format_system_status_json(
            {
                "brightness": [{"name": "amdgpu_bl1", "percent": 71}],
                "shy-mode": "on",
            }
        )

        status = json.loads(rendered)
        self.assertEqual(status["brightness"][0]["percent"], 71)
        self.assertEqual(status["shy-mode"], "on")
        self.assertEqual(status["monitors"], "unknown")

    def test_formats_missing_values_as_unknown_without_losing_available_values(self) -> None:
        rendered = format_system_status({"notifications": "on"})

        self.assertIn("Notifications: on", rendered)
        self.assertIn("Notification sounds: unknown", rendered)
        self.assertIn("Monitors: unknown", rendered)
        self.assertIn("Power profile: unknown", rendered)



class LidCloseBehaviorDetectionTest(unittest.TestCase):
    def test_detects_hibernate_mode_from_hybrid_sleep_drop_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lid_close_conf = Path(temp_dir) / "lid-close.conf"
            lid_close_conf.write_text(
                """[Login]
HandleLidSwitch=hybrid-sleep
HandleLidSwitchDocked=hybrid-sleep
HandleLidSwitchExternalPower=hybrid-sleep
""",
                encoding="utf-8",
            )

            self.assertEqual(detect_lid_close_behavior(lid_close_conf), HIBERNATE_MODE)

    def test_detects_lock_mode_from_ignore_drop_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lid_close_conf = Path(temp_dir) / "lid-close.conf"
            lid_close_conf.write_text(
                """[Login]
HandleLidSwitch=ignore
HandleLidSwitchDocked=ignore
HandleLidSwitchExternalPower=ignore
""",
                encoding="utf-8",
            )

            self.assertEqual(detect_lid_close_behavior(lid_close_conf), LOCK_MODE)

    def test_detects_none_mode_from_marked_ignore_drop_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lid_close_conf = Path(temp_dir) / "lid-close.conf"
            lid_close_conf.write_text(
                """# ArchieLidCloseBehavior=none
[Login]
HandleLidSwitch=ignore
HandleLidSwitchDocked=ignore
HandleLidSwitchExternalPower=ignore
""",
                encoding="utf-8",
            )

            self.assertEqual(detect_lid_close_behavior(lid_close_conf), NONE_MODE)

    def test_reports_unknown_for_missing_or_unmanaged_drop_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lid_close_conf = Path(temp_dir) / "lid-close.conf"
            self.assertEqual(detect_lid_close_behavior(lid_close_conf), UNKNOWN_MODE)

            lid_close_conf.write_text("[Login]\nHandleLidSwitch=suspend\n", encoding="utf-8")
            self.assertEqual(detect_lid_close_behavior(lid_close_conf), UNKNOWN_MODE)


class LidCloseBehaviorCommandTest(unittest.TestCase):
    def test_install_lid_close_behavior_installs_generated_drop_in(self) -> None:
        commands: list[list[str]] = []
        generated_content = ""

        def executor(command: list[str]) -> int:
            nonlocal generated_content
            commands.append(command)
            if command[0:4] == ["sudo", "install", "-m", "0644"]:
                generated_content = Path(command[4]).read_text(encoding="utf-8")
            return 0

        code = install_lid_close_behavior(
            LOCK_MODE,
            Path("/etc/systemd/logind.conf.d/lid-close.conf"),
            executor=executor,
        )

        self.assertEqual(code, 0)
        self.assertEqual(commands[0], ["sudo", "mkdir", "-p", "/etc/systemd/logind.conf.d"])
        self.assertEqual(commands[1][0:4], ["sudo", "install", "-m", "0644"])
        self.assertEqual(commands[1][5], "/etc/systemd/logind.conf.d/lid-close.conf")

        self.assertIn("HandleLidSwitch=ignore", generated_content)
        self.assertFalse(Path(commands[1][4]).exists())

    def test_reload_logind_skips_reload_when_service_is_inactive(self) -> None:
        commands: list[list[str]] = []

        def executor(command: list[str]) -> int:
            commands.append(command)
            return 3

        self.assertEqual(reload_logind_if_active(executor=executor), 0)
        self.assertEqual(commands, [["sudo", "systemctl", "is-active", "--quiet", "systemd-logind.service"]])

    def test_reload_logind_sends_hup_when_service_is_active(self) -> None:
        commands: list[list[str]] = []

        def executor(command: list[str]) -> int:
            commands.append(command)
            return 0

        self.assertEqual(reload_logind_if_active(executor=executor), 0)
        self.assertEqual(commands, [
            ["sudo", "systemctl", "is-active", "--quiet", "systemd-logind.service"],
            ["sudo", "systemctl", "kill", "-s", "HUP", "systemd-logind.service"],
        ])

    def test_run_system_get_prints_detected_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lid_close_conf = Path(temp_dir) / "lid-close.conf"
            lid_close_conf.write_text(
                """[Login]
HandleLidSwitch=hybrid-sleep
HandleLidSwitchDocked=hybrid-sleep
HandleLidSwitchExternalPower=hybrid-sleep
""",
                encoding="utf-8",
            )
            args = argparse.Namespace(setting="lid-close-behavior")
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                code = run_system_get(args, lid_close_conf_path=lid_close_conf)

            self.assertEqual(code, 0)
            self.assertEqual(stdout.getvalue(), "hibernate\n")

    def test_run_system_set_installs_behavior_and_reloads_logind(self) -> None:
        commands: list[list[str]] = []

        def executor(command: list[str]) -> int:
            commands.append(command)
            return 0

        args = argparse.Namespace(setting="lid-close-behavior", value="none")

        code = run_system_set(
            args,
            lid_close_conf_path=Path("/etc/systemd/logind.conf.d/lid-close.conf"),
            executor=executor,
        )

        self.assertEqual(code, 0)
        self.assertEqual(commands[0], ["sudo", "mkdir", "-p", "/etc/systemd/logind.conf.d"])
        self.assertEqual(commands[1][0:4], ["sudo", "install", "-m", "0644"])
        self.assertEqual(commands[2], ["sudo", "systemctl", "is-active", "--quiet", "systemd-logind.service"])
        self.assertEqual(commands[3], ["sudo", "systemctl", "kill", "-s", "HUP", "systemd-logind.service"])

    def test_main_exposes_system_subcommand(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as error, redirect_stdout(stdout), redirect_stderr(stderr):
            main(["system", "set", "lid-close-behavior", "suspend"])

        self.assertEqual(error.exception.code, 2)
        self.assertIn("invalid choice: 'suspend'", stderr.getvalue())

    def test_lid_close_behavior_set_help_is_setting_specific(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as error, redirect_stdout(stdout), redirect_stderr(stderr):
            main(["system", "set", "lid-close-behavior", "--help"])

        self.assertEqual(error.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("usage: archie system set lid-close-behavior", stdout.getvalue())
        self.assertIn("{hibernate,lock,none}", stdout.getvalue())
        self.assertIn("hybrid-sleep", stdout.getvalue())
        self.assertIn("ignore lid events", stdout.getvalue())

    def test_lid_close_behavior_get_help_is_setting_specific(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as error, redirect_stdout(stdout), redirect_stderr(stderr):
            main(["system", "get", "lid-close-behavior", "--help"])

        self.assertEqual(error.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("usage: archie system get lid-close-behavior", stdout.getvalue())

    def test_help_all_prints_command_hierarchy(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as error, redirect_stdout(stdout), redirect_stderr(stderr):
            main(["--help-all"])

        self.assertEqual(error.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("archie\n", stdout.getvalue())
        self.assertIn("  downgrade - Resolve Arch Linux Archive package URLs", stdout.getvalue())
        self.assertIn("  system - Inspect or change Archie-owned system policy.", stdout.getvalue())
        self.assertIn("    get", stdout.getvalue())
        self.assertIn("    get - Read an Archie-owned system setting.", stdout.getvalue())
        self.assertIn("    status - Print the same best-effort system summary", stdout.getvalue())
        self.assertIn("    set", stdout.getvalue())
        self.assertIn("      lid-close-behavior - Change Archie-managed lid close behavior.", stdout.getvalue())
        self.assertIn("lock after reopening", stdout.getvalue())


class KdeconnectDetectionTest(unittest.TestCase):
    def test_reports_on_when_backend_is_enabled(self) -> None:
        with patch("archie.system.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(
                [], 0, stdout="Bluetooth|AsyncLinkProvider|enabled\nLAN|LanLinkProvider|enabled\n"
            )

            self.assertEqual(detect_kdeconnect_state(), ON_VALUE)

            run.assert_called_once_with(
                ["kdeconnect-cli", "-b"],
                check=False,
                capture_output=True,
                text=True,
            )

    def test_reports_off_when_backends_are_disabled(self) -> None:
        with patch("archie.system.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(
                [], 0, stdout="Bluetooth|AsyncLinkProvider|disabled\nLAN|LanLinkProvider|disabled\n"
            )

            self.assertEqual(detect_kdeconnect_state(), OFF_VALUE)

    def test_set_kdeconnect_toggles_backends(self) -> None:
        with patch("archie.system.subprocess.run") as run:
            self.assertEqual(set_kdeconnect(ON_VALUE), 0)
            self.assertEqual(run.call_count, 2)
            run.assert_any_call(["kdeconnect-cli", "--enable-backend", "lan"], check=False)
            run.assert_any_call(["kdeconnect-cli", "--enable-backend", "bluetooth"], check=False)

        with patch("archie.system.subprocess.run") as run:
            self.assertEqual(set_kdeconnect(OFF_VALUE), 0)
            self.assertEqual(run.call_count, 2)
            run.assert_any_call(["kdeconnect-cli", "--disable-backend", "lan"], check=False)
            run.assert_any_call(["kdeconnect-cli", "--disable-backend", "bluetooth"], check=False)


class BrightnessCommandTest(unittest.TestCase):
    def test_formats_brightness_device_as_tab_separated_state(self) -> None:
        device = BrightnessDevice("amdgpu_bl1", current=181, maximum=255)

        self.assertEqual(format_brightness_device(device), "amdgpu_bl1\t71\t181\t255")

    def test_lists_backlight_device_names_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            backlight_path = Path(temp_dir)
            (backlight_path / "intel_backlight").mkdir()
            (backlight_path / "amdgpu_bl1").mkdir()

            self.assertEqual(
                list_backlight_device_names(backlight_path),
                ["amdgpu_bl1", "intel_backlight"],
            )

    def test_set_brightness_clamps_percent_and_runs_brightnessctl(self) -> None:
        commands: list[list[str]] = []

        def executor(command: list[str]) -> int:
            commands.append(command)
            return 0

        self.assertEqual(set_brightness("amdgpu_bl1", 137, executor=executor), 0)
        self.assertEqual(
            commands,
            [["brightnessctl", "--device", "amdgpu_bl1", "set", "100%"]],
        )
        self.assertEqual(clamp_brightness_percent(-1), 0)
        self.assertEqual(clamp_brightness_percent(55), 55)
        self.assertEqual(clamp_brightness_percent(101), 100)

    def test_run_system_get_prints_brightness_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            backlight_path = Path(temp_dir)
            (backlight_path / "amdgpu_bl1").mkdir()

            def fake_run(command, **_kwargs):
                if command[-1] == "get":
                    return subprocess.CompletedProcess(command, 0, stdout="181\n", stderr="")
                if command[-1] == "max":
                    return subprocess.CompletedProcess(command, 0, stdout="255\n", stderr="")
                return subprocess.CompletedProcess(command, 1, stdout="", stderr="unexpected")

            stdout = io.StringIO()
            with patch("archie.system.subprocess.run", side_effect=fake_run), redirect_stdout(stdout):
                code = run_system_get(argparse.Namespace(setting="brightness"), backlight_path=backlight_path)

            self.assertEqual(code, 0)
            self.assertEqual(stdout.getvalue(), "amdgpu_bl1\t71\t181\t255\n")

    def test_run_system_set_sets_brightness(self) -> None:
        commands: list[list[str]] = []

        def executor(command: list[str]) -> int:
            commands.append(command)
            return 0

        code = run_system_set(
            argparse.Namespace(setting="brightness", device="amdgpu_bl1", percent=43),
            executor=executor,
        )

        self.assertEqual(code, 0)
        self.assertEqual(commands, [["brightnessctl", "--device", "amdgpu_bl1", "set", "43%"]])

    def test_main_exposes_brightness_subcommand(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as error, redirect_stdout(stdout), redirect_stderr(stderr):
            main(["system", "set", "brightness", "--help"])

        self.assertEqual(error.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("usage: archie system set brightness", stdout.getvalue())
        self.assertIn("Brightness percentage", stdout.getvalue())
