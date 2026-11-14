from datetime import datetime, timezone

from radar.engine import collect_source
from radar.store import Store


class FeedFetcher:
    def get(self, url, cache=False):
        items = "".join(
            f"<item><title>AI commerce case study number {i}</title><link>https://example.com/{i}</link><pubDate>Fri, 13 Nov 2026 00:00:00 GMT</pubDate></item>"
            for i in range(4)
        )
        return f"<rss><channel>{items}</channel></rss>", "application/rss+xml", url


def test_per_source_queue_cap_retains_extra_titles(tmp_path):
    source = {"id": "feed", "name": "Feed", "kind": "publisher", "beats": ["enterprise"],
              "enabled": True, "interval_hours": 24, "max_pages": 1, "lookback_days": 14,
              "queue_limit": 2, "endpoints": [{"type": "feed", "url": "https://example.com/feed"}]}
    store = Store(tmp_path / "radar.sqlite")
    store.register([source])
    store.execute("INSERT INTO runs(id,started) VALUES('run','2026-11-14T00:00:00+00:00')")
    collect_source(store, FeedFetcher(), source, datetime(2026, 11, 14, tzinfo=timezone.utc), "run")
    assert store.one("SELECT count(*) AS n FROM articles WHERE state='queued'")["n"] == 2
    assert store.one("SELECT count(*) AS n FROM articles WHERE state='title_only'")["n"] == 2
    assert "2 queued for full text" in store.one("SELECT detail FROM sources WHERE id='feed'")["detail"]
    store.close()
