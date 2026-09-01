from collections.abc import Mapping

from archie.store.database import StoreDatabase

NOTIFICATION_SOUNDS_ENABLED = "notifications.sounds.enabled"
NOTIFICATION_SOUND_SOURCE = "notifications.sound.source"
SHY_MODE_ENABLED = "privacy.shy-mode.enabled"
SHY_MODE_REPLAY_COUNT = "privacy.shy-mode.replay-count"
SHY_MODE_REPLAY_INTERVAL = "privacy.shy-mode.replay-interval"
WAYBAR_THEME = "desktop.waybar.theme"

POLICY_DEFAULTS: dict[str, str] = {
    NOTIFICATION_SOUNDS_ENABLED: "on",
    NOTIFICATION_SOUND_SOURCE: "default",
    SHY_MODE_ENABLED: "off",
    SHY_MODE_REPLAY_COUNT: "10",
    SHY_MODE_REPLAY_INTERVAL: "5",
    WAYBAR_THEME: "cjbassi",
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
