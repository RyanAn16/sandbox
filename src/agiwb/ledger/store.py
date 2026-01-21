"""SQLite ledger helpers."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Optional, List, Dict, Any

from agiwb.ledger.schema import RUNS_TABLE, EVENTS_TABLE


class LedgerStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.execute(RUNS_TABLE)
        self._connection.execute(EVENTS_TABLE)
        self._connection.commit()

    def add_run(self, run_id: str, total: int, matched: int) -> None:
        self._connection.execute(
            "INSERT INTO runs (run_id, total, matched) VALUES (?, ?, ?)",
            (run_id, total, matched),
        )
        self._connection.commit()

    def add_event(self, run_id: str, test_id: str, text: str, rule_id: Optional[str], matched: bool) -> None:
        self._connection.execute(
            "INSERT INTO events (run_id, test_id, text, rule_id, matched) VALUES (?, ?, ?, ?, ?)",
            (run_id, test_id, text, rule_id, 1 if matched else 0),
        )
        self._connection.commit()

    def add_events(self, run_id: str, events: Iterable[Dict[str, Any]]) -> None:
        payload = [
            (
                run_id,
                event["test_id"],
                event.get("text", ""),
                event.get("rule_id"),
                1 if event.get("matched") else 0,
            )
            for event in events
        ]
        self._connection.executemany(
            "INSERT INTO events (run_id, test_id, text, rule_id, matched) VALUES (?, ?, ?, ?, ?)",
            payload,
        )
        self._connection.commit()

    def fetch_events(
        self, matched: Optional[bool] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        query = "SELECT run_id, test_id, text, rule_id, matched, created_at FROM events"
        params: List[Any] = []
        if matched is not None:
            query += " WHERE matched = ?"
            params.append(1 if matched else 0)
        query += " ORDER BY id DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        cursor = self._connection.execute(query, params)
        rows = cursor.fetchall()
        results = []
        for run_id, test_id, text, rule_id, matched_value, created_at in rows:
            results.append(
                {
                    "run_id": run_id,
                    "test_id": test_id,
                    "text": text,
                    "rule_id": rule_id,
                    "matched": bool(matched_value),
                    "created_at": created_at,
                }
            )
        return results

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "LedgerStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
