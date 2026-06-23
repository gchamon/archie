import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from archie.cli import main
from archie.system import (
    HIBERNATE_MODE,
    LOCK_MODE,
    NONE_MODE,
    UNKNOWN_MODE,
    detect_lid_close_behavior,
    install_lid_close_behavior,
    reload_logind_if_active,
    run_system_get,
    run_system_set,
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
