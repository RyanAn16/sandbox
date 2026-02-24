from __future__ import annotations


def _preview(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _short_hash(value: str | None) -> str:
    if not value:
        return "n/a"
    return value[:12]


def build_research_markdown(query: str, rows: list[dict]) -> str:
    lines: list[str] = []
    lines.append("# Research Local")
    lines.append("")
    lines.append("## Query")
    lines.append("")
    lines.append(f"- {query}")
    lines.append("")

    lines.append("## Draft answer")
    lines.append("")
    seen_excerpt: set[str] = set()
    for row in rows[:3]:
        excerpt = _preview(row["text"])
        if excerpt in seen_excerpt:
            continue
        seen_excerpt.add(excerpt)
        lines.append(f"- [chunk_id={row['chunk_id']}] {excerpt}")
    if not rows:
        lines.append("- No evidence found.")
    lines.append("")

    lines.append("## Evidence list")
    lines.append("")
    for row in rows:
        lines.append(
            f"- chunk_id={row['chunk_id']} | snapshot_id={row['snapshot_id']} | "
            f"text_hash={_short_hash(row.get('text_hash'))} | url={row['url']}"
        )
        lines.append(f"  - preview: {_preview(row['text'])}")

    return "\n".join(lines) + "\n"
