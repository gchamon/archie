import io
import os
import subprocess
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import gi

gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GObject  # type: ignore[attr-defined]

from archie.cli import main
from archie.gui import (
    NOTIFICATION_BODY_MAX_HEIGHT,
    ArchieControlsWindow,
    can_write_store,
    filter_documentation_rows,
    filter_notifications,
    filter_shortcut_rows,
    get_notification_sound,
    get_notification_sounds_state,
    highlight_matches_markup,
    load_gui_settings_snapshot,
    load_gui_settings_snapshot_from_environment,
    load_main_tab_index,
    main_tab_id,
    main_tab_index,
    notification_shell_command,
    parse_brightness_devices,
    parse_markdown_table,
    save_main_tab,
    selected_font_family,
    snap_brightness_percent,
    store_write_warning,
)
from archie.gui_state import (
    GuiSettingsSnapshot,
    deserialize_gui_settings_snapshot,
    serialize_gui_settings_snapshot,
)
from archie.monitor import MonitorOutput
from archie.privacy import DunstHistoryResult, DunstNotification, ShyModeSettings
from archie.store import GUI_MAIN_TAB, PolicyStore, StoreDatabase


class CliExposureTest(unittest.TestCase):
    def test_calendar_launcher_accepts_only_constrained_presets(self) -> None:
        with patch("archie.system._set_calendar_launcher", return_value=0) as setter:
            self.assertEqual(
                main(["system", "set", "calendar-launcher", "gnome-calendar"]),
                0,
            )
            setter.assert_called_once()
            self.assertEqual(setter.call_args.args[:3], ("right", "gnome-calendar", ""))

        with patch("archie.system._set_calendar_launcher", return_value=0) as setter:
            self.assertEqual(
                main(
                    [
                        "system",
                        "set",
                        "calendar-launcher",
                        "browser-url",
                        "https://calendar.example/",
                    ]
                ),
                0,
            )
            self.assertEqual(
                setter.call_args.args[:3],
                ("right", "browser-url", "https://calendar.example/"),
            )

    def test_help_uses_command_metavar_instead_of_root_choice_tuple(self) -> None:
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as error, redirect_stdout(stdout):
            main(["--help"])

        self.assertEqual(error.exception.code, 0)
        self.assertIn("Archie system operational and maintenance tools.", stdout.getvalue())
        self.assertIn("positional arguments:\n  COMMAND", stdout.getvalue())
        self.assertNotIn("{applet,downgrade,gui,system}", stdout.getvalue())

    def test_nested_help_hides_long_setting_choice_tuple(self) -> None:
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as error, redirect_stdout(stdout):
            main(["system", "get", "--help"])

        self.assertEqual(error.exception.code, 0)
        self.assertIn("usage: archie system get [-h] setting ...", stdout.getvalue())
        self.assertNotIn("{lid-close-behavior,notifications", stdout.getvalue())

    def test_parse_error_restores_setting_choices_for_diagnostics(self) -> None:
        stderr = io.StringIO()
        with self.assertRaises(SystemExit) as error, redirect_stderr(stderr):
            main(["system", "get"])

        self.assertEqual(error.exception.code, 2)
        self.assertIn("{calendar-launcher,datetime-launcher,lid-close-behavior,notifications", stderr.getvalue())
        self.assertIn("the following arguments are required: setting", stderr.getvalue())

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

    def test_reads_notification_sound_from_the_system_cli(self) -> None:
        with patch("archie.gui.run_cli") as run_cli:
            run_cli.return_value = subprocess.CompletedProcess([], 0, "/usr/share/sounds/test.ogg\n", "")
            self.assertEqual(get_notification_sound(), "/usr/share/sounds/test.ogg")
            run_cli.assert_called_once_with(["archie", "system", "get", "notification-sound"])


