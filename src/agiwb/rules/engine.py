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


def matched_rule_ids(rules: List[Dict[str, Any]], record: Dict[str, Any]) -> List[str]:
    return [rule["id"] for rule in rules if match_rule(rule, record)]


def evaluate_records(records: Iterable[Dict[str, Any]], rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = 0
    matched = 0
    matched_records: List[Dict[str, Any]] = []
    event_results: List[Dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        total += 1
        rule_ids = matched_rule_ids(rules, record)
        is_matched = bool(rule_ids)
        if is_matched:
            matched += 1
            matched_records.append(record)
        event_results.append(
            {
                "test_id": record.get("id", f"case-{index}"),
                "text": record.get("text", ""),
                "matched": is_matched,
                "rule_id": rule_ids[0] if rule_ids else None,
            }
        )
    return {
        "total": total,
        "matched": matched,
        "matched_records": matched_records,
        "event_results": event_results,
    }
