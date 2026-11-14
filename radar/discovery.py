from __future__ import annotations

import calendar
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit

import feedparser
from bs4 import BeautifulSoup

from .store import canonical_url


def iso_date(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError):
        return None


def feed_date(entry, field):
    parsed = entry.get(field + "_parsed")
    return datetime.fromtimestamp(calendar.timegm(parsed), timezone.utc).isoformat() if parsed else None


def parse_feed(text, base):
    feed = feedparser.parse(text)
    if not feed.entries:
        raise ValueError("No feed entries found")
    entries = []
    for entry in feed.entries:
        if not entry.get("link"):
            continue
        try:
            url = canonical_url(urljoin(base, entry.link))
        except ValueError:
            continue
        entries.append({"url": url, "title": BeautifulSoup(entry.get("title", ""), "html.parser").get_text(" ", strip=True),
                        "published": feed_date(entry, "published"), "modified": feed_date(entry, "updated")})
    nxt = next((urljoin(base, link.href) for link in feed.feed.get("links", [])
                if link.get("rel") == "next"), None)
    return entries, nxt


def parse_sitemap(text, base, source):
    """Read a configured URL sitemap. Sitemap indexes must be expanded in config.

    Using explicit child sitemaps keeps the collector bounded and avoids walking a
    publisher's unrelated site sections.
    """
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ValueError("Invalid sitemap XML") from exc
    if root.tag.rsplit("}", 1)[-1] == "sitemapindex":
        raise ValueError("Sitemap index needs explicit child sitemap endpoints")
    entries = []
    hosts = source.get("hosts", [urlsplit(base).hostname])
    for node in root.findall(".//{*}url"):
        loc = node.find("{*}loc")
        if loc is None or not loc.text:
            continue
        try:
            url = canonical_url(urljoin(base, loc.text.strip()))
        except ValueError:
            continue
        parsed = urlsplit(url)
        if parsed.hostname not in hosts:
            continue
        if source.get("include") and not re.search(source["include"], parsed.path):
            continue
        if re.search(source.get("exclude", r"$^"), url):
            continue
        lastmod = node.find("{*}lastmod")
        slug = parsed.path.rstrip("/").rsplit("/", 1)[-1]
        title = re.sub(r"[-_]", " ", slug).strip().title() or url
        if source.get("title_include") and not re.search(source["title_include"], title, re.I):
            continue
        entries.append({"url": url, "title": title, "published": None,
                        "modified": iso_date(lastmod.text if lastmod is not None else None)})
    if not entries:
        raise ValueError("No article links extracted from sitemap")
    entries.sort(key=lambda item: (item.get("modified") or "", item["title"]), reverse=True)
    return entries[:source.get("max_entries", len(entries))], None


def parse_listing(text, base, source):
    soup = BeautifulSoup(text, "html.parser")
    entries = {}
    # Structured article data gives dates even when the visible listing omits them.
    def visit(obj):
        if isinstance(obj, list):
            for child in obj:
                visit(child)
        elif isinstance(obj, dict):
            kind = obj.get("@type", "")
            if kind in ("NewsArticle", "Article", "BlogPosting") and obj.get("url"):
                try:
                    url = canonical_url(urljoin(base, obj["url"]))
                    entries[url] = {"url": url, "title": obj.get("headline", ""),
                                    "published": iso_date(obj.get("datePublished")),
                                    "modified": iso_date(obj.get("dateModified"))}
                except (ValueError, TypeError):
                    pass
            for value in obj.values():
                if isinstance(value, (list, dict)):
                    visit(value)
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            visit(json.loads(script.get_text()))
        except (ValueError, TypeError):
            pass
    hosts = source.get("hosts", [urlsplit(base).hostname])
    for a in soup.select(source.get("selector", "main a[href], article a[href], h2 a[href], h3 a[href]")):
        title = a.get_text(" ", strip=True)
        if len(title.split()) < 5 or len(title) > 350:
            continue
        try:
            url = canonical_url(urljoin(base, a.get("href", "")))
        except ValueError:
            continue
        parsed = urlsplit(url)
        if parsed.hostname not in hosts or url == canonical_url(base):
            continue
        if re.search(r"\.(pdf|docx?|xlsx?|pptx?|zip)(?:$|\?)", url, re.I):
            continue
        if re.search(source.get("exclude", r"/(tag|category|author|topic|about|contact|subscribe|events|privacy|login|search)(/|\?|$)"), url):
            continue
        if source.get("include") and not re.search(source["include"], parsed.path):
            continue
        parent = a.find_parent("article") or a.parent
        time_tag = parent.find("time") if parent else None
        date = iso_date(time_tag.get("datetime")) if time_tag else None
        entries.setdefault(url, {"url": url, "title": title, "published": date, "modified": None})
    nxt = soup.select_one('a[rel="next"]')
    if not nxt:
        nxt = next((a for a in soup.find_all("a", href=True)
                    if a.get_text(" ", strip=True).lower() in ("next", "next page", "older posts", "older")), None)
    if not entries:
        raise ValueError("No article links extracted; selector or access needs attention")
    return list(entries.values())[:source.get("max_entries", len(entries))], urljoin(base, nxt["href"]) if nxt else None

