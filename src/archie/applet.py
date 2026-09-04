import argparse
import importlib.resources
import logging
import logging.handlers
import os
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Mapping
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from archie.applet_bus import APPLET_BUS_NAME, APPLET_OBJECT_PATH
from archie.gui import load_gui_settings_snapshot, run_cli, set_lid_behavior
from archie.gui_state import (
    GUI_SETTINGS_SNAPSHOT_ENV,
    GuiSettingsSnapshot,
    serialize_gui_settings_snapshot,
)
from archie.privacy import (
    DunstClient,
    ShyModeController,
    ShyModeSettings,
    ShyModeViewState,
    detect_share_active,
    load_shy_mode_settings,
)
from archie.system import collect_system_status, format_system_status
from archie.version import installed_archie_version

logger = logging.getLogger(__name__)

APPLET_ICON_RESOURCE = "assets/applet-icon.png"
APPLET_BADGE_RESOURCES = {
    color: f"assets/applet-icon-badge-{color}.png"
    for color in ("orange", "green", "red", "yellow", "blue")
}
SNI_BUS_NAME = "org.kde.StatusNotifierWatcher"
SNI_WATCHER_PATH = "/StatusNotifierWatcher"
SNI_WATCHER_INTERFACE = "org.kde.StatusNotifierWatcher"
SNI_OBJECT_PATH = "/org/archie/sni"

DBUS_INTERFACE = "org.freedesktop.DBus"
DBUS_OBJECT_PATH = "/org/freedesktop/DBus"

DBUSMENU_OBJECT_PATH = "/org/archie/menu"
DBUSMENU_INTERFACE = "com.canonical.dbusmenu"

MENU_ITEM_OPEN = 1
MENU_ITEM_RESTART = 2
MENU_ITEM_SEP = 3
MENU_ITEM_QUIT = 4
MENU_ITEM_LID_HIBERNATE = 5
MENU_ITEM_LID_LOCK = 6
MENU_ITEM_NOTIFICATIONS = 7
MENU_ITEM_NOTIFICATION_SOUNDS = 8
MENU_QUICK_SWITCH_IDS = (
    MENU_ITEM_LID_HIBERNATE,
    MENU_ITEM_LID_LOCK,
    MENU_ITEM_NOTIFICATIONS,
    MENU_ITEM_NOTIFICATION_SOUNDS,
)
RUNNING_VERSION = installed_archie_version()

SNI_XML = """
<node>
  <interface name="org.kde.StatusNotifierItem">
    <method name="ContextMenu">
      <arg name="x" type="i" direction="in"/>
      <arg name="y" type="i" direction="in"/>
    </method>
    <method name="Activate">
      <arg name="x" type="i" direction="in"/>
      <arg name="y" type="i" direction="in"/>
    </method>
    <method name="SecondaryActivate">
      <arg name="x" type="i" direction="in"/>
      <arg name="y" type="i" direction="in"/>
    </method>
    <method name="Scroll">
      <arg name="delta" type="i" direction="in"/>
      <arg name="orientation" type="s" direction="in"/>
    </method>
    <property name="Category" type="s" access="read"/>
    <property name="Id" type="s" access="read"/>
    <property name="Title" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="WindowId" type="i" access="read"/>
    <property name="IconName" type="s" access="read"/>
    <property name="IconPixmap" type="a(iiay)" access="read"/>
    <property name="OverlayIconName" type="s" access="read"/>
    <property name="OverlayIconPixmap" type="a(iiay)" access="read"/>
    <property name="AttentionIconName" type="s" access="read"/>
    <property name="AttentionIconPixmap" type="a(iiay)" access="read"/>
    <property name="AttentionMovieName" type="s" access="read"/>
    <property name="ToolTip" type="(sa(iiay)ss)" access="read"/>
    <property name="ItemIsMenu" type="b" access="read"/>
    <property name="Menu" type="o" access="read"/>
    <signal name="NewIcon"/>
    <signal name="NewToolTip"/>
  </interface>
</node>
"""

