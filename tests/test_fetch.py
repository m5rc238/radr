"""Fetcher tests: decompression, binary rejection, robots opt-out.
No network — _raw_get is monkeypatched."""

import gzip
import unittest

from radar.fetch import Fetcher, FetchError, decompress_body


def make_fetcher(raw_response) -> Fetcher:
    f = Fetcher(user_agent="TestFetcher/0.1", robots_check=False)
    f._raw_get = lambda url: raw_response  # type: ignore[method-assign]
    return f


class DecompressTests(unittest.TestCase):
    def test_gzip_magic_bytes_decompressed_without_header(self):
        # deepmind.google serves gzip bodies with no Content-Encoding header.
        payload = gzip.compress(b"<html><body>hello</body></html>")
        self.assertEqual(
            decompress_body(payload, ""),
            b"<html><body>hello</body></html>",
        )

    def test_gzip_with_content_encoding_header(self):
        payload = gzip.compress(b"abc")
        self.assertEqual(decompress_body(payload, "gzip"), b"abc")

    def test_plain_body_untouched(self):
        body = b"<html>plain</html>"
        self.assertEqual(decompress_body(body, "identity"), body)

    def test_deflate_decompressed(self):
        import zlib

        payload = zlib.compress(b"deflated")
        self.assertEqual(decompress_body(payload, "deflate"), b"deflated")

    def test_corrupt_gzip_returns_original_bytes(self):
        broken = b"\x1f\x8b" + b"garbage-not-really-gzip"
        self.assertEqual(decompress_body(broken, ""), broken)


class FetcherTests(unittest.TestCase):
    def test_decompresses_gzip_body_on_fetch(self):
        body = gzip.compress(b"<html><p>content</p></html>")
        f = make_fetcher((200, body, "text/html", ""))
        out, ctype = f.fetch("https://example.org/x")
        self.assertEqual(out, b"<html><p>content</p></html>")
        self.assertEqual(ctype, "text/html")

    def test_binary_content_rejected(self):
        f = make_fetcher((200, b"%PDF-1.4\x00\x00binary", "application/pdf", ""))
        with self.assertRaises(FetchError):
            f.fetch("https://example.org/x.pdf")

    def test_non_200_is_error(self):
        f = make_fetcher((404, b"missing", "text/html", ""))
        with self.assertRaises(FetchError):
            f.fetch("https://example.org/x")

    def test_robots_disabled_allows_fetch(self):
        f = make_fetcher((200, b"<html>ok</html>", "text/html", ""))
        self.assertTrue(f._robots_allowed("https://example.org/x"))

    def test_identity_header_used(self):
        captured = {}

        class FakeResp:
            status = 200
            headers = None

            def __init__(self):
                import email.message

                self.headers = email.message.Message()
                self.headers["Content-Type"] = "text/html"

            def read(self):
                return b"<html>ok</html>"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        import urllib.request

        def fake_urlopen(req, timeout=None):
            captured["headers"] = dict(req.header_items())
            return FakeResp()

        original = urllib.request.urlopen
        urllib.request.urlopen = fake_urlopen
        try:
            f = Fetcher(user_agent="TestFetcher/0.1", robots_check=False)
            f.fetch("https://example.org/")
        finally:
            urllib.request.urlopen = original

        headers = {k.lower(): v for k, v in captured["headers"].items()}
        self.assertEqual(headers.get("accept-encoding"), "identity")
        self.assertIn("testfetcher", headers.get("user-agent", "").lower())


if __name__ == "__main__":
    unittest.main()
