from __future__ import annotations

import ipaddress
import socket
import time
from urllib.parse import urlsplit, urljoin, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx

from .store import canonical_url, utcnow


class FetchError(Exception):
    pass


class BudgetExceeded(FetchError):
    pass


class Fetcher:
    user_agent = "MartechRadar/0.1 (personal research collector)"

    def __init__(self, store, max_requests=180, max_seconds=540, transport=None, delay=1.0):
        self.store = store
        self.max_requests = max_requests
        self.deadline = time.monotonic() + max_seconds
        self.requests = 0
        self.bytes = 0
        self.cache_hits = 0
        self.delay = delay
        self.last_host = {}
        self.robots = {}
        self.testing = transport is not None
        self.client = httpx.Client(timeout=20, transport=transport, follow_redirects=False,
                                   headers={"User-Agent": self.user_agent,
                                            "Accept": "text/html,application/rss+xml,application/atom+xml,application/xml;q=0.9,*/*;q=0.5"})

    def validate(self, url):
        # Preserve the publisher's exact path. Canonicalisation is for deduplication;
        # applying it here can turn a legitimate `/path/` redirect into a loop.
        p = urlsplit(url.strip())
        if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
            raise FetchError("Only public HTTP URLs are allowed")
        url = urlunsplit((p.scheme.lower(), p.netloc, p.path or "/", p.query, ""))
        if self.testing:
            return url
        host = p.hostname
        try:
            port = p.port or (443 if p.scheme == "https" else 80)
            addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise FetchError(f"DNS unavailable for {host}") from exc
        if any(not ipaddress.ip_address(x[4][0]).is_global for x in addresses):
            raise FetchError("Non-public address refused")
        return url

    def _request(self, url, headers=None, check_redirect_robots=True):
        for _ in range(6):
            url = self.validate(url)
            host = urlsplit(url).hostname
            if self.requests >= self.max_requests or time.monotonic() >= self.deadline:
                raise BudgetExceeded("Run limit reached; pending work retained")
            time.sleep(max(0, self.delay - (time.monotonic() - self.last_host.get(host, 0))))
            self.requests += 1
            try:
                with self.client.stream("GET", url, headers=headers or {}) as r:
                    self.last_host[host] = time.monotonic()
                    if r.status_code in (300, 301, 302, 303, 307, 308) and r.headers.get("location"):
                        destination = urljoin(url, r.headers["location"])
                        if check_redirect_robots:
                            self.allowed(destination)
                        url = destination
                        headers = None
                        continue
                    chunks, size = [], 0
                    for chunk in r.iter_bytes():
                        size += len(chunk)
                        self.bytes += len(chunk)
                        if size > 5_000_000:
                            raise FetchError("Page exceeds 5 MB limit")
                        chunks.append(chunk)
                    return r.status_code, dict(r.headers), b"".join(chunks), str(r.url)
            except httpx.HTTPError as exc:
                raise FetchError(f"{type(exc).__name__}: request failed for {host}") from exc
        raise FetchError("Too many redirects")

    def allowed(self, url):
        p = urlsplit(url)
        origin = f"{p.scheme}://{p.netloc}"
        if origin not in self.robots:
            code, _, body, _ = self._request(origin + "/robots.txt", check_redirect_robots=False)
            if code in (401, 403, 429) or code >= 500:
                raise FetchError(f"robots.txt unavailable ({code}); deferred")
            parser = RobotFileParser()
            parser.parse(body.decode("utf-8", "replace").splitlines() if code == 200 else [])
            self.robots[origin] = parser
        if not self.robots[origin].can_fetch(self.user_agent, url):
            raise FetchError("Publisher robots.txt disallows this URL")

    def get(self, url, cache=False):
        url = self.validate(url)
        self.allowed(url)
        old = self.store.one("SELECT * FROM cache WHERE url=?", (url,)) if cache else None
        headers = {}
        if old:
            if old["etag"]:
                headers["If-None-Match"] = old["etag"]
            if old["modified"]:
                headers["If-Modified-Since"] = old["modified"]
        code, h, body, final_url = self._request(url, headers)
        if code == 304 and old:
            self.cache_hits += 1
            return old["body"].decode("utf-8", "replace"), old["content_type"], final_url
        if code != 200:
            raise FetchError(f"HTTP {code} for {urlsplit(url).hostname}")
        kind = h.get("content-type", "")
        if "pdf" in kind or "image/" in kind:
            raise FetchError("Document requires manual review (PDF/media)")
        if cache:
            self.store.execute("INSERT OR REPLACE INTO cache VALUES(?,?,?,?,?,?)",
                               (url, h.get("etag"), h.get("last-modified"), body, kind, utcnow()))
        return body.decode("utf-8", "replace"), kind, final_url

    def close(self):
        self.client.close()