DBUSMENU_XML = """
<node>
  <interface name="com.canonical.dbusmenu">
    <property name="Version" type="u" access="read"/>
    <property name="TextDirection" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="IconThemePath" type="as" access="read"/>
    <method name="GetLayout">
      <arg name="parentId" type="i" direction="in"/>
      <arg name="recursionDepth" type="i" direction="in"/>
      <arg name="propertyNames" type="as" direction="in"/>
      <arg name="revision" type="u" direction="out"/>
      <arg name="layout" type="(ia{sv}av)" direction="out"/>
    </method>
    <method name="GetGroupProperties">
      <arg name="ids" type="ai" direction="in"/>
      <arg name="propertyNames" type="as" direction="in"/>
      <arg name="properties" type="a(ia{sv})" direction="out"/>
    </method>
    <method name="GetProperty">
      <arg name="id" type="i" direction="in"/>
      <arg name="name" type="s" direction="in"/>
      <arg name="value" type="v" direction="out"/>
    </method>
    <method name="Event">
      <arg name="id" type="i" direction="in"/>
      <arg name="eventId" type="s" direction="in"/>
      <arg name="data" type="v" direction="in"/>
      <arg name="timestamp" type="u" direction="in"/>
    </method>
    <method name="EventGroup">
      <arg name="events" type="a(isvu)" direction="in"/>
      <arg name="idErrors" type="ai" direction="out"/>
    </method>
    <method name="AboutToShow">
      <arg name="id" type="i" direction="in"/>
      <arg name="needUpdate" type="b" direction="out"/>
    </method>
    <method name="AboutToShowGroup">
      <arg name="ids" type="ai" direction="in"/>
      <arg name="updatesNeeded" type="ai" direction="out"/>
      <arg name="idErrors" type="ai" direction="out"/>
    </method>
    <signal name="ItemsPropertiesUpdated">
      <arg name="updatedProps" type="a(ia{sv})"/>
      <arg name="removedProps" type="a(ias)"/>
    </signal>
    <signal name="LayoutUpdated">
      <arg name="revision" type="u"/>
      <arg name="parent" type="i"/>
    </signal>
    <signal name="ItemActivationRequested">
      <arg name="id" type="i"/>
      <arg name="timestamp" type="u"/>
    </signal>
  </interface>
</node>
"""

APPLET_XML = """
<node>
  <interface name="com.gchamon.Archie.Applet">
    <method name="SettingsChanged"/>
    <method name="GetVersion">
      <arg name="version" type="s" direction="out"/>
    </method>
    <method name="Restart"/>
  </interface>
</node>
"""


def format_tooltip(
    snapshot: dict[str, object] | None = None,
    shy_state: ShyModeViewState | None = None,
    *,
    privacy_ready: bool = True,
) -> str:
    """Return a best-effort snapshot of Archie-controlled settings."""
    values = dict(snapshot or {})
    if privacy_ready and shy_state is not None:
        values["share-state"] = "on" if shy_state.sharing else "off"
    status = (
        "starting privacy monitor…"
        if not privacy_ready
        else format_shy_mode_status(shy_state)
    )
    return format_system_status(
        values,
        shy_mode_status=status,
    )


def format_tooltip_title(version: str = RUNNING_VERSION) -> str:
    return f"Archie Controls v{version}"


def format_shy_mode_status(state: ShyModeViewState | None = None) -> str:
    current = state
    if current is None:
        settings = load_shy_mode_settings()
        return format_configured_shy_mode(settings)
    if not current.enabled:
        return "off"
    if current.sharing and current.owns_pause and current.pending:
        return "on, sharing; notifications pending"
    if current.sharing and current.owns_pause:
        return "on, guarding active share"
    if current.replaying:
        return "on, replaying missed notifications"
    if current.pending:
        return "on, notifications pending"
    return "on, ready"


def format_configured_shy_mode(settings: ShyModeSettings) -> str:
    if not settings.enabled:
        return "off"
    return (
        f"on, replay {settings.replay_count} at "
        f"{settings.replay_interval:g}s intervals"
    )


def select_applet_icon(state: ShyModeViewState) -> str:
    return "orange" if state.pending else "base"


def load_applet_snapshot() -> dict[str, object]:
    snapshot, _errors = collect_system_status()
    return snapshot


