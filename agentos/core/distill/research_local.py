from __future__ import annotations


def _preview(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


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
    for row in rows[:3]:
        lines.append(f"- [chunk_id={row['chunk_id']}] {_preview(row['text'])}")
    if not rows:
        lines.append("- No evidence found.")
    lines.append("")

    lines.append("## Evidence list")
    lines.append("")
    for row in rows:
        lines.append(f"- chunk_id={row['chunk_id']} | snapshot_id={row['snapshot_id']} | url={row['url']}")
        lines.append(f"  - preview: {_preview(row['text'])}")

    return "\n".join(lines) + "\n"
