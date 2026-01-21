"""Rule induction helpers."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable, Dict, Any
import re

import yaml

from agiwb.ledger.store import LedgerStore
from agiwb.rules.loader import load_rules

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")


def _tokenize(text: str) -> Iterable[str]:
    return (match.group(0).lower() for match in _TOKEN_RE.finditer(text))


def write_incremental_rules(records: Iterable[Dict[str, Any]], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rules = []
    for index, record in enumerate(records, start=1):
        text = record.get("text")
        if not text:
            continue
        rules.append({"id": f"incremental-{index}", "contains": text[:40], "field": "text"})
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(rules, handle, sort_keys=False)


def induce_rules(ledger_path: str | Path, seed_rules: str | Path, output_path: str | Path) -> Dict[str, Any]:
    seed_rule_entries = load_rules([seed_rules])
    seed_terms = {rule.get("contains", "").lower() for rule in seed_rule_entries}

    with LedgerStore(ledger_path) as store:
        unmatched_cases = store.fetch_cases(matched=False)

    token_counts = Counter()
    for case in unmatched_cases:
        for token in _tokenize(case.get("text", "")):
            if token in seed_terms:
                continue
            token_counts[token] += 1

    candidates = [token for token, _count in token_counts.most_common()]
    approved = candidates[:10]

    rules = [
        {"id": f"induced-{token}", "contains": token, "field": "text"} for token in approved
    ]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(rules, handle, sort_keys=False)

    return {
        "candidates": len(candidates),
        "approved": len(approved),
        "saved": len(rules),
        "out": str(output_path),
    }
