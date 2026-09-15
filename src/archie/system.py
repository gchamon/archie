import argparse
import configparser
import importlib.resources
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

from archie.argparse import add_command_subparsers
from archie.monitor import MonitorOutput, list_monitors_quiet
from archie.privacy import (
    DEFAULT_DUNST_HISTORY_LIMIT,
    ShyModeSettings,
    detect_share_active,
    format_shy_mode_settings,
    load_shy_mode_settings,
    save_shy_mode_settings,
)
from archie.store import (
    CALENDAR_BROWSER_URL,
    CALENDAR_CLICK,
    CALENDAR_LAUNCHER,
    CALENDAR_LEFT_BROWSER_URL,
    CALENDAR_LEFT_PRESET,
    CALENDAR_PRESET,
    CALENDAR_RIGHT_BROWSER_URL,
    CALENDAR_RIGHT_PRESET,
    DATETIME_LEFT_BROWSER_URL,
    DATETIME_LEFT_PRESET,
    DATETIME_RIGHT_BROWSER_URL,
    DATETIME_RIGHT_PRESET,
    NOTIFICATION_SOUND_SOURCE,
    NOTIFICATION_SOUNDS_ENABLED,
    POLICY_DEFAULTS,
    SHY_MODE_ENABLED,
    SHY_MODE_REPLAY_COUNT,
    SHY_MODE_REPLAY_INTERVAL,
    STORE_DATABASE_PATH,
    WAYBAR_FONT_FAMILY,
    WAYBAR_FONT_SIZE,
    WAYBAR_MENU_FONT_FAMILY,
    WAYBAR_MENU_FONT_SIZE,
    WAYBAR_THEME,
    WAYBAR_TOOLTIP_FONT_FAMILY,
    WAYBAR_TOOLTIP_FONT_SIZE,
    PolicyStore,
    StoreDatabase,
    StoreError,
)

LID_CLOSE_CONF_PATH = Path("/etc/systemd/logind.conf.d/lid-close.conf")
WAYBAR_THEME_STATE_PATH = STORE_DATABASE_PATH
WAYBAR_CONFIG_PATH = Path("/var/lib/archie/waybar/config")
WAYBAR_STYLE_PATH = Path("/var/lib/archie/waybar/style.css")
BACKLIGHT_PATH = Path("/sys/class/backlight")

HIBERNATE_MODE = "hibernate"
LOCK_MODE = "lock"
NONE_MODE = "none"
UNKNOWN_MODE = "unknown"

ON_VALUE = "on"
OFF_VALUE = "off"

PERFORMANCE_PROFILE = "performance"
BALANCED_PROFILE = "balanced"
POWER_SAVER_PROFILE = "power-saver"
POWER_PROFILES = [PERFORMANCE_PROFILE, BALANCED_PROFILE, POWER_SAVER_PROFILE]

DEFAULT_THEME = "cjbassi"
MECHABAR_THEME = "mechabar"
TOKYONIGHT_THEME = "tokyonight"
WAYBAR_THEMES = [DEFAULT_THEME, MECHABAR_THEME, TOKYONIGHT_THEME]
WAYBAR_FONT_MIN_SIZE = 6
WAYBAR_FONT_MAX_SIZE = 72
CALENDAR_PRESET_GNOME = "gnome-calendar"
CALENDAR_PRESET_BROWSER = "browser-url"
CALENDAR_PRESET_UNSET = "unset"
CALENDAR_PRESETS = (CALENDAR_PRESET_UNSET, CALENDAR_PRESET_GNOME, CALENDAR_PRESET_BROWSER)
CALENDAR_CLICK_LEFT = "left"
CALENDAR_CLICK_RIGHT = "right"
CALENDAR_CLICKS = (CALENDAR_CLICK_LEFT, CALENDAR_CLICK_RIGHT)
CALENDAR_OPEN_COMMAND = "archie system open calendar"
CALENDAR_POLICY_KEYS = {
    CALENDAR_CLICK_LEFT: (CALENDAR_LEFT_PRESET, CALENDAR_LEFT_BROWSER_URL),
    CALENDAR_CLICK_RIGHT: (CALENDAR_RIGHT_PRESET, CALENDAR_RIGHT_BROWSER_URL),
}
DATETIME_PRESET_GNOME = "gnome-datetime"
DATETIME_PRESET_BROWSER = "browser-url"
DATETIME_PRESET_UNSET = "unset"
DATETIME_PRESETS = (DATETIME_PRESET_UNSET, DATETIME_PRESET_GNOME, DATETIME_PRESET_BROWSER)
DATETIME_OPEN_COMMAND = "archie system open datetime"
CALENDAR_VIEW_MONTH = "month"
DATETIME_VIEWS = ("agenda", "week")
DATETIME_POLICY_KEYS = {
    CALENDAR_CLICK_LEFT: (DATETIME_LEFT_PRESET, DATETIME_LEFT_BROWSER_URL),
    CALENDAR_CLICK_RIGHT: (DATETIME_RIGHT_PRESET, DATETIME_RIGHT_BROWSER_URL),
}


def normalize_calendar_url(value: str) -> str:
    if not value or any(character.isspace() for character in value):
        raise ValueError("calendar URL must not be empty or contain whitespace")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
    except ValueError as error:
        raise ValueError("calendar URL is malformed") from error
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not hostname:
        raise ValueError("calendar URL must be an absolute http or https URL")
    return value


