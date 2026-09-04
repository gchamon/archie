import argparse
import importlib.resources
import os
import signal
import subprocess
import threading
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from archie.applet_bus import (
    get_applet_version,
    notify_applet_settings_changed,
    restart_applet,
)
from archie.gui_state import (
    GUI_SETTINGS_SNAPSHOT_ENV,
    GuiSettingsSnapshot,
    deserialize_gui_settings_snapshot,
)
from archie.monitor import (
    MonitorOutput,
    apply_monitor_toggle,
    list_monitors,
    restore_monitors,
)
from archie.privacy import ShyModeSettings
from archie.store import STORE_DATABASE_PATH
from archie.system import (
    HIBERNATE_MODE,
    LOCK_MODE,
    NONE_MODE,
    OFF_VALUE,
    ON_VALUE,
    POWER_PROFILES,
    WAYBAR_THEMES,
)
from archie.version import applet_update_required, installed_archie_version

LID_BEHAVIORS = [HIBERNATE_MODE, LOCK_MODE, NONE_MODE]
TOGGLE_VALUES = [ON_VALUE, OFF_VALUE]
KEYBOARD_SHORTCUTS_PATHS = [
    Path.cwd() / "docs/user/KEYBOARD_SHORTCUTS.md",
    Path(__file__).resolve().parents[2] / "docs/user/KEYBOARD_SHORTCUTS.md",
    Path("/usr/share/doc/archie-cli/KEYBOARD_SHORTCUTS.md"),
]
SHELL_COMMANDS_PATHS = [
    Path.cwd() / "deployment-packages/local/lib/zsh/README.md",
    Path(__file__).resolve().parents[2] / "deployment-packages/local/lib/zsh/README.md",
    Path("/usr/share/doc/archie-cli/ZSH_COMMANDS.md"),
]
BRIGHTNESS_DEBOUNCE_MS = 500


@dataclass(frozen=True)
class GuiBrightnessDevice:
    name: str
    percent: int
    current: int
    maximum: int


def add_gui_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "gui",
        help="Open Archie graphical controls.",
        description="Open Archie graphical controls.",
    )
    parser.set_defaults(func=run_gui)


def run_gui(_args: argparse.Namespace) -> int:
    application = build_application()
    signal.signal(signal.SIGINT, lambda *_args: application.quit())
    signal.signal(signal.SIGTERM, lambda *_args: application.quit())
    try:
        return application.run([])
    except KeyboardInterrupt:
        print("archie gui interrupted", flush=True)
        return 0


def build_application():
    import gi

    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk  # type: ignore[attr-defined]

    class ArchieGui(Gtk.Application):
        def __init__(self) -> None:
            super().__init__(application_id="com.gchamon.Archie.Gui")
            self.window = None

        def do_activate(self) -> None:
            if self.window is None:
                self.window = ArchieControlsWindow(self)
            self.window.present()

    return ArchieGui()


