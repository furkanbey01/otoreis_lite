from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator


class DB:
    def __init__(self, path: str):
        self.path = path

    @contextmanager
    def conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self) -> None:
        with self.conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT NOT NULL DEFAULT '',
                    plan_json TEXT NOT NULL,
                    current_step INTEGER NOT NULL DEFAULT 0,
                    total_steps INTEGER NOT NULL DEFAULT 0,
                    pending_approval_json TEXT,
                    options_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    event TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def create_task(self, goal: str, status: str, plan: list[dict[str, Any]], options: dict[str, Any]) -> int:
        with self.conn() as conn:
            cur = conn.execute(
                "INSERT INTO tasks(goal,status,plan_json,total_steps,options_json) VALUES (?,?,?,?,?)",
                (goal, status, json.dumps(plan), len(plan), json.dumps(options)),
            )
            return int(cur.lastrowid)

    def update_task(self, task_id: int, **updates: Any) -> None:
        if not updates:
            return
        cols = ", ".join([f"{k}=?" for k in updates]) + ", updated_at=CURRENT_TIMESTAMP"
        values = list(updates.values()) + [task_id]
        with self.conn() as conn:
            conn.execute(f"UPDATE tasks SET {cols} WHERE id=?", values)

    def get_task(self, task_id: int) -> dict[str, Any] | None:
        with self.conn() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            return dict(row) if row else None

    def list_tasks(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.conn() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def add_log(self, task_id: int, level: str, event: str, data: dict[str, Any]) -> None:
        with self.conn() as conn:
            conn.execute(
                "INSERT INTO task_logs(task_id, level, event, data_json) VALUES (?,?,?,?)",
                (task_id, level, event, json.dumps(data, ensure_ascii=False)),
            )

    def get_logs(self, task_id: int, limit: int = 200) -> list[dict[str, Any]]:
        with self.conn() as conn:
            rows = conn.execute(
                "SELECT ts, level, event, data_json FROM task_logs WHERE task_id=? ORDER BY id ASC LIMIT ?",
                (task_id, limit),
            ).fetchall()
            out = []
            for r in rows:
                out.append(
                    {
                        "ts": r["ts"],
                        "level": r["level"],
                        "event": r["event"],
                        "data": json.loads(r["data_json"]),
                    }
                )
            return out

    def get_setting(self, key: str, default: Any) -> Any:
        with self.conn() as conn:
            row = conn.execute("SELECT value_json FROM app_settings WHERE key=?", (key,)).fetchone()
            if not row:
                return default
            return json.loads(row["value_json"])

    def set_setting(self, key: str, value: Any) -> None:
        with self.conn() as conn:
            conn.execute(
                """
                INSERT INTO app_settings(key, value_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=CURRENT_TIMESTAMP
                """,
                (key, json.dumps(value)),
            )
