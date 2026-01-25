"""Pipeline orchestration helpers."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict, Any

from agiwb.ledger.store import LedgerStore
from agiwb.rules.engine import evaluate_records
from agiwb.rules.loader import load_rules
from agiwb.reflection.rule_induction import induce_rules
from agiwb.reflection.synth import synthesize_cases


def _load_eval_records(path: str | Path):
    eval_path = Path(path)
    with eval_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _write_summary(out_dir: str | Path, summary: Dict[str, Any]) -> Path:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    summary_path = out_path / "summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
    return summary_path


def run_eval(
    eval_file: str | Path, rules_paths: list[str | Path], out: str | Path, ledger: str | Path
) -> Dict[str, Any]:
    rules = load_rules(rules_paths)
    records = list(_load_eval_records(eval_file))
    results = evaluate_records(records, rules)
    run_id = str(uuid.uuid4())
    summary = {
        "run_id": run_id,
        "total": results["total"],
        "matched": results["matched"],
        "eval_file": str(eval_file),
        "rules": [str(path) for path in rules_paths],
    }
    summary_path = _write_summary(out, summary)

    with LedgerStore(ledger) as store:
        store.add_run(run_id, results["total"], results["matched"])
        store.add_events(run_id, results["event_results"])

    summary["summary_path"] = str(summary_path)
    summary["matched_records"] = results.get("matched_records", [])
    return summary


def run_pipeline(
    seed_eval: str | Path,
    seed_rules: str | Path,
    out_dir: str | Path,
    ledger: str | Path,
    n: int,
    strict: bool = False,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    seed_dir = out_dir / "seed"
    round2_dir = out_dir / "round2"
    incremental_rules_path = out_dir / "incremental_rules.yaml"
    synth_path = out_dir / "synth_tests.jsonl"

    seed_summary = run_eval(seed_eval, [seed_rules], seed_dir, ledger)
    induction_stats = induce_rules(ledger, seed_rules, incremental_rules_path)
    synth_stats = synthesize_cases(ledger, synth_path, n)

    if strict and synth_stats["generated"] == 0:
        raise RuntimeError("No synthetic tests generated")

    round2_summary = run_eval(synth_path, [seed_rules, incremental_rules_path], round2_dir, ledger)

    summary = {
        "seed": seed_summary,
        "induce": induction_stats,
        "synth": synth_stats,
        "round2": round2_summary,
    }
    summary_path = _write_summary(out_dir, summary)
    summary["summary_path"] = str(summary_path)
    return summary
