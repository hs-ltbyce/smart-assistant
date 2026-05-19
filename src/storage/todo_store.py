"""SQLite 待办存储：表 todos（id, user_id, content, status, created_at）。"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_db_path() -> Path:
    raw = os.getenv("SMART_ASSISTANT_TODOS_DB", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parents[2] / "data" / "todos.db"


def _connect(path: Path | None = None) -> sqlite3.Connection:
    db = path or default_db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def ensure_db(path: Path | None = None) -> sqlite3.Connection:
    conn = _connect(path)
    init_schema(conn)
    return conn


def add_row(user_id: str, content: str, path: Path | None = None) -> int:
    uid = (user_id or "").strip() or "default_user"
    text = (content or "").strip()
    if not text:
        raise ValueError("content 不能为空")
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    conn = ensure_db(path)
    cur = conn.execute(
        "INSERT INTO todos (user_id, content, status, created_at) VALUES (?, ?, 'pending', ?)",
        (uid, text, now),
    )
    conn.commit()
    tid = int(cur.lastrowid)
    conn.close()
    return tid


def list_rows(
    user_id: str,
    status_filter: str | None = None,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    uid = (user_id or "").strip() or "default_user"
    conn = ensure_db(path)
    st = (status_filter or "").strip().lower()
    if st in {"pending", "done"}:
        rows = conn.execute(
            "SELECT id, content, status, created_at FROM todos WHERE user_id = ? AND status = ? ORDER BY id",
            (uid, st),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, content, status, created_at FROM todos WHERE user_id = ? ORDER BY id",
            (uid,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_row(user_id: str, todo_id: int, path: Path | None = None) -> bool:
    uid = (user_id or "").strip() or "default_user"
    conn = ensure_db(path)
    cur = conn.execute(
        "UPDATE todos SET status = 'done' WHERE id = ? AND user_id = ? AND status = 'pending'",
        (todo_id, uid),
    )
    conn.commit()
    n = cur.rowcount
    conn.close()
    return n > 0


def delete_row(user_id: str, todo_id: int, path: Path | None = None) -> bool:
    uid = (user_id or "").strip() or "default_user"
    conn = ensure_db(path)
    cur = conn.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, uid))
    conn.commit()
    n = cur.rowcount
    conn.close()
    return n > 0
