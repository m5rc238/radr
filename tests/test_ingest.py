"""Corpus-integrity tests: ingestion, dedupe, snapshots, change history,
failure isolation. All run against a fake fetcher — no network."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from radar import db
from radar.ingest import run_ingest
from radar.stats import corpus_stats

from helpers import (
    ALPHA_FEED_V1,
    ALPHA_FEED_V2,
    BETA_FEED,
    BETA_PAGE,
    FakeFetcher,
    base_mapping,
    rss_feed,
    write_config,
)


class IngestTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.config = write_config(self.tmp)
        self.db_path = self.tmp / "corpus.db"

    def ingest(self, mapping, **kwargs):
        return run_ingest(self.config, self.db_path, fetcher=FakeFetcher(mapping), **kwargs)

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def count(self, table: str) -> int:
        conn = self.connect()
        n = conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]
        conn.close()
        return n


class FreshIngestTests(IngestTestBase):
    def test_fresh_ingest_stores_documents_with_provenance(self):
        report = self.ingest(base_mapping())

        self.assertEqual(report.new, 4)  # 3 alpha + 1 beta
        self.assertEqual(report.failed, 0)
        self.assertEqual(report.existing, 0)
        self.assertEqual(report.changed, 0)
        self.assertEqual(self.count("documents"), 4)
        self.assertEqual(self.count("snapshots"), 1)
        self.assertEqual(self.count("document_versions"), 4)

        conn = self.connect()
        doc = conn.execute(
            "SELECT * FROM documents WHERE canonical_url = ?",
            ("https://alpha.example.org/papers/one",),
        ).fetchone()
        conn.close()

        self.assertEqual(doc["source_id"], "src-alpha")
        self.assertEqual(doc["url"], "https://alpha.example.org/papers/one")
        self.assertTrue(doc["published_at"].startswith("2026-10-05"))
        self.assertEqual(doc["author"], "A. Author")
        self.assertIn("Alpha one abstract", doc["normalized_content"])
        self.assertEqual(len(doc["content_hash"]), 64)
        # Normalized content is stored, not just raw HTML.
        self.assertNotIn("<p>", doc["normalized_content"])

    def test_utm_url_normalizes_to_canonical_document(self):
        self.ingest(base_mapping())
        conn = self.connect()
        doc = conn.execute(
            "SELECT * FROM documents WHERE canonical_url = ?",
            ("https://alpha.example.org/papers/two",),
        ).fetchone()
        conn.close()
        self.assertIsNotNone(doc)
        # Original URL as discovered is preserved.
        self.assertIn("utm_source", doc["url"])

    def test_snapshot_records_documents_and_sources(self):
        self.ingest(base_mapping())
        conn = self.connect()
        snap_docs = conn.execute("SELECT COUNT(*) c FROM snapshot_documents").fetchone()["c"]
        snap_sources = conn.execute("SELECT * FROM snapshot_sources ORDER BY source_id").fetchall()
        conn.close()
        self.assertEqual(snap_docs, 4)
        self.assertEqual([s["source_id"] for s in snap_sources], ["src-alpha", "src-beta"])
        self.assertTrue(all(s["status"] == "ok" for s in snap_sources))

    def test_missing_publication_date_is_counted(self):
        feed = rss_feed(
            [
                {
                    "link": "https://alpha.example.org/papers/undated",
                    "title": "Undated",
                    "content": "<p>Content without a date.</p>",
                }
            ]
        )
        report = self.ingest(
            {"https://alpha.example.org/feed.xml": feed, "https://beta.example.org/feed.xml": BETA_FEED, "https://beta.example.org/posts/b1": BETA_PAGE}
        )
        self.assertEqual(report.missing_dates, 1)
        conn = self.connect()
        doc = conn.execute("SELECT published_at FROM documents").fetchone()
        conn.close()
        self.assertIsNone(doc["published_at"])


class RepeatIngestTests(IngestTestBase):
    def test_repeat_ingest_creates_no_duplicate_documents(self):
        first = self.ingest(base_mapping())
        second = self.ingest(base_mapping())

        self.assertEqual(first.new, 4)
        self.assertEqual(second.new, 0)
        self.assertEqual(second.existing, 4)
        self.assertEqual(second.changed, 0)
        self.assertEqual(self.count("documents"), 4)

        # A second snapshot exists and references the same documents.
        self.assertEqual(self.count("snapshots"), 2)
        conn = self.connect()
        snap2_docs = conn.execute(
            "SELECT COUNT(*) c FROM snapshot_documents WHERE snapshot_id = 2"
        ).fetchone()["c"]
        conn.close()
        self.assertEqual(snap2_docs, 4)

        # Document appears in both snapshots via one stored row.
        self.assertEqual(self.count("snapshot_documents"), 8)
        self.assertEqual(self.count("documents"), 4)

    def test_observations_accumulate_across_runs(self):
        self.ingest(base_mapping())
        self.ingest(base_mapping())
        conn = self.connect()
        row = conn.execute(
            "SELECT COUNT(*) c FROM observations WHERE document_id = ?",
            (db.document_id_for("https://alpha.example.org/papers/one"),),
        ).fetchone()
        conn.close()
        self.assertEqual(row["c"], 2)

    def test_duplicate_link_within_single_feed_is_counted(self):
        feed = rss_feed(
            [
                {
                    "link": "https://alpha.example.org/papers/same",
                    "title": "Same",
                    "content": "<p>Same content.</p>",
                },
                {
                    "link": "https://alpha.example.org/papers/same",
                    "title": "Same again",
                    "content": "<p>Same content.</p>",
                },
            ]
        )
        report = self.ingest(
            {
                "https://alpha.example.org/feed.xml": feed,
                "https://beta.example.org/feed.xml": BETA_FEED,
                "https://beta.example.org/posts/b1": BETA_PAGE,
            }
        )
        self.assertEqual(report.duplicates, 1)
        conn = self.connect()
        n = conn.execute(
            "SELECT COUNT(*) c FROM documents WHERE source_id = 'src-alpha'"
        ).fetchone()["c"]
        conn.close()
        self.assertEqual(n, 1)

    def test_cross_url_identical_content_is_retained_not_rejected(self):
        feed = rss_feed(
            [
                {
                    "link": "https://alpha.example.org/canonical",
                    "title": "Original",
                    "content": "<p>Identical body text.</p>",
                },
                {
                    "link": "https://alpha.example.org/syndicated",
                    "title": "Syndicated",
                    "content": "<p>Identical body text.</p>",
                },
            ]
        )
        report = self.ingest(
            {
                "https://alpha.example.org/feed.xml": feed,
                "https://beta.example.org/feed.xml": BETA_FEED,
                "https://beta.example.org/posts/b1": BETA_PAGE,
            }
        )
        # Conservative: both retained, collision reported.
        self.assertEqual(report.identical_content_other_url, 1)
        self.assertEqual(report.new, 3)  # 2 alpha + 1 beta
        conn = self.connect()
        n = conn.execute(
            "SELECT COUNT(*) c FROM documents WHERE source_id = 'src-alpha'"
        ).fetchone()["c"]
        conn.close()
        self.assertEqual(n, 2)


class ChangedContentTests(IngestTestBase):
    def test_changed_content_updates_and_preserves_history(self):
        mapping = base_mapping()
        self.ingest(mapping)

        # Source alpha publishes revised content for papers/one.
        mapping["https://alpha.example.org/feed.xml"] = ALPHA_FEED_V2
        report = self.ingest(mapping)

        self.assertEqual(report.changed, 1)
        self.assertEqual(report.existing, 3)
        self.assertEqual(self.count("documents"), 4)

        doc_id = db.document_id_for("https://alpha.example.org/papers/one")
        conn = self.connect()
        versions = conn.execute(
            "SELECT * FROM document_versions WHERE document_id = ? ORDER BY id",
            (doc_id,),
        ).fetchall()
        doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        changed_obs = conn.execute(
            "SELECT COUNT(*) c FROM observations WHERE document_id = ? AND changed = 1",
            (doc_id,),
        ).fetchone()["c"]
        conn.close()

        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0]["is_initial"], 1)
        self.assertIn("Alpha one abstract", versions[0]["normalized_content"])
        self.assertIn("Alpha ONE revised", versions[1]["normalized_content"])
        # Current document reflects new content.
        self.assertIn("Alpha ONE revised", doc["normalized_content"])
        self.assertEqual(changed_obs, 1)

    def test_untouched_documents_do_not_gain_versions(self):
        mapping = base_mapping()
        self.ingest(mapping)
        mapping["https://alpha.example.org/feed.xml"] = ALPHA_FEED_V2
        self.ingest(mapping)
        conn = self.connect()
        rows = conn.execute(
            "SELECT document_id, COUNT(*) c FROM document_versions GROUP BY document_id"
        ).fetchall()
        conn.close()
        counts = {r["document_id"]: r["c"] for r in rows}
        changed_id = db.document_id_for("https://alpha.example.org/papers/one")
        for doc_id, c in counts.items():
            self.assertEqual(c, 2 if doc_id == changed_id else 1, doc_id)


class FailureIsolationTests(IngestTestBase):
    def test_failed_source_does_not_block_others(self):
        mapping = base_mapping()
        del mapping["https://alpha.example.org/feed.xml"]  # unreachable
        report = self.ingest(mapping)

        self.assertEqual(report.attempted, 2)
        self.assertEqual(report.succeeded, 1)
        self.assertEqual(report.failed, 1)
        self.assertEqual(report.new, 1)  # beta still ingested

        conn = self.connect()
        alpha = conn.execute(
            "SELECT * FROM snapshot_sources WHERE source_id = 'src-alpha'"
        ).fetchone()
        errors = conn.execute(
            "SELECT * FROM ingest_errors WHERE source_id = 'src-alpha'"
        ).fetchall()
        docs = conn.execute(
            "SELECT COUNT(*) c FROM documents WHERE source_id = 'src-beta'"
        ).fetchone()["c"]
        conn.close()
        self.assertEqual(alpha["status"], "failed")
        self.assertTrue(errors)
        self.assertEqual(docs, 1)

    def test_page_fetch_failure_keeps_source_running_and_reports(self):
        mapping = base_mapping()
        del mapping["https://beta.example.org/posts/b1"]  # page unreachable
        report = self.ingest(mapping)

        self.assertEqual(report.new, 3)  # alpha still fully ingested
        self.assertEqual(report.failures, 1)
        self.assertEqual(report.failed, 0)  # source itself succeeded (feed fetched)
        conn = self.connect()
        docs = conn.execute(
            "SELECT COUNT(*) c FROM documents WHERE source_id = 'src-beta'"
        ).fetchone()["c"]
        conn.close()
        self.assertEqual(docs, 0)

    def test_empty_content_is_invalid_not_stored(self):
        feed = rss_feed(
            [
                {
                    "link": "https://alpha.example.org/empty",
                    "title": "Empty",
                    "content": "",
                }
            ]
        )
        report = self.ingest(
            {
                "https://alpha.example.org/feed.xml": feed,
                "https://beta.example.org/feed.xml": BETA_FEED,
                "https://beta.example.org/posts/b1": BETA_PAGE,
            }
        )
        self.assertEqual(report.invalid, 1)
        self.assertEqual(report.new, 1)
        conn = self.connect()
        n = conn.execute(
            "SELECT COUNT(*) c FROM documents WHERE canonical_url LIKE '%empty%'"
        ).fetchone()["c"]
        conn.close()
        self.assertEqual(n, 0)


class PageModeTests(IngestTestBase):
    def test_page_content_is_fetched_normalized_and_stored(self):
        self.ingest(base_mapping())
        conn = self.connect()
        doc = conn.execute(
            "SELECT * FROM documents WHERE source_id = 'src-beta'"
        ).fetchone()
        conn.close()
        self.assertIsNotNone(doc)
        self.assertIn("Beta post body content", doc["normalized_content"])
        self.assertNotIn("Menu", doc["normalized_content"])
        self.assertNotIn("Copyright noise", doc["normalized_content"])


class StatsTests(IngestTestBase):
    def test_stats_reports_real_counts(self):
        self.ingest(base_mapping())
        text = corpus_stats(self.db_path, self.config)
        self.assertIn("Documents: 4", text)
        self.assertIn("Snapshots: 1", text)
        self.assertIn("Source Alpha", text)
        self.assertIn("AI systems", text)
        self.assertIn("HCI", text)


class RebuildTests(IngestTestBase):
    def test_corpus_can_be_deleted_and_rebuilt(self):
        self.ingest(base_mapping())
        self.assertTrue(self.db_path.exists())
        self.db_path.unlink()
        report = self.ingest(base_mapping())
        self.assertEqual(report.new, 4)
        self.assertEqual(self.count("documents"), 4)
        self.assertEqual(self.count("snapshots"), 1)


if __name__ == "__main__":
    unittest.main()


SHARED_LINK_CONFIG = """
[ingest]
user_agent = "TestFetcher/0.1"
delay_seconds = 0.0
timeout_seconds = 5
robots_check = false

