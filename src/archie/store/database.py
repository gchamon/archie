import os
import sqlite3
from collections.abc import Iterable, Sequence
from pathlib import Path

STORE_DATABASE_PATH = Path("/var/lib/archie/store.sqlite3")
STORE_SCHEMA_VERSION = 1


class StoreError(RuntimeError):
    """Raised when the shared Archie store cannot be read or written."""


class StoreDatabase:
    """SQLite lifecycle and schema boundary shared by Archie domain stores."""

    def __init__(self, path: Path = STORE_DATABASE_PATH) -> None:
        self.path = path

    def fetch_all(
        self,
        query: str,
        parameters: Sequence[object] = (),
    ) -> list[tuple[object, ...]]:
        if not self.path.exists():
            return []
        try:
            with self._connect() as connection:
                self._verify_schema(connection)
                return connection.execute(query, parameters).fetchall()
        except sqlite3.Error as error:
            raise StoreError(f"could not read store: {error}") from error

    def execute_many(self, query: str, rows: Iterable[Sequence[object]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._connect(create=True) as connection:
                self._initialize_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                connection.executemany(query, rows)
                connection.commit()
        except sqlite3.Error as error:
            raise StoreError(f"could not write store: {error}") from error
        self.path.chmod(0o664)

    def ensure_table(self, ddl: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._connect(create=True) as connection:
                self._initialize_schema(connection)
                connection.execute(ddl)
                connection.commit()
        except sqlite3.Error as error:
            raise StoreError(f"could not initialize store table: {error}") from error
        self.path.chmod(0o664)

    def has_rows(self, table: str) -> bool:
        if not self.table_exists(table):
            return False
        rows = self.fetch_all(f"SELECT 1 FROM {table} LIMIT 1")
        return bool(rows)

    def table_exists(self, table: str) -> bool:
        rows = self.fetch_all(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        )
        return bool(rows)

    def ensure_schema(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._connect(create=True) as connection:
                self._initialize_schema(connection)
        except sqlite3.Error as error:
            raise StoreError(f"could not initialize store: {error}") from error
        self.path.chmod(0o664)

    def _connect(self, *, create: bool = False) -> sqlite3.Connection:
        if create:
            previous_umask = os.umask(0o002)
            try:
                connection = sqlite3.connect(self.path, timeout=2)
            finally:
                os.umask(previous_umask)
        else:
            connection = sqlite3.connect(self.path, timeout=2)
        connection.execute("PRAGMA busy_timeout = 2000")
        return connection

    def _initialize_schema(self, connection: sqlite3.Connection) -> None:
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if version > STORE_SCHEMA_VERSION:
            raise StoreError(
                f"store schema {version} is newer than supported "
                f"schema {STORE_SCHEMA_VERSION}"
            )
        if version == 0:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS store_meta ("
                "key TEXT PRIMARY KEY, value TEXT NOT NULL"
                ")"
            )
            connection.execute(f"PRAGMA user_version = {STORE_SCHEMA_VERSION}")
            connection.commit()
        self._verify_schema(connection)

    @staticmethod
    def _verify_schema(connection: sqlite3.Connection) -> None:
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if version != STORE_SCHEMA_VERSION:
            raise StoreError(
                f"unsupported store schema {version}; expected {STORE_SCHEMA_VERSION}"
            )