class ArchieControlsWindow:
    def __init__(self, application) -> None:
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gio, GLib, Gtk, Pango  # type: ignore[attr-defined]

        self.Gio = Gio
        self.Gtk = Gtk
        self.GLib = GLib
        self.Pango = Pango
        self.application = application
        self.monitors: list[MonitorOutput] = []
        self.pending_snapshot: list[MonitorOutput] | None = None
        self.pending_timeout_id: int | None = None
        self.brightness_timeout_ids: dict[str, int] = {}
        self.documentation_tabs: dict[str, tuple[str, object]] = {}
        self.store_write_warning: str | None = None
        self.settings_loading = False
        self.settings_visible = False
        self.settings_revision = 0
        self.settings_changes_in_progress = 0
        self.settings_refresh_pending = False
        self.brightness_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.monitor_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.lid_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.lid_box.add_css_class("archie-lid-segments")
        self.lid_box.add_css_class("linked")
        self.notifications_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.notifications_box.add_css_class("archie-lid-segments")
        self.notifications_box.add_css_class("linked")
        self.notification_sounds_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.notification_sounds_box.add_css_class("archie-lid-segments")
        self.notification_sounds_box.add_css_class("linked")
        self.notification_sound_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.shy_mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.shy_mode_box.add_css_class("archie-lid-segments")
        self.shy_mode_box.add_css_class("linked")
        self.shy_mode_status = Gtk.Label()
        self.shy_mode_status.set_xalign(0)
        self.shy_mode_status.set_wrap(True)
        self.shy_mode_status.set_sensitive(False)
        self.kdeconnect_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.kdeconnect_box.add_css_class("archie-lid-segments")
        self.kdeconnect_box.add_css_class("linked")
        self.power_profile_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.power_profile_box.add_css_class("archie-lid-segments")
        self.power_profile_box.add_css_class("linked")
        self.waybar_theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.waybar_theme_box.add_css_class("archie-lid-segments")
        self.waybar_theme_box.add_css_class("linked")
        self.waybar_font_dialog = Gtk.FontDialog()
        self.waybar_font_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.waybar_menu_font_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.waybar_tooltip_font_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.message_buffer = Gtk.TextBuffer()
        self.message_view = Gtk.TextView(buffer=self.message_buffer)
        self.message_view.set_editable(False)
        self.message_view.set_cursor_visible(False)
        self.message_view.set_wrap_mode(Gtk.WrapMode.NONE)
        self.message_view.add_css_class("archie-message-view")
        self._message_selection: tuple[int, int] | None = None
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect("leave", self._on_message_view_focus_leave)
        self.message_view.add_controller(focus_controller)
        self.message_scroller = Gtk.ScrolledWindow()
        self.message_scroller.set_min_content_height(84)
        self.message_scroller.set_max_content_height(84)
        self.message_scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.message_scroller.set_child(self.message_view)
        self.message_scroller.add_css_class("archie-message-scroller")
        self.confirm_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.applet_restart_pending = False
        self.applet_restart_attempts = 0
        self.update_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.update_bar.add_css_class("archie-update-bar")
        self.archie_version_label = Gtk.Label()
        self.archie_version_label.set_xalign(0)
        self.archie_version_label.set_hexpand(True)
        self.update_notice_label = Gtk.Label(label="Update installed. Restart the applet to apply it.")
        self.update_notice_label.set_xalign(0)
        self.restart_applet_button = Gtk.Button(label="Restart to update")
        self.restart_applet_button.connect("clicked", self.on_restart_applet_clicked)
        self.update_bar.append(self.archie_version_label)
        self.update_bar.append(self.update_notice_label)
        self.update_bar.append(self.restart_applet_button)
        self.render_applet_update_state(None)

        self.window = Gtk.ApplicationWindow(application=application)
        self.window.set_title("Archie Controls")
        self.window.set_default_size(520, 360)
        self.window.connect("close-request", self._on_close_request)
        self.install_css()
        self.window.set_child(self.build_content())
        self._install_copy_shortcut()
        if snapshot := load_gui_settings_snapshot_from_environment():
            self.render_settings_snapshot(snapshot, controls_enabled=True)
        self.GLib.timeout_add(50, self.refresh)
        self.GLib.timeout_add(50, self.refresh_applet_update_state)

    def present(self) -> None:
        self.window.present()

    def _on_close_request(self, _window) -> bool:
        self.application.window = None
        return False

    def build_content(self):
        Gtk = self.Gtk
        notebook = Gtk.Notebook()
        notebook.set_tab_pos(Gtk.PositionType.TOP)
        notebook.append_page(self.build_system_settings_tab(), Gtk.Label(label="System settings"))
        notebook.append_page(
            self.build_documentation_table_tab(
                tab_id="keyboard-shortcuts",
                search_placeholder="Search keyboard shortcuts",
                read_markdown=read_keyboard_shortcuts_markdown,
            ),
            Gtk.Label(label="Keyboard shortcuts"),
        )
        notebook.append_page(
            self.build_documentation_table_tab(
                tab_id="shell-commands",
                search_placeholder="Search shell commands",
                read_markdown=read_shell_commands_markdown,
            ),
            Gtk.Label(label="Shell commands"),
        )
        return notebook

    def build_system_settings_tab(self):
        Gtk = self.Gtk
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        root.set_margin_top(14)
        root.set_margin_bottom(14)
        root.set_margin_start(14)
        root.set_margin_end(14)

        self.system_settings_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.system_settings_content.set_vexpand(True)
        root.append(self.system_settings_content)
        self.render_settings_loading()

        logs_label = Gtk.Label(label="Logs:")
        logs_label.set_xalign(0)
        root.append(logs_label)
        root.append(self.message_scroller)
        root.append(self.confirm_box)
        root.append(self.update_bar)

        return root

    def build_system_settings_options(self):
        Gtk = self.Gtk
        options = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        options.append(self.build_setting_row("Screen brightness:", self.brightness_box))
        options.append(self.build_setting_row("Monitors:", self.monitor_box))
        options.append(self.build_setting_row("Lid close behavior:", self.lid_box))
        options.append(self.build_setting_row("Notifications:", self.notifications_box))
        options.append(self.build_setting_row("Notification sounds:", self.notification_sounds_box))
        options.append(self.build_setting_row("Notification sound:", self.notification_sound_box))
        options.append(self.build_setting_row("Shy mode:", self.shy_mode_box))
        options.append(self.shy_mode_status)
        options.append(self.build_setting_row("KDE Connect:", self.kdeconnect_box))
        options.append(self.build_setting_row("Power profile:", self.power_profile_box))
        options.append(self.build_setting_row("Waybar theme:", self.waybar_theme_box))
        options.append(self.build_setting_row("Waybar elements:", self.waybar_font_box))
        options.append(self.build_setting_row("Context menus:", self.waybar_menu_font_box))
        options.append(self.build_setting_row("Tooltips:", self.waybar_tooltip_font_box))

        options_scroller = Gtk.ScrolledWindow()
        options_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        options_scroller.set_vexpand(True)
        options_scroller.set_child(options)
        return options_scroller

    def build_setting_row(self, label_text: str, control):
        row = self.Gtk.Box(orientation=self.Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("archie-setting-row")
        label = self.Gtk.Label(label=label_text)
        label.set_xalign(0)
        label.set_hexpand(True)
        control.set_halign(self.Gtk.Align.END)
        row.append(label)
        row.append(control)
        return row

    def build_documentation_table_tab(self, tab_id: str, search_placeholder: str, read_markdown):
        Gtk = self.Gtk
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        root.set_margin_top(12)
        root.set_margin_bottom(12)
        root.set_margin_start(12)
        root.set_margin_end(12)

        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text(search_placeholder)
        search_entry.connect("search-changed", self.on_documentation_search_changed, tab_id)
        root.append(search_entry)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_top(2)
        content.set_margin_bottom(2)
        content.set_margin_start(2)
        content.set_margin_end(2)

        try:
            markdown = read_markdown()
        except FileNotFoundError as error:
            label = Gtk.Label(label=str(error))
            label.set_xalign(0)
            label.add_css_class("archie-shortcuts-error")
            content.append(label)
        else:
            self.documentation_tabs[tab_id] = (markdown, content)
            self.render_documentation_tables(markdown, content, "")

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        scroller.set_child(content)
        root.append(scroller)
        return root

    def render_documentation_tables(self, markdown: str, content, query: str) -> None:
        query = query.casefold().strip()
        lines = markdown.splitlines()
        index = 0
        while index < len(lines):
            line = lines[index]
            if line.startswith("# "):
                index += 1
                continue
            if line.startswith("## "):
                heading = self.Gtk.Label(label=line.removeprefix("## ").strip())
                heading.set_xalign(0)
                heading.add_css_class("archie-shortcuts-heading")
                content.append(heading)
                index += 1
                continue
            if line.startswith("|"):
                table_lines: list[str] = []
                while index < len(lines) and lines[index].startswith("|"):
                    table_lines.append(lines[index])
                    index += 1
                self.render_documentation_table(table_lines, content, query)
                continue
            index += 1

    def render_documentation_table(self, table_lines: Sequence[str], content, query: str) -> None:
        rows = parse_markdown_table(table_lines)
        if not rows:
            return
        header = rows[0]
        body = filter_documentation_rows(rows[1:], query)
        if not body:
            return
        grid = self.Gtk.Grid(column_spacing=10, row_spacing=6)
        grid.add_css_class("archie-shortcuts-grid")
        for row_index, row in enumerate([header, *body]):
            for column_index, value in enumerate(row):
                label = self.Gtk.Label(label=value)
                label.set_xalign(0)
                label.set_yalign(0)
                label.set_wrap(True)
                label.set_selectable(True)
                if row_index == 0:
                    label.add_css_class("archie-shortcuts-header")
                else:
                    label.add_css_class("archie-shortcuts-cell")
                grid.attach(label, column_index, row_index, 1, 1)
        content.append(grid)

    def on_documentation_search_changed(self, search_entry, tab_id: str) -> None:
        tab_state = self.documentation_tabs.get(tab_id)
        if tab_state is None:
            return
        markdown, content = tab_state
        self.clear_box(content)
        self.render_documentation_tables(markdown, content, search_entry.get_text())

    def refresh(self) -> bool:
        if self.settings_loading:
            return False
        self.settings_loading = True
        if not self.settings_visible:
            self.render_settings_loading()
        refresh_revision = self.settings_revision
        self.run_cli_async(
            load_gui_settings_snapshot,
            lambda snapshot: self.on_settings_snapshot_loaded(snapshot, refresh_revision),
        )
        return False

    def refresh_applet_update_state(self) -> bool:
        self.run_cli_async(get_applet_version, self.on_applet_version_loaded)
        return False

    def on_applet_version_loaded(self, running_version: str | None) -> bool:
        self.render_applet_update_state(running_version)
        if not self.applet_restart_pending:
            return False
        if running_version == installed_archie_version():
            self.applet_restart_pending = False
            self.set_status("Applet restarted with the installed update.")
        elif self.applet_restart_attempts < 10:
            self.applet_restart_attempts += 1
            self.GLib.timeout_add_seconds(1, self.refresh_applet_update_state)
        else:
            self.applet_restart_pending = False
            self.set_status("Applet restart is taking longer than expected.")
        return False

    def render_applet_update_state(self, running_version: str | None) -> None:
        installed_version = installed_archie_version()
        self.archie_version_label.set_label(f"Archie {installed_version}")
        update_pending = applet_update_required(running_version, installed_version)
        self.update_notice_label.set_visible(update_pending)
        self.restart_applet_button.set_visible(update_pending)
        if update_pending:
            self.update_bar.add_css_class("archie-update-pending")
        else:
            self.update_bar.remove_css_class("archie-update-pending")

    def on_restart_applet_clicked(self, _button) -> None:
        self.restart_applet_button.set_sensitive(False)
        self.set_status("Restarting applet to apply the installed update…")
        self.run_cli_async(restart_applet, self.on_restart_applet_done)

    def on_restart_applet_done(self, restarted: bool) -> bool:
        self.restart_applet_button.set_sensitive(True)
        if not restarted:
            self.set_status("Could not reach the running Archie applet.")
            return False
        self.applet_restart_pending = True
        self.applet_restart_attempts = 0
        self.GLib.timeout_add_seconds(1, self.refresh_applet_update_state)
        return False

    def render_settings_loading(self) -> None:
        self.clear_box(self.system_settings_content)
        loading_box = self.Gtk.Box(orientation=self.Gtk.Orientation.VERTICAL)
        loading_box.set_vexpand(True)
        loading_pill = self.Gtk.Button(label="Loading system settings…")
        loading_pill.set_sensitive(False)
        loading_pill.set_halign(self.Gtk.Align.CENTER)
        loading_pill.set_valign(self.Gtk.Align.CENTER)
        loading_pill.set_vexpand(True)
        loading_pill.add_css_class("archie-loading-pill")
        loading_box.append(loading_pill)
        self.system_settings_content.append(loading_box)

    def on_settings_snapshot_loaded(
        self, snapshot: GuiSettingsSnapshot, refresh_revision: int
    ) -> bool:
        self.settings_loading = False
        if refresh_revision != self.settings_revision:
            if self.settings_changes_in_progress:
                self.settings_refresh_pending = True
            else:
                self.refresh()
            return False
        self.render_settings_snapshot(snapshot, controls_enabled=True)
        return False

    def begin_settings_change(self) -> None:
        self.settings_revision += 1
        self.settings_changes_in_progress += 1

    def finish_settings_change(self) -> None:
        self.settings_changes_in_progress -= 1
        if self.settings_changes_in_progress == 0 and self.settings_refresh_pending:
            self.settings_refresh_pending = False
            self.refresh()

    def render_settings_snapshot(self, snapshot: GuiSettingsSnapshot, *, controls_enabled: bool) -> None:
        self.clear_box(self.brightness_box)
        self.clear_box(self.monitor_box)
        self.clear_box(self.lid_box)
        self.clear_box(self.notifications_box)
        self.clear_box(self.notification_sounds_box)
        self.clear_box(self.notification_sound_box)
        self.clear_box(self.shy_mode_box)
        self.clear_box(self.kdeconnect_box)
        self.clear_box(self.power_profile_box)
        self.clear_box(self.waybar_theme_box)
        self.clear_box(self.waybar_font_box)
        self.clear_box(self.waybar_menu_font_box)
        self.clear_box(self.waybar_tooltip_font_box)
        self.render_brightness(snapshot.brightness_result)
        self.monitors = snapshot.monitors
        if snapshot.monitor_error is None:
            self.render_monitors()
        else:
            self.set_status(f"Monitor error: {snapshot.monitor_error}")
        self.render_lid_behavior(snapshot.lid_behavior)
        self.render_notifications(snapshot.notifications)
        self.render_notification_sounds(snapshot.notification_sounds)
        self.render_notification_sound(snapshot.notification_sound)
        self.render_shy_mode(snapshot.shy_mode)
        self.render_kdeconnect(snapshot.kdeconnect)
        self.render_power_profile(snapshot.power_profile)
        self.render_waybar_theme(snapshot.waybar_theme)
        self.render_waybar_font(
            self.waybar_font_box,
            "Waybar elements",
            "waybar-font",
            snapshot.waybar_font_family,
            snapshot.waybar_font_size,
        )
        self.render_waybar_font(
            self.waybar_menu_font_box,
            "Context menu",
            "waybar-menu-font",
            snapshot.waybar_menu_font_family,
            snapshot.waybar_menu_font_size,
        )
        self.render_waybar_font(
            self.waybar_tooltip_font_box,
            "Tooltip",
            "waybar-tooltip-font",
            snapshot.waybar_tooltip_font_family,
            snapshot.waybar_tooltip_font_size,
        )
        self.clear_box(self.system_settings_content)
        self.system_settings_content.append(self.build_system_settings_options())
        self.settings_visible = True
        self.set_system_settings_sensitive(controls_enabled)
        self.report_store_write_access()

    def report_store_write_access(self) -> None:
        warning = store_write_warning()
        if warning == self.store_write_warning:
            return
        self.store_write_warning = warning
        if warning is not None:
            self.set_status(warning)

    def set_system_settings_sensitive(self, sensitive: bool) -> None:
        for box in (
            self.brightness_box,
            self.monitor_box,
            self.lid_box,
            self.notifications_box,
            self.notification_sounds_box,
            self.notification_sound_box,
            self.shy_mode_box,
            self.kdeconnect_box,
            self.power_profile_box,
            self.waybar_theme_box,
            self.waybar_font_box,
            self.waybar_menu_font_box,
            self.waybar_tooltip_font_box,
        ):
            self.set_box_sensitive(box, sensitive)

    def render_monitors(self) -> None:
        for monitor in self.monitors:
            button = self.Gtk.Button(label=monitor.name)
            button.set_tooltip_text(monitor.label)
            if monitor.enabled:
                button.add_css_class("suggested-action")
            else:
                button.add_css_class("flat")
            button.connect("clicked", self.on_monitor_clicked, monitor.name)
            self.monitor_box.append(button)

    def render_brightness(self, result: subprocess.CompletedProcess[str] | None = None) -> None:
        if result is None:
            result = get_brightness_devices()
        if result.returncode != 0:
            self.render_brightness_unavailable("Brightness unavailable.")
            self.set_status(f"Brightness error: {result.stderr.strip()}")
            return
        devices = parse_brightness_devices(result.stdout)
        if not devices:
            self.render_brightness_unavailable("No screen backlight detected.")
            return
        for device in devices:
            self.render_brightness_row(device)

    def render_brightness_unavailable(self, message: str) -> None:
        label = self.Gtk.Label(label=message)
        label.set_xalign(0)
        label.set_sensitive(False)
        self.brightness_box.append(label)

    def render_brightness_row(self, device: GuiBrightnessDevice) -> None:
        Gtk = self.Gtk
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.add_css_class("archie-brightness-row")

        name_label = Gtk.Label(label=device.name)
        name_label.set_xalign(0)
        name_label.set_width_chars(14)
        row.append(name_label)

        adjustment = Gtk.Adjustment(
            value=snap_brightness_percent(device.percent),
            lower=0,
            upper=100,
            step_increment=10,
            page_increment=10,
            page_size=0,
        )
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        scale.set_size_request(220, -1)
        scale.set_digits(0)
        scale.set_draw_value(False)
        scale.connect("value-changed", self.on_brightness_changed, device.name)
        row.append(scale)

        value_label = Gtk.Label(label=f"{snap_brightness_percent(device.percent)}%")
        value_label.set_width_chars(4)
        value_label.set_xalign(1)
        scale.connect("value-changed", self.on_brightness_label_changed, value_label)
        row.append(value_label)

        self.brightness_box.append(row)

    def render_lid_behavior(self, active: str | None = None) -> None:
        if active is None:
            active = get_lid_behavior()
        for index, behavior in enumerate(LID_BEHAVIORS):
            button = self.Gtk.ToggleButton(label=behavior)
            if index == 0:
                button.add_css_class("archie-segment-left")
            elif index == len(LID_BEHAVIORS) - 1:
                button.add_css_class("archie-segment-right")
            else:
                button.add_css_class("archie-segment-middle")
            button.set_active(behavior == active)
            button.connect("clicked", self.on_lid_clicked, behavior)
            self.lid_box.append(button)

    def on_monitor_clicked(self, _button, monitor_name: str) -> None:
        if self.pending_snapshot is not None:
            self.set_status("Confirm or revert the current monitor change first.")
            return
        self.begin_settings_change()
        try:
            self.pending_snapshot = apply_monitor_toggle(self.monitors, monitor_name)
        except Exception as error:
            self.set_status(str(error))
            self.finish_settings_change()
            return
        notify_applet_settings_changed()
        self.set_status("Confirm monitor layout within 10 seconds.")
        self.render_confirmation()
        self.pending_timeout_id = self.add_timeout(10, self.revert_pending_change)
        self.refresh_monitor_buttons_only()
        self.finish_settings_change()

    def render_confirmation(self) -> None:
        self.clear_box(self.confirm_box)
        confirm = self.Gtk.Button(label="Confirm")
        confirm.add_css_class("suggested-action")
        confirm.connect("clicked", self.confirm_pending_change)
        revert = self.Gtk.Button(label="Revert")
        revert.connect("clicked", self.revert_pending_change)
        self.confirm_box.append(confirm)
        self.confirm_box.append(revert)

    def confirm_pending_change(self, *_args) -> bool:
        self.pending_snapshot = None
        self.clear_box(self.confirm_box)
        self.set_status("Monitor layout confirmed.")
        self.refresh()
        return False

    def revert_pending_change(self, *_args) -> bool:
        if self.pending_snapshot is not None:
            self.begin_settings_change()
            try:
                restore_monitors(self.pending_snapshot)
                notify_applet_settings_changed()
                self.set_status("Monitor layout restored.")
            except Exception as error:
                self.set_status(f"Restore failed: {error}")
            self.finish_settings_change()
        self.pending_snapshot = None
        self.clear_box(self.confirm_box)
        self.refresh()
        return False

    def on_lid_clicked(self, _button, behavior: str) -> None:
        self.begin_settings_change()
        self.set_box_sensitive(self.lid_box, False)
        self.set_status(f"Setting lid close behavior to {behavior}...")
        self.run_cli_async(
            lambda: set_lid_behavior(behavior),
            lambda result: self.on_lid_set_done(result, behavior),
        )

    def on_lid_set_done(self, result: subprocess.CompletedProcess[str], behavior: str) -> bool:
        if result.returncode == 0:
            self.set_status(f"Lid close behavior set to {behavior}.")
            notify_applet_settings_changed()
        else:
            self.set_status(lid_error_message(result))
        self.clear_box(self.lid_box)
        self.render_lid_behavior()
        self.finish_settings_change()
        return False

    def render_toggle_row(self, box, active_value: str, on_clicked) -> None:
        for index, value in enumerate(TOGGLE_VALUES):
            button = self.Gtk.ToggleButton(label=value)
            if index == 0:
                button.add_css_class("archie-segment-left")
            else:
                button.add_css_class("archie-segment-right")
            button.set_active(value == active_value)
            button.connect("clicked", on_clicked, value)
            box.append(button)

    def render_segmented_row(self, box, values: list[str], active_value: str, on_clicked) -> None:
        for index, value in enumerate(values):
            button = self.Gtk.ToggleButton(label=value)
            if index == 0:
                button.add_css_class("archie-segment-left")
            elif index == len(values) - 1:
                button.add_css_class("archie-segment-right")
            else:
                button.add_css_class("archie-segment-middle")
            button.set_active(value == active_value)
            button.connect("clicked", on_clicked, value)
            box.append(button)

    def render_notifications(self, active: str | None = None) -> None:
        if active is None:
            active = get_notifications_state()
        self.render_toggle_row(self.notifications_box, active, self.on_notifications_clicked)

    def render_notification_sounds(self, active: str | None = None) -> None:
        if active is None:
            active = get_notification_sounds_state()
        self.render_toggle_row(
            self.notification_sounds_box,
            active,
            self.on_notification_sounds_clicked,
        )

    def render_notification_sound(self, value: str | None = None) -> None:
        if value is None:
            value = get_notification_sound()
        label = self.Gtk.Label(label="Bundled default" if value == "default" else value)
        label.set_xalign(0)
        label.set_hexpand(True)
        label.set_ellipsize(3)
        label.set_tooltip_text("Bundled default" if value == "default" else value)
        choose_button = self.Gtk.Button(label="Choose sound…")
        choose_button.connect("clicked", self.on_choose_notification_sound)
        reset_button = self.Gtk.Button(label="Reset to default")
        reset_button.set_sensitive(value != "default")
        reset_button.connect("clicked", self.on_reset_notification_sound)
        self.notification_sound_box.append(label)
        self.notification_sound_box.append(choose_button)
        self.notification_sound_box.append(reset_button)

    def render_shy_mode(self, settings: ShyModeSettings | None = None) -> None:
        if settings is None:
            settings = get_shy_mode_settings()
        active = ON_VALUE if settings.enabled else OFF_VALUE
        self.render_toggle_row(self.shy_mode_box, active, self.on_shy_mode_clicked)
        self.shy_mode_status.set_label(
            "Pauses notifications during screen sharing; recalls up to "
            f"{settings.replay_count} at {settings.replay_interval:g}s intervals."
        )

    def render_kdeconnect(self, active: str | None = None) -> None:
        if active is None:
            active = get_kdeconnect_state()
        self.render_toggle_row(self.kdeconnect_box, active, self.on_kdeconnect_clicked)

    def render_power_profile(self, active: str | None = None) -> None:
        if active is None:
            active = get_power_profile()
        self.render_segmented_row(self.power_profile_box, POWER_PROFILES, active, self.on_power_profile_clicked)

    def render_waybar_theme(self, active: str | None = None) -> None:
        if active is None:
            active = get_waybar_theme()
        self.render_segmented_row(self.waybar_theme_box, WAYBAR_THEMES, active, self.on_waybar_theme_clicked)

    def render_waybar_font(
        self, container, surface_label: str, setting_prefix: str, family: str, size: int
    ) -> None:
        font_button = self.Gtk.FontDialogButton.new(self.waybar_font_dialog)
        font_button.set_size_request(190, -1)
        font_button.set_font_desc(self.Pango.FontDescription.from_string(family))
        size_adjustment = self.Gtk.Adjustment(value=size, lower=6, upper=72, step_increment=1)
        size_spin = self.Gtk.SpinButton(adjustment=size_adjustment)
        size_spin.set_tooltip_text(f"{surface_label} font size in pixels")
        apply_button = self.Gtk.Button(label="Apply")
        apply_button.connect(
            "clicked",
            self.on_waybar_font_apply,
            container,
            surface_label,
            setting_prefix,
            font_button,
            size_spin,
        )
        container.append(font_button)
        container.append(size_spin)
        container.append(apply_button)

    def on_notifications_clicked(self, _button, value: str) -> None:
        self.begin_settings_change()
        result = run_cli(["archie", "system", "set", "notifications", value])
        if result.returncode == 0:
            self.set_status(f"Notifications set to {value}.")
            notify_applet_settings_changed()
        else:
            self.set_status(f"Failed to set notifications: {result.stderr.strip()}")
        self.clear_box(self.notifications_box)
        self.render_notifications()
        self.finish_settings_change()

    def on_notification_sounds_clicked(self, _button, value: str) -> None:
        self.begin_settings_change()
        result = run_cli(["archie", "system", "set", "notification-sounds", value])
        if result.returncode == 0:
            self.set_status(f"Notification sounds set to {value}.")
            notify_applet_settings_changed()
        else:
            self.set_status(f"Failed to set notification sounds: {result.stderr.strip()}")
        self.clear_box(self.notification_sounds_box)
        self.render_notification_sounds()
        self.finish_settings_change()

    def on_choose_notification_sound(self, _button) -> None:
        chooser = self.Gtk.FileChooserNative.new(
            "Choose notification sound", self.window, self.Gtk.FileChooserAction.OPEN, "Choose sound", "Cancel"
        )
        sounds_directory = Path("/usr/share/sounds")
        if sounds_directory.is_dir():
            chooser.set_current_folder(self.Gio.File.new_for_path(str(sounds_directory)))
        audio_filter = self.Gtk.FileFilter()
        audio_filter.set_name("Audio files")
        audio_filter.add_mime_type("audio/*")
        chooser.add_filter(audio_filter)
        chooser.connect("response", self.on_notification_sound_chosen)
        chooser.show()

    def on_notification_sound_chosen(self, chooser, response) -> None:
        if response == self.Gtk.ResponseType.ACCEPT and (selected := chooser.get_file()):
            path = selected.get_path()
            if path is not None:
                self.set_notification_sound(path)
        chooser.destroy()

    def on_reset_notification_sound(self, _button) -> None:
        self.set_notification_sound("default")

    def set_notification_sound(self, value: str) -> None:
        self.begin_settings_change()
        result = run_cli(["archie", "system", "set", "notification-sound", value])
        if result.returncode == 0:
            self.set_status("Notification sound reset to bundled default." if value == "default" else "Notification sound updated.")
            notify_applet_settings_changed()
        else:
            self.set_status(f"Could not use that sound: {result.stderr.strip()}")
        self.clear_box(self.notification_sound_box)
        self.render_notification_sound()
        self.finish_settings_change()

    def on_shy_mode_clicked(self, _button, value: str) -> None:
        self.begin_settings_change()
        result = run_cli(["archie", "system", "set", "shy-mode", value])
        if result.returncode == 0:
            self.set_status(f"Shy mode set to {value}.")
            notify_applet_settings_changed()
        else:
            self.set_status(f"Failed to set shy mode: {result.stderr.strip()}")
        self.clear_box(self.shy_mode_box)
        self.render_shy_mode()
        self.finish_settings_change()

    def on_kdeconnect_clicked(self, _button, value: str) -> None:
        self.begin_settings_change()
        result = run_cli(["archie", "system", "set", "kdeconnect", value])
        if result.returncode == 0:
            self.set_status(f"KDE Connect set to {value}.")
            notify_applet_settings_changed()
        else:
            self.set_status(f"Failed to set KDE Connect: {result.stderr.strip()}")
        self.clear_box(self.kdeconnect_box)
        self.render_kdeconnect()
        self.finish_settings_change()

    def on_power_profile_clicked(self, _button, value: str) -> None:
        self.begin_settings_change()
        result = run_cli(["archie", "system", "set", "power-profile", value])
        if result.returncode == 0:
            self.set_status(f"Power profile set to {value}.")
            notify_applet_settings_changed()
        else:
            self.set_status(f"Failed to set power profile: {result.stderr.strip()}")
        self.clear_box(self.power_profile_box)
        self.render_power_profile()
        self.finish_settings_change()

    def on_waybar_theme_clicked(self, _button, value: str) -> None:
        self.begin_settings_change()
        result = run_cli(["archie", "system", "set", "waybar-theme", value])
        if result.returncode == 0:
            self.set_status(f"Waybar theme set to {value}.")
            notify_applet_settings_changed()
        else:
            self.set_status(f"Failed to set waybar theme: {result.stderr.strip()}")
        self.clear_box(self.waybar_theme_box)
        self.render_waybar_theme()
        self.finish_settings_change()

    def on_waybar_font_apply(
        self, _button, container, surface_label: str, setting_prefix: str, font_button, size_spin
    ) -> None:
        self.begin_settings_change()
        family = selected_font_family(font_button)
        size = str(size_spin.get_value_as_int())
        family_result = run_cli(["archie", "system", "set", f"{setting_prefix}-family", family])
        size_result = run_cli(["archie", "system", "set", f"{setting_prefix}-size", size])
        if family_result.returncode == 0 and size_result.returncode == 0:
            self.set_status(f"{surface_label} font updated.")
        else:
            detail = family_result.stderr.strip() or size_result.stderr.strip()
            self.set_status(f"Failed to update {surface_label.lower()} font: {detail}")
        self.clear_box(container)
        updated_family, updated_size = get_waybar_font(setting_prefix)
        self.render_waybar_font(
            container, surface_label, setting_prefix, updated_family, updated_size
        )
        self.finish_settings_change()

    def on_brightness_label_changed(self, scale, label) -> None:
        label.set_label(f"{brightness_scale_value(scale)}%")

    def on_brightness_changed(self, scale, device_name: str) -> None:
        percent = brightness_scale_value(scale)
        if round(scale.get_value()) != percent:
            scale.set_value(percent)
            return
        if timeout_id := self.brightness_timeout_ids.pop(device_name, None):
            self.GLib.source_remove(timeout_id)
        else:
            self.begin_settings_change()
        timeout_id = self.GLib.timeout_add(
            BRIGHTNESS_DEBOUNCE_MS,
            self.commit_brightness_change,
            device_name,
            percent,
        )
        self.brightness_timeout_ids[device_name] = timeout_id

    def commit_brightness_change(self, device_name: str, percent: int) -> bool:
        self.brightness_timeout_ids.pop(device_name, None)
        result = run_cli(["archie", "system", "set", "brightness", device_name, str(percent)])
        if result.returncode == 0:
            self.set_status(f"Brightness for {device_name} set to {percent}%.")
            notify_applet_settings_changed()
        else:
            self.set_status(f"Failed to set brightness for {device_name}: {result.stderr.strip()}")
        self.finish_settings_change()
        return False

    def refresh_monitor_buttons_only(self) -> None:
        self.clear_box(self.monitor_box)
        self.monitors = list_monitors()
        self.render_monitors()

    def refresh_lid_buttons_only(self) -> None:
        self.clear_box(self.lid_box)
        self.render_lid_behavior()

    def set_box_sensitive(self, box, sensitive: bool) -> None:
        child = box.get_first_child()
        while child is not None:
            child.set_sensitive(sensitive)
            child = child.get_next_sibling()

    def run_cli_async(self, run_command, on_complete) -> None:
        def worker() -> None:
            result = run_command()
            self.GLib.idle_add(on_complete, result)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _on_message_view_focus_leave(self, _controller) -> None:
        bounds = self.message_buffer.get_selection_bounds()
        if len(bounds) == 2:
            self._message_selection = (bounds[0].get_offset(), bounds[1].get_offset())
        else:
            self._message_selection = None

    def _install_copy_shortcut(self) -> None:
        from gi.repository import Gdk  # type: ignore[attr-defined]

        key_controller = self.Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_window_key_pressed)
        self.window.add_controller(key_controller)
        clipboard = Gdk.Display.get_default().get_clipboard()
        self.message_buffer.add_selection_clipboard(clipboard)

    def _on_window_key_pressed(self, _controller, keyval, _keycode, state) -> bool:
        from gi.repository import Gdk  # type: ignore[attr-defined]

        ctrl = state & Gdk.ModifierType.CONTROL_MASK
        if ctrl and keyval == Gdk.KEY_c and self._message_selection is not None:
            clipboard = Gdk.Display.get_default().get_clipboard()
            self.message_buffer.copy_clipboard(clipboard)
            return True
        return False

    def set_status(self, message: str) -> None:
        print(message, flush=True)
        entry = f"{datetime.now().strftime('%H:%M:%S')}  {message}"
        if self.message_buffer.get_char_count() > 0:
            entry = f"{entry}\n"
        start_iter = self.message_buffer.get_start_iter()
        self.message_buffer.insert(start_iter, entry)
        self.message_view.scroll_to_iter(self.message_buffer.get_start_iter(), 0.0, False, 0.0, 0.0)

    def add_timeout(self, seconds: int, callback):
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import GLib  # type: ignore[attr-defined]

        return GLib.timeout_add_seconds(seconds, callback)

    def clear_box(self, box) -> None:
        while child := box.get_first_child():
            box.remove(child)

    def install_css(self) -> None:
        from gi.repository import Gdk  # type: ignore[attr-defined]

        css_provider = self.Gtk.CssProvider()
        css_content = importlib.resources.files("archie").joinpath("gui.css").read_text(encoding="utf-8")
        css_provider.load_from_data(css_content)
        self.Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            self.Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )


