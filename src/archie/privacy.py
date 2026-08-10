import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Protocol

DEFAULT_REPLAY_COUNT = 10
DEFAULT_REPLAY_INTERVAL = 5.0
DEFAULT_DUNST_HISTORY_LIMIT = 20
SHARE_NODE_NAME = "xdg-desktop-portal-hyprland"


def shy_mode_config_path() -> Path:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "archie/shy-mode.json"


@dataclass(frozen=True)
class ShyModeSettings:
    enabled: bool = False
    replay_count: int = DEFAULT_REPLAY_COUNT
    replay_interval: float = DEFAULT_REPLAY_INTERVAL


def load_shy_mode_settings(path: Path | None = None) -> ShyModeSettings:
    settings_path = path or shy_mode_config_path()
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return ShyModeSettings()

    try:
        return ShyModeSettings(
            enabled=bool(data["enabled"]),
            replay_count=int(data["replay_count"]),
            replay_interval=float(data["replay_interval"]),
        )
    except (KeyError, TypeError, ValueError):
        return ShyModeSettings()


def save_shy_mode_settings(settings: ShyModeSettings, path: Path | None = None) -> None:
    settings_path = path or shy_mode_config_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = settings_path.with_suffix(f"{settings_path.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(asdict(settings), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(settings_path)


def format_shy_mode_settings(settings: ShyModeSettings) -> str:
    interval = f"{settings.replay_interval:g}"
    enabled = "on" if settings.enabled else "off"
    return (
        f"enabled: {enabled}\n"
        f"replay-count: {settings.replay_count}\n"
        f"replay-interval: {interval}s"
    )


def parse_share_active(output: str) -> bool:
    try:
        objects = json.loads(output)
    except json.JSONDecodeError:
        return False
    if not isinstance(objects, list):
        return False
    return any(
        isinstance(item, dict)
        and isinstance(item.get("info"), dict)
        and isinstance(item["info"].get("props"), dict)
        and item["info"]["props"].get("node.name") == SHARE_NODE_NAME
        for item in objects
    )


def detect_share_active() -> bool:
    try:
        result = subprocess.run(
            ["pw-dump"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0 and parse_share_active(result.stdout)


class CommandRunner(Protocol):
    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]: ...


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, check=False, capture_output=True, text=True)
    except FileNotFoundError as error:
        return subprocess.CompletedProcess(command, 127, stdout="", stderr=str(error))


class DunstClient:
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self.runner = runner or run_command

    def is_paused(self) -> bool | None:
        result = self.runner(["dunstctl", "is-paused"])
        if result.returncode != 0:
            return None
        return result.stdout.strip() == "true"

    def set_paused(self, paused: bool) -> bool:
        result = self.runner(
            ["dunstctl", "set-paused", "true" if paused else "false"]
        )
        return result.returncode == 0

    def waiting_count(self) -> int | None:
        return self._count("waiting")

    def history_count(self) -> int | None:
        return self._count("history")

    def history_pop(self) -> bool:
        return self.runner(["dunstctl", "history-pop"]).returncode == 0

    def _count(self, kind: str) -> int | None:
        result = self.runner(["dunstctl", "count", kind])
        if result.returncode != 0:
            return None
        try:
            return max(0, int(result.stdout.strip()))
        except ValueError:
            return None


@dataclass(frozen=True)
class ShyModeViewState:
    enabled: bool
    sharing: bool
    owns_pause: bool
    pending: bool
    replaying: bool


class ShyModeController:
    def __init__(
        self,
        dunst: DunstClient,
        *,
        settings_loader: Callable[[], ShyModeSettings] = load_shy_mode_settings,
    ) -> None:
        self.dunst = dunst
        self.settings_loader = settings_loader
        self.enabled = False
        self.sharing = False
        self.owns_pause = False
        self.pending = False
        self.replay_remaining = 0
        self.next_replay_at: float | None = None
        self.waiting_at_start = 0

    def poll(self, sharing: bool, now: float) -> ShyModeViewState:
        settings = self.settings_loader()
        if not settings.enabled:
            self._disable()
            self.sharing = sharing
            self.enabled = False
            return self.view_state(settings)

        if sharing and (not self.sharing or not self.enabled):
            self._start_share()
        elif sharing and self.owns_pause:
            paused = self.dunst.is_paused()
            if paused is False:
                self.owns_pause = False
                self.pending = False
            else:
                waiting = self.dunst.waiting_count()
                if waiting is not None and waiting > self.waiting_at_start:
                    self.pending = True
        elif not sharing and self.sharing:
            self._finish_share(settings, now)
        elif not sharing:
            self._advance_replay(settings, now)

        self.sharing = sharing
        self.enabled = True
        return self.view_state(settings)

    def view_state(self, settings: ShyModeSettings | None = None) -> ShyModeViewState:
        current = settings or self.settings_loader()
        return ShyModeViewState(
            enabled=current.enabled,
            sharing=self.sharing,
            owns_pause=self.owns_pause,
            pending=self.pending,
            replaying=self.replay_remaining > 0,
        )

    def _start_share(self) -> None:
        paused = self.dunst.is_paused()
        self.waiting_at_start = self.dunst.waiting_count() or 0
        self.owns_pause = paused is False and self.dunst.set_paused(True)
        self.pending = False
        self.replay_remaining = 0
        self.next_replay_at = None

    def _finish_share(self, settings: ShyModeSettings, now: float) -> None:
        if not self.owns_pause:
            self._clear_lifecycle()
            return

        waiting = self.dunst.waiting_count()
        missed_count = 0 if waiting is None else max(0, waiting - self.waiting_at_start)
        self.pending = self.pending or missed_count > 0
        self.dunst.set_paused(False)
        self.owns_pause = False
        if not self.pending:
            self._clear_replay()
            return

        history_count = self.dunst.history_count()
        available = missed_count if history_count is None else min(missed_count, history_count)
        self.replay_remaining = min(settings.replay_count, available)
        if self.replay_remaining == 0:
            self._clear_replay()
            return
        self.next_replay_at = now
        self._advance_replay(settings, now)

    def _advance_replay(self, settings: ShyModeSettings, now: float) -> None:
        if self.replay_remaining <= 0 or self.next_replay_at is None:
            return
        if now < self.next_replay_at:
            return
        if not self.dunst.history_pop():
            self._clear_replay()
            return
        self.replay_remaining -= 1
        if self.replay_remaining == 0:
            self._clear_replay()
            return
        self.next_replay_at = now + settings.replay_interval

    def _disable(self) -> None:
        if self.owns_pause:
            self.dunst.set_paused(False)
        self.owns_pause = False
        self.pending = False
        self._clear_replay()

    def _clear_lifecycle(self) -> None:
        self.owns_pause = False
        self.pending = False
        self._clear_replay()

    def _clear_replay(self) -> None:
        self.replay_remaining = 0
        self.next_replay_at = None
        self.pending = False
