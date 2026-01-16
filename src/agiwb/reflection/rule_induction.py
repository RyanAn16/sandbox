"""Rule induction helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Dict, Any

import yaml


def write_incremental_rules(records: Iterable[Dict[str, Any]], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rules = []
    for index, record in enumerate(records, start=1):
        text = record.get("text")
        if not text:
            continue
        rules.append({"id": f"incremental-{index}", "contains": text[:40]})
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(rules, handle, sort_keys=False)
