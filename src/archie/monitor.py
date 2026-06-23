import json
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class MonitorOutput:
    name: str
    description: str
    width: int
    height: int
    refresh_rate: float
    x: int
    y: int
    scale: float
    transform: int
    disabled: bool
    focused: bool

    @property
    def enabled(self) -> bool:
        return not self.disabled

    @property
    def label(self) -> str:
        if self.description:
            return self.description
        return self.name


class MonitorCommandError(RuntimeError):
    def __init__(self, result: CommandResult) -> None:
        self.result = result
        super().__init__(f"{' '.join(result.command)} exited with {result.returncode}")


def run_logged(command: Sequence[str]) -> CommandResult:
    command_list = list(command)
    print(f"$ {' '.join(command_list)}", flush=True)
    completed = subprocess.run(command_list, check=False, capture_output=True, text=True)
    result = CommandResult(
        command=command_list,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    if result.stdout:
        print(result.stdout, end="", flush=True)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr, flush=True)
    print(f"exit {result.returncode}: {' '.join(command_list)}", flush=True)
    return result


def require_success(result: CommandResult) -> CommandResult:
    if result.returncode != 0:
        raise MonitorCommandError(result)
    return result


def parse_monitors_json(content: str) -> list[MonitorOutput]:
    raw_monitors = json.loads(content)
    monitors: list[MonitorOutput] = []
    for raw in raw_monitors:
        monitors.append(
            MonitorOutput(
                name=str(raw.get("name", "")),
                description=str(raw.get("description", "")),
                width=int(raw.get("width", 0)),
                height=int(raw.get("height", 0)),
                refresh_rate=float(raw.get("refreshRate", 0.0)),
                x=int(raw.get("x", 0)),
                y=int(raw.get("y", 0)),
                scale=float(raw.get("scale", 1.0)),
                transform=int(raw.get("transform", 0)),
                disabled=bool(raw.get("disabled", False)),
                focused=bool(raw.get("focused", False)),
            )
        )
    return monitors


def list_monitors() -> list[MonitorOutput]:
    result = require_success(run_logged(["hyprctl", "-j", "monitors", "all"]))
    return parse_monitors_json(result.stdout)


def enabled_monitors(monitors: Sequence[MonitorOutput]) -> list[MonitorOutput]:
    return [monitor for monitor in monitors if monitor.enabled]


def can_disable(monitors: Sequence[MonitorOutput], monitor_name: str) -> bool:
    target = find_monitor(monitors, monitor_name)
    if target is None or not target.enabled:
        return False
    return len(enabled_monitors(monitors)) > 1


def find_monitor(monitors: Sequence[MonitorOutput], monitor_name: str) -> MonitorOutput | None:
    for monitor in monitors:
        if monitor.name == monitor_name:
            return monitor
    return None


def disable_monitor_command(monitor_name: str) -> list[str]:
    return ["hyprctl", "keyword", "monitor", f"{monitor_name},disable"]


def enable_monitor_command(monitor_name: str) -> list[str]:
    return ["hyprctl", "keyword", "monitor", f"{monitor_name},preferred,auto,1"]


def restore_monitor_commands(snapshot: Sequence[MonitorOutput]) -> list[list[str]]:
    commands: list[list[str]] = []
    for monitor in snapshot:
        if monitor.disabled:
            commands.append(disable_monitor_command(monitor.name))
        else:
            commands.append(["hyprctl", "keyword", "monitor", monitor_layout_value(monitor)])
    return commands


def monitor_layout_value(monitor: MonitorOutput) -> str:
    refresh = f"{monitor.refresh_rate:.2f}".rstrip("0").rstrip(".")
    value = (
        f"{monitor.name},"
        f"{monitor.width}x{monitor.height}@{refresh},"
        f"{monitor.x}x{monitor.y},"
        f"{format_scale(monitor.scale)}"
    )
    if monitor.transform:
        value = f"{value},transform,{monitor.transform}"
    return value


def format_scale(scale: float) -> str:
    return f"{scale:.3f}".rstrip("0").rstrip(".")


def restore_monitors(snapshot: Sequence[MonitorOutput]) -> None:
    for command in restore_monitor_commands(snapshot):
        require_success(run_logged(command))


def apply_monitor_toggle(monitors: Sequence[MonitorOutput], monitor_name: str) -> list[MonitorOutput]:
    target = find_monitor(monitors, monitor_name)
    if target is None:
        raise ValueError(f"unknown monitor: {monitor_name}")
    if target.enabled:
        if not can_disable(monitors, monitor_name):
            raise ValueError("refusing to disable the last enabled monitor")
        command = disable_monitor_command(monitor_name)
    else:
        command = enable_monitor_command(monitor_name)
    snapshot = list(monitors)
    try:
        require_success(run_logged(command))
    except MonitorCommandError:
        restore_monitors(snapshot)
        raise
    return snapshot
