import httpx
import pytest

from radar.network import FetchError, Fetcher
from radar.store import Store


def test_redirect_keeps_trailing_slash_and_checks_robots(tmp_path):
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.path == "/news":
            return httpx.Response(301, headers={"location": "/news/"})
        if request.url.path == "/news/":
            return httpx.Response(200, text="ok", headers={"content-type": "text/html"})
        return httpx.Response(404)

    store = Store(tmp_path / "radar.sqlite")
    fetcher = Fetcher(store, transport=httpx.MockTransport(handler), delay=0)
    body, _, resolved = fetcher.get("https://example.com/news")
    assert body == "ok"
    assert resolved == "https://example.com/news/"
    assert seen.count("https://example.com/robots.txt") == 1
    fetcher.close()
    store.close()


def test_conditional_request_uses_cached_body(tmp_path):
    listing_requests = []

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        listing_requests.append(dict(request.headers))
        if request.headers.get("if-none-match") == '"v1"':
            return httpx.Response(304)
        return httpx.Response(200, text="first", headers={"etag": '"v1"', "content-type": "text/html"})

    store = Store(tmp_path / "radar.sqlite")
    fetcher = Fetcher(store, transport=httpx.MockTransport(handler), delay=0)
    assert fetcher.get("https://example.com/list", cache=True)[0] == "first"
    assert fetcher.get("https://example.com/list", cache=True)[0] == "first"
    assert listing_requests[1]["if-none-match"] == '"v1"'
    assert fetcher.cache_hits == 1
    fetcher.close()
    store.close()


def test_private_addresses_are_refused(monkeypatch, tmp_path):
    monkeypatch.setattr("socket.getaddrinfo", lambda *args, **kwargs: [(None, None, None, None, ("127.0.0.1", 443))])
    store = Store(tmp_path / "radar.sqlite")
    fetcher = Fetcher(store, delay=0)
    with pytest.raises(FetchError, match="Non-public"):
        fetcher.validate("https://localhost/secret")
    fetcher.close()
    store.close()
