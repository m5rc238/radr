"""CLI inspection of individual documents and snapshots."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import load_config

EXCERPT_CHARS = 600


def _resolve_doc(conn: sqlite3.Connection, doc_ref: str) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_ref,)).fetchone()
    if row is not None:
        return row
    matches = conn.execute(
        "SELECT * FROM documents WHERE id LIKE ?", (doc_ref + "%",)
    ).fetchall()
    if len(matches) == 1:
        return matches[0]
    return None


def inspect_document(db_path: Path, config_path: Path, doc_ref: str) -> str:
    _, sources = load_config(config_path)
    topics_by_source = {s.id: s.topics for s in sources}
    names_by_source = {s.id: s.name for s in sources}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    row = _resolve_doc(conn, doc_ref)
    if row is None:
        matches = conn.execute(
            "SELECT id, title FROM documents WHERE id LIKE ?", (doc_ref + "%",)
        ).fetchall()
        if not matches:
            conn.close()
            return f"No document matches '{doc_ref}'."
        lines = [f"Ambiguous document id '{doc_ref}'. Candidates:"]
        for m in matches:
            lines.append(f"  {m['id']}  {m['title']}")
        conn.close()
        return "\n".join(lines)

    versions = conn.execute(
        "SELECT content_hash, observed_at, is_initial FROM document_versions "
        "WHERE document_id = ? ORDER BY id",
        (row["id"],),
    ).fetchall()
    observations = conn.execute(
        "SELECT COUNT(*) c, SUM(changed) changed FROM observations WHERE document_id = ?",
        (row["id"],),
    ).fetchone()
    snapshots = [
        r["snapshot_id"]
        for r in conn.execute(
            "SELECT snapshot_id FROM snapshot_documents WHERE document_id = ? "
            "ORDER BY snapshot_id",
            (row["id"],),
        )
    ]
    conn.close()

    topics = topics_by_source.get(row["source_id"], [])
    excerpt = row["normalized_content"][:EXCERPT_CHARS]
    if len(row["normalized_content"]) > EXCERPT_CHARS:
        excerpt += " …"

    lines = [
        f"Document {row['id']}",
        "=" * (len(row["id"]) + 9),
        f"Title:            {row['title'] or '(none)'}",
        f"Source:           {names_by_source.get(row['source_id'], row['source_id'])} ({row['source_id']})",
        f"Topics:           {', '.join(topics) or '(none)'}",
        f"URL:              {row['url']}",
        f"Canonical URL:    {row['canonical_url']}",
        f"Author:           {row['author'] or '(unknown)'}",
        f"Published:        {row['published_at'] or '(unknown)'}",
        f"Retrieved (first): {row['retrieved_at']}",
        f"Retrieved (last): {row['last_retrieved_at']}",
        f"Content hash:     {row['content_hash']}",
        f"Content length:   {len(row['normalized_content'])} chars (normalized)",
        f"Observations:     {observations['c']} ({observations['changed'] or 0} changed)",
        f"Versions:         {len(versions)}",
        f"Snapshots:        {', '.join(str(s) for s in snapshots) or '(none)'}",
        "",
        "Version history:",
    ]
    for v in versions:
        label = "initial" if v["is_initial"] else "changed"
        lines.append(f"  {v['observed_at']}  {label:7}  {v['content_hash'][:16]}")
    lines += ["", "Content excerpt:", "-" * 40, excerpt]
    return "\n".join(lines)


def inspect_snapshot(db_path: Path, snapshot_ref: str) -> str:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        snap_id = int(snapshot_ref)
    except ValueError:
        conn.close()
        return f"Snapshot id must be a number, got '{snapshot_ref}'."

    snap = conn.execute("SELECT * FROM snapshots WHERE id = ?", (snap_id,)).fetchone()
    if snap is None:
        conn.close()
        return f"No snapshot with id {snap_id}."

    src_rows = conn.execute(
        "SELECT * FROM snapshot_sources WHERE snapshot_id = ? ORDER BY source_id",
        (snap_id,),
    ).fetchall()
    doc_rows = conn.execute(
        "SELECT d.id, d.source_id, d.title, d.published_at FROM snapshot_documents sd "
        "JOIN documents d ON d.id = sd.document_id WHERE sd.snapshot_id = ? "
        "ORDER BY d.source_id, d.id",
        (snap_id,),
    ).fetchall()
    conn.close()

    dist: dict[str, int] = {}
    for r in doc_rows:
        dist[r["source_id"]] = dist.get(r["source_id"], 0) + 1

    lines = [
        f"Snapshot {snap_id}",
        "=" * (len(str(snap_id)) + 9),
        f"Created:   {snap['created_at']}",
        f"Run id:    {snap['run_id']}",
        f"Documents: {len(doc_rows)}",
        "",
        "Sources:",
    ]
    for s in src_rows:
        detail = f"  ({s['detail']})" if s["detail"] else ""
        lines.append(f"  {s['source_id']:25} {s['status']}{detail}")

    lines.append("")
    lines.append("Source distribution:")
    for sid, count in sorted(dist.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {sid:25} {count}")

    lines.append("")
    lines.append(f"Document IDs ({len(doc_rows)}):")
    for r in doc_rows:
        title = (r["title"] or "")[:70]
        lines.append(f"  {r['id']}  {title}")
    return "\n".join(lines)