def get_lid_behavior() -> str:
    result = run_cli(["archie", "system", "get", "lid-close-behavior"])
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def set_lid_behavior(behavior: str) -> subprocess.CompletedProcess[str]:
    command = ["pkexec", "archie", "system", "set", "lid-close-behavior", behavior]
    try:
        result = run_cli(command)
    except FileNotFoundError:
        result = run_cli(["archie", "system", "set", "lid-close-behavior", behavior])
    if result.returncode == 127:
        result = run_cli(["archie", "system", "set", "lid-close-behavior", behavior])
    return result


def lid_error_message(result: subprocess.CompletedProcess[str]) -> str:
    stderr = result.stderr.strip()
    if result.returncode in {126, 127} and not stderr:
        return "Lid close behavior change cancelled."
    if "dismissed" in stderr.casefold() or "cancel" in stderr.casefold():
        return "Lid close behavior change cancelled."
    detail = stderr or f"exit {result.returncode}"
    return f"Failed to set lid close behavior: {detail}"


def get_notifications_state() -> str:
    result = run_cli(["archie", "system", "get", "notifications"])
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def get_notification_sounds_state() -> str:
    result = run_cli(["archie", "system", "get", "notification-sounds"])
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def get_notification_sound() -> str:
    result = run_cli(["archie", "system", "get", "notification-sound"])
    return result.stdout.strip() if result.returncode == 0 else "default"


