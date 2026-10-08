"""URL identity and document-id stability tests."""

import unittest

from radar.db import document_id_for
from radar.urls import canonical_url


class CanonicalUrlTests(unittest.TestCase):
    def test_strips_tracking_params(self):
        self.assertEqual(
            canonical_url("https://Example.org/a?utm_source=x&utm_medium=y&b=2&a=1"),
            "https://example.org/a?a=1&b=2",
        )

    def test_strips_fragment(self):
        self.assertEqual(
            canonical_url("https://example.org/a#section"),
            "https://example.org/a",
        )

    def test_sorts_query_params(self):
        self.assertEqual(
            canonical_url("https://example.org/a?z=1&a=2"),
            canonical_url("https://example.org/a?a=2&z=1"),
        )

    def test_removes_trailing_slash(self):
        self.assertEqual(
            canonical_url("https://example.org/a/"),
            "https://example.org/a",
        )

    def test_keeps_root_slash(self):
        self.assertEqual(canonical_url("https://example.org/"), "https://example.org/")

    def test_removes_default_port(self):
        self.assertEqual(
            canonical_url("https://example.org:443/a"),
            "https://example.org/a",
        )
        self.assertEqual(
            canonical_url("http://example.org:80/a"),
            "http://example.org/a",
        )

    def test_keeps_non_default_port(self):
        self.assertEqual(
            canonical_url("https://example.org:8443/a"),
            "https://example.org:8443/a",
        )

    def test_conservative_no_scheme_cross_mapping(self):
        # http and https must NOT be merged: too risky for false-positive dedupe.
        self.assertNotEqual(
            canonical_url("http://example.org/a"),
            canonical_url("https://example.org/a"),
        )

    def test_drops_known_tracking_only(self):
        self.assertEqual(
            canonical_url("https://example.org/a?fbclid=abc&id=7"),
            "https://example.org/a?id=7",
        )


class DocumentIdTests(unittest.TestCase):
    def test_stable_identity(self):
        url = "https://example.org/paper"
        self.assertEqual(document_id_for(url), document_id_for(url))
        self.assertEqual(len(document_id_for(url)), 16)

    def test_identity_follows_canonical_url(self):
        a = canonical_url("https://Example.org/paper?utm_source=x")
        b = canonical_url("https://example.org/paper")
        self.assertEqual(document_id_for(a), document_id_for(b))

    def test_different_urls_different_ids(self):
        self.assertNotEqual(
            document_id_for("https://example.org/a"),
            document_id_for("https://example.org/b"),
        )


if __name__ == "__main__":
    unittest.main()