[[sources]]
id = "src-one"
name = "Source One"
url = "https://one.example.org"
feed_url = "https://one.example.org/feed.xml"
source_type = "academic"
topics = ["AI systems"]
enabled = true
content_from = "feed"
max_entries = 50
description = "first"

[[sources]]
id = "src-two"
name = "Source Two"
url = "https://two.example.org"
feed_url = "https://two.example.org/feed.xml"
source_type = "academic"
topics = ["AI systems"]
enabled = true
content_from = "feed"
max_entries = 50
description = "second; carries one item also present in source one"
"""


class CrossSourceDuplicateTests(IngestTestBase):
    def test_same_url_from_second_source_counts_as_duplicate(self):
        from helpers import rss_feed

        config = write_config(self.tmp, SHARED_LINK_CONFIG)
        shared = rss_feed(
            [
                {
                    "link": "https://one.example.org/shared",
                    "title": "Shared",
                    "content": "<p>Shared body.</p>",
                },
                {
                    "link": "https://one.example.org/only-one",
                    "title": "Only One",
                    "content": "<p>Only in source one.</p>",
                },
            ]
        )
        # Source two announces the same paper (arXiv-style cross-list).
        same_link_other_feed = rss_feed(
            [
                {
                    "link": "https://one.example.org/shared",
                    "title": "Shared (cross)",
                    "content": "<p>Shared body with cross announce type.</p>",
                },
                {
                    "link": "https://two.example.org/only-two",
                    "title": "Only Two",
                    "content": "<p>Only in source two.</p>",
                },
            ]
        )
        report = run_ingest(
            config,
            self.db_path,
            fetcher=FakeFetcher(
                {
                    "https://one.example.org/feed.xml": shared,
                    "https://two.example.org/feed.xml": same_link_other_feed,
                }
            ),
        )

        # Stored once, counted as duplicate, no spurious change.
        self.assertEqual(report.new, 3)  # shared, only-one, only-two
        self.assertEqual(report.duplicates, 1)
        self.assertEqual(report.changed, 0)
        conn = self.connect()
        n = conn.execute(
            "SELECT COUNT(*) c FROM documents WHERE canonical_url = 'https://one.example.org/shared'"
        ).fetchone()["c"]
        changed = conn.execute(
            "SELECT COUNT(*) c FROM observations WHERE changed = 1"
        ).fetchone()["c"]
        conn.close()
        self.assertEqual(n, 1)
        self.assertEqual(changed, 0)
