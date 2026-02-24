from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from core.crawler.fetch import fetch_url
from core.distill.research_local import build_research_markdown
from core.evidence.db import EvidenceDB
from core.evidence.search import search_chunks_keyword


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentos")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize the project")
    init_parser.set_defaults(func=cmd_init)

    chunk_demo_parser = subparsers.add_parser("chunk-demo", help="Run chunking demo")
    chunk_demo_parser.set_defaults(func=cmd_chunk_demo)

    fetch_url_parser = subparsers.add_parser("fetch-url", help="Fetch URL content")
    fetch_url_parser.add_argument("url", help="Target URL")
    fetch_url_parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable SSL certificate verification",
    )
    fetch_url_parser.set_defaults(func=cmd_fetch_url)

    research_local_parser = subparsers.add_parser(
        "research-local", help="Run local keyword research and output markdown"
    )
    research_local_parser.add_argument("query", help="Query text")
    research_local_parser.add_argument("--db", default="evidence.sqlite", help="SQLite DB path")
    research_local_parser.add_argument("--top-k", type=int, default=5, help="Top k rows")
    research_local_parser.add_argument("--out-dir", default="outputs", help="Output directory")
    research_local_parser.add_argument(
        "--dedup",
        dest="dedup",
        action="store_true",
        default=True,
        help="Deduplicate duplicate chunks by text_hash",
    )
    research_local_parser.add_argument(
        "--no-dedup",
        dest="dedup",
        action="store_false",
        help="Deduplicate duplicate chunks by text_hash",
    )
    research_local_parser.set_defaults(func=cmd_research_local)

    return parser


def cmd_init(_args: argparse.Namespace) -> int:
    print("init completed")
    return 0


def cmd_chunk_demo(_args: argparse.Namespace) -> int:
    print("chunk-demo completed")
    return 0


def cmd_fetch_url(args: argparse.Namespace) -> int:
    content = fetch_url(args.url, verify_ssl=not args.insecure)
    print(content)
    return 0


def cmd_research_local(args: argparse.Namespace) -> int:
    db_path = Path(args.db)
    out_dir = Path(args.out_dir)

    db = EvidenceDB(db_path)
    db.init()

    rows = search_chunks_keyword(
        db_path=db_path,
        query=args.query,
        top_k=args.top_k,
        dedup=args.dedup,
    )
    if not rows:
        print("No evidence found for query. Try broader keywords.")
        return 4

    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = out_dir / f"{stamp}__research_local.md"
    markdown = build_research_markdown(args.query, rows)
    output_path.write_text(markdown, encoding="utf-8")

    run_id = db.insert_run(query=args.query, mode="research-local", output_path=output_path)

    top_chunk_ids = [row["chunk_id"] for row in rows[:3]]
    previews = [" ".join(row["text"].split())[:80] for row in rows[:3]]
    print(f"run_id={run_id}")
    print(f"output_path={output_path}")
    print(f"dedup={args.dedup}")
    print(f"top_chunk_ids={top_chunk_ids}")
    for i, preview in enumerate(previews, start=1):
        print(f"preview_{i}={preview}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
