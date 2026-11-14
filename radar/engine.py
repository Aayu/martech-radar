from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from urllib.parse import urljoin, urlsplit

import trafilatura
from bs4 import BeautifulSoup

from .discovery import parse_feed, parse_json_index, parse_listing, parse_sitemap
from .network import FetchError, BudgetExceeded
from .ranking import rank, normalize
from .store import utcnow, canonical_url


def due(source, state, now):
    if not source.get("enabled", True):
        return False
    if state.get("next_due"):
        return state["next_due"] <= now.isoformat()
    return source.get("weekday", now.weekday()) == now.weekday()


def collect_source(store, fetcher, source, now, run_id):
    sid = source["id"]
    previous = store.one("SELECT * FROM sources WHERE id=?", (sid,))
    timestamp = now.isoformat()
    store.execute("UPDATE sources SET last_attempt=? WHERE id=?", (timestamp, sid))
    discovered, errors, dates, successful_pages = 0, [], [], 0
    queued_new, retained_titles = 0, 0
    checkpoint = previous["checkpoint"]
    horizon = checkpoint or (now - timedelta(days=source.get("lookback_days", 14))).isoformat()
    covered = False
    visited = set()
    sampled_low_signal = 0
    try:
        for endpoint in source["endpoints"]:
            url = endpoint["url"]
            endpoint_ok = False
            for page in range(source.get("max_pages", 3)):
                if url in visited:
                    break
                visited.add(url)
                try:
                    text, _, resolved = fetcher.get(url, cache=True)
                    if endpoint["type"] == "feed":
                        entries, nxt = parse_feed(text, resolved)
                    elif endpoint["type"] == "sitemap":
                        entries, nxt = parse_sitemap(text, resolved, source)
                    elif endpoint["type"] == "json":
                        entries, nxt = parse_json_index(text, resolved, source)
                    else:
                        entries, nxt = parse_listing(text, resolved, source)
                except BudgetExceeded:
                    raise
                except (FetchError, ValueError) as exc:
                    errors.append(str(exc))
                    break
                successful_pages += 1
                endpoint_ok = True
                for entry in entries:
                    # Keep older discoveries for traceability without spending the
                    # extraction budget on articles outside this source's window.
                    effective_date = entry.get("published") or entry.get("modified")
                    outside_window = bool(effective_date and effective_date < horizon)
                    low_signal = rank(entry.get("title", ""), "", source,
                                      entry.get("published") or entry.get("modified"), now)["priority"] == 0
                    if outside_window:
                        entry = {**entry, "state": "outside_window"}
                    aid, is_new = store.add_article(sid, entry, timestamp)
                    if is_new and not outside_window:
                        queue_limit = source.get("queue_limit", 8)
                        low_limit = source.get("low_signal_samples", 2)
                        if queued_new >= queue_limit:
                            retained_titles += 1
                            store.execute("UPDATE articles SET state='title_only',reason='Title retained after per-run source cap' WHERE id=?", (aid,))
                        elif low_signal and sampled_low_signal >= low_limit:
                            retained_titles += 1
                            store.execute("UPDATE articles SET state='title_only',reason='Title retained; no target signal found' WHERE id=?", (aid,))
                        else:
                            queued_new += 1
                            if low_signal:
                                sampled_low_signal += 1
                    discovered += int(is_new)
                    if effective_date:
                        dates.append(effective_date)
                if dates and min(dates) <= horizon:
                    covered = True
                    break
                if not nxt:
                    break
                # Pagination is kept on the configured host; outward citations are handled separately.
                if urlsplit(nxt).hostname != urlsplit(resolved).hostname:
                    errors.append("Pagination left source domain; review needed")
                    break
                url = nxt
            if endpoint_ok and covered:
                break
        if not successful_pages:
            raise FetchError("; ".join(errors) or "No source page succeeded")
        # Bootstrap establishes a starting point but explicitly reports unverified earlier coverage.
        status = "Checked" if covered else "Partial coverage"
        detail = (f"{successful_pages} pages; {discovered} new links; {queued_new} queued for full text; "
                  f"{retained_titles} retained title-only. " +
                  ("Dated archive reaches prior checkpoint." if covered else
                   "Archive continuity not verified; older/missing entries need the weekly audit."))
        if errors:
            detail += " Fallback notes: " + "; ".join(errors)
        next_due = (now + timedelta(hours=source["interval_hours"])).isoformat()
        new_checkpoint = timestamp if covered or not checkpoint else checkpoint
        store.execute("UPDATE sources SET last_success=?,checkpoint=?,next_due=?,status=?,detail=?,discovered=discovered+?,consecutive_failures=0 WHERE id=?",
                      (timestamp, new_checkpoint, next_due, status, detail, discovered, sid))
    except FetchError as exc:
        status = "Deferred" if isinstance(exc, BudgetExceeded) else "Failed"
        detail = str(exc)
        retry_hours = 6 if status == "Deferred" else min(72, 6 * 2 ** min(previous["consecutive_failures"], 4))
        store.execute("UPDATE sources SET status=?,detail=?,next_due=?,consecutive_failures=consecutive_failures+1 WHERE id=?",
                      (status, detail, (now + timedelta(hours=retry_hours)).isoformat(), sid))
        if isinstance(exc, BudgetExceeded):
            store.execute("INSERT INTO checks VALUES(?,?,?,?,?,?)", (run_id, sid, timestamp, status, detail, discovered))
            raise
    store.execute("INSERT INTO checks VALUES(?,?,?,?,?,?)", (run_id, sid, timestamp, status, detail, discovered))
    return status, discovered


