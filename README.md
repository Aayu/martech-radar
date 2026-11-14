# Martech Radar

Martech Radar is a no-paid-services research collector for FMCG, consumer digital and digital commerce. It checks a governed source list, retains a durable queue, removes exact duplicates, extracts readable article text, and publishes a small reading inbox plus a searchable browser view.

The collector does not assign the 20-point editorial score automatically. Its priority is a provisional triage signal. An article reaches the three-item Inbox only after a human verifies the mechanism, original evidence, outcome and caveat, then scores relevance, evidence, novelty and learning value.

## What it covers

The source registry has 53 named sources. Twenty-nine passed the initial server probe and are enabled. The others remain visible as `Pending access`, with the exact reason: publisher robots rules, a blocked server request, a client-rendered index, or a PDF-only newsroom. This avoids treating a failed check as successful coverage.

Every run considers three standing beats:

- major FMCG and CPG companies and their marketing or commerce technology;
- Fortune-scale companies outside FMCG and their customer technology;
- campaigns whose data, technology and touchpoints form a connected consumer journey.

Regulation, measurement, commerce platforms, case libraries and practitioner signals provide additional coverage. Company newsrooms rotate weekly; publishers and regulators run every one to three days according to the source registry.

## What is produced

- `outputs/collector/index.html`: searchable browser view with Inbox, Candidates, Library, Sources and Runs;
- `outputs/collector/*.csv`: spreadsheet-friendly exports of those views;
- `outputs/collector/radar.json`: the same output as structured data;
- `state/snapshot/`: text-based durable state for deduplication, source checkpoints, reading status and notes;
- `outputs/collector/Martech Radar.xlsx`: the verified local Excel reader created during setup. It is intentionally ignored by Git because the hosted run publishes the live HTML and CSV views.

The browser view is read-only. Reading status and notes can be updated with the `review` command or, after a Google Sheets connection is explicitly approved, through a synced spreadsheet workflow.

## Run locally

Python 3.12 is used in the hosted workflow.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m radar run
```

The collector obeys publisher robots rules, sends an identifying user agent, limits request rate and page size, validates redirects, refuses private network addresses, and retains failed work for retry. A default run stops after 14 due sources, 24 article extractions, 180 requests or nine minutes.

During discovery, every URL is retained. Up to eight new items per source enter the full-text queue in one run, including two low-signal audit samples. Additional headlines remain in the Library as `title_only`; this prevents a large newsroom or sitemap from crowding out other beats without deleting the lead.

## Host on GitHub

Use a separate repository such as `Aayu/martech-radar`. This keeps the radar independent of `Aayu/job-kit`, whose daily job already starts at 05:47 IST.

1. Create the new repository and push this folder to its `main` branch.
2. In **Settings → Actions → General**, allow workflows to read and write repository contents.
3. Open **Actions → Daily Martech Radar → Run workflow** for the first controlled run.
4. Check the run summary, the `Sources` view and the committed `state/snapshot` changes.
5. In **Settings → Pages**, choose **GitHub Actions** as the publishing source. The daily workflow publishes the generated dashboard after every collection run, so day-to-day use requires only one bookmarked link and no downloads.

The expected dashboard address is `https://aayu.github.io/martech-radar/`. GitHub Pages is available for public repositories on GitHub Free; private-repository availability depends on the account plan. Publishing the dashboard makes its contents publicly accessible even when the source repository is private, so repository visibility must never be changed implicitly.

The schedule targets 08:00 IST (`02:30 UTC`). GitHub schedules can start late during busy periods, so 08:00 is a target rather than a delivery guarantee. The workflow has a 15-minute ceiling and also uploads the current reading files as a 14-day downloadable artifact.

Keep the existing ChatGPT radar automation active until the first hosted run completes and the dashboard contains the expected three-item Inbox. It can then be retired without losing the prior 120-story deduplication ledger, which has already been migrated into the text snapshot.

## Review an article

Reading status and notes use the stable Story ID shown in the exports.

```bash
.venv/bin/python -m radar review --id STORY_ID --reading-status Saved --notes "Your note"
```

A promising `title_only` item can be promoted for full-text extraction:

```bash
.venv/bin/python -m radar review --id STORY_ID --queue
```

For editorial scoring, provide a JSON file containing integer scores from 0 to 5 for `relevance`, `evidence`, `novelty` and `learning`, plus non-empty `mechanism`, `evidence_url`, `outcome` and `caveat` fields.

```bash
.venv/bin/python -m radar review --id STORY_ID --evidence-file review.json
```

Only reviewed items scoring at least 14/20 are eligible for the Inbox. No post, article or newsletter draft is created or published automatically.
