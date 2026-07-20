import argparse
import configparser
import importlib.resources
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

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
    )
    get_subparsers = get_parser.add_subparsers(dest="setting", required=True)

    lid_get_parser = get_subparsers.add_parser(
        "lid-close-behavior",
        help="Read lid close behavior.",
        description="Read Archie-managed lid close behavior.",
    )
    lid_get_parser.set_defaults(func=run_system_get)

    notifications_get_parser = get_subparsers.add_parser(
        "notifications",
        help="Read dunst notification state.",
        description="Read whether dunst notifications are on or off.",
    )
    notifications_get_parser.set_defaults(func=run_system_get)

    kdeconnect_get_parser = get_subparsers.add_parser(
        "kdeconnect",
        help="Read KDE Connect daemon state.",
        description="Read whether the KDE Connect daemon is running.",
    )
    kdeconnect_get_parser.set_defaults(func=run_system_get)

    power_profile_get_parser = get_subparsers.add_parser(
        "power-profile",
        help="Read the active power profile.",
        description="Read the active power profile via power-profiles-daemon.",
    )
    power_profile_get_parser.set_defaults(func=run_system_get)

    waybar_theme_get_parser = get_subparsers.add_parser(
        "waybar-theme",
        help="Read the active waybar theme.",
        description="Read the Archie-managed waybar theme.",
    )
    waybar_theme_get_parser.set_defaults(func=run_system_get)

    brightness_get_parser = get_subparsers.add_parser(
        "brightness",
        help="Read screen brightness state.",
        description="Read screen backlight brightness state.",
    )
    brightness_get_parser.set_defaults(func=run_system_get)

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

    kdeconnect_set_parser = set_subparsers.add_parser(
        "kdeconnect",
        help="Start or stop the KDE Connect daemon.",
        description="Start or stop kdeconnectd and kdeconnect-indicator.",
    )
    kdeconnect_set_parser.add_argument(
        "value",
        choices=[ON_VALUE, OFF_VALUE],
        help="Use on to start KDE Connect or off to stop it.",
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
) -> int:
    match args.setting:
        case "lid-close-behavior":
            print(detect_lid_close_behavior(lid_close_conf_path))
            return 0
        case "notifications":
            print(detect_notifications_state())
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


def run_system_set(
    args: argparse.Namespace,
    *,
    lid_close_conf_path: Path = LID_CLOSE_CONF_PATH,
    waybar_theme_state_path: Path = WAYBAR_THEME_STATE_PATH,
    waybar_config_path: Path = WAYBAR_CONFIG_PATH,
    waybar_style_path: Path = WAYBAR_STYLE_PATH,
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
    if is_user_unit_active(KDECONNECT_AUTOSTART_UNIT):
        return ON_VALUE
    if is_user_unit_active(KDECONNECT_DBUS_UNIT_GLOB):
        return ON_VALUE
    return OFF_VALUE


KDECONNECT_AUTOSTART_UNIT = "app-org.kde.kdeconnect.daemon@autostart.service"
# kdeconnectd also runs as a transient D-Bus-activated unit whose name carries a
# volatile bus-name instance (e.g. dbus-:1.2-org.kde.kdeconnect@2.service); match
# it by glob so a plain pkill is not undone by systemd/D-Bus reactivating it.
KDECONNECT_DBUS_UNIT_GLOB = "dbus-*org.kde.kdeconnect*.service"


def is_user_unit_active(unit: str) -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "--quiet", unit],
            check=False,
        )
    except FileNotFoundError:
        return is_process_running("kdeconnectd")
    return result.returncode == 0


def is_process_running(process_name: str) -> bool:
    result = subprocess.run(
        ["pgrep", "-x", process_name],
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def set_kdeconnect(value: str) -> int:
    if value == OFF_VALUE:
        # kdeconnectd is systemd/D-Bus managed; killing the process alone is
        # undone by reactivation. Stop both the autostart and the transient
        # D-Bus-activated units so it actually stays down.
        subprocess.run(
            ["systemctl", "--user", "stop", KDECONNECT_AUTOSTART_UNIT, KDECONNECT_DBUS_UNIT_GLOB],
            check=False,
        )
        # The tray indicator is a plain app, not a unit. pkill -x cannot be used:
        # comm is truncated to 15 chars so "kdeconnect-indicator" never matches by
        # name; match the basename whether launched bare or by full path.
        subprocess.run(["pkill", "-f", r"(^|/)kdeconnect-indicator( |$)"], check=False)
        return 0
    subprocess.run(
        ["systemctl", "--user", "start", KDECONNECT_AUTOSTART_UNIT],
        check=False,
    )
    _spawn_detached(["kdeconnect-indicator"])
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
        result = subprocess.run(
            ["powerprofilesctl", "get"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("unavailable", file=sys.stderr)
        print(UNKNOWN_MODE)
        return 0
    if result.returncode != 0:
        print(
            f"archie system get power-profile: {result.stderr.strip()}", file=sys.stderr
        )
        return result.returncode
    print(result.stdout.strip())
    return 0


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
