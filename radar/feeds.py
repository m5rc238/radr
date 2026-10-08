"""Feed parsing (RSS 2.0 and Atom) using only the standard library."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

DC_NS = "http://purl.org/dc/elements/1.1/"
CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"
ATOM_NS = "http://www.w3.org/2005/Atom"


@dataclass
class FeedEntry:
    link: str
    title: str
    published_at: str | None  # ISO 8601 UTC, or None
    author: str | None
    content: str  # best available feed-provided content (may be "")
    guid: str | None


class FeedParseError(Exception):
    pass


def _to_iso(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    # RFC 822 (RSS pubDate, arXiv dc:date)
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        pass
    # ISO 8601 (Atom)
    try:
        iso = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _entry_content(item: ET.Element) -> str:
    """Best available content: prefer content:encoded, then description."""
    encoded = _text(item.find(f"{{{CONTENT_NS}}}encoded"))
    description = _text(item.find("description"))
    if len(encoded) >= len(description):
        return encoded
    return description


def _parse_rss(root: ET.Element) -> list[FeedEntry]:
    entries: list[FeedEntry] = []
    for item in root.findall(".//item"):
        link = _text(item.find("link"))
        title = _text(item.find("title"))
        if not link and not title:
            continue
        entries.append(
            FeedEntry(
                link=link,
                title=title,
                published_at=_to_iso(
                    _text(item.find("pubDate")) or _text(item.find(f"{{{DC_NS}}}date"))
                ),
                author=_text(item.find(f"{{{DC_NS}}}creator")) or None,
                content=_entry_content(item),
                guid=_text(item.find("guid")) or None,
            )
        )
    return entries


def _parse_atom(root: ET.Element) -> list[FeedEntry]:
    entries: list[FeedEntry] = []
    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        link = ""
        for link_el in entry.findall(f"{{{ATOM_NS}}}link"):
            if link_el.get("rel") in (None, "alternate"):
                link = link_el.get("href", "")
                if link:
                    break
        content = (
            _text(entry.find(f"{{{ATOM_NS}}}content"))
            or _text(entry.find(f"{{{ATOM_NS}}}summary"))
        )
        author_el = entry.find(f"{{{ATOM_NS}}}author")
        author = ""
        if author_el is not None:
            author = _text(author_el.find(f"{{{ATOM_NS}}}name"))
        entries.append(
            FeedEntry(
                link=link,
                title=_text(entry.find(f"{{{ATOM_NS}}}title")),
                published_at=_to_iso(
                    _text(entry.find(f"{{{ATOM_NS}}}published"))
                    or _text(entry.find(f"{{{ATOM_NS}}}updated"))
                ),
                author=author or None,
                content=content,
                guid=_text(entry.find(f"{{{ATOM_NS}}}id")) or None,
            )
        )
    return entries


def parse_feed(data: bytes) -> list[FeedEntry]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise FeedParseError(f"invalid XML: {exc}") from exc

    tag = root.tag
    if tag.endswith("rss") or tag == "rdf:RDF" or tag.endswith("RDF"):
        entries = _parse_rss(root)
    elif tag == f"{{{ATOM_NS}}}feed":
        entries = _parse_atom(root)
    else:
        raise FeedParseError(f"unrecognized feed root element: {tag}")

    if not entries:
        raise FeedParseError("feed contains no entries")
    return entries
