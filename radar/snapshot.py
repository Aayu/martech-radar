from __future__ import annotations

import json
from pathlib import Path


TABLES = ("sources", "articles", "sightings", "legacy", "runs", "checks")
ORDER = {
    "sources": "id",
    "articles": "id",
    "sightings": "article_id,source_id",
    "legacy": "story_key",
    "runs": "started,id",
    "checks": "checked,run_id,source_id",
}


def _columns(store, table):
    columns = [r["name"] for r in store.rows(f"PRAGMA table_info({table})")]
    # Full article bodies and fetch caches are transient. Hashes, excerpts,
    # decisions and notes are sufficient for durable deduplication and reading.
    return [c for c in columns if not (table == "articles" and c == "text")]


def export_snapshot(store, directory):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    manifest = {"version": 1, "tables": {}}
    for table in TABLES:
        columns = _columns(store, table)
        query = f"SELECT {','.join(columns)} FROM {table} ORDER BY {ORDER[table]}"
        rows = store.rows(query)
        target = root / f"{table}.jsonl"
        temporary = root / f".{table}.jsonl.tmp"
        temporary.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))
        temporary.replace(target)
        manifest["tables"][table] = {"rows": len(rows), "columns": columns}
    temporary = root / ".manifest.json.tmp"
    temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    temporary.replace(root / "manifest.json")
    return manifest


def restore_snapshot(store, directory):
    root = Path(directory)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        return 0
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("version") != 1:
        raise ValueError("Unsupported snapshot version")
    restored = 0
    with store.db:
        for table in TABLES:
            source = root / f"{table}.jsonl"
            if not source.exists():
                continue
            for line in source.read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                columns = list(row)
                placeholders = ",".join("?" for _ in columns)
                store.db.execute(
                    f"INSERT OR REPLACE INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                    [row[c] for c in columns],
                )
                restored += 1
    return restored