def get_shy_mode_settings() -> ShyModeSettings:
    result = run_cli(["archie", "system", "get", "shy-mode"])
    if result.returncode != 0:
        return ShyModeSettings()
    values = dict(
        line.split(": ", 1)
        for line in result.stdout.splitlines()
        if ": " in line
    )
    try:
        return ShyModeSettings(
            enabled=values.get("enabled") == ON_VALUE,
            replay_count=int(values["replay-count"]),
            replay_interval=float(values["replay-interval"].removesuffix("s")),
        )
    except (KeyError, ValueError):
        return ShyModeSettings()


def get_kdeconnect_state() -> str:
    result = run_cli(["archie", "system", "get", "kdeconnect"])
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def get_power_profile() -> str:
    result = run_cli(["archie", "system", "get", "power-profile"])
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def get_waybar_theme() -> str:
    result = run_cli(["archie", "system", "get", "waybar-theme"])
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def get_waybar_font(setting_prefix: str) -> tuple[str, int]:
    family = run_cli(["archie", "system", "get", f"{setting_prefix}-family"])
    size = run_cli(["archie", "system", "get", f"{setting_prefix}-size"])
    if family.returncode != 0 or size.returncode != 0:
        return "MesloLGM Nerd Font", 20
    try:
        return family.stdout.strip(), int(size.stdout.strip())
    except ValueError:
        return "MesloLGM Nerd Font", 20


