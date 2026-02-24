from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from core.crawler.fetch import fetch_url
from core.distill.research_local import build_research_markdown
from core.evidence.db import EvidenceDB
from core.evidence.search import search_chunks_keyword

try:
    import typer
except ModuleNotFoundError:  # pragma: no cover - local fallback when typer isn't installed
    typer = None


def _run_research_local(query: str, db: str, top_k: int, out_dir: str, dedup: bool) -> int:
    db_path = Path(db)
    out_path = Path(out_dir)

    evidence_db = EvidenceDB(db_path)
    evidence_db.init()

    rows = search_chunks_keyword(
        db_path=db_path,
        query=query,
        top_k=top_k,
        dedup=dedup,
    )
    if not rows:
        print("No evidence found for query. Try broader keywords.")
        return 4

    out_path.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = out_path / f"{stamp}__research_local.md"
    markdown = build_research_markdown(query, rows)
    output_path.write_text(markdown, encoding="utf-8")

    run_id = evidence_db.insert_run(query=query, mode="research-local", output_path=output_path)

    top_chunk_ids = [row["chunk_id"] for row in rows[:3]]
    previews = [" ".join((row.get("text") or "").split())[:80] for row in rows[:3]]

    print(f"run_id={run_id}")
    print(f"output_path={output_path}")
    print(f"dedup={dedup}")
    print(f"top_chunk_ids={top_chunk_ids}")
    for i, preview in enumerate(previews, start=1):
        print(f"preview_{i}={preview}")
    return 0


if typer is not None:
    app = typer.Typer(help="agentos CLI")

    @app.command("init")
    def cmd_init() -> None:
        print("init completed")

    @app.command("chunk-demo")
    def cmd_chunk_demo() -> None:
        print("chunk-demo completed")

    @app.command("fetch-url")
    def cmd_fetch_url(url: str, insecure: bool = typer.Option(False, "--insecure")) -> None:
        content = fetch_url(url, verify_ssl=not insecure)
        print(content)

    @app.command("research-local")
    def cmd_research_local(
        query: str,
        db: str = typer.Option("evidence.sqlite", "--db"),
        top_k: int = typer.Option(5, "--top-k"),
        out_dir: str = typer.Option("outputs", "--out-dir"),
        dedup: bool = typer.Option(
            True,
            "--dedup/--no-dedup",
            help="Deduplicate duplicate chunks by text_hash",
        ),
    ) -> None:
        code = _run_research_local(query=query, db=db, top_k=top_k, out_dir=out_dir, dedup=dedup)
        if code:
            raise typer.Exit(code=code)


    def main(argv: list[str] | None = None) -> int:
        args = sys.argv[1:] if argv is None else argv
        try:
            app(prog_name="agentos", args=args)
            return 0
        except SystemExit as exc:
            return int(exc.code) if isinstance(exc.code, int) else 1


else:

    def build_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="agentos")
        subparsers = parser.add_subparsers(dest="command", required=True)

        init_parser = subparsers.add_parser("init", help="Initialize the project")
        init_parser.set_defaults(func=lambda _args: (print("init completed"), 0)[1])

        chunk_parser = subparsers.add_parser("chunk-demo", help="Run chunking demo")
        chunk_parser.set_defaults(func=lambda _args: (print("chunk-demo completed"), 0)[1])

        fetch_parser = subparsers.add_parser("fetch-url", help="Fetch URL content")
        fetch_parser.add_argument("url", help="Target URL")
        fetch_parser.add_argument("--insecure", action="store_true", help="Disable SSL certificate verification")
        fetch_parser.set_defaults(
            func=lambda args: (print(fetch_url(args.url, verify_ssl=not args.insecure)), 0)[1]
        )

        research_parser = subparsers.add_parser(
            "research-local", help="Run local keyword research and output markdown"
        )
        research_parser.add_argument("query", help="Query text")
        research_parser.add_argument("--db", default="evidence.sqlite", help="SQLite DB path")
        research_parser.add_argument("--top-k", type=int, default=5, help="Top k rows")
        research_parser.add_argument("--out-dir", default="outputs", help="Output directory")
        research_parser.add_argument(
            "--dedup",
            dest="dedup",
            action="store_true",
            default=True,
            help="Deduplicate duplicate chunks by text_hash",
        )
        research_parser.add_argument(
            "--no-dedup",
            dest="dedup",
            action="store_false",
            help="Deduplicate duplicate chunks by text_hash",
        )
        research_parser.set_defaults(
            func=lambda args: _run_research_local(
                query=args.query,
                db=args.db,
                top_k=args.top_k,
                out_dir=args.out_dir,
                dedup=args.dedup,
            )
        )

        return parser


    def main(argv: list[str] | None = None) -> int:
        parser = build_parser()
        args = parser.parse_args(argv)
        return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
