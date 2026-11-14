import json

from radar.store import Store, canonical_url


def test_tracking_parameters_deduplicate_but_meaningful_query_survives(tmp_path):
    store = Store(tmp_path / "radar.sqlite")
    first, created = store.add_article("one", {"url": "https://EXAMPLE.com/story/?utm_source=x&id=7", "title": "A story"})
    second, created_again = store.add_article("two", {"url": "https://example.com/story?id=7&utm_medium=y", "title": "A story"})
    assert first == second
    assert created is True and created_again is False
    assert canonical_url("https://example.com/story?id=7&utm_medium=y") == "https://example.com/story?id=7"
    assert store.one("SELECT count(*) AS n FROM articles")["n"] == 1
    assert store.one("SELECT count(*) AS n FROM sightings")["n"] == 2
    store.close()


def test_modified_article_requeues_without_losing_notes(tmp_path):
    store = Store(tmp_path / "radar.sqlite")
    aid, _ = store.add_article("one", {"url": "https://example.com/story", "title": "A story", "modified": "2026-11-01T00:00:00+00:00"})
    store.execute("UPDATE articles SET state='extracted',notes='My note',read_status='Saved' WHERE id=?", (aid,))
    store.add_article("one", {"url": "https://example.com/story", "title": "A story", "modified": "2026-11-02T00:00:00+00:00"})
    item = store.one("SELECT * FROM articles WHERE id=?", (aid,))
    assert item["state"] == "queued"
    assert item["notes"] == "My note"
    assert item["read_status"] == "Saved"
    store.close()


def test_legacy_import_is_idempotent(tmp_path):
    ledger = tmp_path / "seen.jsonl"
    ledger.write_text(json.dumps({"story_key": "same-story", "url": "https://example.com/a", "first_seen": "2026-10-01", "score": 16}) + "\n")
    store = Store(tmp_path / "radar.sqlite")
    assert store.import_legacy(ledger) == 1
    assert store.import_legacy(ledger) == 0
    assert store.one("SELECT count(*) AS n FROM legacy")["n"] == 1
    store.close()
