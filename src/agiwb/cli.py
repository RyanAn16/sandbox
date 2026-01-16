"""CLI entrypoint for AGI Workbench."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Dict, Any
import uuid

from agiwb.rules.loader import load_rules
from agiwb.rules.engine import evaluate_records
from agiwb.ledger.store import LedgerStore
from agiwb.reflection.rule_induction import write_incremental_rules


def _load_eval_records(path: str | Path) -> Iterable[Dict[str, Any]]:
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


def eval_command(args: argparse.Namespace) -> int:
    rules = load_rules([args.rules])
    records = list(_load_eval_records(args.eval_file))
    results = evaluate_records(records, rules)
    run_id = str(uuid.uuid4())
    summary = {
        "run_id": run_id,
        "total": results["total"],
        "matched": results["matched"],
        "eval_file": str(args.eval_file),
        "rules": str(args.rules),
    }
    summary_path = _write_summary(args.out, summary)

    with LedgerStore(args.ledger) as store:
        store.add_run(run_id, results["total"], results["matched"])

    if args.write_incremental:
        write_incremental_rules(results["matched_records"], args.incremental_rules_out)

    print(f"Wrote summary to {summary_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agiwb")
    subparsers = parser.add_subparsers(dest="command")

    eval_parser = subparsers.add_parser("eval", help="Run evaluation on an eval set")
    eval_parser.add_argument("--eval-file", required=True, help="Path to eval JSONL file")
    eval_parser.add_argument("--rules", required=True, help="Path to rules YAML file")
    eval_parser.add_argument("--out", required=True, help="Output directory for reports")
    eval_parser.add_argument("--ledger", required=True, help="SQLite ledger path")
    eval_parser.add_argument(
        "--incremental-rules-out",
        default="rulesets/incremental_rules.yaml",
        help="Where to write incremental rules (default: rulesets/incremental_rules.yaml)",
    )
    eval_parser.add_argument(
        "--write-incremental",
        action="store_true",
        help="Write incremental rules based on matched records",
    )
    eval_parser.set_defaults(func=eval_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
