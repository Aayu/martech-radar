from radar.snapshot import export_snapshot, restore_snapshot
from radar.store import Store


def test_text_snapshot_preserves_decisions_without_full_article_body(tmp_path):
    first = Store(tmp_path / "first.sqlite")
    aid, _ = first.add_article("source", {"url": "https://example.com/a", "title": "Story"})
    first.execute("UPDATE articles SET state='extracted',text='large transient body',excerpt='small',notes='My note',read_status='Saved' WHERE id=?", (aid,))
    export_snapshot(first, tmp_path / "snapshot")
    assert "large transient body" not in (tmp_path / "snapshot" / "articles.jsonl").read_text()
    first.close()

    second = Store(tmp_path / "second.sqlite")
    assert restore_snapshot(second, tmp_path / "snapshot") > 0
    restored = second.one("SELECT * FROM articles WHERE id=?", (aid,))
    assert restored["state"] == "extracted"
    assert restored["text"] == ""
    assert restored["notes"] == "My note"
    assert restored["read_status"] == "Saved"
    second.close()