def extract_article(store, fetcher, article, source, now):
    aid = article["id"]
    try:
        raw, _, resolved = fetcher.get(article["url"])
        soup = BeautifulSoup(raw, "html.parser")
        data = json.loads(trafilatura.extract(raw, url=resolved, output_format="json", with_metadata=True,
                                             include_comments=False, include_tables=True, favor_recall=True) or "{}")
        text = data.get("text", "")
        if len(text.split()) < 80:
            raise FetchError("Insufficient article text; access or extraction needs review")
        if any(s in normalize(text[:800]) for s in ("verify you are human", "enable javascript and cookies", "access denied")):
            raise FetchError("Access challenge returned instead of article")
        title = data.get("title") or article["title"]
        canon = soup.select_one('link[rel="canonical"]')
        canonical_hint = canonical_url(urljoin(resolved, canon["href"])) if canon and canon.get("href") else canonical_url(resolved)
        fingerprint = hashlib.sha256(re.sub(r"\s+", " ", normalize(text)).encode()).hexdigest()
        duplicate = store.one("SELECT id FROM articles WHERE content_hash=? AND id!=? ORDER BY first_seen LIMIT 1", (fingerprint, aid))
        if not duplicate:
            duplicate = store.one("SELECT id FROM articles WHERE (url=? OR canonical_hint=?) AND id!=? ORDER BY first_seen LIMIT 1",
                                  (canonical_hint, canonical_hint, aid))
        related = None
        # Similar titles only flag a review. They never silently delete a possible substantive update.
        for other in store.rows("SELECT id,title FROM articles WHERE id!=? AND (state IN ('extracted','legacy')) ORDER BY first_seen DESC LIMIT 1500", (aid,)):
            if SequenceMatcher(None, normalize(title), normalize(other["title"])).ratio() >= .86:
                related = other["id"]
                break
        ranked = rank(title, text[:30000], source, published, now)
        links = []
        container = soup.find("article") or soup.find("main") or soup
        for a in container.select("a[href]"):
            try:
                url = canonical_url(urljoin(resolved, a["href"]))
            except ValueError:
                continue
            if urlsplit(url).hostname != urlsplit(resolved).hostname and len(a.get_text(" ", strip=True)) > 3:
                if urlsplit(url).hostname not in {"www.facebook.com", "twitter.com", "x.com", "www.linkedin.com"}:
                    links.append(url)
        published = article["published"] or data.get("date")
        future = bool(published and published[:10] > now.date().isoformat())
        error = "Source publication date is in the future; verify before recommending" if future else ""
        store.db.execute("INSERT OR IGNORE INTO revisions VALUES(?,?,?,?)", (aid, now.isoformat(), fingerprint, text[:200000]))
        store.db.execute("""UPDATE articles SET title=?,published=?,state='extracted',attempts=attempts+1,
          retry_after=NULL,text=?,excerpt=?,content_hash=?,canonical_hint=?,tags=?,companies=?,beats=?,
          priority=?,reason=?,evidence=?,duplicate_of=?,related_to=?,original_links=?,error=? WHERE id=?""",
          (title, published, text[:200000], " ".join(text.split()[:120]), fingerprint, canonical_hint,
           json.dumps(ranked["tags"]), json.dumps(ranked["companies"]), json.dumps(ranked["beats"]),
           ranked["priority"], ranked["reason"], ranked["evidence"], duplicate["id"] if duplicate else None,
           related, json.dumps(list(dict.fromkeys(links))[:15]), error, aid))
        store.db.commit()
        return True
    except BudgetExceeded:
        raise
    except (FetchError, ValueError) as exc:
        delay = min(168, 6 * 2 ** min(article["attempts"], 5))
        store.execute("UPDATE articles SET state='failed',attempts=attempts+1,retry_after=?,error=? WHERE id=?",
                      ((now + timedelta(hours=delay)).isoformat(), str(exc), aid))
        return False


