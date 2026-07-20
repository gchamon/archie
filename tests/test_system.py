import argparse
import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from archie.cli import main
from archie.system import (
    BrightnessDevice,
    HIBERNATE_MODE,
    LOCK_MODE,
    NONE_MODE,
    OFF_VALUE,
    ON_VALUE,
    UNKNOWN_MODE,
    clamp_brightness_percent,
    detect_lid_close_behavior,
    detect_kdeconnect_state,
    format_brightness_device,
    install_lid_close_behavior,
    list_backlight_device_names,
    reload_logind_if_active,
    run_system_get,
    run_system_set,
    set_brightness,
)


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
        self.assertIn("      lid-close-behavior - Read Archie-managed lid close behavior.", stdout.getvalue())
        self.assertIn("    set", stdout.getvalue())
        self.assertIn("      lid-close-behavior - Change Archie-managed lid close behavior.", stdout.getvalue())
        self.assertIn("lock after reopening", stdout.getvalue())


class KdeconnectDetectionTest(unittest.TestCase):
    def test_reports_on_when_autostart_unit_is_active(self) -> None:
        with patch("archie.system.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0)

            self.assertEqual(detect_kdeconnect_state(), ON_VALUE)

            run.assert_called_once_with(
                ["systemctl", "--user", "is-active", "--quiet", "app-org.kde.kdeconnect.daemon@autostart.service"],
                check=False,
            )

    def test_reports_off_when_units_are_inactive_even_if_stale_process_exists(self) -> None:
        with patch("archie.system.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 3)

            self.assertEqual(detect_kdeconnect_state(), OFF_VALUE)

            self.assertEqual(run.call_count, 2)


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
