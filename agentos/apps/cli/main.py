from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import typer

from core.crawler.fetch import fetch_url
from core.distill.research_local import build_research_markdown
from core.evidence.db import EvidenceDB
from core.evidence.search import search_chunks_keyword

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
        raise typer.Exit(code=4)

    out_path.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = out_path / f"{stamp}__research_local.md"
    markdown = build_research_markdown(query, rows)
    output_path.write_text(markdown, encoding="utf-8")

    run_id = evidence_db.insert_run(query=query, mode="research-local", output_path=output_path)

    top_chunk_ids = [row["chunk_id"] for row in rows[:3]]
    previews = [" ".join((row.get("text") or "").split())[:80] for row in rows[:3]]

    typer.echo(f"run_id={run_id}")
    typer.echo(f"output_path={output_path}")
    typer.echo(f"dedup={dedup}")
    typer.echo(f"top_chunk_ids={top_chunk_ids}")
    for i, preview in enumerate(previews, start=1):
        typer.echo(f"preview_{i}={preview}")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else None
    try:
        app(prog_name="agentos", args=args)
        return 0
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1


if __name__ == "__main__":
    raise SystemExit(main())
