"""Load and validate the source registry (sources/sources.toml)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

VALID_SOURCE_TYPES = {"academic", "official-research", "technical", "news", "other"}
VALID_CONTENT_FROM = {"feed", "page"}

DEFAULT_CONFIG = Path("sources/sources.toml")
DEFAULT_DB = Path("data/radar.db")


@dataclass
class IngestSettings:
    user_agent: str = "InformationRadar/0.1 (personal research corpus; polite fetcher)"
    delay_seconds: float = 1.0
    timeout_seconds: float = 20.0
    robots_check: bool = True


@dataclass
class Source:
    id: str
    name: str
    url: str
    feed_url: str
    source_type: str
    topics: list[str] = field(default_factory=list)
    enabled: bool = True
    content_from: str = "feed"
    max_entries: int = 30
    description: str = ""


class ConfigError(Exception):
    pass


def _require(entry: dict, key: str, source_id: str) -> object:
    if key not in entry or entry[key] in (None, ""):
        raise ConfigError(f"source '{source_id}': missing required field '{key}'")
    return entry[key]


def load_config(path: Path) -> tuple[IngestSettings, list[Source]]:
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    with open(path, "rb") as fh:
        data = tomllib.load(fh)

    settings = IngestSettings(**(data.get("ingest") or {}))

    sources: list[Source] = []
    seen_ids: set[str] = set()
    for entry in data.get("sources") or []:
        sid = str(_require(entry, "id", entry.get("id", "?")))
        if sid in seen_ids:
            raise ConfigError(f"duplicate source id: {sid}")
        seen_ids.add(sid)

        source_type = str(_require(entry, "source_type", sid))
        if source_type not in VALID_SOURCE_TYPES:
            raise ConfigError(f"source '{sid}': invalid source_type '{source_type}'")

        content_from = str(entry.get("content_from", "feed"))
        if content_from not in VALID_CONTENT_FROM:
            raise ConfigError(f"source '{sid}': invalid content_from '{content_from}'")

        max_entries = int(entry.get("max_entries", 30))
        if max_entries < 1:
            raise ConfigError(f"source '{sid}': max_entries must be >= 1")

        sources.append(
            Source(
                id=sid,
                name=str(_require(entry, "name", sid)),
                url=str(_require(entry, "url", sid)),
                feed_url=str(_require(entry, "feed_url", sid)),
                source_type=source_type,
                topics=[str(t) for t in entry.get("topics", [])],
                enabled=bool(entry.get("enabled", True)),
                content_from=content_from,
                max_entries=max_entries,
                description=str(entry.get("description", "")),
            )
        )

    if not sources:
        raise ConfigError("config contains no sources")
    if len({s.url for s in sources}) != len(sources):
        raise ConfigError("two sources share the same url")

    return settings, sources