def valid_calendar_url(value: str) -> str:
    try:
        return normalize_calendar_url(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error

SYSTEM_STATUS_SETTINGS = [
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
]

LID_CLOSE_CONTENT_BY_MODE = {
    HIBERNATE_MODE: """[Login]
HandleLidSwitch=hybrid-sleep
HandleLidSwitchDocked=hybrid-sleep
HandleLidSwitchExternalPower=hybrid-sleep
""",
    LOCK_MODE: """[Login]
HandleLidSwitch=ignore
HandleLidSwitchDocked=ignore
HandleLidSwitchExternalPower=ignore
""",
    NONE_MODE: """# ArchieLidCloseBehavior=none
[Login]
HandleLidSwitch=ignore
HandleLidSwitchDocked=ignore
HandleLidSwitchExternalPower=ignore
""",
}


class Executor(Protocol):
    def __call__(self, command: list[str]) -> int: ...


@dataclass(frozen=True)
class BrightnessDevice:
    name: str
    current: int
    maximum: int

    @property
    def percent(self) -> int:
        if self.maximum <= 0:
            return 0
        return round((self.current / self.maximum) * 100)


class CasePreservingConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return optionstr


def add_system_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "system",
        help="Manage Archie-owned system policy.",
        description="Inspect or change Archie-owned system policy.",
    )
    system_subparsers = add_command_subparsers(parser, dest="system_command", metavar="COMMAND")

    get_parser = system_subparsers.add_parser(
        "get",
        help="Read an Archie-owned system setting.",
        description="Read an Archie-owned system setting.",
    )
    get_subparsers = add_command_subparsers(get_parser, dest="setting", metavar="setting")
    for setting, help_text, description in (
        ("calendar-launcher", "Read the calendar launcher.", "Read the Archie-managed calendar launcher preset and URL."),
        ("datetime-launcher", "Read the datetime launcher.", "Read the Archie-managed datetime launcher preset and URL."),
        ("lid-close-behavior", "Read lid close behavior.", "Read Archie-managed lid close behavior."),
        ("notifications", "Read dunst notification state.", "Read whether dunst notifications are on or off."),
        ("notification-sounds", "Read notification sound state.", "Read whether Dunst notification sounds are on or off."),
        ("notification-sound", "Read the notification sound.", "Read the configured Dunst notification sound path."),
        ("shy-mode", "Read shy mode notification privacy settings.", "Read Archie-managed shy mode and replay settings."),
        ("share-state", "Read the managed screen-share state.", "Read whether the managed Hyprland portal is sharing a screen."),
        ("kdeconnect", "Read KDE Connect daemon state.", "Read whether the KDE Connect daemon is running."),
        ("power-profile", "Read the active power profile.", "Read the active power profile via power-profiles-daemon."),
        ("waybar-theme", "Read the active waybar theme.", "Read the Archie-managed waybar theme."),
        ("waybar-font-family", "Read the Waybar element font family.", "Read the Archie-managed Waybar element font family."),
        ("waybar-font-size", "Read the Waybar element font size.", "Read the Archie-managed Waybar element font size in pixels."),
        ("waybar-menu-font-family", "Read the Waybar context-menu font family.", "Read the Archie-managed Waybar context-menu font family."),
        ("waybar-menu-font-size", "Read the Waybar context-menu font size.", "Read the Archie-managed Waybar context-menu font size in pixels."),
        ("waybar-tooltip-font-family", "Read the Waybar tooltip font family.", "Read the Archie-managed Waybar tooltip font family."),
        ("waybar-tooltip-font-size", "Read the Waybar tooltip font size.", "Read the Archie-managed Waybar tooltip font size in pixels."),
        ("brightness", "Read screen brightness state.", "Read screen backlight brightness state."),
    ):
        setting_parser = get_subparsers.add_parser(
            setting,
            help=help_text,
            description=description,
        )
        setting_parser.set_defaults(func=run_system_get)

    status_parser = system_subparsers.add_parser(
        "status",
        help="Summarize current system status.",
        description="Print the same best-effort system summary used by the Archie applet.",
    )
    status_parser.add_argument(
        "-f",
        "--format",
        choices=("table", "json"),
        default="table",
        help="Render as a human-readable table or JSON object (default: table).",
    )
    status_parser.add_argument(
        "-j",
        "--json",
        action="store_const",
        const="json",
        dest="format",
        help="Alias for --format json.",
    )
    status_parser.set_defaults(func=run_system_status)

    initialize_parser = system_subparsers.add_parser(
        "initialize-store",
        help="Initialize the shared Archie store.",
        description="Initialize the shared store and migrate one user's legacy settings.",
    )
    initialize_parser.add_argument(
        "--legacy-home",
        type=Path,
        required=True,
        help="Absolute home directory containing legacy Archie settings.",
    )
    initialize_parser.set_defaults(func=run_system_initialize_store)

    open_parser = system_subparsers.add_parser(
        "open",
        help="Open an Archie-managed desktop destination.",
        description="Open an Archie-managed desktop destination.",
    )
    open_subparsers = add_command_subparsers(open_parser, dest="target", metavar="target")
    calendar_open_parser = open_subparsers.add_parser(
        "calendar",
        help="Open the configured calendar launcher.",
        description="Open the configured calendar launcher without a shell.",
    )
    calendar_open_parser.add_argument(
        "--click",
        choices=CALENDAR_CLICKS,
        default=CALENDAR_CLICK_RIGHT,
        help="Open the action configured for the left or right click.",
    )
    calendar_open_parser.add_argument(
        "--view",
        choices=(CALENDAR_VIEW_MONTH,),
        default=CALENDAR_VIEW_MONTH,
        help="Open GNOME Calendar in month view.",
    )
    calendar_open_parser.set_defaults(func=run_system_open)
    datetime_open_parser = open_subparsers.add_parser(
        "datetime",
        help="Open the configured datetime launcher.",
        description="Open the configured datetime launcher without a shell.",
    )
    datetime_open_parser.add_argument(
        "--click",
        choices=CALENDAR_CLICKS,
        default=CALENDAR_CLICK_RIGHT,
        help="Open the action configured for the left or right click.",
    )
    datetime_open_parser.add_argument(
        "--view",
        choices=DATETIME_VIEWS,
        default="agenda",
        help="Open GNOME Calendar in agenda or week view.",
    )
    datetime_open_parser.set_defaults(func=run_system_open)

    set_parser = system_subparsers.add_parser(
        "set",
        help="Change an Archie-owned system setting.",
    )
    set_subparsers = add_command_subparsers(set_parser, dest="setting", metavar="setting")

    lid_set_parser = set_subparsers.add_parser(
        "lid-close-behavior",
        help="Change lid close behavior.",
        description=(
            "Change Archie-managed lid close behavior. "
            "'hibernate' maps to systemd-logind hybrid-sleep; "
            "'lock' makes logind ignore lid close so Hyprland can turn displays off on close "
            "and lock after reopening; "
            "'none' makes logind ignore lid close and leaves Hyprland lid events as no-ops."
        ),
    )
    lid_set_parser.add_argument(
        "value",
        choices=[HIBERNATE_MODE, LOCK_MODE, NONE_MODE],
        help="Use hibernate for hybrid sleep, lock for display-off-then-lock, or none to ignore lid events.",
    )
    lid_set_parser.set_defaults(func=run_system_set)

    notifications_set_parser = set_subparsers.add_parser(
        "notifications",
        help="Pause or resume dunst notifications.",
        description="Pause or resume dunst desktop notifications.",
    )
    notifications_set_parser.add_argument(
        "value",
        choices=[ON_VALUE, OFF_VALUE],
        help="Use on to resume notifications or off to pause them.",
    )
    notifications_set_parser.set_defaults(func=run_system_set)

    notification_sounds_set_parser = set_subparsers.add_parser(
        "notification-sounds",
        help="Enable or disable Dunst notification sounds.",
        description="Enable or disable sounds played for Dunst desktop notifications.",
    )
    notification_sounds_set_parser.add_argument(
        "value",
        choices=[ON_VALUE, OFF_VALUE],
        help="Use on to play notification sounds or off to silence them.",
    )
    notification_sounds_set_parser.set_defaults(func=run_system_set)

    notification_sound_set_parser = set_subparsers.add_parser(
        "notification-sound",
        help="Change the Dunst notification sound.",
        description="Use an absolute readable sound-file path or 'default'.",
    )
    notification_sound_set_parser.add_argument("value", help="An absolute sound-file path or 'default'.")
    notification_sound_set_parser.set_defaults(func=run_system_set)

    shy_mode_set_parser = set_subparsers.add_parser(
        "shy-mode",
        help="Enable or disable shy mode notification privacy.",
        description="Persist Archie shy mode and its notification replay behavior.",
    )
    shy_mode_set_parser.add_argument(
        "value",
        choices=[ON_VALUE, OFF_VALUE],
        help="Use on to guard screen shares or off to disable shy mode.",
    )
    shy_mode_set_parser.add_argument(
        "--replay-count",
        type=int,
        choices=range(1, DEFAULT_DUNST_HISTORY_LIMIT + 1),
        metavar=f"1-{DEFAULT_DUNST_HISTORY_LIMIT}",
        help="Recall at most this many notifications after sharing ends.",
    )
    shy_mode_set_parser.add_argument(
        "--replay-interval",
        type=positive_float,
        metavar="SECONDS",
        help="Wait this many seconds between recalled notifications.",
    )
    shy_mode_set_parser.set_defaults(func=run_system_set)

    kdeconnect_set_parser = set_subparsers.add_parser(
        "kdeconnect",
        help="Enable or disable KDE Connect backends.",
        description="Enable or disable KDE Connect backends via kdeconnect-cli.",
    )
    kdeconnect_set_parser.add_argument(
        "value",
        choices=[ON_VALUE, OFF_VALUE],
        help="Use on to enable KDE Connect backends or off to disable them.",
    )
    kdeconnect_set_parser.set_defaults(func=run_system_set)

    power_profile_set_parser = set_subparsers.add_parser(
        "power-profile",
        help="Change the active power profile.",
        description="Change the active power profile via power-profiles-daemon.",
    )
    power_profile_set_parser.add_argument(
        "value",
        choices=POWER_PROFILES,
        help="Use performance, balanced, or power-saver.",
    )
    power_profile_set_parser.set_defaults(func=run_system_set)

    waybar_theme_set_parser = set_subparsers.add_parser(
        "waybar-theme",
        help="Switch the waybar theme.",
        description="Switch the Archie-managed waybar theme.",
    )
    waybar_theme_set_parser.add_argument(
        "value",
        choices=WAYBAR_THEMES,
        help="Use default, mechabar, or tokyonight.",
    )
    waybar_theme_set_parser.set_defaults(func=run_system_set)

    calendar_launcher_set_parser = set_subparsers.add_parser(
        "calendar-launcher",
        help="Change the calendar launcher.",
        description="Choose the calendar application or a validated browser URL.",
    )
    calendar_launcher_set_parser.add_argument(
        "--click",
        choices=CALENDAR_CLICKS,
        default=CALENDAR_CLICK_RIGHT,
        help="Use the left or right click on the Waybar date.",
    )
    calendar_presets = add_command_subparsers(
        calendar_launcher_set_parser,
        dest="calendar_preset",
        metavar="PRESET",
    )
    calendar_presets.add_parser(
        CALENDAR_PRESET_UNSET,
        help="Remove the calendar action for this click.",
        description="Leave this click without a calendar action.",
    ).set_defaults(func=run_system_set)
    calendar_presets.add_parser(
        CALENDAR_PRESET_GNOME,
        help="Use GNOME Calendar.",
        description="Open GNOME Calendar.",
    ).set_defaults(func=run_system_set)
    browser_parser = calendar_presets.add_parser(
        CALENDAR_PRESET_BROWSER,
        help="Open a browser URL.",
        description="Open a validated HTTP or HTTPS URL in the configured browser.",
    )
    browser_parser.add_argument(
        "url",
        type=valid_calendar_url,
        help="HTTP or HTTPS calendar URL.",
    )
    browser_parser.set_defaults(func=run_system_set)

    datetime_launcher_set_parser = set_subparsers.add_parser(
        "datetime-launcher",
        help="Change the datetime launcher.",
        description="Choose the datetime application or a validated browser URL.",
    )
    datetime_launcher_set_parser.add_argument(
        "--click",
        choices=CALENDAR_CLICKS,
        default=CALENDAR_CLICK_RIGHT,
        help="Use the left or right click on the Waybar hour and weekday.",
    )
    datetime_presets = add_command_subparsers(
        datetime_launcher_set_parser,
        dest="datetime_preset",
        metavar="PRESET",
    )
    datetime_presets.add_parser(
        DATETIME_PRESET_UNSET,
        help="Remove the datetime action for this click.",
        description="Leave this click without a datetime action.",
    ).set_defaults(func=run_system_set)
    datetime_presets.add_parser(
        DATETIME_PRESET_GNOME,
        help="Open GNOME Date & Time settings.",
        description="Open the GNOME Date & Time settings panel.",
    ).set_defaults(func=run_system_set)
    datetime_browser_parser = datetime_presets.add_parser(
        DATETIME_PRESET_BROWSER,
        help="Open a browser URL.",
        description="Open a validated HTTP or HTTPS URL in the configured browser.",
    )
    datetime_browser_parser.add_argument(
        "url",
        type=valid_calendar_url,
        help="HTTP or HTTPS datetime URL.",
    )
    datetime_browser_parser.set_defaults(func=run_system_set)

    for setting, help_text, value_help, value_type in (
        ("waybar-font-family", "Change the Waybar element font family.", "Installed font family name.", valid_waybar_font_family),
        ("waybar-font-size", "Change the Waybar element font size.", f"Font size in pixels ({WAYBAR_FONT_MIN_SIZE}-{WAYBAR_FONT_MAX_SIZE}).", valid_waybar_font_size),
        ("waybar-menu-font-family", "Change the Waybar context-menu font family.", "Installed font family name.", valid_waybar_font_family),
        ("waybar-menu-font-size", "Change the Waybar context-menu font size.", f"Font size in pixels ({WAYBAR_FONT_MIN_SIZE}-{WAYBAR_FONT_MAX_SIZE}).", valid_waybar_font_size),
        ("waybar-tooltip-font-family", "Change the Waybar tooltip font family.", "Installed font family name.", valid_waybar_font_family),
        ("waybar-tooltip-font-size", "Change the Waybar tooltip font size.", f"Font size in pixels ({WAYBAR_FONT_MIN_SIZE}-{WAYBAR_FONT_MAX_SIZE}).", valid_waybar_font_size),
    ):
        font_parser = set_subparsers.add_parser(setting, help=help_text, description=help_text)
        font_parser.add_argument("value", type=value_type, help=value_help)
        font_parser.set_defaults(func=run_system_set)

    brightness_set_parser = set_subparsers.add_parser(
        "brightness",
        help="Change screen brightness.",
        description="Change screen backlight brightness via brightnessctl.",
    )
    brightness_set_parser.add_argument("device", help="Backlight device name.")
    brightness_set_parser.add_argument("percent", type=int, help="Brightness percentage from 0 to 100.")
    brightness_set_parser.set_defaults(func=run_system_set)


