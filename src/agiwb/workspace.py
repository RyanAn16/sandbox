"""Workspace helpers."""
from __future__ import annotations

from pathlib import Path


def get_workspace_home() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    workspace = repo_root / "data"
    (workspace / "reports").mkdir(parents=True, exist_ok=True)
    (workspace / "ledger").mkdir(parents=True, exist_ok=True)
    return workspace
