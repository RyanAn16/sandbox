"""SQLite ledger helpers."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable, Optional, List, Dict, Any

from agiwb.ledger.schema import RUNS_TABLE, CASES_TABLE


class LedgerStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.execute(RUNS_TABLE)
        self._connection.execute(CASES_TABLE)
        self._connection.commit()

    def add_run(self, run_id: str, total: int, matched: int) -> None:
        self._connection.execute(
            "INSERT INTO runs (run_id, total, matched) VALUES (?, ?, ?)",
            (run_id, total, matched),
        )
        self._connection.commit()

    def add_cases(self, run_id: str, cases: Iterable[Dict[str, Any]]) -> None:
        payload = [
            (
                run_id,
                case["case_id"],
                case.get("text", ""),
                1 if case.get("matched") else 0,
                json.dumps(case.get("matched_rule_ids", [])),
            )
            for case in cases
        ]
        self._connection.executemany(
            "INSERT INTO cases (run_id, case_id, text, matched, matched_rule_ids) VALUES (?, ?, ?, ?, ?)",
            payload,
        )
        self._connection.commit()

    def fetch_cases(self, matched: Optional[bool] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        query = "SELECT run_id, case_id, text, matched, matched_rule_ids, created_at FROM cases"
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
        for run_id, case_id, text, matched_value, matched_rule_ids, created_at in rows:
            results.append(
                {
                    "run_id": run_id,
                    "case_id": case_id,
                    "text": text,
                    "matched": bool(matched_value),
                    "matched_rule_ids": json.loads(matched_rule_ids),
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
