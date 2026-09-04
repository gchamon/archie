import sqlite3
import tempfile
import unittest
from pathlib import Path

from archie.store import (
    NOTIFICATION_SOUNDS_ENABLED,
    SHY_MODE_REPLAY_COUNT,
    STORE_SCHEMA_VERSION,
    WAYBAR_FONT_FAMILY,
    WAYBAR_FONT_SIZE,
    WAYBAR_MENU_FONT_FAMILY,
    WAYBAR_MENU_FONT_SIZE,
    WAYBAR_TOOLTIP_FONT_FAMILY,
    WAYBAR_TOOLTIP_FONT_SIZE,
    PolicyStore,
    StoreDatabase,
    StoreError,
)


class StoreDatabaseTest(unittest.TestCase):
    def test_missing_store_is_read_as_empty_without_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "store.sqlite3"
            database = StoreDatabase(path)

            self.assertEqual(database.fetch_all("SELECT 1"), [])
            self.assertFalse(path.exists())

    def test_initializes_preprovisioned_store_without_changing_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "store.sqlite3"
            path.touch()
            path.chmod(0o600)
            StoreDatabase(path).ensure_schema()

            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with sqlite3.connect(path) as connection:
                version = connection.execute("PRAGMA user_version").fetchone()[0]
            self.assertEqual(version, STORE_SCHEMA_VERSION)

    def test_write_fails_without_creating_missing_store(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "store.sqlite3"

            with self.assertRaises(StoreError):
                PolicyStore(StoreDatabase(path)).set(NOTIFICATION_SOUNDS_ENABLED, "off")

            self.assertFalse(path.exists())

    def test_precreated_empty_store_can_be_initialized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "store.sqlite3"
            path.touch()
            database = StoreDatabase(path)

            database.ensure_schema()

            with sqlite3.connect(path) as connection:
                version = connection.execute("PRAGMA user_version").fetchone()[0]
            self.assertEqual(version, STORE_SCHEMA_VERSION)

    def test_rejects_newer_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "store.sqlite3"
            with sqlite3.connect(path) as connection:
                connection.execute("PRAGMA user_version = 99")

            with self.assertRaises(StoreError):
                StoreDatabase(path).fetch_all("SELECT 1")

    def test_database_schema_is_not_specific_to_policy_store(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "store.sqlite3"
            path.touch()
            database = StoreDatabase(path)
            database.ensure_table(
                "CREATE TABLE example (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            database.execute_many(
                "INSERT INTO example(key, value) VALUES (?, ?)",
                (("hello", "world"),),
            )

            self.assertEqual(
                database.fetch_all("SELECT value FROM example WHERE key = 'hello'"),
                [("world",)],
            )


class PolicyStoreTest(unittest.TestCase):
    def test_defaults_and_round_trips_are_domain_specific(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "store.sqlite3"
            path.touch()
            store = PolicyStore(StoreDatabase(path))

            self.assertEqual(store.get(NOTIFICATION_SOUNDS_ENABLED), "on")
            self.assertEqual(store.get(WAYBAR_FONT_FAMILY), "MesloLGM Nerd Font")
            self.assertEqual(store.get(WAYBAR_FONT_SIZE), "20")
            self.assertEqual(store.get(WAYBAR_MENU_FONT_FAMILY), "MesloLGM Nerd Font")
            self.assertEqual(store.get(WAYBAR_MENU_FONT_SIZE), "20")
            self.assertEqual(store.get(WAYBAR_TOOLTIP_FONT_FAMILY), "MesloLGM Nerd Font")
            self.assertEqual(store.get(WAYBAR_TOOLTIP_FONT_SIZE), "20")
            store.set_many(
                {
                    NOTIFICATION_SOUNDS_ENABLED: "off",
                    SHY_MODE_REPLAY_COUNT: "6",
                }
            )
            self.assertEqual(store.get(NOTIFICATION_SOUNDS_ENABLED), "off")
            self.assertEqual(store.get(SHY_MODE_REPLAY_COUNT), "6")

    def test_initialize_does_not_overwrite_existing_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "store.sqlite3"
            path.touch()
            store = PolicyStore(StoreDatabase(path))
            store.set(NOTIFICATION_SOUNDS_ENABLED, "off")

            self.assertFalse(store.initialize({NOTIFICATION_SOUNDS_ENABLED: "on"}))
            self.assertEqual(store.get(NOTIFICATION_SOUNDS_ENABLED), "off")

    def test_rejects_unknown_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "store.sqlite3"
            path.touch()
            store = PolicyStore(StoreDatabase(path))
            with self.assertRaises(KeyError):
                store.set("unknown", "value")
