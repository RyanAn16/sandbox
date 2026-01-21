"""Synthetic data generation helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

from agiwb.ledger.store import LedgerStore


def synthesize_cases(ledger_path: str | Path, output_path: str | Path, n: int) -> Dict[str, Any]:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with LedgerStore(ledger_path) as store:
        cases = store.fetch_cases(matched=False, limit=n)
        if not cases:
            cases = store.fetch_cases(limit=n)

    records: List[Dict[str, Any]] = []
    for index, case in enumerate(cases, start=1):
        text = case.get("text", "").strip()
        if not text:
            continue
        records.append({"id": f"synthetic-{index}", "text": f"Synthetic: {text}"})

    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {"generated": len(records), "out": str(output_path)}
