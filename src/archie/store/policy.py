from collections.abc import Mapping

from archie.store.database import StoreDatabase

CALENDAR_LAUNCHER = "desktop.calendar.launcher"
CALENDAR_CLICK = "desktop.calendar.click"
CALENDAR_PRESET = "desktop.calendar.preset"
CALENDAR_BROWSER_URL = "desktop.calendar.browser-url"
CALENDAR_LEFT_PRESET = "desktop.calendar.left.preset"
CALENDAR_LEFT_BROWSER_URL = "desktop.calendar.left.browser-url"
CALENDAR_RIGHT_PRESET = "desktop.calendar.right.preset"
CALENDAR_RIGHT_BROWSER_URL = "desktop.calendar.right.browser-url"
DATETIME_LEFT_PRESET = "desktop.datetime.left.preset"
DATETIME_LEFT_BROWSER_URL = "desktop.datetime.left.browser-url"
DATETIME_RIGHT_PRESET = "desktop.datetime.right.preset"
DATETIME_RIGHT_BROWSER_URL = "desktop.datetime.right.browser-url"
NOTIFICATION_SOUNDS_ENABLED = "notifications.sounds.enabled"
NOTIFICATION_SOUND_SOURCE = "notifications.sound.source"
SHY_MODE_ENABLED = "privacy.shy-mode.enabled"
SHY_MODE_REPLAY_COUNT = "privacy.shy-mode.replay-count"
SHY_MODE_REPLAY_INTERVAL = "privacy.shy-mode.replay-interval"
WAYBAR_THEME = "desktop.waybar.theme"
WAYBAR_FONT_FAMILY = "desktop.waybar.font-family"
WAYBAR_FONT_SIZE = "desktop.waybar.font-size"
WAYBAR_MENU_FONT_FAMILY = "desktop.waybar.menu-font-family"
WAYBAR_MENU_FONT_SIZE = "desktop.waybar.menu-font-size"
WAYBAR_TOOLTIP_FONT_FAMILY = "desktop.waybar.tooltip-font-family"
WAYBAR_TOOLTIP_FONT_SIZE = "desktop.waybar.tooltip-font-size"

POLICY_DEFAULTS: dict[str, str] = {
    CALENDAR_LEFT_PRESET: "unset",
    CALENDAR_LEFT_BROWSER_URL: "",
    CALENDAR_RIGHT_PRESET: "gnome-calendar",
    CALENDAR_RIGHT_BROWSER_URL: "",
    DATETIME_LEFT_PRESET: "unset",
    DATETIME_LEFT_BROWSER_URL: "",
    DATETIME_RIGHT_PRESET: "gnome-datetime",
    DATETIME_RIGHT_BROWSER_URL: "",
    NOTIFICATION_SOUNDS_ENABLED: "on",
    NOTIFICATION_SOUND_SOURCE: "default",
    SHY_MODE_ENABLED: "off",
    SHY_MODE_REPLAY_COUNT: "10",
    SHY_MODE_REPLAY_INTERVAL: "5",
    WAYBAR_THEME: "cjbassi",
    WAYBAR_FONT_FAMILY: "MesloLGM Nerd Font",
    WAYBAR_FONT_SIZE: "20",
    WAYBAR_MENU_FONT_FAMILY: "MesloLGM Nerd Font",
    WAYBAR_MENU_FONT_SIZE: "20",
    WAYBAR_TOOLTIP_FONT_FAMILY: "MesloLGM Nerd Font",
    WAYBAR_TOOLTIP_FONT_SIZE: "20",
}


class PolicyStore:
    """Domain store for Archie-owned persistent desktop policy."""

    def __init__(self, database: StoreDatabase | None = None) -> None:
        self.database = database or StoreDatabase()

    def get(self, key: str) -> str:
        default = self._default(key)
        if not self.database.table_exists("policy"):
            return default
        rows = self.database.fetch_all(
            "SELECT value FROM policy WHERE key = ?",
            (key,),
        )
        return default if not rows else str(rows[0][0])

    def get_optional(self, key: str) -> str | None:
        if not self.database.table_exists("policy"):
            return None
        rows = self.database.fetch_all(
            "SELECT value FROM policy WHERE key = ?",
            (key,),
        )
        return None if not rows else str(rows[0][0])

    def get_many(self, keys: tuple[str, ...]) -> dict[str, str]:
        for key in keys:
            self._default(key)
        values = {key: POLICY_DEFAULTS[key] for key in keys}
        if not self.database.table_exists("policy"):
            return values
        placeholders = ", ".join("?" for _key in keys)
        rows = self.database.fetch_all(
            f"SELECT key, value FROM policy WHERE key IN ({placeholders})",
            keys,
        )
        values.update((str(key), str(value)) for key, value in rows)
        return values

    def set(self, key: str, value: str) -> None:
        self.set_many({key: value})

    def set_many(self, values: Mapping[str, str]) -> None:
        for key in values:
            self._default(key)
        self.database.ensure_table(
            "CREATE TABLE IF NOT EXISTS policy ("
            "key TEXT PRIMARY KEY, value TEXT NOT NULL"
            ")"
        )
        self.database.execute_many(
            "INSERT INTO policy(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            tuple(values.items()),
        )

    def delete(self, key: str) -> None:
        if not self.database.table_exists("policy"):
            return
        self.database.execute_many(
            "DELETE FROM policy WHERE key = ?",
            ((key,),),
        )

    def is_initialized(self) -> bool:
        return self.database.has_rows("policy")

    def initialize(self, values: Mapping[str, str] | None = None) -> bool:
        if self.is_initialized():
            return False
        self.set_many(values or POLICY_DEFAULTS)
        return True

    @staticmethod
    def _default(key: str) -> str:
        try:
            return POLICY_DEFAULTS[key]
        except KeyError as error:
            raise KeyError(f"unknown Archie policy key: {key}") from error