def menu_toggle_state(item_id: int, snapshot: Mapping[str, object]) -> int | None:
    if item_id == MENU_ITEM_LID_HIBERNATE:
        value = snapshot.get("lid-close-behavior")
        return None if value not in {"hibernate", "lock"} else int(value == "hibernate")
    if item_id == MENU_ITEM_LID_LOCK:
        value = snapshot.get("lid-close-behavior")
        return None if value not in {"hibernate", "lock"} else int(value == "lock")
    if item_id == MENU_ITEM_NOTIFICATIONS:
        value = snapshot.get("notifications")
        return None if value not in {"on", "off"} else int(value == "on")
    if item_id == MENU_ITEM_NOTIFICATION_SOUNDS:
        value = snapshot.get("notification-sounds")
        return None if value not in {"on", "off"} else int(value == "on")
    return None


def menu_action_value(item_id: int, snapshot: Mapping[str, object]) -> str | None:
    if item_id == MENU_ITEM_LID_HIBERNATE:
        return "hibernate" if menu_toggle_state(item_id, snapshot) is not None else None
    if item_id == MENU_ITEM_LID_LOCK:
        return "lock" if menu_toggle_state(item_id, snapshot) is not None else None
    if item_id == MENU_ITEM_NOTIFICATIONS:
        value = snapshot.get("notifications")
        return {"on": "off", "off": "on"}.get(str(value))
    if item_id == MENU_ITEM_NOTIFICATION_SOUNDS:
        value = snapshot.get("notification-sounds")
        return {"on": "off", "off": "on"}.get(str(value))
    return None


