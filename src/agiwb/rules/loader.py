"""Rule loading helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Dict, Any

import yaml


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or []


def load_rules(paths: Iterable[str | Path]) -> List[Dict[str, Any]]:
    rules: List[Dict[str, Any]] = []
    for path in paths:
        path_obj = Path(path)
        payload = _load_yaml(path_obj)
        if isinstance(payload, dict):
            payload = payload.get("rules", [])
        if not isinstance(payload, list):
            raise ValueError(f"Rules file {path_obj} must contain a list or 'rules' key")
        for index, rule in enumerate(payload, start=1):
            if not isinstance(rule, dict):
                raise ValueError(f"Rule entry must be a mapping in {path_obj}")
            rule = dict(rule)
            rule.setdefault("id", f"{path_obj.stem}-{index}")
            rules.append(rule)
    return rules