def run_system_get(
    args: argparse.Namespace,
    *,
    lid_close_conf_path: Path = LID_CLOSE_CONF_PATH,
    waybar_theme_state_path: Path = WAYBAR_THEME_STATE_PATH,
    backlight_path: Path = BACKLIGHT_PATH,
    shy_mode_path: Path | None = None,
    notification_sounds_path: Path | None = None,
) -> int:
    handlers: dict[str, Callable[[], int]] = {
        "calendar-launcher": lambda: _print_system_setting(
            format_calendar_settings(get_calendar_settings(waybar_theme_state_path))
        ),
        "datetime-launcher": lambda: _print_system_setting(
            format_datetime_settings(get_datetime_settings(waybar_theme_state_path))
        ),
        "lid-close-behavior": lambda: _print_system_setting(
            detect_lid_close_behavior(lid_close_conf_path)
        ),
        "notifications": lambda: _print_system_setting(detect_notifications_state()),
        "notification-sounds": lambda: _print_system_setting(
            ON_VALUE if load_notification_sounds_enabled(notification_sounds_path) else OFF_VALUE
        ),
        "notification-sound": lambda: _print_system_setting(
            load_notification_sound_path(notification_sounds_path) or "default"
        ),
        "shy-mode": lambda: _print_system_setting(
            format_shy_mode_settings(load_shy_mode_settings(shy_mode_path))
        ),
        "share-state": lambda: _print_system_setting(
            ON_VALUE if detect_share_active() else OFF_VALUE
        ),
        "kdeconnect": lambda: _print_system_setting(detect_kdeconnect_state()),
        "power-profile": detect_power_profile,
        "waybar-theme": lambda: _print_system_setting(
            detect_waybar_theme(waybar_theme_state_path)
        ),
        "brightness": lambda: print_brightness_state(backlight_path),
    }
    handlers.update(
        {
            setting: lambda setting=setting: _print_system_setting(
                get_waybar_font_setting(setting, waybar_theme_state_path)
            )
            for setting in WAYBAR_FONT_POLICY_BY_SETTING
        }
    )
    handler = handlers.get(args.setting)
    if handler is None:
        print(f"archie system get: unsupported setting: {args.setting}", file=sys.stderr)
        return 2
    return handler()


def run_system_open(
    args: argparse.Namespace,
    *,
    waybar_theme_state_path: Path = WAYBAR_THEME_STATE_PATH,
) -> int:
    if args.target == "calendar":
        settings = get_calendar_settings(waybar_theme_state_path)
        return open_calendar_launcher(args.click, *settings[args.click], view=args.view)
    if args.target == "datetime":
        settings = get_datetime_settings(waybar_theme_state_path)
        return open_datetime_launcher(args.click, *settings[args.click], view=args.view)
    else:
        print(f"archie system open: unsupported target: {args.target}", file=sys.stderr)
        return 2


def _print_system_setting(value: object) -> int:
    print(value)
    return 0


def collect_system_status(
    *,
    lid_close_conf_path: Path = LID_CLOSE_CONF_PATH,
    waybar_theme_state_path: Path = WAYBAR_THEME_STATE_PATH,
    backlight_path: Path = BACKLIGHT_PATH,
    shy_mode_path: Path | None = None,
    notification_sounds_path: Path | None = None,
) -> tuple[dict[str, object], dict[str, str]]:
    readers: dict[str, Callable[[], object]] = {
        "lid-close-behavior": lambda: detect_lid_close_behavior(lid_close_conf_path),
        "notifications": detect_notifications_state,
        "notification-sounds": lambda: ON_VALUE
        if load_notification_sounds_enabled(notification_sounds_path)
        else OFF_VALUE,
        "notification-sound": lambda: load_notification_sound_path(notification_sounds_path) or "default",
        "shy-mode": lambda: ON_VALUE if load_shy_mode_settings(shy_mode_path).enabled else OFF_VALUE,
        "share-state": lambda: ON_VALUE if detect_share_active() else OFF_VALUE,
        "kdeconnect": detect_kdeconnect_state,
        "power-profile": read_power_profile,
        "waybar-theme": lambda: detect_waybar_theme(waybar_theme_state_path),
        "brightness": lambda: [
            asdict(device) | {"percent": device.percent}
            for device in detect_brightness_devices(backlight_path)
        ],
        "monitors": lambda: [
            serialize_monitor(monitor) for monitor in list_monitors_quiet()
        ],
    }
    values: dict[str, object] = {}
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=len(SYSTEM_STATUS_SETTINGS)) as executor:
        futures = {
            executor.submit(readers[setting]): setting
            for setting in SYSTEM_STATUS_SETTINGS
        }
        for future in as_completed(futures):
            setting = futures[future]
            try:
                values[setting] = future.result()
            # Each reader is isolated so one unavailable service does not hide other status.
            except Exception as error:  # noqa: BLE001
                errors[setting] = str(error) or error.__class__.__name__
    return (
        {setting: values[setting] for setting in SYSTEM_STATUS_SETTINGS if setting in values},
        {setting: errors[setting] for setting in SYSTEM_STATUS_SETTINGS if setting in errors},
    )


