from __future__ import annotations

import hashlib
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
                    content_hash TEXT,
                    fetched_at TEXT,
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
                    text_hash TEXT,
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
            self._migrate_legacy_schema(conn)
            self._seed_if_empty(conn)

    def insert_run(self, query: str, mode: str, output_path: Path) -> int:
        started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO runs(query, started_at, mode, output_path) VALUES (?, ?, ?, ?)",
                (query, started_at, mode, str(output_path)),
            )
            return int(cursor.lastrowid)

    def _migrate_legacy_schema(self, conn: sqlite3.Connection) -> None:
        snapshot_cols = {row[1] for row in conn.execute("PRAGMA table_info(snapshots)").fetchall()}
        chunk_cols = {row[1] for row in conn.execute("PRAGMA table_info(chunks)").fetchall()}

        if "content_hash" not in snapshot_cols:
            conn.execute("ALTER TABLE snapshots ADD COLUMN content_hash TEXT")
        if "fetched_at" not in snapshot_cols:
            conn.execute("ALTER TABLE snapshots ADD COLUMN fetched_at TEXT")
        if "text_hash" not in chunk_cols:
            conn.execute("ALTER TABLE chunks ADD COLUMN text_hash TEXT")

        missing_chunk_hashes = conn.execute(
            "SELECT id, text FROM chunks WHERE text_hash IS NULL"
        ).fetchall()
        for chunk_id, text in missing_chunk_hashes:
            conn.execute(
                "UPDATE chunks SET text_hash = ? WHERE id = ?",
                (self._hash(text or ""), chunk_id),
            )

        missing_snapshot_hashes = conn.execute(
            "SELECT id, url, title FROM snapshots WHERE content_hash IS NULL"
        ).fetchall()
        for snapshot_id, url, title in missing_snapshot_hashes:
            conn.execute(
                "UPDATE snapshots SET content_hash = ? WHERE id = ?",
                (self._hash(f"{url or ''}\n{title or ''}"), snapshot_id),
            )

        missing_fetched = conn.execute(
            "SELECT id, created_at FROM snapshots WHERE fetched_at IS NULL"
        ).fetchall()
        for snapshot_id, created_at in missing_fetched:
            conn.execute(
                "UPDATE snapshots SET fetched_at = ? WHERE id = ?",
                (created_at, snapshot_id),
            )

    def _seed_if_empty(self, conn: sqlite3.Connection) -> None:
        row = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
        if row and row[0] > 0:
            return

        now = datetime.now(timezone.utc)
        text_hash = self._hash(SEED_TEXT)
        content_hash = self._hash(SEED_URL + "\n" + SEED_TITLE + "\n" + SEED_TEXT)

        first_ts = (now.replace(microsecond=0)).strftime("%Y-%m-%dT%H:%M:%SZ")
        second_ts = (now.replace(microsecond=0)).strftime("%Y-%m-%dT%H:%M:%SZ")

        cur1 = conn.execute(
            "INSERT INTO snapshots(url, title, content_hash, fetched_at, created_at) VALUES (?, ?, ?, ?, ?)",
            (SEED_URL, SEED_TITLE, content_hash, first_ts, first_ts),
        )
        snapshot_id_1 = int(cur1.lastrowid)
        conn.execute(
            "INSERT INTO chunks(snapshot_id, chunk_index, text, text_hash) VALUES (?, ?, ?, ?)",
            (snapshot_id_1, 0, SEED_TEXT, text_hash),
        )

        cur2 = conn.execute(
            "INSERT INTO snapshots(url, title, content_hash, fetched_at, created_at) VALUES (?, ?, ?, ?, ?)",
            (SEED_URL, SEED_TITLE, content_hash, second_ts, second_ts),
        )
        snapshot_id_2 = int(cur2.lastrowid)
        conn.execute(
            "INSERT INTO chunks(snapshot_id, chunk_index, text, text_hash) VALUES (?, ?, ?, ?)",
            (snapshot_id_2, 0, SEED_TEXT, text_hash),
        )

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
