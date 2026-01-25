"""CLI entrypoint for AGI Workbench."""
from __future__ import annotations

import argparse

from agiwb.pipeline import run_eval, run_pipeline
from agiwb.reflection.rule_induction import write_incremental_rules, induce_rules
from agiwb.reflection.synth import synthesize_cases
from agiwb.workspace import get_workspace_home


def eval_command(args: argparse.Namespace) -> int:
    summary = run_eval(args.eval_file, [args.rules], args.out, args.ledger)
    if args.write_incremental:
        write_incremental_rules(summary.get("matched_records", []), args.incremental_rules_out)
    print(f"Wrote summary to {summary['summary_path']}")
    return 0


def init_command(args: argparse.Namespace) -> int:
    workspace = get_workspace_home()
    print(f"Initialized workspace at {workspace}")
    return 0


def where_command(args: argparse.Namespace) -> int:
    workspace = get_workspace_home()
    print(workspace)
    return 0


def induce_command(args: argparse.Namespace) -> int:
    results = induce_rules(args.ledger, args.seed_rules, args.out)
    print(
        "Induction results: candidates={candidates}, approved={approved}, saved={saved}, out={out}".format(
            **results
        )
    )
    return 0


def synth_command(args: argparse.Namespace) -> int:
    results = synthesize_cases(args.ledger, args.out, args.n)
    print(f"Synth results: generated={results['generated']} out={results['out']}")
    return 0


def pipeline_command(args: argparse.Namespace) -> int:
    summary = run_pipeline(
        args.seed,
        args.seed_rules,
        args.out_dir,
        args.ledger,
        args.n,
        args.strict,
    )
    print(f"Wrote pipeline summary to {summary['summary_path']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agiwb")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize local workspace")
    init_parser.set_defaults(func=init_command)

    where_parser = subparsers.add_parser("where", help="Show workspace location")
    where_parser.set_defaults(func=where_command)

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

    induce_parser = subparsers.add_parser("induce", help="Induce incremental rules from ledger")
    induce_parser.add_argument("--ledger", required=True, help="SQLite ledger path")
    induce_parser.add_argument("--seed-rules", required=True, help="Seed rules YAML path")
    induce_parser.add_argument("--out", required=True, help="Output path for induced rules YAML")
    induce_parser.set_defaults(func=induce_command)

    synth_parser = subparsers.add_parser("synth", help="Generate synthetic eval cases")
    synth_parser.add_argument("--ledger", required=True, help="SQLite ledger path")
    synth_parser.add_argument("--out", required=True, help="Output path for synthetic JSONL")
    synth_parser.add_argument("--n", type=int, default=20, help="Number of synthetic cases to emit")
    synth_parser.set_defaults(func=synth_command)

    pipeline_parser = subparsers.add_parser("pipeline", help="Run full evaluation pipeline")
    pipeline_parser.add_argument("--seed", required=True, help="Seed eval JSONL path")
    pipeline_parser.add_argument("--seed-rules", required=True, help="Seed rules YAML path")
    pipeline_parser.add_argument("--out-dir", required=True, help="Output directory for pipeline")
    pipeline_parser.add_argument("--ledger", required=True, help="SQLite ledger path")
    pipeline_parser.add_argument("--n", type=int, default=20, help="Number of synthetic cases")
    pipeline_parser.add_argument(
        "--strict", action="store_true", help="Fail pipeline if synth outputs zero cases"
    )
    pipeline_parser.set_defaults(func=pipeline_command)

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