def serialize_monitor(monitor: MonitorOutput) -> dict[str, object]:
    return asdict(monitor) | {"enabled": monitor.enabled, "label": monitor.label}


def format_system_status(
    values: dict[str, object], *, shy_mode_status: str | None = None
) -> str:
    shy_status = shy_mode_status or format_status_value(values.get("shy-mode"))
    return "\n".join(
        (
            "Hardware",
            f"  {format_brightness_status(values)}",
            f"  {format_monitors_status(values)}",
            "",
            "Desktop",
            f"  Lid close: {format_status_value(values.get('lid-close-behavior'))}",
            f"  KDE Connect: {format_status_value(values.get('kdeconnect'))}",
            f"  Power profile: {format_status_value(values.get('power-profile'))}",
            f"  Waybar theme: {format_status_value(values.get('waybar-theme'))}",
            "",
            "Privacy",
            f"  Notifications: {format_status_value(values.get('notifications'))}",
            f"  Notification sounds: {format_status_value(values.get('notification-sounds'))}",
            f"  Shy mode: {shy_status}",
            f"  Share: {format_status_value(values.get('share-state'))}",
        )
    )


def format_system_status_json(values: dict[str, object]) -> str:
    status = {
        setting: values.get(setting, UNKNOWN_MODE)
        for setting in SYSTEM_STATUS_SETTINGS
    }
    return json.dumps(status, indent=2)


def format_brightness_status(values: dict[str, object]) -> str:
    devices = values.get("brightness")
    if not isinstance(devices, list):
        return "Brightness: unknown"
    if not devices:
        return "Brightness: unavailable"
    details = ", ".join(
        f"{device.get('name', 'unknown')} {device.get('percent', 'unknown')}%"
        for device in devices
        if isinstance(device, dict)
    )
    return f"Brightness: {details}" if details else "Brightness: unknown"


def format_monitors_status(values: dict[str, object]) -> str:
    monitors = values.get("monitors")
    if not isinstance(monitors, list):
        return "Monitors: unknown"
    if not monitors:
        return "Monitors: unavailable"
    details = ", ".join(
        f"{monitor.get('name', 'unknown')} "
        f"{monitor.get('label', monitor.get('name', 'unknown'))}: "
        f"{'enabled' if monitor.get('enabled') else 'disabled'}"
        f"{' (focused)' if monitor.get('focused') else ''}"
        for monitor in monitors
        if isinstance(monitor, dict)
    )
    return f"Monitors: {details}" if details else "Monitors: unknown"


def format_status_value(value: object) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else UNKNOWN_MODE


def run_system_status(
    args: argparse.Namespace,
    *,
    lid_close_conf_path: Path = LID_CLOSE_CONF_PATH,
    waybar_theme_state_path: Path = WAYBAR_THEME_STATE_PATH,
    backlight_path: Path = BACKLIGHT_PATH,
    shy_mode_path: Path | None = None,
    notification_sounds_path: Path | None = None,
) -> int:
    values, _errors = collect_system_status(
        lid_close_conf_path=lid_close_conf_path,
        waybar_theme_state_path=waybar_theme_state_path,
        backlight_path=backlight_path,
        shy_mode_path=shy_mode_path,
        notification_sounds_path=notification_sounds_path,
    )
    if getattr(args, "format", "table") == "json":
        print(format_system_status_json(values))
    else:
        print(format_system_status(values))
    return 0


def run_system_set(
    args: argparse.Namespace,
    *,
    lid_close_conf_path: Path = LID_CLOSE_CONF_PATH,
    waybar_theme_state_path: Path = WAYBAR_THEME_STATE_PATH,
    waybar_config_path: Path = WAYBAR_CONFIG_PATH,
    waybar_style_path: Path = WAYBAR_STYLE_PATH,
    shy_mode_path: Path | None = None,
    notification_sounds_path: Path | None = None,
    executor: Executor | None = None,
) -> int:
    execute = executor or execute_command
    handlers: dict[str, Callable[[], int]] = {
        "calendar-launcher": lambda: _set_calendar_launcher(
            getattr(args, "click", CALENDAR_CLICK_RIGHT),
            args.calendar_preset,
            getattr(args, "url", ""),
            waybar_theme_state_path,
            waybar_config_path,
            waybar_style_path,
        ),
        "datetime-launcher": lambda: _set_datetime_launcher(
            getattr(args, "click", CALENDAR_CLICK_RIGHT),
            args.datetime_preset,
            getattr(args, "url", ""),
            waybar_theme_state_path,
            waybar_config_path,
            waybar_style_path,
        ),
        "lid-close-behavior": lambda: _set_lid_close_behavior(
            args.value, lid_close_conf_path, execute
        ),
        "notifications": lambda: set_notifications(args.value, executor=execute),
        "notification-sounds": lambda: _set_notification_sounds(
            args.value, notification_sounds_path
        ),
        "notification-sound": lambda: _set_notification_sound(
            args.value, notification_sounds_path
        ),
        "shy-mode": lambda: _set_shy_mode(args, shy_mode_path),
        "kdeconnect": lambda: set_kdeconnect(args.value),
        "power-profile": lambda: set_power_profile(args.value, executor=execute),
        "waybar-theme": lambda: _set_waybar_theme(
            args.value,
            waybar_theme_state_path,
            waybar_config_path,
            waybar_style_path,
        ),
        "brightness": lambda: set_brightness(args.device, args.percent, executor=execute),
    }
    handlers.update(
        {
            setting: lambda setting=setting: _set_waybar_font(
                setting,
                args.value,
                waybar_theme_state_path,
                waybar_style_path,
            )
            for setting in WAYBAR_FONT_POLICY_BY_SETTING
        }
    )
    handler = handlers.get(args.setting)
    if handler is None:
        print(f"archie system set: unsupported setting: {args.setting}", file=sys.stderr)
        return 2
    return handler()


def _set_lid_close_behavior(value: str, path: Path, executor: Executor) -> int:
    if value not in LID_CLOSE_CONTENT_BY_MODE:
        print(f"archie system set: unsupported lid-close-behavior: {value}", file=sys.stderr)
        return 2
    install_code = install_lid_close_behavior(value, path, executor=executor)
    return install_code or reload_logind_if_active(executor=executor)


def _set_calendar_launcher(
    click: str,
    preset: str,
    url: str,
    path: Path,
    config_path: Path,
    style_path: Path,
) -> int:
    try:
        click = normalize_calendar_click(click)
        preset, url = normalize_calendar_settings(preset, url)
        settings = dict(get_calendar_settings(path))
        settings[click] = (preset, url)
        policy_values = {
            key: value
            for side, (preset_key, url_key) in CALENDAR_POLICY_KEYS.items()
            for key, value in (
                (preset_key, settings[side][0]),
                (url_key, settings[side][1]),
            )
        }
        PolicyStore(StoreDatabase(path)).set_many(policy_values)
        theme = detect_waybar_theme(path)
        result = set_waybar_theme(
            theme,
            waybar_theme_state_path=path,
            waybar_config_path=config_path,
            waybar_style_path=style_path,
        )
        if result != 0:
            return result
    except (OSError, StoreError, ValueError) as error:
        print(f"archie system set calendar-launcher: {error}", file=sys.stderr)
        return 2 if isinstance(error, ValueError) else 1
    return 0


def normalize_calendar_click(click: str) -> str:
    if click not in CALENDAR_CLICKS:
        raise ValueError(f"unsupported calendar click: {click}")
    return click


def normalize_calendar_settings(preset: str, url: str = "") -> tuple[str, str]:
    if preset == CALENDAR_PRESET_UNSET:
        return preset, ""
    if preset == CALENDAR_PRESET_GNOME:
        return preset, ""
    if preset == CALENDAR_PRESET_BROWSER:
        return preset, normalize_calendar_url(url)
    raise ValueError(f"unsupported calendar preset: {preset}")


