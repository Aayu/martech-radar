from __future__ import annotations

import csv
import html
import json
from pathlib import Path

from .ranking import rank
from .store import utcnow


def safe_cell(value):
    value = "" if value is None else str(value)
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def tables(store):
    articles = store.rows("SELECT * FROM articles ORDER BY first_seen DESC")
    by_id = {a["id"]: a for a in articles}
    source_records = store.rows("SELECT * FROM sources ORDER BY id")
    source_configs = {s["id"]: json.loads(s["config"]) for s in source_records}
    source_names = {sid: config["name"] for sid, config in source_configs.items()}
    reviewed = [a for a in articles if a["review_status"] in ("Reviewed", "Imported recommendation")
                and (a["editorial_score"] or 0) >= 14 and a["read_status"] in ("To read", "Saved")
                and not a["duplicate_of"]]
    reviewed.sort(key=lambda a: (a["first_seen"], a["editorial_score"] or 0), reverse=True)
    candidates = [a for a in articles if a["state"] == "extracted" and not a["duplicate_of"]
                  and a["review_status"] == "Unreviewed" and a["read_status"] != "Skip"]
    candidates.sort(key=lambda a: (a["priority"], a["published"] or "", a["first_seen"]), reverse=True)

    # This is a transparent machine shortlist, not an editorial verdict. Re-score
    # from the durable excerpt so ranking improvements apply to prior runs too.
    assessed = []
    for article in candidates:
        assessment = rank(article["title"], article["excerpt"],
                          source_configs.get(article["source_id"], {}),
                          article["published"] or article["modified"])
        signals = set(assessment["signals"])
        evidence_signal = bool(signals & {"Quantified or business outcome", "Failure or counter-evidence",
                                          "Rule, standard or measurement framework"})
        strong = evidence_signal and assessment["priority"] >= 40
        strong = strong or {"Live or scaled implementation", "Concrete mechanism"} <= signals
        strong = strong or {"Strategic platform shift", "Concrete mechanism"} <= signals
        if assessment["priority"] >= 40 and strong:
            assessed.append((article, assessment))
    assessed.sort(key=lambda item: (item[1]["priority"], item[0]["published"] or "",
                                      item[0]["first_seen"]), reverse=True)
    leadership, source_counts = [], {}
    for article, assessment in assessed:
        if source_counts.get(article["source_id"], 0) >= 2:
            continue
        leadership.append((article, assessment))
        source_counts[article["source_id"]] = source_counts.get(article["source_id"], 0) + 1
        if len(leadership) == 5:
            break
    def record(a):
        return [a["id"], a["published"] or "Date unknown", a["source_id"], a["title"], a["url"],
                ", ".join(json.loads(a["tags"])), a["reason"], a["evidence"], a["read_status"],
                a["notes"], a["review_status"], a["editorial_score"],
                by_id.get(a["related_to"], {}).get("url", ""), "\n".join(json.loads(a["original_links"])),
                a["state"], a["error"], a["first_seen"]]
    headers = ["Story ID", "Published", "Source", "Headline", "Link", "Topics", "Why queued", "Evidence",
               "Reading status", "Your notes", "Editorial review", "Editorial score /20", "Related story",
               "Links to investigate", "Collection status", "Collection issue", "First discovered"]
    source_rows = []
    for s in source_records:
        c = json.loads(s["config"])
        source_rows.append([s["id"], c["name"], c["kind"], ", ".join(c["beats"]), c["interval_hours"],
                            "Enabled" if c.get("enabled", True) else "Pending access",
                            s["status"], s["last_success"] or "Never", s["next_due"] or "Initial schedule",
                            s["discovered"], s["detail"] or c.get("disabled_reason", ""), c["endpoints"][0]["url"]])
    run_rows = []
    for r in store.rows("SELECT * FROM runs ORDER BY started DESC LIMIT 60"):
        d = json.loads(r["detail"])
        run_rows.append([r["id"], r["started"], r["status"], d.get("sources_checked", 0), d.get("new_links", 0),
                         d.get("articles_extracted", 0), d.get("queued_articles", 0), d.get("requests", 0),
                         round(d.get("bytes", 0) / 1_000_000, 2), d.get("seconds", 0), d.get("stop_reason") or ""])
    return {
        "Leadership Signals": [["Priority", "Headline", "Source", "Published", "Why read", "Link",
                                "Evidence", "Triage /100", "Story ID", "Topics"],
                               *[[i + 1, a["title"], source_names.get(a["source_id"], a["source_id"]),
                                  a["published"] or "Date unknown",
                                  score["reason"], a["url"], score["evidence"], score["priority"], a["id"],
                                  ", ".join(score["tags"])]
                                 for i, (a, score) in enumerate(leadership)]],
        "Inbox": [["Priority", "Headline", "Source", "Published", "Why read", "Link", "Review", "Score /20", "Story ID"],
                  *[[i + 1, a["title"], a["source_id"], a["published"] or "See original", a["reason"] or a["notes"],
                     a["url"], a["review_status"], a["editorial_score"], a["id"]] for i, a in enumerate(reviewed[:3])]],
        "Candidates": [headers, *[record(a) for a in candidates[:100]]],
        "Library": [headers, *[record(a) for a in articles]],
        "Sources": [["Source ID", "Source", "Type", "Beats", "Check interval (hours)", "Enabled", "Coverage",
                     "Last successful check", "Next due", "New links total", "Issue or detail", "Entry page"], *source_rows],
        "Runs": [["Run ID", "Started UTC", "Status", "Sources checked", "New links", "Articles extracted",
                  "Pending articles", "HTTP requests", "Downloaded MB", "Seconds", "Stop reason"], *run_rows],
    }


