"""Shared test helpers: fake fetcher and RSS feed builder."""

from __future__ import annotations


class FakeFetcher:
    """URL -> bytes map. Missing URL or Exception value -> FetchError."""

    def __init__(self, mapping: dict[str, object]):
        self.mapping = dict(mapping)
        self.calls: list[str] = []

    def fetch(self, url: str):
        from radar.fetch import FetchError

        self.calls.append(url)
        value = self.mapping.get(url)
        if value is None:
            raise FetchError(f"request failed: unreachable {url}")
        if isinstance(value, BaseException):
            raise FetchError(str(value))
        if isinstance(value, tuple):
            return value
        if isinstance(value, bytes):
            return value, "application/xml"
        return str(value).encode("utf-8"), "application/xml"


def rss_feed(items: list[dict]) -> str:
    """Build an RSS 2.0 document. Item keys: link, title, date, content, author."""
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:content="http://purl.org/rss/1.0/modules/content/">',
        "<channel><title>Test Feed</title><link>https://example.org</link>",
        "<description>test</description>",
    ]
    for item in items:
        parts.append("<item>")
        parts.append(f"<title><![CDATA[{item.get('title', '')}]]></title>")
        parts.append(f"<link>{item.get('link', '')}</link>")
        if item.get("date"):
            parts.append(f"<pubDate>{item['date']}</pubDate>")
        if item.get("author"):
            parts.append(
                f"<dc:creator><![CDATA[{item['author']}]]></dc:creator>"
            )
        content = item.get("content", "")
        parts.append(
            f"<content:encoded><![CDATA[{content}]]></content:encoded>"
        )
        parts.append(f"<description><![CDATA[{item.get('summary', '')}]]></description>")
        parts.append("</item>")
    parts.append("</channel></rss>")
    return "\n".join(parts)


DEFAULT_CONFIG = """
[ingest]
user_agent = "TestFetcher/0.1"
delay_seconds = 0.0
timeout_seconds = 5
robots_check = false

[[sources]]
id = "src-alpha"
name = "Source Alpha"
url = "https://alpha.example.org"
feed_url = "https://alpha.example.org/feed.xml"
source_type = "academic"
topics = ["AI systems"]
enabled = true
content_from = "feed"
max_entries = 50
description = "test source"

[[sources]]
id = "src-beta"
name = "Source Beta"
url = "https://beta.example.org"
feed_url = "https://beta.example.org/feed.xml"
source_type = "technical"
topics = ["HCI"]
enabled = true
content_from = "page"
max_entries = 50
description = "test source with page content"
"""


def write_config(tmp_path, text: str = DEFAULT_CONFIG):
    path = tmp_path / "sources.toml"
    path.write_text(text, encoding="utf-8")
    return path


ALPHA_FEED_V1 = rss_feed(
    [
        {
            "link": "https://alpha.example.org/papers/one",
            "title": "Paper One",
            "date": "Mon, 05 Oct 2026 10:00:00 +0000",
            "author": "A. Author",
            "content": "<p>Alpha <b>one</b> abstract with sufficient content.</p>",
        },
        {
            "link": "https://alpha.example.org/papers/two?utm_source=rss",
            "title": "Paper Two",
            "date": "Tue, 06 Oct 2026 10:00:00 +0000",
            "content": "<p>Alpha two abstract with sufficient content.</p>",
        },
        {
            "link": "https://alpha.example.org/papers/three",
            "title": "Paper Three",
            "date": "Wed, 07 Oct 2026 10:00:00 +0000",
            "content": "<p>Alpha three abstract with sufficient content.</p>",
        },
    ]
)

ALPHA_FEED_V2 = rss_feed(
    [
        {
            "link": "https://alpha.example.org/papers/one",
            "title": "Paper One (revised)",
            "date": "Mon, 05 Oct 2026 10:00:00 +0000",
            "author": "A. Author",
            "content": "<p>Alpha ONE revised abstract with sufficient content.</p>",
        },
        {
            "link": "https://alpha.example.org/papers/two",
            "title": "Paper Two",
            "date": "Tue, 06 Oct 2026 10:00:00 +0000",
            "content": "<p>Alpha two abstract with sufficient content.</p>",
        },
        {
            "link": "https://alpha.example.org/papers/three",
            "title": "Paper Three",
            "date": "Wed, 07 Oct 2026 10:00:00 +0000",
            "content": "<p>Alpha three abstract with sufficient content.</p>",
        },
    ]
)

BETA_PAGE = """
<html><head><title>Beta Post</title><script>var x=1;</script></head>
<body><nav>Home | About | Login</nav>
<article><h1>Beta Post</h1><p>Beta post body content that is meaningful.</p></article>
<footer>Copyright noise</footer></body></html>
"""

BETA_FEED = rss_feed(
    [
        {
            "link": "https://beta.example.org/posts/b1",
            "title": "Beta Post",
            "date": "Thu, 08 Oct 2026 09:00:00 +0000",
            "summary": "tiny teaser",
        }
    ]
)


def base_mapping() -> dict[str, object]:
    return {
        "https://alpha.example.org/feed.xml": ALPHA_FEED_V1,
        "https://beta.example.org/feed.xml": BETA_FEED,
        "https://beta.example.org/posts/b1": BETA_PAGE,
    }
