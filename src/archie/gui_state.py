import json
import subprocess
from dataclasses import asdict, dataclass

from archie.monitor import MonitorOutput
from archie.privacy import ShyModeSettings

GUI_SETTINGS_SNAPSHOT_ENV = "ARCHIE_GUI_SETTINGS_SNAPSHOT"
GUI_SETTINGS_SNAPSHOT_VERSION = 1


@dataclass(frozen=True)
class GuiSettingsSnapshot:
    brightness_result: subprocess.CompletedProcess[str]
    monitors: list[MonitorOutput]
    monitor_error: str | None
    lid_behavior: str
    notifications: str
    notification_sounds: str
    notification_sound: str
    shy_mode: ShyModeSettings
    kdeconnect: str
    power_profile: str
    waybar_theme: str


def serialize_gui_settings_snapshot(snapshot: GuiSettingsSnapshot) -> str:
    return json.dumps(
        {
            "version": GUI_SETTINGS_SNAPSHOT_VERSION,
            "brightness": {
                "returncode": snapshot.brightness_result.returncode,
                "stdout": snapshot.brightness_result.stdout,
                "stderr": snapshot.brightness_result.stderr,
            },
            "monitors": [asdict(monitor) for monitor in snapshot.monitors],
            "monitor_error": snapshot.monitor_error,
            "lid_behavior": snapshot.lid_behavior,
            "notifications": snapshot.notifications,
            "notification_sounds": snapshot.notification_sounds,
            "notification_sound": snapshot.notification_sound,
            "shy_mode": asdict(snapshot.shy_mode),
            "kdeconnect": snapshot.kdeconnect,
            "power_profile": snapshot.power_profile,
            "waybar_theme": snapshot.waybar_theme,
        },
        separators=(",", ":"),
    )


def deserialize_gui_settings_snapshot(payload: str) -> GuiSettingsSnapshot | None:
    try:
        data = json.loads(payload)
        if not isinstance(data, dict) or data.get("version") != GUI_SETTINGS_SNAPSHOT_VERSION:
            return None
        brightness = _require_dict(data, "brightness")
        monitors = _require_list(data, "monitors")
        shy_mode = _require_dict(data, "shy_mode")
        monitor_error = data["monitor_error"]
        if monitor_error is not None and not isinstance(monitor_error, str):
            return None
        return GuiSettingsSnapshot(
            brightness_result=subprocess.CompletedProcess(
                [],
                _require_int(brightness, "returncode"),
                _require_str(brightness, "stdout"),
                _require_str(brightness, "stderr"),
            ),
            monitors=[_deserialize_monitor(monitor) for monitor in monitors],
            monitor_error=monitor_error,
            lid_behavior=_require_str(data, "lid_behavior"),
            notifications=_require_str(data, "notifications"),
            notification_sounds=_require_str(data, "notification_sounds"),
            notification_sound=_require_str(data, "notification_sound"),
            shy_mode=ShyModeSettings(
                enabled=_require_bool(shy_mode, "enabled"),
                replay_count=_require_int(shy_mode, "replay_count"),
                replay_interval=_require_number(shy_mode, "replay_interval"),
            ),
            kdeconnect=_require_str(data, "kdeconnect"),
            power_profile=_require_str(data, "power_profile"),
            waybar_theme=_require_str(data, "waybar_theme"),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _deserialize_monitor(data: object) -> MonitorOutput:
    if not isinstance(data, dict):
        raise TypeError("monitor must be an object")
    return MonitorOutput(
        name=_require_str(data, "name"),
        description=_require_str(data, "description"),
        width=_require_int(data, "width"),
        height=_require_int(data, "height"),
        refresh_rate=_require_number(data, "refresh_rate"),
        x=_require_int(data, "x"),
        y=_require_int(data, "y"),
        scale=_require_number(data, "scale"),
        transform=_require_int(data, "transform"),
        disabled=_require_bool(data, "disabled"),
        focused=_require_bool(data, "focused"),
    )


def _require_dict(data: dict[str, object], key: str) -> dict[str, object]:
    value = data[key]
    if not isinstance(value, dict):
        raise TypeError(f"{key} must be an object")
    return value


def _require_list(data: dict[str, object], key: str) -> list[object]:
    value = data[key]
    if not isinstance(value, list):
        raise TypeError(f"{key} must be a list")
    return value


def _require_str(data: dict[str, object], key: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    return value


def _require_bool(data: dict[str, object], key: str) -> bool:
    value = data[key]
    if not isinstance(value, bool):
        raise TypeError(f"{key} must be a boolean")
    return value


def _require_int(data: dict[str, object], key: str) -> int:
    value = data[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{key} must be an integer")
    return value


def _require_number(data: dict[str, object], key: str) -> float:
    value = data[key]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{key} must be a number")
    return float(value)
