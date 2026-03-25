"""Shared extraction utilities: JSON, timestamps, upsert SQL, workspace iteration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any


def json_dumps_payload(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=False, default=str)


def parse_iso_datetime(val: Any) -> datetime | None:
    if val is None or not isinstance(val, str):
        return None
    s = val.strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is not None:
            dt = dt.astimezone(UTC).replace(tzinfo=None)
        return dt
    except ValueError:
        return None


def synced_at_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def tri_bool(val: Any) -> int | None:
    if val is None:
        return None
    return 1 if val else 0


def pick_str(d: dict[str, Any], *keys: str) -> str | None:
    for k in keys:
        if k in d and d[k] is not None and d[k] != "":
            v = d[k]
            return v if isinstance(v, str) else str(v)
    return None


def pick_int(d: dict[str, Any], *keys: str) -> int | None:
    for k in keys:
        if k in d and d[k] is not None:
            try:
                return int(d[k])
            except (TypeError, ValueError):
                return None
    return None


def fetch_groups_json(pbi: Any) -> list[dict[str, Any]]:
    r = pbi.call("get", "groups")
    r.raise_for_status()
    data = r.json()
    return list(data.get("value") or [])


def upsert_row(
    cursor: Any,
    *,
    table: str,
    columns: list[str],
    pk_columns: set[str],
    values: tuple[Any, ...],
) -> None:
    if len(columns) != len(values):
        raise ValueError("columns and values length mismatch")
    quoted = ", ".join(f"`{c}`" for c in columns)
    placeholders = ", ".join(["?"] * len(columns))
    non_pk = [c for c in columns if c not in pk_columns]
    if not non_pk:
        raise ValueError("need at least one non-PK column for upsert")
    updates = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in non_pk)
    sql = f"INSERT INTO `{table}` ({quoted}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"
    cursor.execute(sql, values)
