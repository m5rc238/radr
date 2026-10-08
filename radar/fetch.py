"""HTTP fetching: polite, rate-limited, robots-aware.

The fetcher is injected into ingestion, so tests can substitute a fake
and run the entire pipeline without network access.
"""

from __future__ import annotations

import gzip
import time
import urllib.error
import urllib.request
import urllib.robotparser
import zlib
from dataclasses import dataclass, field
from urllib.parse import urlsplit

_GZIP_MAGIC = b"\x1f\x8b"


def decompress_body(body: bytes, content_encoding: str = "") -> bytes:
    """Decode compressed HTTP bodies.

    Some servers (observed: deepmind.google) serve gzip bodies without a
    Content-Encoding header, so the gzip magic bytes are checked too.
    """
    encoding = (content_encoding or "").lower().strip()
    if "gzip" in encoding or body.startswith(_GZIP_MAGIC):
        try:
            return gzip.decompress(body)
        except (OSError, EOFError):
            return body
    if "deflate" in encoding:
        try:
            return zlib.decompress(body)
        except zlib.error:
            try:
                return zlib.decompress(body, -zlib.MAX_WBITS)
            except zlib.error:
                return body
    return body


class FetchError(Exception):
    pass


class RobotsBlocked(FetchError):
    pass


@dataclass
class Fetcher:
    user_agent: str
    delay_seconds: float = 1.0
    timeout_seconds: float = 20.0
    robots_check: bool = True
    _last_request_at: float = 0.0
    _robots_cache: dict[str, urllib.robotparser.RobotFileParser | None] = field(
        default_factory=dict
    )

    def _throttle(self) -> None:
        if self.delay_seconds <= 0:
            return
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)
        self._last_request_at = time.monotonic()

    def _raw_get(self, url: str) -> tuple[int, bytes, str, str]:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "*/*",
                "Accept-Encoding": "identity",
            },
        )
        self._throttle()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                return (
                    resp.status,
                    resp.read(),
                    resp.headers.get_content_type(),
                    resp.headers.get("Content-Encoding", ""),
                )
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read() if exc.fp else b"", "", ""
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise FetchError(f"request failed: {exc}") from exc

    def _robots_allowed(self, url: str) -> bool:
        if not self.robots_check:
            return True
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots_cache:
            robots_url = f"{origin}/robots.txt"
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            try:
                status, body, _, _ = self._raw_get(robots_url)
                if status == 200:
                    rp.parse(body.decode("utf-8", errors="replace").splitlines())
                    self._robots_cache[origin] = rp
                else:
                    # No robots.txt (404 etc.) -> nothing disallowed.
                    self._robots_cache[origin] = None
            except FetchError:
                # Unreachable robots.txt: record as unknown, allow politely.
                self._robots_cache[origin] = None
        rp = self._robots_cache[origin]
        if rp is None:
            return True
        return rp.can_fetch(self.user_agent, url)

    def fetch(self, url: str) -> tuple[bytes, str]:
        """Fetch *url* -> (bytes, content_type). Raises FetchError.

        Returns the body fully decompressed. Bodies that still contain NUL
        bytes after decompression are rejected as binary content.
        """
        if not self._robots_allowed(url):
            raise RobotsBlocked(f"blocked by robots.txt: {url}")
        status, body, content_type, content_encoding = self._raw_get(url)
        if status != 200:
            raise FetchError(f"HTTP {status} for {url}")
        if not body:
            raise FetchError(f"empty response for {url}")
        body = decompress_body(body, content_encoding)
        if b"\x00" in body:
            raise FetchError(f"binary content for {url} ({content_type})")
        return body, content_type