def export_all(store, directory):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    result = tables(store)
    pending = store.one("SELECT count(*) AS n FROM articles WHERE state IN ('queued','failed')")["n"]
    payload = {"generated_at": utcnow(), "current_pending": pending, "tables": result}
    (root / "radar.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    for name, rows in result.items():
        with (root / f"{name.lower()}.csv").open("w", newline="", encoding="utf-8") as f:
            csv.writer(f, lineterminator="\n").writerows([[safe_cell(c) for c in row] for row in rows])
    build_html(payload, root / "index.html")
    return payload


def build_html(payload, path):
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
    template = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Martech Radar</title><style>
:root{font-family:system-ui,-apple-system,sans-serif;color:#172a35;background:#f5f4ef}body{max-width:1400px;margin:auto;padding:32px}header{display:flex;align-items:baseline;justify-content:space-between;gap:20px}h1{font-size:32px;letter-spacing:-1px;margin:0}p{line-height:1.55}.sub{color:#53616a;font-size:14px}.tabs{display:flex;flex-wrap:wrap;gap:8px;margin:24px 0}button{font:inherit;border:1px solid #b8c2c4;border-radius:6px;padding:9px 16px;background:white;color:#172a35;cursor:pointer}button.active{background:#172a35;color:white}input,select{font:inherit;padding:11px;border:1px solid #b8c2c4;border-radius:6px;background:white}input{width:min(500px,85%)}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;margin:24px 0}.card{background:white;border:1px solid #d5dcda;padding:22px;border-radius:10px}.card h2{font-size:21px;line-height:1.4}.card a{color:#165b62;text-decoration:none}.label{font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#626d72}.tablewrap{overflow:auto;margin-top:20px;border:1px solid #d5dcda;background:white;border-radius:8px;max-height:65vh}table{border-collapse:collapse;width:100%;font-size:13px}th{position:sticky;top:0;text-align:left;background:#233d48;color:white;padding:12px;white-space:nowrap}td{padding:11px;border-bottom:1px solid #e5e7e4;vertical-align:top;min-width:100px;max-width:370px;overflow-wrap:anywhere}td:nth-child(4){min-width:300px}a{color:#165b62}.notice{background:#fff4d9;border-left:3px solid #b6872e;padding:12px 16px;border-radius:3px}.hidden{display:none}@media(max-width:600px){body{padding:18px}header{display:block}.cards{grid-template-columns:1fr}h1{font-size:28px}}
</style></head><body><header><h1>Martech Radar</h1><span class="sub" id="updated"></span></header>
<p class="sub">FMCG · Consumer digital · Commerce</p><nav class="tabs" id="tabs"></nav>
<p id="context"></p><div id="notice"></div><div class="cards" id="cards"></div>
<input id="search" aria-label="Search radar" placeholder="Search companies, topics or headlines"><span class="sub" id="count"></span>
<div class="tablewrap"><table><thead id="head"></thead><tbody id="body"></tbody></table></div>
<p class="sub">This is a saved reading view. Reading status and notes can be edited in the connected spreadsheet. Sources shows checks that failed or need attention.</p>
<script type="application/json" id="data">__DATA__</script><script>
const data=JSON.parse(document.getElementById('data').textContent);let tab='Leadership Signals';
const el=id=>document.getElementById(id);el('updated').textContent='Updated '+new Date(data.generated_at).toLocaleString('en-IN',{timeZone:'Asia/Kolkata'})+' IST';
const contexts={'Leadership Signals':'Up to five new items with implementation, outcome, failure or standards evidence. This is a machine shortlist for human review, not a publishing recommendation.',Inbox:'Your three reviewed reading priorities. Imported recommendations retain their original assessment.',Candidates:'New articles awaiting evidence review. Their order is provisional; they have not been given a verified editorial score.',Library:'All collected and previously evaluated stories, including pending articles and duplicates.',Sources:'Source-by-source coverage. Partial coverage means the archive interval could not be verified.',Runs:'Collection history, pending work and measured resource use.'};
function cell(value){const t=document.createElement('td');const s=String(value??'');if(/^https?:\\/\\/[^\\s]+$/.test(s)){const a=document.createElement('a');a.href=s;a.textContent='Open source';a.target='_blank';a.rel='noopener noreferrer';t.append(a);}else t.textContent=s;return t;}
function draw(){el('tabs').replaceChildren();for(const name of Object.keys(data.tables)){const b=document.createElement('button');b.textContent=name;b.className=tab===name?'active':'';b.onclick=()=>{tab=name;el('search').value='';draw()};el('tabs').append(b);}el('context').textContent=contexts[tab];const latest=data.tables.Runs[1],pending=data.current_pending??(latest?latest[6]:0);el('notice').className=pending?'notice':'hidden';el('notice').textContent=latest?'Latest run: '+latest[2]+'. '+pending+' articles are currently waiting for extraction. Check Sources for collection gaps.':'';const rows=data.tables[tab],q=el('search').value.toLowerCase();el('head').replaceChildren();const hr=document.createElement('tr');rows[0].forEach(v=>{const th=document.createElement('th');th.textContent=v;hr.append(th)});el('head').append(hr);el('body').replaceChildren();const filtered=rows.slice(1).filter(r=>r.join(' ').toLowerCase().includes(q));filtered.forEach(r=>{const tr=document.createElement('tr');r.forEach(v=>tr.append(cell(v)));el('body').append(tr)});el('count').textContent=' '+filtered.length+' records';el('cards').replaceChildren();if(tab==='Inbox'||tab==='Leadership Signals'){filtered.forEach(r=>{const c=document.createElement('article');c.className='card';const l=document.createElement('span');l.className='label';l.textContent=(tab==='Inbox'?'Read ':'Signal ')+r[0]+' · '+r[2]+(tab==='Leadership Signals'?' · '+r[7]+'/100':'');const h=document.createElement('h2'),a=document.createElement('a');a.href=r[5];a.textContent=r[1];a.target='_blank';a.rel='noopener noreferrer';h.append(a);const p=document.createElement('p');p.textContent=r[4];c.append(l,h,p);el('cards').append(c)});}}
el('search').oninput=draw;draw();</script></body></html>'''
    path.write_text(template.replace("__DATA__", data))

