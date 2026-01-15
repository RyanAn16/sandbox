import argparse
import json
import sys

from app.core.eval import run_eval
from app.core.pipeline import run_pipeline
from app.core.reflect import run_reflect


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="app.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    eval_parser = subparsers.add_parser("eval", help="Run evaluation")
    eval_parser.add_argument("--evalset", required=True)
    eval_parser.add_argument("--rules", required=True)
    eval_parser.add_argument("--out", required=True)
    eval_parser.add_argument("--ledger", required=True)

    reflect_parser = subparsers.add_parser("reflect", help="Run reflection")
    reflect_parser.add_argument("--reports", required=True)
    reflect_parser.add_argument("--out_tests", required=True)
    reflect_parser.add_argument("--n", type=int, required=True)

    pipeline_parser = subparsers.add_parser("pipeline", help="Run eval + reflect + eval")
    pipeline_parser.add_argument("--seed_evalset")
    pipeline_parser.add_argument("--seed_rules")
    pipeline_parser.add_argument("--seed_out")
    pipeline_parser.add_argument("--seed_ledger")
    pipeline_parser.add_argument("--reflect_reports")
    pipeline_parser.add_argument("--reflect_out_tests")
    pipeline_parser.add_argument("--reflect_n", type=int)
    pipeline_parser.add_argument("--round2_evalset")
    pipeline_parser.add_argument("--round2_rules")
    pipeline_parser.add_argument("--round2_out")
    pipeline_parser.add_argument("--round2_ledger")
    pipeline_parser.add_argument("--outdir")
    pipeline_parser.add_argument("--strict", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "eval":
        summary = run_eval(
            evalset=args.evalset,
            rules=args.rules,
            out_dir=args.out,
            ledger=args.ledger,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if args.command == "reflect":
        summary = run_reflect(
            reports=args.reports,
            out_tests=args.out_tests,
            n=args.n,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if args.command == "pipeline":
        try:
            summary = run_pipeline(
                seed_evalset=args.seed_evalset,
                seed_rules=args.seed_rules,
                seed_out=args.seed_out,
                seed_ledger=args.seed_ledger,
                reflect_reports=args.reflect_reports,
                reflect_out_tests=args.reflect_out_tests,
                reflect_n=args.reflect_n,
                round2_evalset=args.round2_evalset,
                round2_rules=args.round2_rules,
                round2_out=args.round2_out,
                round2_ledger=args.round2_ledger,
                outdir=args.outdir,
                strict=args.strict,
            )
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