@dataclass
class ArchieStatusNotifier:
    connection: Any
    icon_pixmaps: dict[str, Any]
    controller: ShyModeController
    revision: int = 0
    shy_state: ShyModeViewState = field(
        default_factory=lambda: ShyModeViewState(False, False, False, False, False)
    )
    snapshot: dict[str, object] = field(default_factory=dict)
    privacy_ready: bool = False
    privacy_refresh_in_progress: bool = False
    tooltip_refresh_in_progress: bool = False
    gui_snapshot: GuiSettingsSnapshot | None = None
    gui_snapshot_refresh_in_progress: bool = False
    menu_action_in_progress: bool = False

    def on_method_call(
        self,
        _connection,
        _sender: str,
        _object_path: str,
        _interface_name: str,
        method_name: str,
        parameters,
        invocation,
    ) -> None:
        if method_name == "Activate":
            logger.info("archie applet activate")
            self.open_gui()
        elif method_name == "ContextMenu":
            # Hosts that render the menu themselves (Waybar) use the DBusMenu
            # object exposed via the Menu property and never reach this branch.
            logger.info("archie applet context menu")
        elif method_name == "SecondaryActivate":
            logger.info("archie applet secondary activate")
        invocation.return_value(None)

    def on_get_property(
        self,
        _connection,
        _sender: str,
        _object_path: str,
        _interface_name: str,
        property_name: str,
    ):
        import gi

        gi.require_version("GLib", "2.0")
        from gi.repository import GLib  # type: ignore[attr-defined]

        if property_name == "ToolTip":
            self.request_gui_snapshot_refresh()
        icon_pixmap = self.icon_pixmaps[select_applet_icon(self.shy_state)]
        values = {
            "Category": GLib.Variant("s", "Hardware"),
            "Id": GLib.Variant("s", "archie"),
            "Title": GLib.Variant("s", format_tooltip_title()),
            "Status": GLib.Variant("s", "Active"),
            "WindowId": GLib.Variant("i", 0),
            "IconName": GLib.Variant("s", "archie-controls"),
            "IconPixmap": icon_pixmap,
            "OverlayIconName": GLib.Variant("s", ""),
            "OverlayIconPixmap": GLib.Variant("a(iiay)", []),
            "AttentionIconName": GLib.Variant("s", ""),
            "AttentionIconPixmap": GLib.Variant("a(iiay)", []),
            "AttentionMovieName": GLib.Variant("s", ""),
            "ToolTip": GLib.Variant(
                "(sa(iiay)ss)",
                (
                    "",
                    [],
                    format_tooltip_title(),
                    format_tooltip(self.snapshot, self.shy_state, privacy_ready=self.privacy_ready),
                ),
            ),
            "ItemIsMenu": GLib.Variant("b", False),
            "Menu": GLib.Variant("o", DBUSMENU_OBJECT_PATH),
        }
        return values[property_name]

    def _item_props(self, item_id: int):
        import gi

        gi.require_version("GLib", "2.0")
        from gi.repository import GLib  # type: ignore[attr-defined]

        if item_id == 0:
            return {"children-display": GLib.Variant("s", "submenu")}
        if item_id == MENU_ITEM_OPEN:
            return {
                "label": GLib.Variant("s", "Open Controls"),
                "enabled": GLib.Variant("b", True),
                "visible": GLib.Variant("b", True),
            }
        if item_id == MENU_ITEM_RESTART:
            return {
                "label": GLib.Variant("s", "Restart applet"),
                "enabled": GLib.Variant("b", True),
                "visible": GLib.Variant("b", True),
            }
        if item_id in MENU_QUICK_SWITCH_IDS:
            labels = {
                MENU_ITEM_LID_HIBERNATE: "Lid close: Hibernate",
                MENU_ITEM_LID_LOCK: "Lid close: Lock",
                MENU_ITEM_NOTIFICATIONS: "Notifications",
                MENU_ITEM_NOTIFICATION_SOUNDS: "Notification sounds",
            }
            toggle_state = menu_toggle_state(item_id, self.snapshot)
            return {
                "label": GLib.Variant("s", labels[item_id]),
                "enabled": GLib.Variant(
                    "b", toggle_state is not None and not self.menu_action_in_progress
                ),
                "visible": GLib.Variant("b", True),
                "toggle-type": GLib.Variant(
                    "s",
                    "radio"
                    if item_id in {MENU_ITEM_LID_HIBERNATE, MENU_ITEM_LID_LOCK}
                    else "checkmark",
                ),
                "toggle-state": GLib.Variant("i", toggle_state or 0),
            }
        if item_id == MENU_ITEM_SEP:
            return {
                "type": GLib.Variant("s", "separator"),
                "enabled": GLib.Variant("b", False),
                "visible": GLib.Variant("b", True),
            }
        if item_id == MENU_ITEM_QUIT:
            return {
                "label": GLib.Variant("s", "Quit Applet"),
                "enabled": GLib.Variant("b", True),
                "visible": GLib.Variant("b", True),
            }
        return None

    def dbusmenu_method_call(
        self,
        _connection,
        _sender: str,
        _object_path: str,
        _interface_name: str,
        method_name: str,
        parameters,
        invocation,
    ) -> None:
        import gi

        gi.require_version("GLib", "2.0")
        gi.require_version("Gtk", "3.0")
        from gi.repository import GLib, Gtk  # type: ignore[attr-defined]

        if method_name == "GetLayout":
            _parent_id, recursion_depth, _property_names = parameters.unpack()
            children = []
            if recursion_depth != 0:
                for child_id in (
                    MENU_ITEM_OPEN,
                    MENU_ITEM_LID_HIBERNATE,
                    MENU_ITEM_LID_LOCK,
                    MENU_ITEM_NOTIFICATIONS,
                    MENU_ITEM_NOTIFICATION_SOUNDS,
                    MENU_ITEM_RESTART,
                    MENU_ITEM_SEP,
                    MENU_ITEM_QUIT,
                ):
                    children.append(GLib.Variant("(ia{sv}av)", (child_id, self._item_props(child_id), [])))
            root = (0, self._item_props(0), children)
            invocation.return_value(GLib.Variant("(u(ia{sv}av))", (self.revision, root)))
        elif method_name == "GetGroupProperties":
            ids, _property_names = parameters.unpack()
            if not ids:
                ids = [
                    0,
                    MENU_ITEM_OPEN,
                    *MENU_QUICK_SWITCH_IDS,
                    MENU_ITEM_RESTART,
                    MENU_ITEM_SEP,
                    MENU_ITEM_QUIT,
                ]
            result = []
            for item_id in ids:
                props = self._item_props(item_id)
                if props is not None:
                    result.append((item_id, props))
            invocation.return_value(GLib.Variant("(a(ia{sv}))", (result,)))
        elif method_name == "GetProperty":
            item_id, name = parameters.unpack()
            props = self._item_props(item_id) or {}
            value = props.get(name)
            if value is None:
                value = GLib.Variant("s", "")
            invocation.return_value(GLib.Variant("(v)", (value,)))
        elif method_name == "Event":
            item_id, event_id, _data, _timestamp = parameters.unpack()
            if event_id == "clicked":
                if item_id == MENU_ITEM_OPEN:
                    self.open_gui()
                elif item_id in MENU_QUICK_SWITCH_IDS:
                    self.start_menu_action(item_id)
                elif item_id == MENU_ITEM_RESTART:
                    self.request_restart()
                elif item_id == MENU_ITEM_QUIT:
                    Gtk.main_quit()
            invocation.return_value(None)
        elif method_name == "EventGroup":
            (events,) = parameters.unpack()
            for item_id, event_id, _data, _timestamp in events:
                if event_id == "clicked":
                    if item_id == MENU_ITEM_OPEN:
                        self.open_gui()
                    elif item_id in MENU_QUICK_SWITCH_IDS:
                        self.start_menu_action(item_id)
                    elif item_id == MENU_ITEM_RESTART:
                        self.request_restart()
                    elif item_id == MENU_ITEM_QUIT:
                        Gtk.main_quit()
            invocation.return_value(GLib.Variant("(ai)", ([],)))
        elif method_name == "AboutToShow":
            invocation.return_value(GLib.Variant("(b)", (False,)))
        elif method_name == "AboutToShowGroup":
            invocation.return_value(GLib.Variant("(aiai)", ([], [])))
        else:
            invocation.return_value(None)

    def dbusmenu_get_property(
        self,
        _connection,
        _sender: str,
        _object_path: str,
        _interface_name: str,
        property_name: str,
    ):
        import gi

        gi.require_version("GLib", "2.0")
        from gi.repository import GLib  # type: ignore[attr-defined]

        values = {
            "Version": GLib.Variant("u", 3),
            "TextDirection": GLib.Variant("s", "ltr"),
            "Status": GLib.Variant("s", "normal"),
            "IconThemePath": GLib.Variant("as", []),
        }
        return values[property_name]

    def applet_method_call(
        self,
        _connection,
        _sender: str,
        _object_path: str,
        _interface_name: str,
        method_name: str,
        _parameters,
        invocation,
    ) -> None:
        if method_name == "SettingsChanged":
            self.request_tooltip_refresh()
        elif method_name == "GetVersion":
            import gi

            gi.require_version("GLib", "2.0")
            from gi.repository import GLib  # type: ignore[attr-defined]

            invocation.return_value(GLib.Variant("(s)", (RUNNING_VERSION,)))
            return
        elif method_name == "Restart":
            self.request_restart()
        invocation.return_value(None)

    def request_restart(self) -> None:
        from gi.repository import GLib  # type: ignore[attr-defined]

        GLib.idle_add(restart_applet_process)

    def request_privacy_refresh(self) -> bool:
        if self.privacy_refresh_in_progress:
            return True
        self.privacy_refresh_in_progress = True

        def worker() -> None:
            import gi

            gi.require_version("GLib", "2.0")
            from gi.repository import GLib  # type: ignore[attr-defined]

            try:
                state = self.controller.poll(detect_share_active(), time.monotonic())
            except Exception:
                logger.exception("could not refresh shy mode state")
                GLib.idle_add(self.mark_privacy_refresh_failed)
                return
            GLib.idle_add(self.apply_privacy_state, state)

        threading.Thread(target=worker, daemon=True).start()
        return True

    def request_tooltip_refresh(self) -> bool:
        if self.tooltip_refresh_in_progress:
            return True
        self.tooltip_refresh_in_progress = True

        def worker() -> None:
            import gi

            gi.require_version("GLib", "2.0")
            from gi.repository import GLib  # type: ignore[attr-defined]

            snapshot: dict[str, object] | None = None
            state: ShyModeViewState | None = None
            try:
                snapshot = load_applet_snapshot()
            except Exception:
                logger.exception("could not refresh applet tooltip status")
            try:
                state = self.controller.poll(detect_share_active(), time.monotonic())
            except Exception:
                logger.exception("could not refresh applet tooltip privacy state")
            GLib.idle_add(self.apply_tooltip_refresh, snapshot, state)

        threading.Thread(target=worker, daemon=True).start()
        return True

    def request_gui_snapshot_refresh(self) -> bool:
        if self.gui_snapshot_refresh_in_progress:
            return True
        self.gui_snapshot_refresh_in_progress = True

        def worker() -> None:
            import gi

            gi.require_version("GLib", "2.0")
            from gi.repository import GLib  # type: ignore[attr-defined]

            try:
                snapshot = load_gui_settings_snapshot()
            except Exception:
                logger.exception("could not refresh GUI settings snapshot")
                GLib.idle_add(self.mark_gui_snapshot_refresh_failed)
                return
            GLib.idle_add(self.apply_gui_snapshot, snapshot)

        threading.Thread(target=worker, daemon=True).start()
        return True

    def start_privacy_monitor(self) -> bool:
        self.request_tooltip_refresh()
        self.request_gui_snapshot_refresh()
        return False

    def mark_privacy_refresh_failed(self) -> bool:
        self.privacy_refresh_in_progress = False
        return False

    def mark_gui_snapshot_refresh_failed(self) -> bool:
        self.gui_snapshot_refresh_in_progress = False
        return False

    def apply_gui_snapshot(self, snapshot: GuiSettingsSnapshot) -> bool:
        self.gui_snapshot = snapshot
        self.gui_snapshot_refresh_in_progress = False
        return False

    def apply_tooltip_refresh(
        self,
        snapshot: dict[str, object] | None,
        state: ShyModeViewState | None,
    ) -> bool:
        changed = False
        if snapshot is not None and snapshot != self.snapshot:
            self.snapshot = snapshot
            changed = True
        if state is not None:
            previous_state = self.shy_state
            was_ready = self.privacy_ready
            self.shy_state = state
            self.privacy_ready = True
            changed = changed or state != previous_state or not was_ready
        self.tooltip_refresh_in_progress = False
        if changed:
            self.emit_state_changed()
        return False

    def open_gui(self) -> None:
        _open_gui(self.gui_snapshot)

    def start_menu_action(self, item_id: int) -> None:
        if self.menu_action_in_progress:
            return
        value = menu_action_value(item_id, self.snapshot)
        if value is None:
            return
        self.menu_action_in_progress = True
        self.emit_state_changed()

        def worker() -> None:
            try:
                if item_id in {MENU_ITEM_LID_HIBERNATE, MENU_ITEM_LID_LOCK}:
                    result = set_lid_behavior(value)
                else:
                    setting = (
                        "notifications"
                        if item_id == MENU_ITEM_NOTIFICATIONS
                        else "notification-sounds"
                    )
                    result = run_cli(["archie", "system", "set", setting, value])
            except Exception:
                logger.exception("could not apply applet menu action")
                result = subprocess.CompletedProcess([], 1, "", "menu action failed")
            from gi.repository import GLib  # type: ignore[attr-defined]

            GLib.idle_add(self.finish_menu_action, item_id, result)

        threading.Thread(target=worker, daemon=True).start()

    def finish_menu_action(
        self, item_id: int, result: subprocess.CompletedProcess[str]
    ) -> bool:
        self.menu_action_in_progress = False
        if result.returncode != 0:
            detail = result.stderr.strip() or f"exit {result.returncode}"
            logger.warning("applet menu action %s failed: %s", item_id, detail)
        self.emit_state_changed()
        self.request_tooltip_refresh()
        return False

    def apply_status_snapshot(self, snapshot: dict[str, object]) -> bool:
        if snapshot != self.snapshot:
            self.snapshot = snapshot
            self.emit_state_changed()
        return False

    def apply_privacy_state(self, state: ShyModeViewState) -> bool:
        previous = self.shy_state
        was_ready = self.privacy_ready
        self.shy_state = state
        self.privacy_ready = True
        self.privacy_refresh_in_progress = False
        if state != previous or not was_ready:
            self.emit_state_changed()
        # This is scheduled with GLib.idle_add(), so it must run once.
        return False

    def emit_state_changed(self) -> None:
        import gi

        gi.require_version("GLib", "2.0")
        from gi.repository import GLib  # type: ignore[attr-defined]

        self.revision += 1
        self.connection.emit_signal(
            None,
            SNI_OBJECT_PATH,
            "org.kde.StatusNotifierItem",
            "NewIcon",
            None,
        )
        self.connection.emit_signal(
            None,
            SNI_OBJECT_PATH,
            "org.kde.StatusNotifierItem",
            "NewToolTip",
            None,
        )
        self.connection.emit_signal(
            None,
            DBUSMENU_OBJECT_PATH,
            DBUSMENU_INTERFACE,
            "LayoutUpdated",
            GLib.Variant("(ui)", (self.revision, 0)),
        )


