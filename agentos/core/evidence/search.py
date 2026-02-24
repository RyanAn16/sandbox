from __future__ import annotations

import re
import sqlite3
from pathlib import Path


def search_chunks_keyword(
    db_path: Path,
    query: str,
    top_k: int = 5,
    dedup: bool = True,
) -> list[dict]:
    query_lower = query.strip().lower()
    terms = re.findall(r"[a-zA-Z0-9]+", query_lower)
    if not query_lower:
        return []

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                c.id AS chunk_id,
                s.id AS snapshot_id,
                s.url AS url,
                s.title AS title,
                c.text AS text,
                c.chunk_index AS chunk_index,
                c.text_hash AS text_hash,
                s.content_hash AS content_hash,
                s.fetched_at AS fetched_at
            FROM chunks c
            JOIN snapshots s ON s.id = c.snapshot_id
            """
        ).fetchall()

    scored: list[dict] = []
    for row in rows:
        text_lower = (row["text"] or "").lower()
        title_lower = (row["title"] or "").lower()
        haystack = f"{title_lower}\n{text_lower}"

        score = 0
        for term in terms:
            score += haystack.count(term)
        if query_lower in haystack:
            score += 5

        if score == 0:
            continue

        scored.append(
            {
                "chunk_id": row["chunk_id"],
                "snapshot_id": row["snapshot_id"],
                "url": row["url"],
                "title": row["title"],
                "text": row["text"],
                "chunk_index": row["chunk_index"],
                "text_hash": row["text_hash"],
                "content_hash": row["content_hash"],
                "fetched_at": row["fetched_at"],
                "score": score,
            }
        )

    if dedup:
        by_text_hash: dict[str, dict] = {}
        for row in scored:
            key = row.get("text_hash") or f"chunk-{row['chunk_id']}"
            existing = by_text_hash.get(key)
            if existing is None:
                by_text_hash[key] = row
                continue
            if row["score"] > existing["score"]:
                by_text_hash[key] = row
                continue
            if row["score"] == existing["score"] and row["snapshot_id"] > existing["snapshot_id"]:
                by_text_hash[key] = row
        scored = list(by_text_hash.values())

    scored.sort(key=lambda item: (-item["score"], -item["snapshot_id"], item["chunk_id"]))
    return scored[:top_k]