def selected_font_family(font_button) -> str:
    font_description = font_button.get_font_desc()
    return (font_description.get_family() if font_description is not None else "") or ""


def get_brightness_devices() -> subprocess.CompletedProcess[str]:
    return run_cli(["archie", "system", "get", "brightness"])


def can_write_store(path: Path = STORE_DATABASE_PATH) -> bool:
    return (
        path.is_file()
        and os.access(path, os.W_OK)
        and os.access(path.parent, os.W_OK | os.X_OK)
    )


def store_write_warning(path: Path = STORE_DATABASE_PATH) -> str | None:
    if not path.is_file():
        return "Archie shared store is missing; reinstall the Archie CLI package to provision it."
    if not can_write_store(path):
        return (
            "Archie cannot write its shared store; log out and back in or reboot "
            "to apply the archie group membership."
        )
    return None


def load_gui_settings_snapshot() -> GuiSettingsSnapshot:
    with ThreadPoolExecutor(max_workers=13) as executor:
        monitors_future = executor.submit(list_monitors)
        brightness_future = executor.submit(get_brightness_devices)
        lid_behavior_future = executor.submit(get_lid_behavior)
        notifications_future = executor.submit(get_notifications_state)
        notification_sounds_future = executor.submit(get_notification_sounds_state)
        notification_sound_future = executor.submit(get_notification_sound)
        shy_mode_future = executor.submit(get_shy_mode_settings)
        kdeconnect_future = executor.submit(get_kdeconnect_state)
        power_profile_future = executor.submit(get_power_profile)
        waybar_theme_future = executor.submit(get_waybar_theme)
        waybar_font_future = executor.submit(get_waybar_font, "waybar-font")
        waybar_menu_font_future = executor.submit(get_waybar_font, "waybar-menu-font")
        waybar_tooltip_font_future = executor.submit(
            get_waybar_font, "waybar-tooltip-font"
        )
        try:
            monitors = monitors_future.result()
            monitor_error = None
        except Exception as error:
            monitors = []
            monitor_error = str(error)
        brightness = brightness_future.result()
        lid_behavior = lid_behavior_future.result()
        notifications = notifications_future.result()
        notification_sounds = notification_sounds_future.result()
        notification_sound = notification_sound_future.result()
        shy_mode = shy_mode_future.result()
        kdeconnect = kdeconnect_future.result()
        power_profile = power_profile_future.result()
        waybar_theme = waybar_theme_future.result()
        waybar_font = waybar_font_future.result()
        waybar_menu_font = waybar_menu_font_future.result()
        waybar_tooltip_font = waybar_tooltip_font_future.result()
    return GuiSettingsSnapshot(
        brightness_result=brightness,
        monitors=monitors,
        monitor_error=monitor_error,
        lid_behavior=lid_behavior,
        notifications=notifications,
        notification_sounds=notification_sounds,
        notification_sound=notification_sound,
        shy_mode=shy_mode,
        kdeconnect=kdeconnect,
        power_profile=power_profile,
        waybar_theme=waybar_theme,
        waybar_font_family=waybar_font[0],
        waybar_font_size=waybar_font[1],
        waybar_menu_font_family=waybar_menu_font[0],
        waybar_menu_font_size=waybar_menu_font[1],
        waybar_tooltip_font_family=waybar_tooltip_font[0],
        waybar_tooltip_font_size=waybar_tooltip_font[1],
    )


