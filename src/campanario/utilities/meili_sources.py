"""Optional localhost-only Meilisearch cache for previously read PUBLIC web pages.

This is NOT a web crawler, a fact checker, or the primary personal memory store.
It indexes only documents passed from a successful web.read response. The cache
is explicitly opt-in, expires entries at lookup time, and never fetches URLs.
"""
from __future__ import annotations

import hashlib
import ipaddress
import os
import re
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit

import httpx

_TRUE = frozenset({"1", "true", "yes", "on"})
_INDEX = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def enabled() -> bool:
    return os.environ.get("CAMPANARIO_MEILI_ENABLED", "").strip().lower() in _TRUE


def _parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Source timestamp must include its timezone")
    return dt.astimezone(timezone.utc)


def _public_source_url(value: str) -> str:
    """Validate a stored provenance URL; does not make any network request."""
    if not isinstance(value, str) or len(value) > 2048 or any(ord(c) < 32 for c in value):
        raise ValueError("Invalid source URL")
    parsed = urlsplit(value)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or
            parsed.username or parsed.password or parsed.port not in {None, 80, 443}):
        raise ValueError("Only public HTTP/HTTPS URLs can be indexed")
    host = parsed.hostname.lower().rstrip(".")
    if (host in _LOCAL_HOSTS or host.endswith((".local", ".localhost", ".internal", ".onion"))):
        raise ValueError("Internal URL cannot be indexed")
    try:
        if not ipaddress.ip_address(host).is_global:
            raise ValueError("Private IP cannot be indexed")
    except ValueError as exc:
        if "cannot be indexed" in str(exc):
            raise
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))


@dataclass(frozen=True, slots=True)
class CachedPage:
    title: str
    url: str
    content: str
    read_at: str
    score: float | None = None


class MeiliSourceStore:
    """Minimal Meilisearch REST adapter using the Campanario's existing httpx.

    The remote endpoint is strictly loopback. Inject an httpx.Client in tests.
    """

    def __init__(
        self,
        *,
        url: str = "http://127.0.0.1:7700",
        api_key: str = "",
        index: str = "campanario_public_sources",
        client: httpx.Client | None = None,
        max_age_days: int = 7,
    ) -> None:
        parts = urlsplit(url)
        if (parts.scheme != "http" or parts.hostname not in _LOCAL_HOSTS or
                parts.username or parts.password or parts.path not in {"", "/"} or
                parts.query or parts.fragment or parts.port is None):
            raise ValueError("Meilisearch must use an explicit localhost HTTP endpoint and port")
        if not _INDEX.fullmatch(index):
            raise ValueError("Invalid Meilisearch index name")
        if not isinstance(max_age_days, int) or not 1 <= max_age_days <= 365:
            raise ValueError("Invalid cache TTL")
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.index = index
        self._client = client
        self.max_age = timedelta(days=max_age_days)

    @classmethod
    def from_env(cls, *, client: httpx.Client | None = None) -> "MeiliSourceStore":
        return cls(
            url=os.environ.get("CAMPANARIO_MEILI_URL", "http://127.0.0.1:7700"),
            api_key=os.environ.get("CAMPANARIO_MEILI_API_KEY", ""),
            index=os.environ.get("CAMPANARIO_MEILI_INDEX", "campanario_public_sources"),
            max_age_days=int(os.environ.get("CAMPANARIO_MEILI_TTL_DAYS", "7")),
            client=client,
        )

    def _request(self, method: str, path: str, *, params=None, payload=None) -> dict:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        factory = (nullcontext(self._client) if self._client is not None
                   else httpx.Client(timeout=httpx.Timeout(5, connect=1),
                                     follow_redirects=False, trust_env=False))
        with factory as client:
            response = client.request(
                method, self.url + path, params=params, json=payload, headers=headers
            )
            if response.is_redirect:
                raise ValueError("Meilisearch redirects are disabled")
            response.raise_for_status()
            result = response.json()
            if not isinstance(result, dict):
                raise ValueError("Invalid Meilisearch response")
            return result

    def health(self) -> bool:
        return self._request("GET", "/health").get("status") == "available"

    def index_read_page(self, *, title: str, url: str, content: str, read_at: str) -> int:
        """Store a page ONLY after the existing web.read tool returned success.

        Meilisearch indexing is asynchronous. The returned task UID is NOT a
        confirmation that indexing has completed.
        """
        url = _public_source_url(url)
        timestamp = _parse_utc(read_at).isoformat()
        body = re.sub(r"\s+", " ", str(content)).strip()[:16000]
        if len(body) < 80:
            raise ValueError("Page content is too short to index")
        doc = {
            "id": hashlib.sha256(url.encode("utf-8")).hexdigest(),
            "url": url,
            "title": re.sub(r"\s+", " ", str(title)).strip()[:240],
            "content": body,
            "read_at": timestamp,
            "content_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        }
        response = self._request(
            "POST", f"/indexes/{self.index}/documents",
            params={"primaryKey": "id"}, payload=[doc]
        )
        task_uid = response.get("taskUid")
        if not isinstance(task_uid, int):
            raise ValueError("Meilisearch did not return an indexing task UID")
        return task_uid

    def search(self, query: str, *, limit: int = 6) -> list[CachedPage]:
        query = str(query).strip()[:220]
        if len(query) < 2:
            return []
        response = self._request(
            "POST", f"/indexes/{self.index}/search",
            payload={
                "q": query,
                "limit": max(1, min(12, int(limit))),
                "attributesToRetrieve": ["id", "title", "url", "content", "read_at"],
                "showRankingScore": True,
            },
        )
        hits = response.get("hits", [])
        if not isinstance(hits, list):
            raise ValueError("Invalid Meilisearch hit list")
        now = datetime.now(timezone.utc)
        out: list[CachedPage] = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            try:
                read_at = _parse_utc(hit["read_at"])
                if read_at > now + timedelta(minutes=5) or now - read_at > self.max_age:
                    continue
                url = _public_source_url(hit["url"])
                title = str(hit.get("title", ""))[:240]
                content = str(hit.get("content", ""))[:16000]
                if len(content) < 80:
                    continue
                score = hit.get("_rankingScore")
                out.append(CachedPage(title, url, content, read_at.isoformat(),
                                      float(score) if isinstance(score, (int, float)) else None))
            except (KeyError, TypeError, ValueError):
                continue
        return out

    def task_status(self, task_uid: int) -> str:
        return str(self._request("GET", f"/tasks/{int(task_uid)}").get("status", "unknown"))
