"""Minimal rule matching engine."""
from __future__ import annotations

from typing import Dict, Any, Iterable, List


def _match_contains(rule: Dict[str, Any], record: Dict[str, Any]) -> bool:
    needle = rule.get("contains")
    if needle is None:
        return False
    field = rule.get("field", "text")
    value = record.get(field, "")
    if not isinstance(value, str):
        value = str(value)
    return needle.lower() in value.lower()


def _match_equals(rule: Dict[str, Any], record: Dict[str, Any]) -> bool:
    if "equals" not in rule:
        return False
    field = rule.get("field", "text")
    return record.get(field) == rule.get("equals")


def match_rule(rule: Dict[str, Any], record: Dict[str, Any]) -> bool:
    return _match_contains(rule, record) or _match_equals(rule, record)


def evaluate_records(records: Iterable[Dict[str, Any]], rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = 0
    matched = 0
    matched_records: List[Dict[str, Any]] = []
    for record in records:
        total += 1
        if any(match_rule(rule, record) for rule in rules):
            matched += 1
            matched_records.append(record)
    return {
        "total": total,
        "matched": matched,
        "matched_records": matched_records,
    }