def load_gui_settings_snapshot_from_environment() -> GuiSettingsSnapshot | None:
    payload = os.environ.get(GUI_SETTINGS_SNAPSHOT_ENV)
    if payload is None:
        return None
    return deserialize_gui_settings_snapshot(payload)


def parse_brightness_devices(output: str) -> list[GuiBrightnessDevice]:
    devices: list[GuiBrightnessDevice] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) != 4:
            continue
        name, percent, current, maximum = parts
        try:
            devices.append(
                GuiBrightnessDevice(
                    name=name,
                    percent=int(percent),
                    current=int(current),
                    maximum=int(maximum),
                )
            )
        except ValueError:
            continue
    return devices


def snap_brightness_percent(percent: int) -> int:
    clamped = max(0, min(100, percent))
    return max(0, min(100, ((clamped + 5) // 10) * 10))


def brightness_scale_value(scale) -> int:
    return snap_brightness_percent(round(scale.get_value()))


def run_cli(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    command_list = list(command)
    print(f"$ {' '.join(command_list)}", flush=True)
    completed = subprocess.run(command_list, check=False, capture_output=True, text=True)
    if completed.stdout:
        print(completed.stdout, end="", flush=True)
    if completed.stderr:
        print(completed.stderr, end="", flush=True)
    print(f"exit {completed.returncode}: {' '.join(command_list)}", flush=True)
    return completed


def read_keyboard_shortcuts_markdown() -> str:
    return read_first_existing_markdown(KEYBOARD_SHORTCUTS_PATHS, "KEYBOARD_SHORTCUTS.md")


def read_shell_commands_markdown() -> str:
    return read_first_existing_markdown(SHELL_COMMANDS_PATHS, "ZSH_COMMANDS.md")


def read_first_existing_markdown(paths: Sequence[Path], label: str) -> str:
    for path in paths:
        if path.exists():
            return path.read_text(encoding="utf-8")
    rendered_paths = ", ".join(str(path) for path in paths)
    raise FileNotFoundError(f"Could not find {label} in: {rendered_paths}")


def parse_markdown_table(table_lines: Sequence[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in table_lines:
        cells = [clean_markdown_cell(cell) for cell in line.strip().strip("|").split("|")]
        if all(is_markdown_separator(cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def clean_markdown_cell(cell: str) -> str:
    return cell.strip().replace("`", "")


def is_markdown_separator(cell: str) -> bool:
    stripped = cell.strip()
    return bool(stripped) and all(character in ":-" for character in stripped)


def filter_documentation_rows(rows: Sequence[Sequence[str]], query: str) -> list[Sequence[str]]:
    normalized_query = query.casefold().strip()
    if not normalized_query:
        return list(rows)
    return [
        row
        for row in rows
        if normalized_query in " ".join(row).casefold()
    ]


filter_shortcut_rows = filter_documentation_rows
