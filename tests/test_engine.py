from datetime import datetime, timezone

from radar.engine import collect_source, due
from radar.store import Store


class FakeFetcher:
    def __init__(self, pages):
        self.pages = pages

    def get(self, url, cache=False):
        return self.pages[url], "application/rss+xml", url


def test_old_feed_items_are_retained_without_entering_queue(tmp_path):
    store = Store(tmp_path / "radar.sqlite")
    source = {"id": "feed", "name": "Feed", "kind": "publisher", "beats": ["fmcg"],
              "enabled": True, "interval_hours": 24, "max_pages": 1, "lookback_days": 14,
              "endpoints": [{"type": "feed", "url": "https://example.com/feed"}]}
    store.register([source])
    run_id = "run"
    store.execute("INSERT INTO runs(id,started) VALUES(?,?)", (run_id, "2026-11-14T00:00:00+00:00"))
    feed = """<rss><channel>
      <item><title>Old but retained customer story</title><link>https://example.com/old</link><pubDate>Thu, 1 Jan 2026 00:00:00 GMT</pubDate></item>
      <item><title>Current customer story for review</title><link>https://example.com/new</link><pubDate>Fri, 13 Nov 2026 00:00:00 GMT</pubDate></item>
      <item><title>Second general corporate announcement today</title><link>https://example.com/sample</link><pubDate>Fri, 13 Nov 2026 00:00:00 GMT</pubDate></item>
      <item><title>Third general corporate announcement today</title><link>https://example.com/retained</link><pubDate>Fri, 13 Nov 2026 00:00:00 GMT</pubDate></item>
    </channel></rss>"""
    collect_source(store, FakeFetcher({"https://example.com/feed": feed}), source,
                   datetime(2026, 11, 14, tzinfo=timezone.utc), run_id)
    assert store.one("SELECT state FROM articles WHERE url='https://example.com/old'")["state"] == "outside_window"
    assert store.one("SELECT state FROM articles WHERE url='https://example.com/new'")["state"] == "queued"
    assert store.one("SELECT state FROM articles WHERE url='https://example.com/sample'")["state"] == "queued"
    assert store.one("SELECT state FROM articles WHERE url='https://example.com/retained'")["state"] == "title_only"
    store.close()


def test_weekly_source_waits_for_its_weekday():
    now = datetime(2026, 11, 14, tzinfo=timezone.utc)  # Saturday
    assert due({"enabled": True, "weekday": 5}, {}, now)
    assert not due({"enabled": True, "weekday": 1}, {}, now)