def add_applet_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "applet",
        help="Run the Archie tray applet.",
        description="Run the Archie tray applet.",
    )
    parser.set_defaults(func=run_applet)


def _setup_logging() -> None:
    log_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "archie"
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "applet.log",
        maxBytes=1_000_000,
        backupCount=3,
    )
    file_handler.setFormatter(formatter)

    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[file_handler, stderr_handler])


def run_applet(_args: argparse.Namespace) -> int:
    _setup_logging()

    import gi

    gi.require_version("Gio", "2.0")
    gi.require_version("GLib", "2.0")
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gio, GLib, Gtk  # type: ignore[attr-defined]

    signal.signal(signal.SIGINT, lambda *_args: Gtk.main_quit())
    signal.signal(signal.SIGTERM, lambda *_args: Gtk.main_quit())

    with ExitStack() as stack:
        icon_path = stack.enter_context(
            importlib.resources.as_file(importlib.resources.files("archie").joinpath(APPLET_ICON_RESOURCE))
        )
        icon_pixmaps = {"base": load_icon_pixmap(icon_path)}
        for color, resource in APPLET_BADGE_RESOURCES.items():
            badge_path = stack.enter_context(
                importlib.resources.as_file(importlib.resources.files("archie").joinpath(resource))
            )
            icon_pixmaps[color] = load_icon_pixmap(badge_path)
        try:
            connection = Gio.bus_get_sync(Gio.BusType.SESSION)
        except GLib.Error as error:
            logger.error("could not connect to the session bus: %s", error)
            return 1
        controller = ShyModeController(DunstClient())
        notifier = ArchieStatusNotifier(
            connection,
            icon_pixmaps,
            controller,
        )
        owns_applet_bus_name = claim_applet_bus_name(connection)
        node_info = Gio.DBusNodeInfo.new_for_xml(SNI_XML)
        interface_info = node_info.interfaces[0]
        registration_id = notifier.connection.register_object(
            SNI_OBJECT_PATH,
            interface_info,
            notifier.on_method_call,
            notifier.on_get_property,
            None,
        )
        menu_node_info = Gio.DBusNodeInfo.new_for_xml(DBUSMENU_XML)
        menu_interface_info = menu_node_info.interfaces[0]
        menu_registration_id = notifier.connection.register_object(
            DBUSMENU_OBJECT_PATH,
            menu_interface_info,
            notifier.dbusmenu_method_call,
            notifier.dbusmenu_get_property,
            None,
        )
        applet_node_info = Gio.DBusNodeInfo.new_for_xml(APPLET_XML)
        applet_registration_id = notifier.connection.register_object(
            APPLET_OBJECT_PATH,
            applet_node_info.interfaces[0],
            notifier.applet_method_call,
            None,
            None,
        )
        def on_watcher_appeared(_connection, _name, _name_owner):
            register_status_notifier_item(notifier.connection)
            notifier.revision += 1
            notifier.connection.emit_signal(
                None,
                DBUSMENU_OBJECT_PATH,
                DBUSMENU_INTERFACE,
                "LayoutUpdated",
                GLib.Variant("(ui)", (notifier.revision, 0)),
            )
            logger.info("registered with StatusNotifierWatcher")

        def on_watcher_vanished(_connection, _name):
            logger.info("StatusNotifierWatcher vanished")

        watcher_id = Gio.bus_watch_name_on_connection(
            notifier.connection,
            SNI_BUS_NAME,
            Gio.BusNameWatcherFlags.NONE,
            on_watcher_appeared,
            on_watcher_vanished,
        )
        GLib.idle_add(notifier.start_privacy_monitor)
        refresh_id = GLib.timeout_add_seconds(5, notifier.request_privacy_refresh)
        tooltip_refresh_id = GLib.timeout_add_seconds(30, notifier.request_tooltip_refresh)
        logger.info("archie applet started")
        try:
            Gtk.main()
        except KeyboardInterrupt:
            logger.info("archie applet interrupted")
        finally:
            Gio.bus_unwatch_name(watcher_id)
            GLib.source_remove(refresh_id)
            GLib.source_remove(tooltip_refresh_id)
            notifier.connection.unregister_object(registration_id)
            notifier.connection.unregister_object(menu_registration_id)
            notifier.connection.unregister_object(applet_registration_id)
            if owns_applet_bus_name:
                release_applet_bus_name(notifier.connection)
    logger.info("archie applet stopped")
    return 0


