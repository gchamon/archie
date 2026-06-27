import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from archie.cli import main
from archie.gui import filter_documentation_rows, filter_shortcut_rows, parse_markdown_table


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