class NotificationHistoryGuiStateTest(unittest.TestCase):
    def test_filters_displayed_notification_fields_case_insensitively(self) -> None:
        notifications = [
            DunstNotification("Mail", "Build complete", "Pipeline succeeded", datetime(2026, 1, 1, tzinfo=UTC)),
            DunstNotification("Chat", "Hello", "See you tomorrow", datetime(2026, 1, 2, tzinfo=UTC)),
        ]

        self.assertEqual(filter_notifications(notifications, "PIPELINE"), [notifications[0]])
        self.assertEqual(filter_notifications(notifications, "chat"), [notifications[1]])
        self.assertEqual(filter_notifications(notifications, ""), notifications)

    def test_individual_disclosure_expands_and_collapses_notification(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        notification = DunstNotification(
            "Mail",
            "Build complete",
            "Pipeline succeeded",
            datetime(2026, 1, 1, tzinfo=UTC),
        )
        window.notification_history = (notification,)
        window.expanded_notifications = set()
        window.notification_reveal_all_button = Mock()
        expander, label = Mock(), Mock()
        expander.get_expanded.side_effect = [True, False]

        window.on_notification_disclosure_changed(
            expander,
            None,
            notification,
            label,
        )

        self.assertEqual(window.expanded_notifications, {notification})
        label.set_text.assert_called_once_with("Hide content")
        window.notification_reveal_all_button.set_label.assert_called_once_with("Collapse all")

        label.reset_mock()
        window.notification_reveal_all_button.reset_mock()
        window.on_notification_disclosure_changed(
            expander,
            None,
            notification,
            label,
        )

        self.assertEqual(window.expanded_notifications, set())
        label.set_text.assert_called_once_with("Show content")
        window.notification_reveal_all_button.set_label.assert_called_once_with("Reveal all")

    def test_notification_title_stays_visible_and_body_is_scrollable(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        notification = DunstNotification(
            "Mail",
            "Build complete",
            "Pipeline succeeded " * 100,
            datetime(2026, 1, 1, tzinfo=UTC),
            notification_id=274,
        )
        window.expanded_notifications = set()
        row, information, source, actions, accordion_header = (
            Mock(), Mock(), Mock(), Mock(), Mock()
        )
        application, timestamp, summary, label, body = (
            Mock(), Mock(), Mock(), Mock(), Mock()
        )
        replay_button, shell_button, copy_button, expander, scroller = (
            Mock(), Mock(), Mock(), Mock(), Mock()
        )
        motion = Mock()
        window.Gtk = Mock()
        window.Gtk.Box.side_effect = [row, information, source, actions, accordion_header]
        window.Gtk.Label.side_effect = [application, timestamp, summary, label, body]
        window.Gtk.Expander.return_value = expander
        window.Gtk.ScrolledWindow.return_value = scroller
        window.Gtk.EventControllerMotion.return_value = motion
        window.Gtk.Button.side_effect = [replay_button, shell_button, copy_button]
        window.Pango = Mock()

        result = window.build_notification_row(notification)
        row.add_controller.assert_called_once_with(motion)
        self.assertEqual(
            [call.args[:2] for call in motion.connect.call_args_list],
            [
                ("enter", window.on_notification_row_pointer_enter),
                ("leave", window.on_notification_row_pointer_leave),
            ],
        )
        window.on_notification_row_pointer_enter(motion, 10, 20, row)
        row.add_css_class.assert_any_call("archie-notification-hover")
        window.on_notification_row_pointer_leave(motion, row)
        row.remove_css_class.assert_called_once_with("archie-notification-hover")

        self.assertIs(result, row)
        self.assertEqual(
            window.Gtk.Box.call_args_list[0].kwargs,
            {"orientation": window.Gtk.Orientation.HORIZONTAL, "spacing": 12},
        )
        self.assertEqual(
            window.Gtk.Box.call_args_list[1].kwargs,
            {"orientation": window.Gtk.Orientation.VERTICAL, "spacing": 3},
        )
        row.set_hexpand.assert_called_once_with(True)
        information.set_hexpand.assert_called_once_with(True)
        self.assertEqual(
            [call.args[0] for call in row.append.call_args_list],
            [information, actions],
        )
        self.assertEqual(
            [call.args[0] for call in information.append.call_args_list],
            [source, summary, expander],
        )
        self.assertEqual(
            [call.args[0] for call in actions.append.call_args_list],
            [replay_button, shell_button, copy_button],
        )
        self.assertEqual(
            [call.args[0] for call in source.append.call_args_list],
            [application, timestamp],
        )
        application.set_hexpand.assert_not_called()
        source.set_hexpand.assert_called_once_with(True)
        actions.set_valign.assert_called_once_with(window.Gtk.Align.START)
        actions.set_hexpand.assert_called_once_with(False)
        actions.set_size_request.assert_called_once_with(176, -1)
        actions.add_css_class.assert_called_once_with("archie-notification-actions")
        self.assertEqual(
            [
                call.kwargs["label"]
                for call in window.Gtk.Button.call_args_list
            ],
            ["Replay", "Check with a shell", "Copy"],
        )
        replay_button.connect.assert_called_once_with(
            "clicked",
            window.on_notification_replay_clicked,
            notification,
        )
        shell_button.connect.assert_called_once_with(
            "clicked",
            window.on_notification_check_with_shell_clicked,
            notification,
        )
        shell_button.set_tooltip_text.assert_called_once_with(
            f"copy: {notification_shell_command(notification)}"
        )
        copy_button.set_tooltip_text.assert_called_once_with(
            "Copy notification data to the clipboard."
        )
        copy_button.connect.assert_called_once_with(
            "clicked",
            window.on_notification_copy_clicked,
            notification,
        )
        expander.set_child.assert_called_once_with(scroller)
        expander.set_expanded.assert_called_once_with(False)
        expander.connect.assert_called_once_with(
            "notify::expanded",
            window.on_notification_disclosure_changed,
            notification,
            label,
        )
        body.set_hexpand.assert_called_once_with(True)
        label.set_xalign.assert_called_once_with(0)
        scroller.set_child.assert_called_once_with(body)
        scroller.set_propagate_natural_height.assert_called_once_with(True)
        scroller.set_max_content_height.assert_called_once_with(NOTIFICATION_BODY_MAX_HEIGHT)

    def test_replay_requests_selected_notification_from_dunst(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        notification = DunstNotification(
            "KDE Connect",
            "Phone linked",
            "",
            datetime(2026, 1, 1, tzinfo=UTC),
            notification_id=274,
        )
        window.set_status = Mock()

        with patch("archie.gui.DunstClient") as dunst_client:
            dunst_client.return_value.history_pop.return_value = True
            window.on_notification_replay_clicked(None, notification)

        dunst_client.return_value.history_pop.assert_called_once_with(274)
        window.set_status.assert_called_once_with(
            "Replayed KDE Connect notification with Dunst."
        )

    def test_shell_action_copies_command_that_prints_notification_text(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        notification = DunstNotification(
            "KDE Connect",
            "Build 'complete' $(printf injected)",
            "Body; printf injected",
            datetime(2026, 1, 1, tzinfo=UTC),
            notification_id=274,
        )
        window.set_status = Mock()
        clipboard = Mock()
        display = Mock()
        display.get_clipboard.return_value = clipboard

        with patch.object(Gdk.Display, "get_default", return_value=display):
            window.on_notification_check_with_shell_clicked(None, notification)

        value = clipboard.set.call_args.args[0]
        self.assertIsInstance(value, GObject.Value)
        result = subprocess.run(
            ["bash", "-c", value.get_string()],
            capture_output=True,
            check=True,
            text=True,
        )
        self.assertEqual(
            result.stdout,
            f"{notification.summary}\n{notification.body}\n",
        )
        window.set_status.assert_called_once_with(
            "Copied shell command for KDE Connect."
        )

    def test_copy_button_copies_notification_metadata_to_clipboard(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        notification = DunstNotification(
            "KDE Connect",
            "Phone linked",
            "Battery at 80%",
            datetime(2026, 1, 2, 3, 4, tzinfo=UTC),
            notification_id=274,
        )
        window.set_status = Mock()
        clipboard = Mock()
        display = Mock()
        display.get_clipboard.return_value = clipboard

        with patch.object(Gdk.Display, "get_default", return_value=display):
            window.on_notification_copy_clicked(None, notification)

        value = clipboard.set.call_args.args[0]
        self.assertIsInstance(value, GObject.Value)
        self.assertEqual(
            value.get_string(),
            "Application: KDE Connect\n"
            "Summary: Phone linked\n"
            "Body: Battery at 80%\n"
            "Timestamp: 2026-01-02T03:04:00+00:00\n"
            "Dunst ID: 274",
        )
        window.set_status.assert_called_once_with(
            "Copied notification data for KDE Connect."
        )

    def test_reveal_all_toggle_reserves_width_for_both_labels(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        window.Gtk = Mock()
        boxes = [Mock() for _ in range(3)]
        window.Gtk.Box.side_effect = boxes
        window.Gtk.Orientation.HORIZONTAL = 0
        window.Gtk.Orientation.VERTICAL = 1
        window.Gtk.PolicyType.NEVER = 0
        window.Gtk.PolicyType.AUTOMATIC = 1
        window.Gtk.ScrolledWindow.return_value = Mock()
        window.render_notification_history = Mock()
        window.Gtk.Button.return_value.create_pango_layout.return_value.get_pixel_size.side_effect = [
            (80, 20),
            (120, 20),
        ]

        window.build_notifications_tab()

        window.notification_reveal_all_button.set_size_request.assert_called_once_with(
            168, -1
        )
    def test_reveal_all_toggles_cached_notifications(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        window.notification_history = (
            DunstNotification("Mail", "Build complete", "", datetime(2026, 1, 1, tzinfo=UTC)),
            DunstNotification("Chat", "Hello", "See you tomorrow", datetime(2026, 1, 2, tzinfo=UTC)),
        )
        window.expanded_notifications = set()
        window.notification_reveal_all_button = Mock()
        window.render_notification_history = Mock()

        window.on_notification_toggle_all_clicked(None)

        self.assertEqual(window.expanded_notifications, set(window.notification_history))
        window.notification_reveal_all_button.set_label.assert_called_once_with("Collapse all")
        window.render_notification_history.assert_called_once_with()

        window.notification_reveal_all_button.reset_mock()
        window.render_notification_history.reset_mock()
        window.on_notification_toggle_all_clicked(None)

        self.assertEqual(window.expanded_notifications, set())
        window.notification_reveal_all_button.set_label.assert_called_once_with("Reveal all")
        window.render_notification_history.assert_called_once_with()

    def test_successful_refresh_prunes_expansion_for_removed_history(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        removed = DunstNotification("Mail", "Old", "", datetime(2026, 1, 1, tzinfo=UTC))
        retained = DunstNotification("Chat", "Current", "", datetime(2026, 1, 2, tzinfo=UTC))
        window.expanded_notifications = {removed, retained}
        window.notification_refresh_button = Mock()
        window.notification_reveal_all_button = Mock()
        window.render_notification_history = Mock()

        window.on_notification_history_loaded(DunstHistoryResult((retained,)))

        self.assertEqual(window.expanded_notifications, {retained})
        self.assertEqual(window.notification_history, (retained,))
        window.notification_reveal_all_button.set_label.assert_called_once_with("Collapse all")
        window.render_notification_history.assert_called_once_with()

    def test_clearing_history_clears_expansion_state(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        window.notification_reveal_all_button = Mock()
        window.notification_clear_button = Mock()
        window.notification_history = (
            DunstNotification("Mail", "Build complete", "", datetime(2026, 1, 1, tzinfo=UTC)),
        )
        window.expanded_notifications = set(window.notification_history)
        window.notification_history_error = "old error"
        window.set_status = Mock()
        window.render_notification_history = Mock()
        window.refresh_notification_history = Mock()

        window.on_notification_history_cleared(True)

        self.assertEqual(window.notification_history, ())
        self.assertEqual(window.expanded_notifications, set())
        self.assertIsNone(window.notification_history_error)
        window.notification_reveal_all_button.set_label.assert_called_once_with("Reveal all")
    def test_notification_poll_does_not_refresh_when_live_updates_are_disabled(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        window.notification_live_updates = False
        window.notification_poll_timeout_id = 12
        window.refresh_notification_history = Mock()

        self.assertFalse(window.poll_notification_history())
        self.assertIsNone(window.notification_poll_timeout_id)
        window.refresh_notification_history.assert_not_called()

    def test_clear_history_constructs_and_presents_a_modal_alert(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        window.Gtk = Mock()
        window.window = Mock()
        window.on_notification_clear_response = Mock()
        dialog = Mock()
        window.Gtk.AlertDialog.return_value = dialog

        window.on_notification_clear_clicked(None)

        window.Gtk.AlertDialog.assert_called_once_with(message="Clear all notification history?")
        dialog.set_detail.assert_called_once_with(
            "This permanently removes every notification stored by Dunst."
        )
        dialog.set_buttons.assert_called_once_with(["Cancel", "Clear history"])
        dialog.set_cancel_button.assert_called_once_with(0)
        dialog.set_default_button.assert_called_once_with(0)
        dialog.set_modal.assert_called_once_with(True)
        dialog.choose.assert_called_once_with(
            window.window,
            None,
            window.on_notification_clear_response,
        )

    def test_clear_history_only_starts_after_confirmation(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        window.notification_clear_button = Mock()
        window.run_cli_async = Mock()
        window.on_notification_history_cleared = Mock()
        dialog = Mock()
        result = Mock()
        dialog.choose_finish.return_value = 0

        window.on_notification_clear_response(dialog, result)

        window.notification_clear_button.set_sensitive.assert_not_called()
        window.run_cli_async.assert_not_called()

        dialog.choose_finish.return_value = 1
        window.on_notification_clear_response(dialog, result)

        window.notification_clear_button.set_sensitive.assert_called_once_with(False)
        window.run_cli_async.assert_called_once()


class SearchHighlightTest(unittest.TestCase):
    def test_highlights_all_case_insensitive_matches_and_escapes_markup(self) -> None:
        markup = highlight_matches_markup("Mail <ready> mail", "MAIL")

        self.assertEqual(
            markup,
            '<span background="#f9e2af" foreground="#1e1e2e" weight="bold">Mail</span> '
            "&lt;ready&gt; "
            '<span background="#f9e2af" foreground="#1e1e2e" weight="bold">mail</span>',
        )

    def test_highlight_escapes_special_characters_without_a_query(self) -> None:
        self.assertEqual(
            highlight_matches_markup("A < B & C", ""),
            "A &lt; B &amp; C",
        )


class GuiStoreAccessTest(unittest.TestCase):
    def test_reports_missing_store(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "store.sqlite3"

            self.assertFalse(can_write_store(path))
            warning = store_write_warning(path)
            self.assertTrue(warning is not None and "store is missing" in warning)

    def test_reports_store_permission_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "store.sqlite3"
            path.touch()

            with patch("archie.gui.os.access", return_value=False):
                self.assertFalse(can_write_store(path))
                warning = store_write_warning(path)

            self.assertTrue(
                warning is not None and "log out and back in or reboot" in warning
            )



class GuiRefreshTest(unittest.TestCase):
    def test_cached_controls_remain_visible_and_interactive_during_refresh(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        window.settings_loading = False
        window.settings_visible = True
        window.settings_revision = 4
        window.render_settings_loading = Mock()
        window.run_cli_async = Mock()

        self.assertFalse(window.refresh())

        window.render_settings_loading.assert_not_called()
        refresh_loader, refresh_callback = window.run_cli_async.call_args.args
        self.assertIs(refresh_loader, load_gui_settings_snapshot)
        window.on_settings_snapshot_loaded = Mock(return_value=False)
        snapshot = Mock()
        refresh_callback(snapshot)
        window.on_settings_snapshot_loaded.assert_called_once_with(snapshot, 4)

    def test_stale_refresh_waits_for_active_setting_change(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        window.settings_loading = True
        window.settings_revision = 2
        window.settings_changes_in_progress = 1
        window.settings_refresh_pending = False
        window.refresh = Mock()
        window.render_settings_snapshot = Mock()

        self.assertFalse(window.on_settings_snapshot_loaded(Mock(), 1))

        self.assertTrue(window.settings_refresh_pending)
        window.refresh.assert_not_called()
        window.render_settings_snapshot.assert_not_called()

        window.finish_settings_change()
        self.assertEqual(window.settings_changes_in_progress, 0)
        self.assertFalse(window.settings_refresh_pending)
        window.refresh.assert_called_once_with()

    def test_current_refresh_replaces_the_cached_snapshot(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        window.settings_loading = True
        window.settings_revision = 2
        window.settings_changes_in_progress = 0
        window.settings_refresh_pending = False
        window.render_settings_snapshot = Mock()
        snapshot = Mock()

        self.assertFalse(window.on_settings_snapshot_loaded(snapshot, 2))

        window.render_settings_snapshot.assert_called_once_with(
            snapshot, controls_enabled=True
        )


class MainTabPersistenceTest(unittest.TestCase):
    def test_persists_each_main_tab_and_defaults_invalid_values_to_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = StoreDatabase(Path(temp_dir) / "store.sqlite3")
            database.path.touch()
            store = PolicyStore(database)
            store.initialize()
            for index, tab_id in enumerate(
                (
                    "dashboard",
                    "system-settings",
                    "notifications",
                    "commands-shortcuts",
                    "quick-links",
                )
            ):
                self.assertEqual(main_tab_index(tab_id), index)
                self.assertEqual(main_tab_id(index), tab_id)
                save_main_tab(index, store)
                self.assertEqual(store.get(GUI_MAIN_TAB), tab_id)
                self.assertEqual(load_main_tab_index(store), index)

            store.set(GUI_MAIN_TAB, "unrecognized")
            self.assertEqual(load_main_tab_index(store), 0)
            self.assertEqual(main_tab_index("unrecognized"), 0)


    def test_switching_to_system_settings_persists_for_next_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = StoreDatabase(Path(temp_dir) / "store.sqlite3")
            database.path.touch()
            store = PolicyStore(database)
            store.initialize()
            window = object.__new__(ArchieControlsWindow)
            window.notifications_tab = object()
            window.stop_notification_polling = Mock()

            with patch("archie.gui.PolicyStore", return_value=store):
                window.on_main_tab_switched(Mock(), object(), 1)

            self.assertEqual(store.get(GUI_MAIN_TAB), "system-settings")
            self.assertEqual(load_main_tab_index(store), 1)

    def test_quick_links_open_archie_repository_and_github_profile(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        window.Gtk = Mock()
        root = window.Gtk.Box.return_value

        self.assertIs(window.build_quick_links_tab(), root)

        self.assertEqual(
            [call.args for call in window.Gtk.LinkButton.new_with_label.call_args_list],
            [
                (
                    "https://gitlab.com/gabriel.chamon/archie",
                    "Archie source repository",
                ),
                (
                    "https://github.com/gchamon",
                    "Gabriel Chamon on GitHub",
                ),
            ],
        )
        self.assertEqual(root.append.call_count, 3)
class GuiSettingsSnapshotTest(unittest.TestCase):
    def test_collects_settings_without_constructing_gtk_widgets(self) -> None:
        brightness = subprocess.CompletedProcess([], 0, "amdgpu_bl1\t71\t181\t255\n", "")
        shy_mode = ShyModeSettings(enabled=True, replay_count=4, replay_interval=2.5)
        monitors = [object()]
        readers_started = threading.Barrier(2)

        def synchronized(value):
            readers_started.wait(timeout=1)
            return value

        with (
            patch(
                "archie.gui.get_brightness_devices",
                side_effect=lambda: synchronized(brightness),
            ),
            patch("archie.gui.list_monitors", return_value=monitors),
            patch(
                "archie.gui.get_lid_behavior",
                side_effect=lambda: synchronized("lock"),
            ),
            patch("archie.gui.get_notifications_state", return_value="on"),
            patch("archie.gui.get_notification_sounds_state", return_value="off"),
            patch("archie.gui.get_notification_sound", return_value="default"),
            patch("archie.gui.get_shy_mode_settings", return_value=shy_mode),
            patch("archie.gui.get_kdeconnect_state", return_value="on"),
            patch("archie.gui.get_power_profile", return_value="balanced"),
            patch(
                "archie.gui.get_calendar_settings",
                return_value={
                    "left": ("unset", ""),
                    "right": ("gnome-calendar", ""),
                },
            ),
            patch("archie.gui.get_waybar_theme", return_value="tokyonight"),
            patch(
                "archie.gui.get_waybar_font",
                side_effect=lambda prefix: {
                    "waybar-font": ("JetBrains Mono", 18),
                    "waybar-menu-font": ("Cantarell", 16),
                    "waybar-tooltip-font": ("Adwaita Sans", 14),
                }[prefix],
            ),
            patch(
                "archie.gui.collect_connected_peripherals",
                return_value={"bluetooth": ["Headphones"], "usb": [], "network": []},
            ),
        ):
            snapshot = load_gui_settings_snapshot()

        self.assertIs(snapshot.brightness_result, brightness)
        self.assertEqual(snapshot.monitors, monitors)
        self.assertIsNone(snapshot.monitor_error)
        self.assertEqual(snapshot.lid_behavior, "lock")
        self.assertEqual(snapshot.notifications, "on")
        self.assertEqual(snapshot.notification_sounds, "off")
        self.assertEqual(snapshot.notification_sound, "default")
        self.assertEqual(snapshot.shy_mode, shy_mode)
        self.assertEqual(snapshot.kdeconnect, "on")
        self.assertEqual(snapshot.power_profile, "balanced")
        self.assertEqual(snapshot.calendar_left_preset, "unset")
        self.assertEqual(snapshot.calendar_left_browser_url, "")
        self.assertEqual(snapshot.calendar_right_preset, "gnome-calendar")
        self.assertEqual(snapshot.calendar_right_browser_url, "")
        self.assertEqual(snapshot.datetime_left_preset, "unset")
        self.assertEqual(snapshot.datetime_left_browser_url, "")
        self.assertEqual(snapshot.datetime_right_preset, "gnome-datetime")
        self.assertEqual(snapshot.datetime_right_browser_url, "")
        self.assertEqual(snapshot.waybar_theme, "tokyonight")
        self.assertEqual(snapshot.waybar_font_family, "JetBrains Mono")
        self.assertEqual(snapshot.waybar_font_size, 18)
        self.assertEqual(snapshot.waybar_menu_font_family, "Cantarell")
        self.assertEqual(snapshot.waybar_menu_font_size, 16)
        self.assertEqual(snapshot.waybar_tooltip_font_family, "Adwaita Sans")
        self.assertEqual(snapshot.waybar_tooltip_font_size, 14)
        self.assertEqual(
            snapshot.peripherals,
            {"bluetooth": ["Headphones"], "usb": [], "network": []},
        )

    def test_keeps_other_settings_when_monitor_discovery_fails(self) -> None:
        with (
            patch("archie.gui.get_brightness_devices", return_value=subprocess.CompletedProcess([], 0, "", "")),
            patch("archie.gui.list_monitors", side_effect=RuntimeError("Hyprland unavailable")),
            patch("archie.gui.get_lid_behavior", return_value="unknown"),
            patch("archie.gui.get_notifications_state", return_value="unknown"),
            patch("archie.gui.get_notification_sounds_state", return_value="unknown"),
            patch("archie.gui.get_notification_sound", return_value="default"),
            patch("archie.gui.get_shy_mode_settings", return_value=ShyModeSettings()),
            patch("archie.gui.get_kdeconnect_state", return_value="unknown"),
            patch("archie.gui.get_power_profile", return_value="unknown"),
            patch(
                "archie.gui.get_calendar_settings",
                return_value={
                    "left": ("unset", ""),
                    "right": ("gnome-calendar", ""),
                },
            ),
            patch("archie.gui.get_waybar_theme", return_value="unknown"),
            patch("archie.gui.get_waybar_font", return_value=("MesloLGM Nerd Font", 20)),
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
            notification_sound="default",
            shy_mode=ShyModeSettings(enabled=True, replay_count=4, replay_interval=2.5),
            share_state="off",
            kdeconnect="on",
            power_profile="balanced",
            calendar_left_preset="unset",
            calendar_left_browser_url="",
            calendar_right_preset="gnome-calendar",
            calendar_right_browser_url="",
            datetime_left_preset="unset",
            datetime_left_browser_url="",
            datetime_right_preset="gnome-datetime",
            datetime_right_browser_url="",
            waybar_theme="tokyonight",
            waybar_font_family="JetBrains Mono",
            waybar_font_size=18,
            waybar_menu_font_family="Cantarell",
            waybar_menu_font_size=16,
            waybar_tooltip_font_family="MesloLGM Nerd Font",
            waybar_tooltip_font_size=20,
            peripherals={"bluetooth": ["Headphones"], "usb": [], "network": []},
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
        self.assertEqual(restored.notification_sound, snapshot.notification_sound)
        self.assertEqual(restored.shy_mode, snapshot.shy_mode)
        self.assertEqual(restored.kdeconnect, snapshot.kdeconnect)
        self.assertEqual(restored.power_profile, snapshot.power_profile)
        self.assertEqual(restored.calendar_left_preset, snapshot.calendar_left_preset)
        self.assertEqual(restored.calendar_left_browser_url, snapshot.calendar_left_browser_url)
        self.assertEqual(restored.calendar_right_preset, snapshot.calendar_right_preset)
        self.assertEqual(restored.calendar_right_browser_url, snapshot.calendar_right_browser_url)
        self.assertEqual(restored.datetime_left_preset, snapshot.datetime_left_preset)
        self.assertEqual(restored.datetime_left_browser_url, snapshot.datetime_left_browser_url)
        self.assertEqual(restored.datetime_right_preset, snapshot.datetime_right_preset)
        self.assertEqual(restored.datetime_right_browser_url, snapshot.datetime_right_browser_url)
        self.assertEqual(restored.waybar_theme, snapshot.waybar_theme)
        self.assertEqual(restored.waybar_font_family, snapshot.waybar_font_family)
        self.assertEqual(restored.waybar_font_size, snapshot.waybar_font_size)
        self.assertEqual(restored.waybar_menu_font_family, snapshot.waybar_menu_font_family)
        self.assertEqual(restored.waybar_menu_font_size, snapshot.waybar_menu_font_size)
        self.assertEqual(restored.waybar_tooltip_font_family, snapshot.waybar_tooltip_font_family)
        self.assertEqual(restored.waybar_tooltip_font_size, snapshot.waybar_tooltip_font_size)
        self.assertEqual(restored.peripherals, snapshot.peripherals)
        self.assertEqual(restored.share_state, snapshot.share_state)

    def test_dashboard_renders_and_copies_all_visible_information(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        window.Gtk = Mock()
        window.dashboard_content = Mock()
        window.dashboard_copy_button = Mock()
        window.dashboard_copy_text = ""
        window.clear_box = Mock()
        window.set_status = Mock()
        snapshot = Mock()
        snapshot.brightness_result = subprocess.CompletedProcess(
            [], 0, "panel\t75\t75\t100\n", ""
        )
        snapshot.monitors = [
            MonitorOutput("eDP-1", "Built-in", 1920, 1080, 60.0, 0, 0, 1.0, 0, False, True)
        ]
        snapshot.peripherals = {
            "bluetooth": ["WH <1000> & headphones"],
            "usb": ["Integrated Camera"],
            "network": [{"device": "wlan0", "type": "wifi", "connection": "Home"}],
        }
        snapshot.lid_behavior = "lock"
        snapshot.kdeconnect = "on"
        snapshot.power_profile = "balanced"
        snapshot.waybar_theme = "tokyonight"
        snapshot.notifications = "on"
        snapshot.notification_sounds = "on"
        snapshot.share_state = "off"
        snapshot.shy_mode = ShyModeSettings()

        with patch("archie.gui.installed_archie_version", return_value="1.2.3"):
            window.render_dashboard(snapshot)

        rendered = [call.kwargs["label"] for call in window.Gtk.Label.call_args_list]
        self.assertIn("Hardware", rendered)
        self.assertIn("Bluetooth: WH <1000> & headphones", rendered)
        self.assertIn("USB: Integrated Camera", rendered)
        self.assertIn("Network: wifi wlan0: Home", rendered)
        self.assertIn("Current Archie configuration", rendered)
        self.assertIn("Power profile: balanced", rendered)
        self.assertIn("Share: off", rendered)
        self.assertNotIn("Managed by Archie", rendered)
        self.assertIn("Archie version: 1.2.3", rendered)
        window.Gtk.Label.return_value.set_markup.assert_any_call(
            "<b>Bluetooth:</b> WH &lt;1000&gt; &amp; headphones"
        )
        window.Gtk.Label.return_value.set_markup.assert_any_call(
            "<b>Power profile:</b> balanced"
        )
        self.assertEqual(window.dashboard_content.append.call_args_list[0].args[0],
                         window.dashboard_copy_button)

        clipboard = Mock()
        display = Mock()
        display.get_clipboard.return_value = clipboard
        with patch.object(Gdk.Display, "get_default", return_value=display):
            window.on_dashboard_copy_clicked(None)

        clipboard_value = clipboard.set.call_args.args[0]
        self.assertIsInstance(clipboard_value, GObject.Value)
        self.assertEqual(
            clipboard_value.get_string(),
            "Hardware\n"
            "Brightness: panel 75%\n"
            "Monitors: eDP-1 Built-in: enabled (focused)\n"
            "Bluetooth: WH <1000> & headphones\n"
            "USB: Integrated Camera\n"
            "Network: wifi wlan0: Home\n\n"
            "Current Archie configuration\n"
            "Lid close behavior: lock\n"
            "KDE Connect: on\n"
            "Power profile: balanced\n"
            "Waybar theme: tokyonight\n"
            "Notifications: on\n"
            "Notification sounds: on\n"
            "Share: off\n"
            "Shy mode: off\n\n"
            "Archie version: 1.2.3",
        )
        window.set_status.assert_called_once_with("Dashboard information copied.")

    def test_dashboard_copy_is_unavailable_while_loading(self) -> None:
        window = object.__new__(ArchieControlsWindow)
        window.Gtk = Mock()
        window.dashboard_content = Mock()
        window.dashboard_copy_button = Mock()
        window.clear_box = Mock()
        window._copy_text_to_clipboard = Mock()
        window.set_status = Mock()

        window.render_dashboard(None)
        window.on_dashboard_copy_clicked(None)

        window.dashboard_copy_button.set_sensitive.assert_called_once_with(False)
        window._copy_text_to_clipboard.assert_not_called()
        window.set_status.assert_not_called()

    def test_font_selector_uses_only_the_selected_family(self) -> None:
        description = Mock()
        description.get_family.return_value = "JetBrains Mono"
        font_button = Mock()
        font_button.get_font_desc.return_value = description

        self.assertEqual(selected_font_family(font_button), "JetBrains Mono")

    def test_ignores_malformed_applet_snapshot_environment(self) -> None:
        with patch.dict(os.environ, {"ARCHIE_GUI_SETTINGS_SNAPSHOT": "not json"}, clear=False):
            self.assertIsNone(load_gui_settings_snapshot_from_environment())

        with patch.dict(
            os.environ,
            {"ARCHIE_GUI_SETTINGS_SNAPSHOT": '{"version": 4}'},
            clear=False,
        ):
            self.assertIsNone(load_gui_settings_snapshot_from_environment())
