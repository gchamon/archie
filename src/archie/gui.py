import argparse
import importlib.resources
import signal
import subprocess
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from archie.monitor import MonitorOutput, apply_monitor_toggle, list_monitors, restore_monitors
from archie.system import (
    HIBERNATE_MODE,
    LOCK_MODE,
    NONE_MODE,
    OFF_VALUE,
    ON_VALUE,
    POWER_PROFILES,
    WAYBAR_THEMES,
)

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
        from gi.repository import GLib, Gtk  # type: ignore[attr-defined]

        self.Gtk = Gtk
        self.GLib = GLib
        self.application = application
        self.monitors: list[MonitorOutput] = []
        self.pending_snapshot: list[MonitorOutput] | None = None
        self.pending_timeout_id: int | None = None
        self.brightness_timeout_ids: dict[str, int] = {}
        self.documentation_tabs: dict[str, tuple[str, object]] = {}
        self.brightness_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.monitor_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.lid_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.lid_box.add_css_class("archie-lid-segments")
        self.lid_box.add_css_class("linked")
        self.notifications_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.notifications_box.add_css_class("archie-lid-segments")
        self.notifications_box.add_css_class("linked")
        self.kdeconnect_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.kdeconnect_box.add_css_class("archie-lid-segments")
        self.kdeconnect_box.add_css_class("linked")
        self.power_profile_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.power_profile_box.add_css_class("archie-lid-segments")
        self.power_profile_box.add_css_class("linked")
        self.waybar_theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.waybar_theme_box.add_css_class("archie-lid-segments")
        self.waybar_theme_box.add_css_class("linked")
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

        self.window = Gtk.ApplicationWindow(application=application)
        self.window.set_title("Archie Controls")
        self.window.set_default_size(520, 360)
        self.window.set_resizable(False)
        self.window.connect("close-request", self._on_close_request)
        self.install_css()
        self.window.set_child(self.build_content())
        self._install_copy_shortcut()
        self.refresh()

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

        options = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        brightness_label = Gtk.Label(label="Screen brightness:")
        brightness_label.set_xalign(0)
        options.append(brightness_label)
        options.append(self.brightness_box)

        monitor_label = Gtk.Label(label="Monitors:")
        monitor_label.set_xalign(0)
        options.append(monitor_label)
        options.append(self.monitor_box)

        lid_label = Gtk.Label(label="Lid close behavior:")
        lid_label.set_xalign(0)
        options.append(lid_label)
        options.append(self.lid_box)

        notifications_label = Gtk.Label(label="Notifications:")
        notifications_label.set_xalign(0)
        options.append(notifications_label)
        options.append(self.notifications_box)

        kdeconnect_label = Gtk.Label(label="KDE Connect:")
        kdeconnect_label.set_xalign(0)
        options.append(kdeconnect_label)
        options.append(self.kdeconnect_box)

        power_profile_label = Gtk.Label(label="Power profile:")
        power_profile_label.set_xalign(0)
        options.append(power_profile_label)
        options.append(self.power_profile_box)

        waybar_theme_label = Gtk.Label(label="Waybar theme:")
        waybar_theme_label.set_xalign(0)
        options.append(waybar_theme_label)
        options.append(self.waybar_theme_box)

        options_scroller = Gtk.ScrolledWindow()
        options_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        options_scroller.set_vexpand(True)
        options_scroller.set_child(options)
        root.append(options_scroller)

        root.append(self.message_scroller)
        root.append(self.confirm_box)

        return root

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

    def refresh(self) -> None:
        self.clear_box(self.brightness_box)
        self.clear_box(self.monitor_box)
        self.clear_box(self.lid_box)
        self.clear_box(self.notifications_box)
        self.clear_box(self.kdeconnect_box)
        self.clear_box(self.power_profile_box)
        self.clear_box(self.waybar_theme_box)
        self.render_brightness()
        try:
            self.monitors = list_monitors()
            self.render_monitors()
        except Exception as error:
            self.set_status(f"Monitor error: {error}")
        self.render_lid_behavior()
        self.render_notifications()
        self.render_kdeconnect()
        self.render_power_profile()
        self.render_waybar_theme()

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

    def render_brightness(self) -> None:
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
        scale.set_hexpand(True)
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

    def render_lid_behavior(self) -> None:
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
        try:
            self.pending_snapshot = apply_monitor_toggle(self.monitors, monitor_name)
        except Exception as error:
            self.set_status(str(error))
            return
        self.set_status("Confirm monitor layout within 10 seconds.")
        self.render_confirmation()
        self.pending_timeout_id = self.add_timeout(10, self.revert_pending_change)
        self.refresh_monitor_buttons_only()

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
            try:
                restore_monitors(self.pending_snapshot)
                self.set_status("Monitor layout restored.")
            except Exception as error:
                self.set_status(f"Restore failed: {error}")
        self.pending_snapshot = None
        self.clear_box(self.confirm_box)
        self.refresh()
        return False

    def on_lid_clicked(self, _button, behavior: str) -> None:
        self.set_box_sensitive(self.lid_box, False)
        self.set_status(f"Setting lid close behavior to {behavior}...")
        self.run_cli_async(
            lambda: set_lid_behavior(behavior),
            lambda result: self.on_lid_set_done(result, behavior),
        )

    def on_lid_set_done(self, result: subprocess.CompletedProcess[str], behavior: str) -> bool:
        if result.returncode == 0:
            self.set_status(f"Lid close behavior set to {behavior}.")
        else:
            self.set_status(lid_error_message(result))
        self.clear_box(self.lid_box)
        self.render_lid_behavior()
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

    def render_notifications(self) -> None:
        active = get_notifications_state()
        self.render_toggle_row(self.notifications_box, active, self.on_notifications_clicked)

    def render_kdeconnect(self) -> None:
        active = get_kdeconnect_state()
        self.render_toggle_row(self.kdeconnect_box, active, self.on_kdeconnect_clicked)

    def render_power_profile(self) -> None:
        active = get_power_profile()
        self.render_segmented_row(self.power_profile_box, POWER_PROFILES, active, self.on_power_profile_clicked)

    def render_waybar_theme(self) -> None:
        active = get_waybar_theme()
        self.render_segmented_row(self.waybar_theme_box, WAYBAR_THEMES, active, self.on_waybar_theme_clicked)

    def on_notifications_clicked(self, _button, value: str) -> None:
        result = run_cli(["archie", "system", "set", "notifications", value])
        if result.returncode == 0:
            self.set_status(f"Notifications set to {value}.")
        else:
            self.set_status(f"Failed to set notifications: {result.stderr.strip()}")
        self.clear_box(self.notifications_box)
        self.render_notifications()

    def on_kdeconnect_clicked(self, _button, value: str) -> None:
        result = run_cli(["archie", "system", "set", "kdeconnect", value])
        if result.returncode == 0:
            self.set_status(f"KDE Connect set to {value}.")
        else:
            self.set_status(f"Failed to set KDE Connect: {result.stderr.strip()}")
        self.clear_box(self.kdeconnect_box)
        self.render_kdeconnect()

    def on_power_profile_clicked(self, _button, value: str) -> None:
        result = run_cli(["archie", "system", "set", "power-profile", value])
        if result.returncode == 0:
            self.set_status(f"Power profile set to {value}.")
        else:
            self.set_status(f"Failed to set power profile: {result.stderr.strip()}")
        self.clear_box(self.power_profile_box)
        self.render_power_profile()

    def on_waybar_theme_clicked(self, _button, value: str) -> None:
        result = run_cli(["archie", "system", "set", "waybar-theme", value])
        if result.returncode == 0:
            self.set_status(f"Waybar theme set to {value}.")
        else:
            self.set_status(f"Failed to set waybar theme: {result.stderr.strip()}")
        self.clear_box(self.waybar_theme_box)
        self.render_waybar_theme()

    def on_brightness_label_changed(self, scale, label) -> None:
        label.set_label(f"{brightness_scale_value(scale)}%")

    def on_brightness_changed(self, scale, device_name: str) -> None:
        percent = brightness_scale_value(scale)
        if round(scale.get_value()) != percent:
            scale.set_value(percent)
            return
        if timeout_id := self.brightness_timeout_ids.pop(device_name, None):
            self.GLib.source_remove(timeout_id)
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
        else:
            self.set_status(f"Failed to set brightness for {device_name}: {result.stderr.strip()}")
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


def get_brightness_devices() -> subprocess.CompletedProcess[str]:
    return run_cli(["archie", "system", "get", "brightness"])


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
