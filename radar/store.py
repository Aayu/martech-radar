from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_url(url):
    p = urlsplit(url.strip())
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
        raise ValueError("Not a public HTTP URL")
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in
             {"gclid", "fbclid", "msclkid", "mc_cid", "mc_eid"}]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/",
                       urlencode(sorted(query)), ""))


def stable_id(url):
    return hashlib.sha256(canonical_url(url).encode()).hexdigest()[:24]


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sources (
 id TEXT PRIMARY KEY, config TEXT NOT NULL, last_attempt TEXT, last_success TEXT,
 checkpoint TEXT, next_due TEXT, status TEXT DEFAULT 'Not yet checked', detail TEXT DEFAULT '',
 discovered INTEGER DEFAULT 0, consecutive_failures INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS articles (
 id TEXT PRIMARY KEY, url TEXT UNIQUE NOT NULL, source_id TEXT NOT NULL, title TEXT NOT NULL,
 published TEXT, modified TEXT, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
 state TEXT DEFAULT 'queued', attempts INTEGER DEFAULT 0, retry_after TEXT,
 text TEXT DEFAULT '', excerpt TEXT DEFAULT '', content_hash TEXT, canonical_hint TEXT,
 tags TEXT DEFAULT '[]', companies TEXT DEFAULT '[]', beats TEXT DEFAULT '[]',
 priority INTEGER DEFAULT 0, reason TEXT DEFAULT '', evidence TEXT DEFAULT 'Unreviewed',
 duplicate_of TEXT, related_to TEXT, original_links TEXT DEFAULT '[]', error TEXT DEFAULT '',
 read_status TEXT DEFAULT 'To read', notes TEXT DEFAULT '', editorial_score INTEGER,
 review_status TEXT DEFAULT 'Unreviewed', review_details TEXT DEFAULT '{}',
 legacy_key TEXT, legacy_disposition TEXT, brief TEXT
);
CREATE TABLE IF NOT EXISTS sightings (
 article_id TEXT NOT NULL REFERENCES articles(id), source_id TEXT NOT NULL,
 first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, PRIMARY KEY(article_id,source_id)
);
CREATE TABLE IF NOT EXISTS legacy (
 story_key TEXT PRIMARY KEY, payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cache (
 url TEXT PRIMARY KEY, etag TEXT, modified TEXT, body BLOB NOT NULL,
 content_type TEXT, fetched TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS revisions (
 article_id TEXT NOT NULL, recorded TEXT NOT NULL, content_hash TEXT NOT NULL,
 text TEXT NOT NULL, PRIMARY KEY(article_id,content_hash)
);
CREATE TABLE IF NOT EXISTS runs (
 id TEXT PRIMARY KEY, started TEXT NOT NULL, finished TEXT, status TEXT DEFAULT 'Running',
 detail TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS checks (
 run_id TEXT NOT NULL, source_id TEXT NOT NULL, checked TEXT NOT NULL,
 status TEXT NOT NULL, detail TEXT NOT NULL, discovered INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS article_queue ON articles(state,retry_after,priority DESC);
"""


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def rows(self, sql, params=()):
        return [dict(r) for r in self.db.execute(sql, params)]

    def one(self, sql, params=()):
        r = self.db.execute(sql, params).fetchone()
        return dict(r) if r else None

    def execute(self, sql, params=()):
        result = self.db.execute(sql, params)
        self.db.commit()
        return result

    def register(self, configs):
        for source in configs:
            self.db.execute("INSERT INTO sources(id,config) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET config=excluded.config",
                            (source["id"], json.dumps(source)))
        self.db.commit()

    def add_article(self, source_id, entry, now=None):
        now = now or utcnow()
        url = canonical_url(entry["url"])
        aid = stable_id(url)
        existing = self.one("SELECT * FROM articles WHERE url=?", (url,))
        if existing:
            # New publisher dates do not overwrite the original publication date.
            updated = entry.get("modified")
            requeue = bool(updated and updated != existing["modified"] and existing["state"] == "extracted")
            self.db.execute("UPDATE articles SET last_seen=?, modified=COALESCE(?,modified), state=? WHERE id=?",
                            (now, updated, "queued" if requeue else existing["state"], aid))
        else:
            self.db.execute("INSERT INTO articles(id,url,source_id,title,published,modified,first_seen,last_seen,state) VALUES(?,?,?,?,?,?,?,?,?)",
                            (aid, url, source_id, entry.get("title") or url, entry.get("published"),
                             entry.get("modified"), now, now, entry.get("state", "queued")))
        self.db.execute("INSERT INTO sightings VALUES(?,?,?,?) ON CONFLICT(article_id,source_id) DO UPDATE SET last_seen=excluded.last_seen",
                        (aid, source_id, now, now))
        self.db.commit()
        return aid, existing is None

    def import_legacy(self, path):
        count = 0
        if not Path(path).exists():
            return 0
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            key = item["story_key"]
            if self.one("SELECT story_key FROM legacy WHERE story_key=?", (key,)):
                continue
            self.db.execute("INSERT INTO legacy VALUES(?,?)", (key, json.dumps(item)))
            if item.get("url"):
                aid, _ = self.add_article("legacy", {"url": item["url"], "title": key.replace("-", " ")},
                                          item.get("first_seen", utcnow())[:10] + "T00:00:00+00:00")
                self.db.execute("UPDATE articles SET state='legacy',legacy_key=?,legacy_disposition=?,brief=?,editorial_score=? WHERE id=?",
                                (key, item.get("disposition"), item.get("brief"), item.get("score"), aid))
            count += 1
        self.db.commit()
        return count

    def backup(self, destination):
        target = sqlite3.connect(str(destination))
        self.db.backup(target)
        target.close()

    def close(self):
        self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        self.db.close()

