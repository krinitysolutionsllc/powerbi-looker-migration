"""Minimal MariaDB access: config from env, context manager with cursor / execute helpers."""

from __future__ import annotations

import os
from collections.abc import Sequence
from types import TracebackType
from typing import Any, Self

import mariadb


def mariadb_config_from_env() -> dict[str, Any]:
    """Build kwargs for mariadb.connect from environment variables."""
    return {
        "host": os.environ["MARIADB_HOST"],
        "port": int(os.environ.get("MARIADB_PORT", "3306")),
        "user": os.environ["MARIADB_USER"],
        "password": os.environ["MARIADB_PASSWORD"],
        "database": os.environ["MARIADB_DATABASE"],
    }


class MariaDBClient:
    """Context manager: ``with MariaDBClient.from_env() as db:`` then ``db.cursor()`` or ``db.execute(sql, params)``.

    Commits on successful exit from the block, rolls back on exception, always closes.
    """

    def __init__(self, **connect_kwargs: Any) -> None:
        self._kwargs = connect_kwargs
        self._conn: mariadb.Connection | None = None

    @classmethod
    def from_env(cls) -> Self:
        return cls(**mariadb_config_from_env())

    def __enter__(self) -> Self:
        self._conn = mariadb.connect(**self._kwargs)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._conn is None:
            return
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self._conn.close()
            self._conn = None

    @property
    def connection(self) -> mariadb.Connection:
        if self._conn is None:
            raise RuntimeError("MariaDBClient must be used inside a 'with' block")
        return self._conn

    def cursor(self, *args: Any, **kwargs: Any) -> Any:
        """Return a new cursor (same as ``connection.cursor()``). Caller should close when done."""
        return self.connection.cursor(*args, **kwargs)

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> int:
        """Run a single SQL statement; commit happens when the ``with`` block exits. Returns ``rowcount``."""
        with self.cursor() as cur:
            cur.execute(sql, tuple(params) if params is not None else ())
            return cur.rowcount
