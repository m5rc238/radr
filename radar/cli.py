"""Command-line interface.

Commands:
  python -m radar ingest                 run one ingestion cycle (creates a snapshot)
  python -m radar stats                  corpus statistics
  python -m radar inspect <doc-id>       inspect one document (id or unique prefix)
  python -m radar snapshot <snapshot-id> inspect one snapshot
  python -m radar snapshots              list snapshots
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from .config import DEFAULT_CONFIG, DEFAULT_DB, ConfigError, load_config
from .inspectors import inspect_document, inspect_snapshot
from .ingest import format_report, run_ingest
from .stats import corpus_stats


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"source registry (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"corpus database (default: {DEFAULT_DB})",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="radar", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="run one ingestion cycle")
    _add_common(p_ingest)

    p_stats = sub.add_parser("stats", help="corpus statistics")
    _add_common(p_stats)

    p_inspect = sub.add_parser("inspect", help="inspect a document")
    _add_common(p_inspect)
    p_inspect.add_argument("document_id", help="document id or unique prefix")

    p_snap = sub.add_parser("snapshot", help="inspect a snapshot")
    _add_common(p_snap)
    p_snap.add_argument("snapshot_id", help="snapshot id")

    p_snaps = sub.add_parser("snapshots", help="list snapshots")
    _add_common(p_snaps)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.command == "ingest":
            report = run_ingest(args.config, args.db)
            print(format_report(report))
            return 0 if report.failed == 0 else 1

        if args.command == "stats":
            print(corpus_stats(args.db, args.config))
            return 0

        if args.command == "inspect":
            print(inspect_document(args.db, args.config, args.document_id))
            return 0

        if args.command == "snapshot":
            print(inspect_snapshot(args.db, args.snapshot_id))
            return 0

        if args.command == "snapshots":
            conn = sqlite3.connect(args.db)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT sn.id, sn.created_at, r.status, "
                "(SELECT COUNT(*) FROM snapshot_documents WHERE snapshot_id = sn.id) docs, "
                "(SELECT COUNT(*) FROM snapshot_sources WHERE snapshot_id = sn.id AND status = 'ok') ok, "
                "(SELECT COUNT(*) FROM snapshot_sources WHERE snapshot_id = sn.id AND status != 'ok') failed "
                "FROM snapshots sn JOIN ingest_runs r ON r.id = sn.run_id ORDER BY sn.id"
            ).fetchall()
            conn.close()
            if not rows:
                print("No snapshots yet. Run: python -m radar ingest")
                return 0
            print(f"{'ID':>4}  {'Created':24}  {'Status':8}  {'Docs':>5}  Sources")
            for r in rows:
                print(
                    f"{r['id']:>4}  {r['created_at']:24}  {r['status']:8}  "
                    f"{r['docs']:>5}  {r['ok']} ok / {r['failed']} failed"
                )
            return 0
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    except sqlite3.Error as exc:
        print(f"database error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
