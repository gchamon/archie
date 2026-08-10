import argparse
import configparser
import importlib.resources
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Protocol

from archie.monitor import MonitorOutput, list_monitors_quiet

from archie.privacy import (
    DEFAULT_DUNST_HISTORY_LIMIT,
    ShyModeSettings,
    detect_share_active,
    format_shy_mode_settings,
    load_shy_mode_settings,
    save_shy_mode_settings,
)

LID_CLOSE_CONF_PATH = Path("/etc/systemd/logind.conf.d/lid-close.conf")
WAYBAR_THEME_STATE_PATH = Path.home() / ".config/waybar/.archie-theme"
WAYBAR_CONFIG_PATH = Path.home() / ".config/waybar/config"
WAYBAR_STYLE_PATH = Path.home() / ".config/waybar/style.css"
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

SYSTEM_STATUS_SETTINGS = [
    "lid-close-behavior",
    "notifications",
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
    system_subparsers = parser.add_subparsers(dest="system_command", required=True)

    get_parser = system_subparsers.add_parser(
        "get",
        help="Read an Archie-owned system setting.",
        description="Read an Archie-owned system setting.",
    )
    get_subparsers = get_parser.add_subparsers(dest="setting", required=True)
    for setting, help_text, description in (
        ("lid-close-behavior", "Read lid close behavior.", "Read Archie-managed lid close behavior."),
        ("notifications", "Read dunst notification state.", "Read whether dunst notifications are on or off."),
        ("shy-mode", "Read shy mode notification privacy settings.", "Read Archie-managed shy mode and replay settings."),
        ("share-state", "Read the managed screen-share state.", "Read whether the managed Hyprland portal is sharing a screen."),
        ("kdeconnect", "Read KDE Connect daemon state.", "Read whether the KDE Connect daemon is running."),
        ("power-profile", "Read the active power profile.", "Read the active power profile via power-profiles-daemon."),
        ("waybar-theme", "Read the active waybar theme.", "Read the Archie-managed waybar theme."),
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

    set_parser = system_subparsers.add_parser(
        "set",
        help="Change an Archie-owned system setting.",
    )
    set_subparsers = set_parser.add_subparsers(dest="setting", required=True)

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
) -> int:
    match args.setting:
        case "lid-close-behavior":
            print(detect_lid_close_behavior(lid_close_conf_path))
            return 0
        case "notifications":
            print(detect_notifications_state())
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
) -> tuple[dict[str, object], dict[str, str]]:
    readers: dict[str, Callable[[], object]] = {
        "lid-close-behavior": lambda: detect_lid_close_behavior(lid_close_conf_path),
        "notifications": detect_notifications_state,
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
) -> int:
    values, _errors = collect_system_status(
        lid_close_conf_path=lid_close_conf_path,
        waybar_theme_state_path=waybar_theme_state_path,
        backlight_path=backlight_path,
        shy_mode_path=shy_mode_path,
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
        case "shy-mode":
            current = load_shy_mode_settings(shy_mode_path)
            settings = ShyModeSettings(
                enabled=args.value == ON_VALUE,
                replay_count=args.replay_count or current.replay_count,
                replay_interval=args.replay_interval or current.replay_interval,
            )
            save_shy_mode_settings(settings, shy_mode_path)
            return 0
        case "kdeconnect":
            return set_kdeconnect(args.value)
        case "power-profile":
            return set_power_profile(args.value, executor=execute)
        case "waybar-theme":
            return set_waybar_theme(
                args.value,
                waybar_theme_state_path=waybar_theme_state_path,
                waybar_config_path=waybar_config_path,
                waybar_style_path=waybar_style_path,
            )
        case "brightness":
            return set_brightness(args.device, args.percent, executor=execute)
        case _:
            print(
                f"archie system set: unsupported setting: {args.setting}",
                file=sys.stderr,
            )
            return 2


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


def detect_waybar_theme(waybar_theme_state_path: Path = WAYBAR_THEME_STATE_PATH) -> str:
    try:
        return waybar_theme_state_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
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
    waybar_config_path.write_text(config_text, encoding="utf-8")
    waybar_style_path.write_text(style_text, encoding="utf-8")
    waybar_theme_state_path.write_text(theme, encoding="utf-8")
    return 0


# --- shared ---


def execute_command(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed
