"""Corpus statistics computed from the database (no fabricated numbers)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .config import load_config


def _sum_run_reports(conn: sqlite3.Connection, key: str) -> int:
    total = 0
    for row in conn.execute("SELECT report FROM ingest_runs WHERE report IS NOT NULL"):
        try:
            report = json.loads(row["report"])
        except json.JSONDecodeError:
            continue
        value = report.get(key)
        if isinstance(value, int):
            total += value
    return total


def corpus_stats(db_path: Path, config_path: Path) -> str:
    _, sources = load_config(config_path)
    topics_by_source = {s.id: s.topics for s in sources}
    names_by_source = {s.id: s.name for s in sources}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    doc_count = conn.execute("SELECT COUNT(*) c FROM documents").fetchone()["c"]
    source_ids = [
        r["source_id"]
        for r in conn.execute(
            "SELECT DISTINCT source_id FROM documents ORDER BY source_id"
        )
    ]
    snapshot_count = conn.execute("SELECT COUNT(*) c FROM snapshots").fetchone()["c"]

    pub = conn.execute(
        "SELECT MIN(published_at) lo, MAX(published_at) hi FROM documents WHERE published_at IS NOT NULL"
    ).fetchone()
    ret = conn.execute(
        "SELECT MIN(retrieved_at) lo, MAX(retrieved_at) hi FROM documents"
    ).fetchone()

    by_source = conn.execute(
        """SELECT source_id, COUNT(*) c FROM documents
           GROUP BY source_id ORDER BY c DESC"""
    ).fetchall()

    topic_counts: dict[str, int] = {}
    for row in by_source:
        for topic in topics_by_source.get(row["source_id"], []):
            topic_counts[topic] = topic_counts.get(topic, 0) + row["c"]

    duplicates = _sum_run_reports(conn, "duplicates")
    fetch_failures = _sum_run_reports(conn, "fetch_failures")
    changed = conn.execute(
        "SELECT COUNT(*) c FROM observations WHERE changed = 1"
    ).fetchone()["c"]
    errors = conn.execute("SELECT COUNT(*) c FROM ingest_errors").fetchone()["c"]

    conn.close()

    lines = [
        "Information Radar — Corpus",
        "",
        f"Documents: {doc_count}",
        f"Sources: {len(source_ids)}",
        f"Snapshots: {snapshot_count}",
        "",
        "Date range:",
        f"  Published: {pub['lo'] or 'unknown'} → {pub['hi'] or 'unknown'}",
        f"  Retrieved: {ret['lo'] or 'unknown'} → {ret['hi'] or 'unknown'}",
        "",
        "Documents by source:",
    ]
    for row in by_source:
        name = names_by_source.get(row["source_id"], row["source_id"])
        lines.append(f"  {name:35} {row['c']}")

    lines.append("")
    lines.append("Documents by topic:")
    for topic, count in sorted(topic_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {topic:35} {count}")

    lines += [
        "",
        f"Duplicates rejected: {duplicates}",
        f"Fetch failures: {fetch_failures}",
        f"Changed documents (observations): {changed}",
        f"Recorded errors: {errors}",
    ]
    return "\n".join(lines)
