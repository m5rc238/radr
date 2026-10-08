"""SQLite storage for the controlled corpus.

One database file. Inspectable with any SQLite client. Reset by deleting
the file (data/radar.db by default) and re-running ingestion.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS ingest_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    report TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    url TEXT NOT NULL,
    canonical_url TEXT NOT NULL UNIQUE,
    title TEXT,
    author TEXT,
    published_at TEXT,
    retrieved_at TEXT NOT NULL,
    last_retrieved_at TEXT NOT NULL,
    raw_content TEXT NOT NULL,
    normalized_content TEXT NOT NULL,
    content_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id),
    content_hash TEXT NOT NULL,
    raw_content TEXT NOT NULL,
    normalized_content TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    is_initial INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_versions_doc ON document_versions(document_id);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES ingest_runs(id),
    document_id TEXT NOT NULL REFERENCES documents(id),
    observed_at TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    changed INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_observations_doc ON observations(document_id);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    run_id INTEGER NOT NULL REFERENCES ingest_runs(id)
);

CREATE TABLE IF NOT EXISTS snapshot_documents (
    snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),
    document_id TEXT NOT NULL REFERENCES documents(id),
    PRIMARY KEY (snapshot_id, document_id)
);

CREATE TABLE IF NOT EXISTS snapshot_sources (
    snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),
    source_id TEXT NOT NULL,
    status TEXT NOT NULL,
    detail TEXT,
    PRIMARY KEY (snapshot_id, source_id)
);

CREATE TABLE IF NOT EXISTS ingest_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES ingest_runs(id),
    source_id TEXT,
    stage TEXT NOT NULL,
    message TEXT NOT NULL
);
"""

USER_VERSION = 1


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.execute(f"PRAGMA user_version = {USER_VERSION}")
    return conn


def document_id_for(canonical: str) -> str:
    import hashlib

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def insert_run(conn: sqlite3.Connection, started_at: str) -> int:
    cur = conn.execute(
        "INSERT INTO ingest_runs (started_at, status) VALUES (?, 'running')",
        (started_at,),
    )
    return int(cur.lastrowid)


def finish_run(
    conn: sqlite3.Connection, run_id: int, finished_at: str, status: str, report: dict
) -> None:
    conn.execute(
        "UPDATE ingest_runs SET finished_at = ?, status = ?, report = ? WHERE id = ?",
        (finished_at, status, json.dumps(report, indent=2), run_id),
    )


def log_error(
    conn: sqlite3.Connection, run_id: int, source_id: str | None, stage: str, message: str
) -> None:
    conn.execute(
        "INSERT INTO ingest_errors (run_id, source_id, stage, message) VALUES (?, ?, ?, ?)",
        (run_id, source_id, stage, message),
    )


def get_document(conn: sqlite3.Connection, doc_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()


def find_document_by_url(conn: sqlite3.Connection, canonical_url: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM documents WHERE canonical_url = ?", (canonical_url,)
    ).fetchone()


def store_new_document(
    conn: sqlite3.Connection,
    *,
    doc_id: str,
    source_id: str,
    url: str,
    canonical_url: str,
    title: str | None,
    author: str | None,
    published_at: str | None,
    observed_at: str,
    raw_content: str,
    normalized_content: str,
    content_hash: str,
) -> None:
    conn.execute(
        """INSERT INTO documents
           (id, source_id, url, canonical_url, title, author, published_at,
            retrieved_at, last_retrieved_at, raw_content, normalized_content, content_hash)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            doc_id,
            source_id,
            url,
            canonical_url,
            title,
            author,
            published_at,
            observed_at,
            observed_at,
            raw_content,
            normalized_content,
            content_hash,
        ),
    )
    conn.execute(
        """INSERT INTO document_versions
           (document_id, content_hash, raw_content, normalized_content, observed_at, is_initial)
           VALUES (?, ?, ?, ?, ?, 1)""",
        (doc_id, content_hash, raw_content, normalized_content, observed_at),
    )


def record_changed_document(
    conn: sqlite3.Connection,
    *,
    doc_id: str,
    title: str | None,
    author: str | None,
    published_at: str | None,
    observed_at: str,
    raw_content: str,
    normalized_content: str,
    content_hash: str,
) -> None:
    """Update the document's current content and append a historical version.

    History is append-only: document_versions always keeps what was
    observed before, so change history can be reconstructed.
    """
    conn.execute(
        """UPDATE documents
           SET title = ?, author = ?, published_at = ?,
               last_retrieved_at = ?, raw_content = ?,
               normalized_content = ?, content_hash = ?
           WHERE id = ?""",
        (
            title,
            author,
            published_at,
            observed_at,
            raw_content,
            normalized_content,
            content_hash,
            doc_id,
        ),
    )
    conn.execute(
        """INSERT INTO document_versions
           (document_id, content_hash, raw_content, normalized_content, observed_at, is_initial)
           VALUES (?, ?, ?, ?, ?, 0)""",
        (doc_id, content_hash, raw_content, normalized_content, observed_at),
    )


def touch_document(conn: sqlite3.Connection, doc_id: str, observed_at: str) -> None:
    conn.execute(
        "UPDATE documents SET last_retrieved_at = ? WHERE id = ?",
        (observed_at, doc_id),
    )


def record_observation(
    conn: sqlite3.Connection,
    run_id: int,
    doc_id: str,
    observed_at: str,
    content_hash: str,
    changed: bool,
) -> None:
    conn.execute(
        """INSERT INTO observations (run_id, document_id, observed_at, content_hash, changed)
           VALUES (?, ?, ?, ?, ?)""",
        (run_id, doc_id, observed_at, content_hash, 1 if changed else 0),
    )


def create_snapshot(conn: sqlite3.Connection, run_id: int, created_at: str) -> int:
    cur = conn.execute(
        "INSERT INTO snapshots (created_at, run_id) VALUES (?, ?)",
        (created_at, run_id),
    )
    return int(cur.lastrowid)


def add_snapshot_document(conn: sqlite3.Connection, snapshot_id: int, doc_id: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO snapshot_documents (snapshot_id, document_id) VALUES (?, ?)",
        (snapshot_id, doc_id),
    )


def add_snapshot_source(
    conn: sqlite3.Connection, snapshot_id: int, source_id: str, status: str, detail: str = ""
) -> None:
    conn.execute(
        "INSERT INTO snapshot_sources (snapshot_id, source_id, status, detail) VALUES (?, ?, ?, ?)",
        (snapshot_id, source_id, status, detail),
    )