def restart_applet_process() -> bool:
    """Replace this process after the D-Bus response has been sent."""
    logger.info("restarting Archie applet to load version %s", installed_archie_version())
    os.execv(sys.argv[0], sys.argv)
    return False


def register_status_notifier_item(connection) -> None:
    import gi

    gi.require_version("Gio", "2.0")
    gi.require_version("GLib", "2.0")
    from gi.repository import Gio, GLib  # type: ignore[attr-defined]

    try:
        connection.call_sync(
            SNI_BUS_NAME,
            SNI_WATCHER_PATH,
            SNI_WATCHER_INTERFACE,
            "RegisterStatusNotifierItem",
            GLib.Variant("(s)", (SNI_OBJECT_PATH,)),
            None,
            Gio.DBusCallFlags.NONE,
            -1,
        )
    except GLib.Error as error:
        logger.warning("could not register status notifier item: %s", error)


def claim_applet_bus_name(connection) -> bool:
    import gi

    gi.require_version("Gio", "2.0")
    gi.require_version("GLib", "2.0")
    from gi.repository import Gio, GLib  # type: ignore[attr-defined]

    try:
        reply = connection.call_sync(
            DBUS_INTERFACE,
            DBUS_OBJECT_PATH,
            DBUS_INTERFACE,
            "RequestName",
            GLib.Variant("(su)", (APPLET_BUS_NAME, 0)),
            GLib.VariantType.new("(u)"),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
    except GLib.Error as error:
        logger.warning("could not claim Archie applet bus name: %s", error)
        return False
    (result,) = reply.unpack()
    if result in {1, 4}:
        return True
    logger.warning("Archie applet bus name is already owned")
    return False


def release_applet_bus_name(connection) -> None:
    import gi

    gi.require_version("Gio", "2.0")
    gi.require_version("GLib", "2.0")
    from gi.repository import Gio, GLib  # type: ignore[attr-defined]

    try:
        connection.call_sync(
            DBUS_INTERFACE,
            DBUS_OBJECT_PATH,
            DBUS_INTERFACE,
            "ReleaseName",
            GLib.Variant("(s)", (APPLET_BUS_NAME,)),
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
    except GLib.Error as error:
        logger.warning("could not release Archie applet bus name: %s", error)


def load_icon_pixmap(icon_path: Path):
    import gi
    from PIL import Image

    gi.require_version("GLib", "2.0")
    from gi.repository import GLib  # type: ignore[attr-defined]

    image = Image.open(icon_path).convert("RGBA")
    width, height = image.size
    argb = bytearray()
    rgba = image.tobytes()
    for offset in range(0, len(rgba), 4):
        red = rgba[offset]
        green = rgba[offset + 1]
        blue = rgba[offset + 2]
        alpha = rgba[offset + 3]
        argb.extend((alpha, red, green, blue))
    return GLib.Variant("a(iiay)", [(width, height, bytes(argb))])


def _open_gui(snapshot: GuiSettingsSnapshot | None = None) -> None:
    command = ["archie", "gui"]
    logger.info("$ %s", " ".join(command))
    environment = os.environ.copy()
    if snapshot is not None:
        environment[GUI_SETTINGS_SNAPSHOT_ENV] = serialize_gui_settings_snapshot(snapshot)
    subprocess.Popen(command, env=environment)
