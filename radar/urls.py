"""URL identity: conservative canonicalization for duplicate detection.

Deliberately conservative: false-positive merging would destroy corpus
integrity, so only well-understood normalizations are applied.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Well-known tracking parameters only. Anything else is preserved.
TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref_src",
    "cmpid",
}


def canonical_url(url: str) -> str:
    """Return a conservative canonical form of *url*.

    Applied: lowercase scheme/host, drop fragment, drop known tracking
    parameters, sort remaining query parameters, remove default ports,
    remove a trailing slash on non-root paths.

    Not applied: http/https cross-mapping, path case changes, query
    value rewriting — too risky for false-positive merges.
    """
    url = url.strip()
    parts = urlsplit(url)

    scheme = parts.scheme.lower()
    host = parts.hostname or ""
    host = host.lower()
    port = parts.port
    if port and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        netloc = f"{host}:{port}"
    else:
        netloc = host
    if parts.username:
        # Credentials in URLs are unexpected here; keep them if present.
        creds = parts.username + (f":{parts.password}" if parts.password else "")
        netloc = f"{creds}@{netloc}"

    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_")
    ]
    pairs.sort()
    query = urlencode(pairs)

    return urlunsplit((scheme, netloc, path, query, ""))
