"""Content normalization: HTML/text -> stable plain text + content hash.

Normalization is deterministic: identical input always produces identical
output and identical hash. It never summarizes, rewrites, or paraphrases;
it only strips markup/boilerplate elements and collapses whitespace.
"""

from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser

SKIP_TAGS = {
    "script",
    "style",
    "noscript",
    "nav",
    "header",
    "footer",
    "aside",
    "iframe",
    "svg",
    "form",
    "button",
    "template",
}

BLOCK_TAGS = {
    "p",
    "div",
    "section",
    "article",
    "main",
    "li",
    "br",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "tr",
    "td",
    "th",
    "blockquote",
    "pre",
    "ul",
    "ol",
    "table",
}

_HTML_TAG_RE = re.compile(r"<[a-zA-Z][^>]*>")


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth += 1
        elif tag in BLOCK_TAGS and self._skip_depth == 0:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag in BLOCK_TAGS and self._skip_depth == 0:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def text(self) -> str:
        return "".join(self._chunks)


def _collapse(text: str) -> str:
    # Normalize newlines, collapse horizontal whitespace, drop blank lines.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t\f\v ]+", " ", line).strip() for line in text.split("\n")]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def extract_text(raw: str) -> str:
    """Strip HTML to plain text when HTML is present; otherwise return as-is."""
    if _HTML_TAG_RE.search(raw):
        parser = _TextExtractor()
        try:
            parser.feed(raw)
            parser.close()
            raw = parser.text()
        except Exception:
            # Malformed HTML: fall back to tag-stripping so content is not lost.
            raw = re.sub(r"<[^>]+>", " ", raw)
    return _collapse(raw)


def normalize(raw: str) -> str:
    """Deterministic normalization used for both storage and hashing."""
    return extract_text(raw)


def content_hash(normalized: str) -> str:
    """Stable sha256 over UTF-8 normalized content."""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
