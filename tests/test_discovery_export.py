import json

from radar.discovery import iso_date, parse_feed, parse_listing, parse_sitemap
from radar.export import export_all, safe_cell
from radar.store import Store


def test_dates_are_normalized_to_utc():
    assert iso_date("2026-11-14") == "2026-11-14T00:00:00+00:00"
    assert iso_date("2026-11-14T08:00:00+05:30") == "2026-11-14T02:30:00+00:00"


def test_feed_and_listing_extract_links():
    feed = """<rss><channel><item><title>Useful commerce platform update</title><link>https://example.com/news/1</link><pubDate>Sat, 14 Nov 2026 02:30:00 GMT</pubDate></item></channel></rss>"""
    entries, _ = parse_feed(feed, "https://example.com/feed/")
    assert entries[0]["published"].startswith("2026-11-14")
    html = """<main><article><a href='/news/2'>A useful connected customer journey story</a><time datetime='2026-11-13'></time></article></main>"""
    entries, _ = parse_listing(html, "https://example.com/", {"include": "/news/"})
    assert entries[0]["url"] == "https://example.com/news/2"


def test_explicit_sitemap_extracts_only_included_articles():
    xml = """<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>
      <url><loc>https://example.com/cases/connected-journey</loc><lastmod>2026-11-12</lastmod></url>
      <url><loc>https://example.com/about</loc></url>
    </urlset>"""
    entries, nxt = parse_sitemap(xml, "https://example.com/sitemap.xml", {"include": "/cases/"})
    assert nxt is None
    assert entries == [{"url": "https://example.com/cases/connected-journey",
                        "title": "Connected Journey", "published": None,
                        "modified": "2026-11-12T00:00:00+00:00"}]


def test_export_preserves_notes_and_neutralizes_formulas(tmp_path):
    assert safe_cell("=HYPERLINK(\"bad\")").startswith("'")
    store = Store(tmp_path / "radar.sqlite")
    aid, _ = store.add_article("source", {"url": "https://example.com/story", "title": "+formula headline"})
    store.execute("UPDATE articles SET state='extracted',notes='Keep this',priority=80 WHERE id=?", (aid,))
    output = tmp_path / "out"
    export_all(store, output)
    payload = json.loads((output / "radar.json").read_text())
    row = next(r for r in payload["tables"]["Library"][1:] if r[0] == aid)
    assert row[9] == "Keep this"
    csv_text = (output / "library.csv").read_text()
    assert "'+formula headline" in csv_text
    assert "<script type=\"application/json\"" in (output / "index.html").read_text()
    store.close()