def run(store, configs, fetcher, max_sources=14, max_articles=24, force=False, source_ids=None, now=None):
    now = now or datetime.now(timezone.utc)
    store.register(configs)
    run_id = now.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]
    store.execute("INSERT INTO runs(id,started) VALUES(?,?)", (run_id, now.isoformat()))
    begin = time.monotonic()
    summary = {"sources_checked": 0, "new_links": 0, "articles_extracted": 0, "article_failures": 0}
    stopped = None
    sources = {s["id"]: s for s in configs}
    states = {s["id"]: s for s in store.rows("SELECT * FROM sources")}
    eligible = [s for s in configs if s.get("enabled", True) and (not source_ids or s["id"] in source_ids)
                and (force or due(s, states[s["id"]], now))]
    # Oldest attempted sources first prevents a broken or busy publisher starving the rotation.
    eligible.sort(key=lambda s: (states[s["id"]]["last_attempt"] or "", s.get("priority", 5), s["id"]))
    try:
        for source in eligible[:max_sources]:
            print(f"Checking {source['name']}", flush=True)
            _, count = collect_source(store, fetcher, source, now, run_id)
            summary["sources_checked"] += 1
            summary["new_links"] += count
        queue = store.rows("SELECT * FROM articles WHERE state IN ('queued','failed') AND (retry_after IS NULL OR retry_after<=?) ORDER BY attempts,first_seen DESC", (now.isoformat(),))
        if source_ids:
            queue = [a for a in queue if a["source_id"] in source_ids]
        # Title triage only orders work; even zero-point articles stay in the durable queue.
        queue.sort(key=lambda a: (a["attempts"], -rank(a["title"], "", sources.get(a["source_id"], {}),
                                                       a.get("published") or a.get("modified"), now)["priority"]))
        for article in queue[:max_articles]:
            print(f"Reading {article['title'][:90]}", flush=True)
            ok = extract_article(store, fetcher, article, sources.get(article["source_id"], {}), now)
            summary["articles_extracted" if ok else "article_failures"] += 1
    except BudgetExceeded as exc:
        stopped = str(exc)
    except Exception:
        store.execute("UPDATE runs SET finished=?,status='Failed',detail=? WHERE id=?",
                      (utcnow(), json.dumps({**summary, "error": "Unexpected error; inspect local log"}), run_id))
        raise
    summary.update({"requests": fetcher.requests, "bytes": fetcher.bytes, "cache_hits": fetcher.cache_hits,
                    "seconds": round(time.monotonic() - begin, 2), "deferred_sources": max(0, len(eligible) - summary["sources_checked"]),
                    "queued_articles": store.one("SELECT count(*) AS n FROM articles WHERE state IN ('queued','failed')")["n"],
                    "stop_reason": stopped})
    failures = store.one("SELECT count(*) AS n FROM checks WHERE run_id=? AND status!='Checked'", (run_id,))["n"]
    status = "Complete" if not (failures or stopped or summary["queued_articles"] or summary["deferred_sources"]) else "Partial"
    store.execute("UPDATE runs SET finished=?,status=?,detail=? WHERE id=?", (utcnow(), status, json.dumps(summary), run_id))
    return {"run_id": run_id, "status": status, **summary}