def get_calendar_settings(
    path: Path = WAYBAR_THEME_STATE_PATH,
) -> dict[str, tuple[str, str]]:
    store = PolicyStore(StoreDatabase(path))
    if (
        not all(
            store.get_optional(key) is not None
            for keys in CALENDAR_POLICY_KEYS.values()
            for key in keys
        )
        and (
            store.get_optional(CALENDAR_CLICK) is not None
            or store.get_optional(CALENDAR_PRESET) is not None
            or store.get_optional(CALENDAR_LAUNCHER) is not None
        )
    ):
        try:
            migrate_calendar_policy(store)
        except (OSError, StoreError):
            pass
    settings = {}
    for click, (preset_key, url_key) in CALENDAR_POLICY_KEYS.items():
        preset = store.get(preset_key)
        url = store.get(url_key)
        try:
            settings[click] = normalize_calendar_settings(preset, url)
        except ValueError:
            settings[click] = (
                CALENDAR_PRESET_UNSET
                if click == CALENDAR_CLICK_LEFT
                else CALENDAR_PRESET_GNOME,
                "",
            )
    return settings


def format_calendar_settings(settings: Mapping[str, tuple[str, str]]) -> str:
    lines = []
    for click in CALENDAR_CLICKS:
        preset, url = settings[click]
        lines.append(f"{click} {preset}" if not url else f"{click} {preset} {url}")
    return "\n".join(lines)


def open_calendar_launcher(
    _click: str,
    preset: str,
    url: str,
    *,
    view: str = CALENDAR_VIEW_MONTH,
    environment: Mapping[str, str] | None = None,
) -> int:
    try:
        normalize_calendar_click(_click)
        preset, url = normalize_calendar_settings(preset, url)
    except ValueError as error:
        print(f"archie system open calendar: {error}", file=sys.stderr)
        return 2
    if preset == CALENDAR_PRESET_UNSET:
        return 0
    command = ["gnome-calendar"]
    if preset == CALENDAR_PRESET_BROWSER:
        variables = environment if environment is not None else os.environ
        command = [variables.get("BROWSER") or "firefox", url]
    else:
        try:
            set_calendar_view(view)
        except OSError as error:
            print(f"archie system open calendar: {error}", file=sys.stderr)
            return 1
    try:
        subprocess.Popen(command, start_new_session=True)
    except OSError as error:
        print(f"archie system open calendar: {error}", file=sys.stderr)
        return 1
    return 0


def _set_datetime_launcher(
    click: str,
    preset: str,
    url: str,
    path: Path,
    config_path: Path,
    style_path: Path,
) -> int:
    try:
        click = normalize_calendar_click(click)
        preset, url = normalize_datetime_settings(preset, url)
        settings = dict(get_datetime_settings(path))
        settings[click] = (preset, url)
        policy_values = {
            key: value
            for side, (preset_key, url_key) in DATETIME_POLICY_KEYS.items()
            for key, value in (
                (preset_key, settings[side][0]),
                (url_key, settings[side][1]),
            )
        }
        PolicyStore(StoreDatabase(path)).set_many(policy_values)
        theme = detect_waybar_theme(path)
        result = set_waybar_theme(
            theme,
            waybar_theme_state_path=path,
            waybar_config_path=config_path,
            waybar_style_path=style_path,
        )
        if result != 0:
            return result
    except (OSError, StoreError, ValueError) as error:
        print(f"archie system set datetime-launcher: {error}", file=sys.stderr)
        return 2 if isinstance(error, ValueError) else 1
    return 0


def normalize_datetime_settings(preset: str, url: str = "") -> tuple[str, str]:
    if preset == DATETIME_PRESET_UNSET:
        return preset, ""
    if preset == DATETIME_PRESET_GNOME:
        return preset, ""
    if preset == DATETIME_PRESET_BROWSER:
        return preset, normalize_calendar_url(url)
    raise ValueError(f"unsupported datetime preset: {preset}")


def get_datetime_settings(
    path: Path = WAYBAR_THEME_STATE_PATH,
) -> dict[str, tuple[str, str]]:
    store = PolicyStore(StoreDatabase(path))
    settings = {}
    for click, (preset_key, url_key) in DATETIME_POLICY_KEYS.items():
        preset = store.get(preset_key)
        url = store.get(url_key)
        try:
            settings[click] = normalize_datetime_settings(preset, url)
        except ValueError:
            settings[click] = (
                DATETIME_PRESET_UNSET
                if click == CALENDAR_CLICK_LEFT
                else DATETIME_PRESET_GNOME,
                "",
            )
    return settings


def format_datetime_settings(settings: Mapping[str, tuple[str, str]]) -> str:
    lines = []
    for click in CALENDAR_CLICKS:
        preset, url = settings[click]
        lines.append(f"{click} {preset}" if not url else f"{click} {preset} {url}")
    return "\n".join(lines)


def open_datetime_launcher(
    _click: str,
    preset: str,
    url: str,
    *,
    view: str = "agenda",
    environment: Mapping[str, str] | None = None,
) -> int:
    try:
        normalize_calendar_click(_click)
        preset, url = normalize_datetime_settings(preset, url)
    except ValueError as error:
        print(f"archie system open datetime: {error}", file=sys.stderr)
        return 2
    if preset == DATETIME_PRESET_UNSET:
        return 0
    command = ["gnome-calendar"]
    if preset == DATETIME_PRESET_BROWSER:
        variables = environment if environment is not None else os.environ
        command = [variables.get("BROWSER") or "firefox", url]
    else:
        try:
            set_calendar_view(view)
        except OSError as error:
            print(f"archie system open datetime: {error}", file=sys.stderr)
            return 1
    try:
        subprocess.Popen(command, start_new_session=True)
    except OSError as error:
        print(f"archie system open datetime: {error}", file=sys.stderr)
        return 1
    return 0


