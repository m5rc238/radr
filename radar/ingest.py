"""Ingestion pipeline: Configured sources -> fetch -> parse -> normalize
-> dedupe -> store -> observe -> snapshot.

Runs are safe to repeat: document identity is canonical-URL based, so
re-ingestion never creates duplicate documents, and content changes are
appended to document_versions instead of overwriting history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import db, normalize
from .config import Source, load_config
from .feeds import FeedParseError, parse_feed
from .fetch import FetchError, Fetcher, RobotsBlocked
from .urls import canonical_url


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class SourceReport:
    source_id: str
    status: str = "ok"
    detail: str = ""
    discovered: int = 0
    new: int = 0
    existing: int = 0
    changed: int = 0
    duplicates: int = 0
    missing_dates: int = 0
    invalid: int = 0
    failures: int = 0


@dataclass
class IngestReport:
    started_at: str = ""
    finished_at: str = ""
    run_id: int = -1
    snapshot_id: int = -1
    sources: list[SourceReport] = field(default_factory=list)
    discovered: int = 0
    new: int = 0
    existing: int = 0
    changed: int = 0
    duplicates: int = 0
    missing_dates: int = 0
    invalid: int = 0
    failures: int = 0
    identical_content_other_url: int = 0

    @property
    def attempted(self) -> int:
        return len(self.sources)

    @property
    def succeeded(self) -> int:
        return sum(1 for s in self.sources if s.status == "ok")

    @property
    def failed(self) -> int:
        return sum(1 for s in self.sources if s.status != "ok")

    def as_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "snapshot_id": self.snapshot_id,
            "sources_attempted": self.attempted,
            "sources_successful": self.succeeded,
            "sources_failed": self.failed,
            "documents_discovered": self.discovered,
            "new_documents": self.new,
            "existing_documents": self.existing,
            "changed_documents": self.changed,
            "duplicates": self.duplicates,
            "missing_publication_dates": self.missing_dates,
            "invalid_documents": self.invalid,
            "fetch_failures": self.failures,
            "identical_content_other_url": self.identical_content_other_url,
            "per_source": [vars(s) for s in self.sources],
        }


def _decode(body: bytes, content_type: str = "") -> str:
    return body.decode("utf-8", errors="replace")


def _process_entry(
    conn,
    source: Source,
    entry,
    *,
    run_id: int,
    observed_at: str,
    fetcher: Fetcher,
    report: IngestReport,
    sreport: SourceReport,
    seen_urls: set[str],
    snapshot_id: int,
) -> None:
    if not entry.link:
        sreport.invalid += 1
        report.invalid += 1
        db.log_error(conn, run_id, source.id, "entry", f"entry without link: {entry.title!r}")
        return

    canonical = canonical_url(entry.link)

    if canonical in seen_urls:
        sreport.duplicates += 1
        report.duplicates += 1
        return
    seen_urls.add(canonical)

    # Obtain content
    if source.content_from == "feed":
        raw = entry.content
    else:
        try:
            body, ctype = fetcher.fetch(entry.link)
            raw = _decode(body, ctype)
        except RobotsBlocked as exc:
            sreport.failures += 1
            report.failures += 1
            db.log_error(conn, run_id, source.id, "fetch", str(exc))
            return
        except FetchError as exc:
            sreport.failures += 1
            report.failures += 1
            db.log_error(conn, run_id, source.id, "fetch", str(exc))
            return

    normalized = normalize.normalize(raw)
    if not normalized:
        sreport.invalid += 1
        report.invalid += 1
        db.log_error(
            conn, run_id, source.id, "normalize", f"empty content for {entry.link}"
        )
        return

    c_hash = normalize.content_hash(normalized)
    doc_id = db.document_id_for(canonical)
    existing = db.get_document(conn, doc_id)
    changed_flag = False

    if existing is None:
        if entry.published_at is None:
            sreport.missing_dates += 1
            report.missing_dates += 1
        db.store_new_document(
            conn,
            doc_id=doc_id,
            source_id=source.id,
            url=entry.link,
            canonical_url=canonical,
            title=entry.title or None,
            author=entry.author,
            published_at=entry.published_at,
            observed_at=observed_at,
            raw_content=raw,
            normalized_content=normalized,
            content_hash=c_hash,
        )
        sreport.new += 1
        report.new += 1
        # Cross-URL identical content: reported, never auto-rejected.
        twin = conn.execute(
            "SELECT id FROM documents WHERE content_hash = ? AND id != ? LIMIT 1",
            (c_hash, doc_id),
        ).fetchone()
        if twin is not None:
            report.identical_content_other_url += 1
    elif existing["content_hash"] != c_hash:
        changed_flag = True
        db.record_changed_document(
            conn,
            doc_id=doc_id,
            title=entry.title or None,
            author=entry.author,
            published_at=entry.published_at,
            observed_at=observed_at,
            raw_content=raw,
            normalized_content=normalized,
            content_hash=c_hash,
        )
        sreport.changed += 1
        report.changed += 1
    else:
        db.touch_document(conn, doc_id, observed_at)
        sreport.existing += 1
        report.existing += 1

    db.record_observation(conn, run_id, doc_id, observed_at, c_hash, changed_flag)
    db.add_snapshot_document(conn, snapshot_id, doc_id)
    sreport.discovered += 1
    report.discovered += 1


def run_ingest(
    config_path: Path,
    db_path: Path,
    fetcher: Fetcher | None = None,
) -> IngestReport:
    settings, sources = load_config(config_path)
    if fetcher is None:
        fetcher = Fetcher(
            user_agent=settings.user_agent,
            delay_seconds=settings.delay_seconds,
            timeout_seconds=settings.timeout_seconds,
            robots_check=settings.robots_check,
        )

    conn = db.connect(db_path)
    report = IngestReport()
    report.started_at = now_utc()
    report.run_id = db.insert_run(conn, report.started_at)
    snapshot_id = db.create_snapshot(conn, report.run_id, now_utc())
    report.snapshot_id = snapshot_id

    enabled = [s for s in sources if s.enabled]
    # Run-wide: the same canonical URL seen from any source in this run
    # (e.g. arXiv cross-lists) is a duplicate of the first occurrence.
    seen_urls: set[str] = set()
    for source in enabled:
        sreport = SourceReport(source_id=source.id)
        report.sources.append(sreport)
        try:
            body, _ = fetcher.fetch(source.feed_url)
            entries = parse_feed(body)[: source.max_entries]
        except (FetchError, FeedParseError) as exc:
            sreport.status = "failed"
            sreport.detail = str(exc)
            db.log_error(conn, report.run_id, source.id, "feed", str(exc))
            db.add_snapshot_source(conn, snapshot_id, source.id, "failed", str(exc))
            conn.commit()
            continue

        for entry in entries:
            _process_entry(
                conn,
                source,
                entry,
                run_id=report.run_id,
                observed_at=now_utc(),
                fetcher=fetcher,
                report=report,
                sreport=sreport,
                seen_urls=seen_urls,
                snapshot_id=snapshot_id,
            )
        db.add_snapshot_source(
            conn,
            snapshot_id,
            source.id,
            "ok",
            f"discovered={sreport.discovered} new={sreport.new} "
            f"existing={sreport.existing} changed={sreport.changed} "
            f"failed={sreport.failures}",
        )
        conn.commit()

    report.finished_at = now_utc()
    status = "ok" if report.failed == 0 else ("partial" if report.succeeded else "failed")
    db.finish_run(conn, report.run_id, report.finished_at, status, report.as_dict())
    conn.commit()
    conn.close()
    return report


def format_report(report: IngestReport) -> str:
    lines = [
        "Ingestion report",
        "================",
        f"Sources attempted: {report.attempted}",
        f"Successful: {report.succeeded}",
        f"Failed: {report.failed}",
        "",
        f"Documents discovered: {report.discovered}",
        f"New documents: {report.new}",
        f"Existing documents: {report.existing}",
        f"Changed documents: {report.changed}",
        f"Duplicates: {report.duplicates}",
        f"Invalid documents: {report.invalid}",
        f"Fetch failures: {report.failures}",
        f"Missing publication dates: {report.missing_dates}",
        f"Identical content at different URL (retained): {report.identical_content_other_url}",
        "",
        f"Snapshot created: {report.snapshot_id} at {report.finished_at}",
        f"Run id: {report.run_id}",
    ]
    failed = [s for s in report.sources if s.status != "ok"]
    if failed:
        lines.append("")
        lines.append("Failed sources:")
        for s in failed:
            lines.append(f"  {s.source_id}: {s.detail}")
    return "\n".join(lines)
