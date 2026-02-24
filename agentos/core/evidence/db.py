from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


SEED_URL = "https://example.com"
SEED_TITLE = "Example Domain"
SEED_TEXT = (
    "Example Domain. This domain is for use in documentation examples without needing "
    "permission. Avoid use in operations."
)


@dataclass
class EvidenceDB:
    db_path: Path

    def init(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    FOREIGN KEY(snapshot_id) REFERENCES snapshots(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    output_path TEXT NOT NULL
                )
                """
            )
            self._seed_if_empty(conn)

    def insert_run(self, query: str, mode: str, output_path: Path) -> int:
        started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO runs(query, started_at, mode, output_path) VALUES (?, ?, ?, ?)",
                (query, started_at, mode, str(output_path)),
            )
            return int(cursor.lastrowid)

    def _seed_if_empty(self, conn: sqlite3.Connection) -> None:
        row = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
        if row and row[0] > 0:
            return
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cur = conn.execute(
            "INSERT INTO snapshots(url, title, created_at) VALUES (?, ?, ?)",
            (SEED_URL, SEED_TITLE, created_at),
        )
        snapshot_id = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO chunks(snapshot_id, chunk_index, text) VALUES (?, ?, ?)",
            (snapshot_id, 0, SEED_TEXT),
        )
