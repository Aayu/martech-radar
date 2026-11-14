import argparse
import json
from pathlib import Path

from .engine import run
from .export import export_all
from .network import Fetcher
from .snapshot import export_snapshot, restore_snapshot
from .store import Store, canonical_url


def main():
    parser = argparse.ArgumentParser(description="Martech Radar — no paid services")
    parser.add_argument("command", choices=["run", "export", "status", "review"])
    parser.add_argument("--config", default="config/sources.json")
    parser.add_argument("--db", default="state/radar.sqlite")
    parser.add_argument("--output", default="outputs/collector")
    parser.add_argument("--legacy", default="work/radar-seen.jsonl")
    parser.add_argument("--snapshot", default="state/snapshot")
    parser.add_argument("--source", action="append")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--max-sources", type=int, default=14)
    parser.add_argument("--max-articles", type=int, default=24)
    parser.add_argument("--max-requests", type=int, default=180)
    parser.add_argument("--max-seconds", type=int, default=540)
    parser.add_argument("--id")
    parser.add_argument("--reading-status", choices=["To read", "Read", "Saved", "Skip"])
    parser.add_argument("--notes")
    parser.add_argument("--queue", action="store_true", help="promote a retained title to the full-text queue")
    parser.add_argument("--evidence-file", help="JSON with score dimensions, mechanism, evidence_url, outcome and caveat")
    args = parser.parse_args()
    store = Store(args.db)
    if not store.one("SELECT 1 AS present FROM articles LIMIT 1"):
        restored = restore_snapshot(store, args.snapshot)
        if restored:
            print(f"Restored {restored} durable state records", flush=True)
    configs = json.loads(Path(args.config).read_text())["sources"]
    store.register(configs)
    imported = store.import_legacy(args.legacy)
    seed = Path("config/reading-seed.json")
    if seed.exists():
        for item in json.loads(seed.read_text()):
            store.execute("UPDATE articles SET title=?,reason=?,review_status='Imported recommendation' WHERE url=? AND state='legacy' AND review_status='Unreviewed'",
                          (item["title"], item["reason"], canonical_url(item["url"])))
    if args.command == "run":
        # A local lock also prevents two manual invocations corrupting run semantics.
        import fcntl
        lock = open(str(Path(args.db).with_suffix(".lock")), "w")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Another collector is running")
        fetcher = Fetcher(store, args.max_requests, args.max_seconds)
        try:
            report = run(store, configs, fetcher, args.max_sources, args.max_articles, args.force, args.source)
            print(json.dumps(report, indent=2))
        finally:
            fetcher.close()
            lock.close()
        export_all(store, args.output)
        export_snapshot(store, args.snapshot)
    elif args.command == "export":
        export_all(store, args.output)
        export_snapshot(store, args.snapshot)
        print(f"Exported to {args.output}; imported {imported} legacy records")
    elif args.command == "status":
        print(json.dumps(store.rows("SELECT id,status,last_success,detail FROM sources"), indent=2))
    else:
        if not args.id or not store.one("SELECT id FROM articles WHERE id=?", (args.id,)):
            parser.error("review requires an existing --id")
        if args.reading_status:
            store.execute("UPDATE articles SET read_status=? WHERE id=?", (args.reading_status, args.id))
        if args.notes is not None:
            store.execute("UPDATE articles SET notes=? WHERE id=?", (args.notes, args.id))
        if args.queue:
            store.execute("UPDATE articles SET state='queued',retry_after=NULL,error='' WHERE id=? AND state='title_only'", (args.id,))
        if args.evidence_file:
            evidence = json.loads(Path(args.evidence_file).read_text())
            dimensions = [evidence.get(k) for k in ("relevance", "evidence", "novelty", "learning")]
            if any(type(v) is not int or not 0 <= v <= 5 for v in dimensions):
                parser.error("Each of relevance/evidence/novelty/learning must be an integer 0–5")
            if any(not evidence.get(k) for k in ("mechanism", "evidence_url", "outcome", "caveat")):
                parser.error("Review needs mechanism, evidence_url, outcome and caveat")
            canonical_url(evidence["evidence_url"])
            store.execute("UPDATE articles SET review_status='Reviewed',editorial_score=?,review_details=? WHERE id=?",
                          (sum(dimensions), json.dumps(evidence), args.id))
        export_all(store, args.output)
        export_snapshot(store, args.snapshot)
    store.close()


if __name__ == "__main__":
    main()