def set_calendar_view(view: str) -> None:
    if view not in (CALENDAR_VIEW_MONTH, *DATETIME_VIEWS):
        raise ValueError(f"unsupported calendar view: {view}")
    result = subprocess.run(
        ["gsettings", "set", "org.gnome.calendar", "active-view", view],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or "gsettings failed"
        raise OSError(message)


def _set_notification_sounds(value: str, path: Path | None) -> int:
    try:
        save_notification_sounds_enabled(value == ON_VALUE, path)
    except (OSError, StoreError) as error:
        print(f"archie system set notification-sounds: {error}", file=sys.stderr)
        return 1
    return 0


def _set_notification_sound(value: str, path: Path | None) -> int:
    try:
        save_notification_sound_path(value, path)
    except (OSError, StoreError, ValueError) as error:
        print(f"archie system set notification-sound: {error}", file=sys.stderr)
        return 2 if isinstance(error, ValueError) else 1
    return 0


def _set_shy_mode(args: argparse.Namespace, path: Path | None) -> int:
    current = load_shy_mode_settings(path)
    settings = ShyModeSettings(
        enabled=args.value == ON_VALUE,
        replay_count=args.replay_count or current.replay_count,
        replay_interval=args.replay_interval or current.replay_interval,
    )
    try:
        save_shy_mode_settings(settings, path)
    except (OSError, StoreError) as error:
        print(f"archie system set shy-mode: {error}", file=sys.stderr)
        return 1
    return 0


def _set_waybar_theme(
    value: str,
    state_path: Path,
    config_path: Path,
    style_path: Path,
) -> int:
    try:
        return set_waybar_theme(
            value,
            waybar_theme_state_path=state_path,
            waybar_config_path=config_path,
            waybar_style_path=style_path,
        )
    except (OSError, StoreError) as error:
        print(f"archie system set waybar-theme: {error}", file=sys.stderr)
        return 1


def _set_waybar_font(setting: str, value: str | int, state_path: Path, style_path: Path) -> int:
    try:
        return set_waybar_font_setting(
            setting,
            value,
            waybar_theme_state_path=state_path,
            waybar_style_path=style_path,
        )
    except (OSError, StoreError, ValueError) as error:
        print(f"archie system set {setting}: {error}", file=sys.stderr)
        return 1


def run_system_initialize_store(args: argparse.Namespace) -> int:
    legacy_home = args.legacy_home
    if not legacy_home.is_absolute():
        print(
            "archie system initialize-store: --legacy-home must be absolute",
            file=sys.stderr,
        )
        return 2
    try:
        initialize_store(legacy_home)
    except (OSError, StoreError, ValueError) as error:
        print(f"archie system initialize-store: {error}", file=sys.stderr)
        return 1
    return 0


# --- lid-close-behavior ---


def detect_lid_close_behavior(lid_close_conf_path: Path = LID_CLOSE_CONF_PATH) -> str:
    try:
        content = lid_close_conf_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return UNKNOWN_MODE

    settings = parse_logind_login_settings(content)
    if "ArchieLidCloseBehavior=none" in content:
        return NONE_MODE

    lid_values = [
        settings.get("HandleLidSwitch"),
        settings.get("HandleLidSwitchDocked"),
        settings.get("HandleLidSwitchExternalPower"),
    ]
    if lid_values == ["hybrid-sleep", "hybrid-sleep", "hybrid-sleep"]:
        return HIBERNATE_MODE
    if lid_values == ["ignore", "ignore", "ignore"]:
        return LOCK_MODE
    return UNKNOWN_MODE


def parse_logind_login_settings(content: str) -> dict[str, str]:
    parser = CasePreservingConfigParser(strict=False)
    parser.read_string(content)
    if not parser.has_section("Login"):
        return {}
    return dict(parser.items("Login"))


def install_lid_close_behavior(
    behavior: str,
    lid_close_conf_path: Path = LID_CLOSE_CONF_PATH,
    *,
    executor: Executor | None = None,
) -> int:
    execute = executor or execute_command
    content = LID_CLOSE_CONTENT_BY_MODE[behavior]

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        install_parent_code = execute(
            ["sudo", "mkdir", "-p", str(lid_close_conf_path.parent)]
        )
        if install_parent_code != 0:
            return install_parent_code
        return execute(
            ["sudo", "install", "-m", "0644", str(temp_path), str(lid_close_conf_path)]
        )
    finally:
        temp_path.unlink(missing_ok=True)


def reload_logind_if_active(*, executor: Executor | None = None) -> int:
    execute = executor or execute_command
    active_code = execute(
        ["sudo", "systemctl", "is-active", "--quiet", "systemd-logind.service"]
    )
    if active_code != 0:
        return 0
    return execute(["sudo", "systemctl", "kill", "-s", "HUP", "systemd-logind.service"])


# --- notifications ---


def notification_sounds_config_path() -> Path:
    return STORE_DATABASE_PATH


def load_notification_sound_settings(path: Path | None = None) -> dict[str, object]:
    try:
        values = PolicyStore(StoreDatabase(path or notification_sounds_config_path())).get_many(
            (NOTIFICATION_SOUNDS_ENABLED, NOTIFICATION_SOUND_SOURCE)
        )
    except (OSError, StoreError):
        return {}
    return {
        "enabled": values[NOTIFICATION_SOUNDS_ENABLED] != OFF_VALUE,
        "sound_path": None
        if values[NOTIFICATION_SOUND_SOURCE] == "default"
        else values[NOTIFICATION_SOUND_SOURCE],
    }


def load_notification_sounds_enabled(path: Path | None = None) -> bool:
    return load_notification_sound_settings(path).get("enabled") is not False


def load_notification_sound_path(path: Path | None = None) -> str | None:
    sound_path = load_notification_sound_settings(path).get("sound_path")
    return sound_path if isinstance(sound_path, str) and sound_path else None


def save_notification_sounds_enabled(enabled: bool, path: Path | None = None) -> None:
    PolicyStore(StoreDatabase(path or notification_sounds_config_path())).set(
        NOTIFICATION_SOUNDS_ENABLED,
        ON_VALUE if enabled else OFF_VALUE,
    )


def save_notification_sound_path(value: str, path: Path | None = None) -> None:
    policy_path = path or notification_sounds_config_path()
    asset_path = notification_sound_asset_path(policy_path)
    if value == "default":
        PolicyStore(StoreDatabase(policy_path)).set(NOTIFICATION_SOUND_SOURCE, "default")
        asset_path.unlink(missing_ok=True)
    else:
        sound_path = Path(value)
        if not sound_path.is_absolute():
            raise ValueError("sound path must be absolute or 'default'")
        if not sound_path.is_file() or not os.access(sound_path, os.R_OK):
            raise ValueError(f"sound file is not readable: {sound_path}")
        copy_notification_sound_asset(sound_path, asset_path)
        PolicyStore(StoreDatabase(policy_path)).set(NOTIFICATION_SOUND_SOURCE, str(sound_path))


def save_notification_sound_settings(settings: dict[str, object], path: Path | None = None) -> None:
    save_notification_sounds_enabled(
        settings.get("enabled") is not False,
        path,
    )
    save_notification_sound_path(str(settings.get("sound_path") or "default"), path)


def notification_sound_asset_path(policy_path: Path | None = None) -> Path:
    return (policy_path or STORE_DATABASE_PATH).parent / "notification-sound"


def copy_notification_sound_asset(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_suffix(".tmp")
    shutil.copyfile(source, temporary_path)
    temporary_path.chmod(0o664)
    temporary_path.replace(destination)


def initialize_store(
    legacy_home: Path,
    *,
    policy_path: Path = STORE_DATABASE_PATH,
    waybar_config_path: Path = WAYBAR_CONFIG_PATH,
    waybar_style_path: Path = WAYBAR_STYLE_PATH,
) -> bool:
    database = StoreDatabase(policy_path)
    database.ensure_schema()
    store = PolicyStore(database)
    initialized = False
    if not store.is_initialized():
        values, legacy_sound = load_legacy_policy(legacy_home)
        if legacy_sound is not None:
            copy_notification_sound_asset(
                legacy_sound,
                notification_sound_asset_path(policy_path),
            )
        initialized = store.initialize(values)

    migrate_calendar_policy(store)
    theme = store.get(WAYBAR_THEME)
    if theme not in WAYBAR_THEMES:
        theme = DEFAULT_THEME
    result = set_waybar_theme(
        theme,
        waybar_theme_state_path=policy_path,
        waybar_config_path=waybar_config_path,
        waybar_style_path=waybar_style_path,
    )
    if result != 0:
        raise ValueError(f"could not materialize Waybar theme {theme!r}")
    return initialized


def migrate_calendar_policy(store: PolicyStore) -> None:
    stored_new = {
        key: store.get_optional(key)
        for keys in CALENDAR_POLICY_KEYS.values()
        for key in keys
    }
    stored_click_value = store.get_optional(CALENDAR_CLICK)
    stored_preset = store.get_optional(CALENDAR_PRESET)
    stored_url_value = store.get_optional(CALENDAR_BROWSER_URL)
    legacy_launcher = store.get_optional(CALENDAR_LAUNCHER)
    if all(value is not None for value in stored_new.values()):
        settings = {}
        for click, (preset_key, url_key) in CALENDAR_POLICY_KEYS.items():
            try:
                settings[click] = normalize_calendar_settings(
                    stored_new[preset_key] or "",
                    stored_new[url_key] or "",
                )
            except ValueError:
                settings[click] = default_calendar_settings()[click]
        if stored_click_value is None and stored_preset is None and legacy_launcher is None:
            return
    else:
        settings = default_calendar_settings()
        if stored_preset is not None or stored_click_value is not None:
            click = stored_click_value or CALENDAR_CLICK_RIGHT
            try:
                click = normalize_calendar_click(click)
                settings[click] = normalize_calendar_settings(
                    stored_preset or CALENDAR_PRESET_GNOME,
                    stored_url_value or "",
                )
            except ValueError:
                pass
        elif legacy_launcher is not None:
            settings[CALENDAR_CLICK_RIGHT] = migrate_legacy_calendar_launcher(legacy_launcher)

    store.set_many(
        {
            key: value
            for click, (preset_key, url_key) in CALENDAR_POLICY_KEYS.items()
            for key, value in (
                (preset_key, settings[click][0]),
                (url_key, settings[click][1]),
            )
        }
    )
    for key in (CALENDAR_CLICK, CALENDAR_PRESET, CALENDAR_BROWSER_URL, CALENDAR_LAUNCHER):
        if store.get_optional(key) is not None:
            store.delete(key)


def default_calendar_settings() -> dict[str, tuple[str, str]]:
    return {
        CALENDAR_CLICK_LEFT: (CALENDAR_PRESET_UNSET, ""),
        CALENDAR_CLICK_RIGHT: (CALENDAR_PRESET_GNOME, ""),
    }


def migrate_legacy_calendar_launcher(legacy_launcher: str | None) -> tuple[str, str]:
    if legacy_launcher == CALENDAR_PRESET_GNOME or legacy_launcher is None:
        return CALENDAR_PRESET_GNOME, ""
    try:
        legacy_command = shlex.split(legacy_launcher)
    except ValueError:
        return CALENDAR_PRESET_GNOME, ""
    if len(legacy_command) != 2 or legacy_command[0] != "xdg-open":
        return CALENDAR_PRESET_GNOME, ""
    try:
        url = normalize_calendar_url(legacy_command[1])
    except ValueError:
        return CALENDAR_PRESET_GNOME, ""
    return CALENDAR_PRESET_BROWSER, url


def load_legacy_policy(legacy_home: Path) -> tuple[dict[str, str], Path | None]:
    values = dict(POLICY_DEFAULTS)
    legacy_sound: Path | None = None

    notification_data = read_json_object(
        legacy_home / ".config/archie/notification-sounds.json"
    )
    if notification_data.get("enabled") is False:
        values[NOTIFICATION_SOUNDS_ENABLED] = OFF_VALUE
    sound_value = notification_data.get("sound_path")
    if isinstance(sound_value, str) and sound_value:
        candidate = Path(sound_value)
        if candidate.is_absolute() and candidate.is_file() and os.access(candidate, os.R_OK):
            values[NOTIFICATION_SOUND_SOURCE] = str(candidate)
            legacy_sound = candidate

    shy_data = read_json_object(legacy_home / ".config/archie/shy-mode.json")
    try:
        enabled = shy_data["enabled"]
        replay_count_value = shy_data["replay_count"]
        replay_interval_value = shy_data["replay_interval"]
        if not isinstance(replay_count_value, (int, float, str)) or isinstance(
            replay_count_value, bool
        ):
            raise TypeError
        if not isinstance(replay_interval_value, (int, float, str)) or isinstance(
            replay_interval_value, bool
        ):
            raise TypeError
        replay_count = int(replay_count_value)
        replay_interval = float(replay_interval_value)
        if not isinstance(enabled, bool) or replay_count <= 0 or replay_interval <= 0:
            raise ValueError
        values[SHY_MODE_ENABLED] = ON_VALUE if enabled else OFF_VALUE
        values[SHY_MODE_REPLAY_COUNT] = str(replay_count)
        values[SHY_MODE_REPLAY_INTERVAL] = f"{replay_interval:g}"
    except (KeyError, TypeError, ValueError):
        pass

    try:
        theme = (legacy_home / ".config/waybar/.archie-theme").read_text(
            encoding="utf-8"
        ).strip()
    except OSError:
        theme = DEFAULT_THEME
    if theme in WAYBAR_THEMES:
        values[WAYBAR_THEME] = theme
    return values, legacy_sound


def read_json_object(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def detect_notifications_state() -> str:
    result = subprocess.run(
        ["dunstctl", "is-paused"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return UNKNOWN_MODE
    return OFF_VALUE if result.stdout.strip() == "true" else ON_VALUE


def set_notifications(value: str, *, executor: Executor | None = None) -> int:
    execute = executor or execute_command
    paused = "true" if value == OFF_VALUE else "false"
    return execute(["dunstctl", "set-paused", paused])


# --- kdeconnect ---


def detect_kdeconnect_state() -> str:
    try:
        result = subprocess.run(
            ["kdeconnect-cli", "-b"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and "enabled" in result.stdout:
            return ON_VALUE
    except FileNotFoundError:
        pass
    return OFF_VALUE


KDECONNECT_BACKENDS = ["lan", "bluetooth"]


def set_kdeconnect(value: str) -> int:
    action = "--enable-backend" if value == ON_VALUE else "--disable-backend"
    for backend in KDECONNECT_BACKENDS:
        subprocess.run(
            ["kdeconnect-cli", action, backend],
            check=False,
        )
    return 0


def _spawn_detached(command: list[str]) -> None:
    """Launch a long-lived app fully detached from this process.

    Without redirecting std streams the child inherits the caller's pipes; when
    the caller is launched with capture_output (as the GUI does), subprocess.run
    blocks until every writer to those pipes closes, which never happens for a
    long-lived app. start_new_session puts the child in its own session so it is
    not tied to the caller's lifetime.
    """
    subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


# --- power-profile ---


def detect_power_profile() -> int:
    try:
        print(read_power_profile())
    except RuntimeError as error:
        print(f"archie system get power-profile: {error}", file=sys.stderr)
        return 1
    return 0


def read_power_profile() -> str:
    try:
        result = subprocess.run(
            ["powerprofilesctl", "get"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return UNKNOWN_MODE
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "powerprofilesctl get failed")
    return result.stdout.strip() or UNKNOWN_MODE


def set_power_profile(value: str, *, executor: Executor | None = None) -> int:
    if executor is not None:
        return executor(["powerprofilesctl", "set", value])
    try:
        return subprocess.run(
            ["powerprofilesctl", "set", value], check=False
        ).returncode
    except FileNotFoundError:
        print(
            "archie system set power-profile: powerprofilesctl not found",
            file=sys.stderr,
        )
        return 1


# --- brightness ---


def print_brightness_state(
    backlight_path: Path = BACKLIGHT_PATH,
) -> int:
    try:
        devices = detect_brightness_devices(backlight_path)
    except FileNotFoundError:
        print("archie system get brightness: no backlight devices found", file=sys.stderr)
        return 0
    except RuntimeError as error:
        print(f"archie system get brightness: {error}", file=sys.stderr)
        return 1
    for device in devices:
        print(format_brightness_device(device))
    return 0


def detect_brightness_devices(
    backlight_path: Path = BACKLIGHT_PATH,
) -> list[BrightnessDevice]:
    device_names = list_backlight_device_names(backlight_path)
    return [read_brightness_device(device_name) for device_name in device_names]


def list_backlight_device_names(backlight_path: Path = BACKLIGHT_PATH) -> list[str]:
    try:
        return sorted(path.name for path in backlight_path.iterdir() if path.is_dir())
    except FileNotFoundError:
        raise FileNotFoundError("no backlight devices found") from None


def read_brightness_device(device_name: str) -> BrightnessDevice:
    current = run_brightnessctl_get(device_name, "get")
    maximum = run_brightnessctl_get(device_name, "max")
    return BrightnessDevice(name=device_name, current=current, maximum=maximum)


def run_brightnessctl_get(device_name: str, operation: str) -> int:
    try:
        result = subprocess.run(
            ["brightnessctl", "--device", device_name, operation],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise RuntimeError("brightnessctl not found") from None
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"brightnessctl {operation} failed for {device_name}")
    try:
        return int(result.stdout.strip())
    except ValueError:
        raise RuntimeError(f"invalid brightnessctl {operation} output for {device_name}: {result.stdout.strip()}") from None


def format_brightness_device(device: BrightnessDevice) -> str:
    return f"{device.name}\t{device.percent}\t{device.current}\t{device.maximum}"


def clamp_brightness_percent(percent: int) -> int:
    return max(0, min(100, percent))


def set_brightness(
    device_name: str,
    percent: int,
    *,
    executor: Executor | None = None,
) -> int:
    execute = executor or execute_command
    return execute(["brightnessctl", "--device", device_name, "set", f"{clamp_brightness_percent(percent)}%"])


# --- waybar-theme ---

WAYBAR_THEMES_RESOURCE = "waybar-themes"


@dataclass(frozen=True)
class WaybarFont:
    family: str
    size: int


@dataclass(frozen=True)
class WaybarTypography:
    elements: WaybarFont
    menus: WaybarFont
    tooltips: WaybarFont


WAYBAR_FONT_POLICY_BY_SETTING = {
    "waybar-font-family": WAYBAR_FONT_FAMILY,
    "waybar-font-size": WAYBAR_FONT_SIZE,
    "waybar-menu-font-family": WAYBAR_MENU_FONT_FAMILY,
    "waybar-menu-font-size": WAYBAR_MENU_FONT_SIZE,
    "waybar-tooltip-font-family": WAYBAR_TOOLTIP_FONT_FAMILY,
    "waybar-tooltip-font-size": WAYBAR_TOOLTIP_FONT_SIZE,
}


def get_waybar_typography(path: Path = WAYBAR_THEME_STATE_PATH) -> WaybarTypography:
    values = PolicyStore(StoreDatabase(path)).get_many(
        (
            WAYBAR_FONT_FAMILY,
            WAYBAR_FONT_SIZE,
            WAYBAR_MENU_FONT_FAMILY,
            WAYBAR_MENU_FONT_SIZE,
            WAYBAR_TOOLTIP_FONT_FAMILY,
            WAYBAR_TOOLTIP_FONT_SIZE,
        )
    )
    return WaybarTypography(
        elements=WaybarFont(values[WAYBAR_FONT_FAMILY], int(values[WAYBAR_FONT_SIZE])),
        menus=WaybarFont(values[WAYBAR_MENU_FONT_FAMILY], int(values[WAYBAR_MENU_FONT_SIZE])),
        tooltips=WaybarFont(
            values[WAYBAR_TOOLTIP_FONT_FAMILY], int(values[WAYBAR_TOOLTIP_FONT_SIZE])
        ),
    )


def get_waybar_font_setting(setting: str, path: Path = WAYBAR_THEME_STATE_PATH) -> str:
    return PolicyStore(StoreDatabase(path)).get(WAYBAR_FONT_POLICY_BY_SETTING[setting])


def detect_waybar_theme(waybar_theme_state_path: Path = WAYBAR_THEME_STATE_PATH) -> str:
    try:
        theme = PolicyStore(StoreDatabase(waybar_theme_state_path)).get(WAYBAR_THEME)
        return theme if theme in WAYBAR_THEMES else DEFAULT_THEME
    except (OSError, StoreError):
        return DEFAULT_THEME


def _read_waybar_theme_resource(theme: str, filename: str) -> str | None:
    resource = importlib.resources.files("archie").joinpath(
        WAYBAR_THEMES_RESOURCE, theme, filename
    )
    if not resource.is_file():
        return None
    return resource.read_text(encoding="utf-8")


def set_waybar_theme(
    theme: str,
    *,
    waybar_theme_state_path: Path = WAYBAR_THEME_STATE_PATH,
    waybar_config_path: Path = WAYBAR_CONFIG_PATH,
    waybar_style_path: Path = WAYBAR_STYLE_PATH,
) -> int:
    config_text = _read_waybar_theme_resource(theme, "config")
    style_text = _read_waybar_theme_resource(theme, "style.css")

    if config_text is None or style_text is None:
        print(
            f"archie system set waybar-theme: theme files not found for theme {theme!r}",
            file=sys.stderr,
        )
        return 1

    calendar_settings = get_calendar_settings(waybar_theme_state_path)
    datetime_settings = get_datetime_settings(waybar_theme_state_path)
    try:
        config_text = render_waybar_calendar_click(config_text, calendar_settings)
        config_text = render_waybar_datetime_click(config_text, datetime_settings)
    except ValueError as error:
        print(f"archie system set waybar-theme: {error}", file=sys.stderr)
        return 1
    waybar_config_path.parent.mkdir(parents=True, exist_ok=True)
    write_shared_text(waybar_config_path, config_text)
    write_shared_text(
        waybar_style_path,
        render_waybar_style(style_text, get_waybar_typography(waybar_theme_state_path)),
    )
    PolicyStore(StoreDatabase(waybar_theme_state_path)).set(WAYBAR_THEME, theme)
    return 0


def render_waybar_calendar_click(
    config_text: str,
    settings: Mapping[str, tuple[str, str]],
) -> str:
    return render_waybar_click_actions(
        config_text,
        "clock#1",
        settings,
        f"{CALENDAR_OPEN_COMMAND} --view {CALENDAR_VIEW_MONTH}",
        "calendar",
    )


def render_waybar_datetime_click(
    config_text: str,
    settings: Mapping[str, tuple[str, str]],
) -> str:
    for module, view in (("clock#2", "agenda"), ("clock#3", "week")):
        config_text = render_waybar_click_actions(
            config_text,
            module,
            settings,
            f"{DATETIME_OPEN_COMMAND} --view {view}",
            "datetime",
        )
    return config_text


def render_waybar_click_actions(
    config_text: str,
    module: str,
    settings: Mapping[str, tuple[str, str]],
    open_command: str,
    label: str,
) -> str:
    start = config_text.find(f'"{module}": {{')
    end = config_text.find("    },", start)
    if start < 0 or end < 0:
        raise ValueError(f"Waybar theme is missing the {module} {label} module")
    block = config_text[start:end]
    for click in CALENDAR_CLICKS:
        preset, _url = settings[click]
        setting = "on-click" if click == CALENDAR_CLICK_LEFT else "on-click-right"
        command = (
            f'{open_command} --click {click}'
            if preset != "unset"
            else None
        )
        block, replacements = re.subn(
            rf'^\s*"{re.escape(setting)}":.*\n',
            "" if command is None else rf'        "{setting}": "{command}"\n',
            block,
            flags=re.MULTILINE,
        )
        if replacements > 1:
            raise ValueError(f"Waybar theme has duplicate {setting} {label} actions")
        if replacements == 0 and command is not None:
            action_line = f'        "{setting}": "{command}"'
            block = block.rstrip("\n") + f",\n{action_line}\n"
    lines = block.splitlines()
    nonempty_lines = [index for index, line in enumerate(lines) if line.strip()]
    if nonempty_lines:
        last_line = nonempty_lines[-1]
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            is_click_action = re.match(r'^\s*"on-click(?:-right)?":', line) is not None
            if index != last_line and not is_click_action:
                continue
            normalized_line = line.rstrip().removesuffix(",")
            if index != last_line:
                normalized_line += ","
            lines[index] = normalized_line
        block = "\n".join(lines) + "\n"
    return config_text[:start] + block + config_text[end:]


def set_waybar_font_setting(
    setting: str,
    value: str | int,
    *,
    waybar_theme_state_path: Path = WAYBAR_THEME_STATE_PATH,
    waybar_style_path: Path = WAYBAR_STYLE_PATH,
) -> int:
    style_text = _read_waybar_theme_resource(
        detect_waybar_theme(waybar_theme_state_path), "style.css"
    )
    if style_text is None:
        raise ValueError("active Waybar theme files are not available")
    policy_key = WAYBAR_FONT_POLICY_BY_SETTING[setting]
    PolicyStore(StoreDatabase(waybar_theme_state_path)).set(policy_key, str(value))
    write_shared_text(
        waybar_style_path,
        render_waybar_style(style_text, get_waybar_typography(waybar_theme_state_path)),
    )
    return 0


def render_waybar_style(style_text: str, typography: WaybarTypography) -> str:
    return (
        style_text.rstrip()
        + "\n\n/* Archie-managed Waybar element typography. */\n"
        + "window#waybar,\nwindow#waybar .module,\n"
        + "window#waybar #workspaces button {\n"
        + f'  font-family: "{typography.elements.family}", monospace;\n'
        + f"  font-size: {typography.elements.size}px;\n}}\n"
        + "\n/* Archie-managed context-menu typography. */\n"
        + "menu,\nmenuitem {\n"
        + f'  font-family: "{typography.menus.family}", monospace;\n'
        + f"  font-size: {typography.menus.size}px;\n}}\n"
        + "\n/* Archie-managed tooltip typography. */\n"
        + "tooltip,\ntooltip label {\n"
        + f'  font-family: "{typography.tooltips.family}", monospace;\n'
        + f"  font-size: {typography.tooltips.size}px;\n}}\n"
    )


def valid_waybar_font_family(value: str) -> str:
    if not value.strip() or any(character in value for character in ('\n', '\r', '"', "'", ";", "{", "}")):
        raise argparse.ArgumentTypeError("font family must be a plain non-empty family name")
    return value.strip()


def valid_waybar_font_size(value: str) -> int:
    try:
        size = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("font size must be an integer") from error
    if not WAYBAR_FONT_MIN_SIZE <= size <= WAYBAR_FONT_MAX_SIZE:
        raise argparse.ArgumentTypeError(f"font size must be {WAYBAR_FONT_MIN_SIZE}-{WAYBAR_FONT_MAX_SIZE}")
    return size


def write_shared_text(path: Path, content: str) -> None:
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(content, encoding="utf-8")
    temporary_path.chmod(0o664)
    temporary_path.replace(path)


# --- shared ---


def execute_command(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed
