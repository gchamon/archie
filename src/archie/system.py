import argparse
import configparser
import importlib.resources
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

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
    match args.setting:
        case "lid-close-behavior":
            print(detect_lid_close_behavior(lid_close_conf_path))
            return 0
        case "notifications":
            print(detect_notifications_state())
            return 0
        case "notification-sounds":
            print(
                ON_VALUE
                if load_notification_sounds_enabled(notification_sounds_path)
                else OFF_VALUE
            )
            return 0
        case "notification-sound":
            print(load_notification_sound_path(notification_sounds_path) or "default")
            return 0
        case "shy-mode":
            print(format_shy_mode_settings(load_shy_mode_settings(shy_mode_path)))
            return 0
        case "share-state":
            print(ON_VALUE if detect_share_active() else OFF_VALUE)
            return 0
        case "kdeconnect":
            print(detect_kdeconnect_state())
            return 0
        case "power-profile":
            return detect_power_profile()
        case "waybar-theme":
            print(detect_waybar_theme(waybar_theme_state_path))
            return 0
        case "waybar-font-family" | "waybar-font-size" | "waybar-menu-font-family" | "waybar-menu-font-size" | "waybar-tooltip-font-family" | "waybar-tooltip-font-size":
            print(get_waybar_font_setting(args.setting, waybar_theme_state_path))
            return 0
        case "brightness":
            return print_brightness_state(backlight_path)
        case _:
            print(
                f"archie system get: unsupported setting: {args.setting}",
                file=sys.stderr,
            )
            return 2


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
            except Exception as error:
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
    match args.setting:
        case "lid-close-behavior":
            if args.value not in LID_CLOSE_CONTENT_BY_MODE:
                print(
                    f"archie system set: unsupported lid-close-behavior: {args.value}",
                    file=sys.stderr,
                )
                return 2
            install_code = install_lid_close_behavior(
                args.value, lid_close_conf_path, executor=execute
            )
            if install_code != 0:
                return install_code
            return reload_logind_if_active(executor=execute)
        case "notifications":
            return set_notifications(args.value, executor=execute)
        case "notification-sounds":
            try:
                save_notification_sounds_enabled(args.value == ON_VALUE, notification_sounds_path)
            except (OSError, StoreError) as error:
                print(f"archie system set notification-sounds: {error}", file=sys.stderr)
                return 1
            return 0
        case "notification-sound":
            try:
                save_notification_sound_path(args.value, notification_sounds_path)
            except (OSError, StoreError, ValueError) as error:
                print(f"archie system set notification-sound: {error}", file=sys.stderr)
                return 2 if isinstance(error, ValueError) else 1
            return 0
        case "shy-mode":
            current = load_shy_mode_settings(shy_mode_path)
            settings = ShyModeSettings(
                enabled=args.value == ON_VALUE,
                replay_count=args.replay_count or current.replay_count,
                replay_interval=args.replay_interval or current.replay_interval,
            )
            try:
                save_shy_mode_settings(settings, shy_mode_path)
            except (OSError, StoreError) as error:
                print(f"archie system set shy-mode: {error}", file=sys.stderr)
                return 1
            return 0
        case "kdeconnect":
            return set_kdeconnect(args.value)
        case "power-profile":
            return set_power_profile(args.value, executor=execute)
        case "waybar-theme":
            try:
                return set_waybar_theme(
                    args.value,
                    waybar_theme_state_path=waybar_theme_state_path,
                    waybar_config_path=waybar_config_path,
                    waybar_style_path=waybar_style_path,
                )
            except (OSError, StoreError) as error:
                print(f"archie system set waybar-theme: {error}", file=sys.stderr)
                return 1
        case "waybar-font-family" | "waybar-font-size" | "waybar-menu-font-family" | "waybar-menu-font-size" | "waybar-tooltip-font-family" | "waybar-tooltip-font-size":
            try:
                return set_waybar_font_setting(
                    args.setting,
                    args.value,
                    waybar_theme_state_path=waybar_theme_state_path,
                    waybar_style_path=waybar_style_path,
                )
            except (OSError, StoreError, ValueError) as error:
                print(f"archie system set {args.setting}: {error}", file=sys.stderr)
                return 1
        case "brightness":
            return set_brightness(args.device, args.percent, executor=execute)
        case _:
            print(
                f"archie system set: unsupported setting: {args.setting}",
                file=sys.stderr,
            )
            return 2


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

    waybar_config_path.parent.mkdir(parents=True, exist_ok=True)
    write_shared_text(waybar_config_path, config_text)
    write_shared_text(
        waybar_style_path,
        render_waybar_style(style_text, get_waybar_typography(waybar_theme_state_path)),
    )
    PolicyStore(StoreDatabase(waybar_theme_state_path)).set(WAYBAR_THEME, theme)
    return 0


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
